#!/usr/bin/env python3
"""Materialize a frozen run repository from a capsule test_repo.

This tool never starts an agent. It only validates and copies the workspace.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from eval_common import file_sha256, load_json, tree_sha256, validate_workspace


def ignore_direct(_directory: str, names: list[str]) -> set[str]:
    return {".ai-workflow"} if ".ai-workflow" in names else set()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_root", type=Path)
    parser.add_argument("dest", type=Path, nargs="?", help="workspace destination")
    parser.add_argument("--condition", choices=("DIRECT", "AI_NATIVE"), required=True)
    parser.add_argument("--run-id", help="create standard runs/<RUN_ID> metadata and workspace")
    parser.add_argument("--attempt-id", default="attempt-01")
    parser.add_argument(
        "--simple-layout",
        action="store_true",
        help="create only the run root, workspace, and RUN.json; retain initial state by immutable hashes",
    )
    parser.add_argument("--non-scored", action="store_true", help="required for qualification dry-runs")
    parser.add_argument(
        "--qualification-root",
        type=Path,
        help="place a non-scored standard run under this isolated qualification directory",
    )
    parser.add_argument(
        "--authorize-scored-materialization",
        action="store_true",
        help="explicit operator guard; materialization still does not execute the run",
    )
    args = parser.parse_args()
    if args.qualification_root and not args.non_scored:
        raise SystemExit("--qualification-root is permitted only with --non-scored")
    if args.qualification_root and not args.run_id:
        raise SystemExit("--qualification-root requires --run-id")
    task_root = args.task_root.resolve()
    source = task_root / "test_repo"
    lock_path = task_root / "TASK_LOCK.json"
    if not source.is_dir() or not lock_path.is_file():
        raise SystemExit("task_root must contain test_repo/ and TASK_LOCK.json")
    lock = load_json(lock_path)
    actual_hash = tree_sha256(source)
    expected_hash = lock.get("surfaces", {}).get("test_repo", {}).get("tree_sha256")
    if expected_hash != actual_hash:
        raise SystemExit(f"wrong/dirty task revision: lock={expected_hash} actual={actual_hash}")
    if not args.non_scored and not args.authorize_scored_materialization:
        raise SystemExit("refusing scored materialization without --authorize-scored-materialization")

    run_dir: Path | None = None
    if args.run_id:
        run_base = args.qualification_root.resolve() if args.qualification_root else task_root
        run_dir = run_base / "runs" / args.run_id
        workspace = args.dest.resolve() if args.dest else run_dir / "workspace"
        if run_dir.exists():
            raise SystemExit(f"run identifier already exists: {run_dir}")
        run_dir.mkdir(parents=True, exist_ok=False)
        if not args.simple_layout:
            for rel in ("main", "executors", "state_loss", "evidence"):
                (run_dir / rel).mkdir()
    elif args.dest:
        workspace = args.dest.resolve()
    else:
        raise SystemExit("provide dest or --run-id")
    if workspace.exists():
        raise SystemExit(f"destination already exists: {workspace}")

    shutil.copytree(source, workspace, ignore=ignore_direct if args.condition == "DIRECT" else None)
    if task_root.name.startswith(("T02_", "T03_", "T04_")):
        checkpoints = workspace / "CHECKPOINTS"
        checkpoints.mkdir()
        shutil.copy2(workspace / "TASK.md", checkpoints / "01.md")
        state_dir = workspace / ".evaluation"
        state_dir.mkdir()
        (state_dir / "CHECKPOINT_STATE.json").write_text(
            json.dumps({"current_checkpoint": 1, "accepted": [], "revealed": [1]}, indent=2) + "\n",
            encoding="utf-8",
        )
    errors = validate_workspace(task_root, workspace, args.condition)
    if errors:
        shutil.rmtree(workspace)
        if run_dir and run_dir.exists():
            shutil.rmtree(run_dir)
        raise SystemExit("workspace validation failed:\n- " + "\n- ".join(errors))

    initial_hash = tree_sha256(workspace)
    result = {
        "schema_version": 1,
        "run_id": args.run_id,
        "attempt_id": args.attempt_id,
        "task_id": lock["task_id"],
        "condition": args.condition,
        "non_scored": args.non_scored,
        "status": "MATERIALIZED_NOT_STARTED",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_test_repo": str(source),
        "source_test_repo_tree_sha256": actual_hash,
        "source_task_lock_sha256": file_sha256(lock_path),
        "workspace": str(workspace),
        "repo_initial_tree_sha256": initial_hash,
        "repo_initial_storage": "hash_ref" if args.simple_layout else "full_snapshot",
        "qualification_root": str(args.qualification_root.resolve()) if args.qualification_root else None,
        "layout_version": "simple-v2" if args.simple_layout else "capsule-v1",
    }
    if run_dir:
        if not args.simple_layout:
            initial = run_dir / "repo_initial"
            shutil.copytree(workspace, initial)
        (run_dir / "RUN.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
