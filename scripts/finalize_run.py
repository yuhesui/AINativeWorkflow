#!/usr/bin/env python3
"""Archive the entire final repository and create a separate result skeleton."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from eval_common import file_sha256, tree_sha256, validate_workspace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_root", type=Path)
    parser.add_argument("run_id")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--validity", choices=("VALID", "INVALID_INFRASTRUCTURE", "FAILED_TASK"), required=True)
    parser.add_argument("--invalidation-reason")
    parser.add_argument("--grader-raw", type=Path, help="native grader output to archive")
    parser.add_argument("--native-primary-metric", type=float)
    parser.add_argument("--normalized-completion-score", type=float)
    parser.add_argument("--metrics-json", type=Path, help="structured native/resource metrics")
    parser.add_argument("--recovery-json", type=Path, help="state-loss recovery measurements")
    parser.add_argument("--qualification-root", type=Path, help="dry-run output outside scored runs/")
    args = parser.parse_args()
    if args.validity == "INVALID_INFRASTRUCTURE" and not args.invalidation_reason:
        raise SystemExit("INVALID_INFRASTRUCTURE requires --invalidation-reason")
    if args.validity in {"VALID", "FAILED_TASK"} and not args.grader_raw:
        raise SystemExit(f"{args.validity} requires --grader-raw")
    for label, path in (("grader raw", args.grader_raw), ("metrics JSON", args.metrics_json), ("recovery JSON", args.recovery_json)):
        if path is not None and not path.is_file():
            raise SystemExit(f"missing {label}: {path}")
    task_root, workspace = args.task_root.resolve(), args.workspace.resolve()
    if args.qualification_root:
        run_dir = args.qualification_root.resolve() / "runs" / args.run_id
        result_dir = args.qualification_root.resolve() / "run_results" / args.run_id
    else:
        run_dir = task_root / "runs" / args.run_id
        result_dir = task_root / "run_results" / args.run_id
    run_json = run_dir / "RUN.json"
    if not run_json.is_file():
        raise SystemExit(f"missing RUN.json: {run_json}")
    run = json.loads(run_json.read_text(encoding="utf-8"))
    errors = validate_workspace(task_root, workspace, run["condition"])
    errors = [e for e in errors if "inherited non-clean plan state" not in e]
    if errors:
        raise SystemExit("final workspace validation failed:\n- " + "\n- ".join(errors))
    final = run_dir / "repo_final"
    if final.exists() or result_dir.exists():
        raise SystemExit("final/result destination already exists; reruns require a new identifier")
    shutil.copytree(workspace, final)
    final_hash = tree_sha256(final, include_transient=True)
    run.update({
        "status": "FINALIZED",
        "validity": args.validity,
        "invalidation_reason": args.invalidation_reason,
        "finalized_utc": datetime.now(timezone.utc).isoformat(),
        "repo_final": str(final),
        "repo_final_tree_sha256": final_hash,
    })
    run_json.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result_dir.mkdir(parents=True)
    grader_rel = None
    grader_hash = None
    if args.grader_raw:
        suffix = "".join(args.grader_raw.suffixes) or ".txt"
        grader_destination = result_dir / f"GRADER_RAW{suffix}"
        shutil.copy2(args.grader_raw, grader_destination)
        grader_rel = str(grader_destination)
        grader_hash = file_sha256(grader_destination)
    score = {
        "schema_version": 1,
        "run_id": args.run_id,
        "task_id": run["task_id"],
        "condition": run["condition"],
        "validity": args.validity,
        "invalidation_reason": args.invalidation_reason,
        "native_primary_metric": args.native_primary_metric,
        "normalized_completion_score": args.normalized_completion_score,
        "repo_final_tree_sha256": final_hash,
        "repo_final": str(final),
        "grader_raw": grader_rel,
        "grader_raw_sha256": grader_hash,
    }
    (result_dir / "SCORE.json").write_text(json.dumps(score, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.metrics_json:
        shutil.copy2(args.metrics_json, result_dir / "METRICS.json")
    else:
        (result_dir / "METRICS.json").write_text("{}\n", encoding="utf-8")
    recovery_source = args.recovery_json
    if recovery_source is None:
        captured = run_dir / "state_loss" / "STATE_LOSS.json"
        if captured.is_file():
            recovery_source = captured
    if recovery_source is not None:
        shutil.copy2(recovery_source, result_dir / "RECOVERY.json")
    (result_dir / "SUMMARY.md").write_text(
        f"# {args.run_id}\n\nValidity: **{args.validity}**. Final repository SHA-256 tree hash: `{final_hash}`.\n",
        encoding="utf-8",
    )
    print(json.dumps(score, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
