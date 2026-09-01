#!/usr/bin/env python3
"""Rebuild the configured runtime archive and reconstruct generated copies."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from eval_common import tree_sha256, validate_clean_runtime
from sync_ai_workflow import (
    ARCHIVE,
    ROOT,
    SOURCE_CONFIG,
    inspect_archive,
    load_source_config,
)


LOCKED_METADATA = (
    ROOT / "RUNTIME_COPY_HASHES.json",
    ROOT / "VALIDATION_RUNTIME_TESTS.txt",
    ROOT / "PACKAGE_MANIFEST.json",
    ROOT / "manifests" / "TASK_LOCK.json",
)


def run_script(name: str, *arguments: str) -> None:
    subprocess.run(
        [sys.executable, "-X", "utf8", str(ROOT / "scripts" / name), *arguments],
        cwd=ROOT,
        check=True,
    )


def run_artifacts() -> list[str]:
    unexpected: list[str] = []
    for task_root in sorted((ROOT / "tasks").glob("T??_*")):
        for surface_name in ("runs", "run_results"):
            surface = task_root / surface_name
            if not surface.is_dir():
                continue
            for path in surface.iterdir():
                if path.name in {"README.md", ".gitkeep"}:
                    continue
                if surface_name == "runs" and path.is_dir():
                    metadata_path = path / "RUN.json"
                    if metadata_path.is_file():
                        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                        status = str(metadata.get("status", ""))
                        unstarted = status == "AWAITING_MAIN" and not any(
                            key in metadata
                            for key in ("main_chat", "main_handoff", "executor_session", "finalization")
                        )
                        if status.startswith("INVALIDATED_") or unstarted:
                            continue
                unexpected.append(path.relative_to(ROOT).as_posix())
    return unexpected


def configured_runtime(override: Path | None) -> Path:
    if override is not None:
        candidate = override.resolve()
        return candidate if candidate.name == ".ai-workflow" else candidate / ".ai-workflow"
    config = load_source_config()
    return (
        ROOT
        / str(config["configured_source_path"])
        / str(config["runtime_subpath"])
    ).resolve()


def metadata_paths() -> list[Path]:
    paths = list(LOCKED_METADATA)
    for task_root in sorted((ROOT / "tasks").glob("T??_*")):
        paths.extend((task_root / "TASK_SOURCE.json", task_root / "TASK_LOCK.json"))
    return paths


def run_runtime_tests(runtime: Path) -> str:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=runtime,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout + result.stderr


def restore_on_failure(
    backup_root: Path, backed_up: list[Path], archive_existed: bool
) -> None:
    archive_backup = backup_root / ARCHIVE.relative_to(ROOT)
    if archive_backup.is_file():
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archive_backup, ARCHIVE)
        run_script("sync_ai_workflow.py")
    elif not archive_existed:
        ARCHIVE.unlink(missing_ok=True)
    for path in backed_up:
        backup = backup_root / path.relative_to(ROOT)
        if backup.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Use AI_WORKFLOW_RUNTIME_SOURCE.json to rebuild the canonical runtime ZIP, install "
            "all generated runtime copies, refresh locks, and validate."
        )
    )
    parser.add_argument(
        "source",
        type=Path,
        nargs="?",
        help="optional source package or .ai-workflow override",
    )
    args = parser.parse_args()

    try:
        source_runtime = configured_runtime(args.source)
        if not source_runtime.is_dir():
            raise ValueError(
                "configured runtime source is missing; restore the tracked source package at "
                f"{source_runtime}"
            )
        source_hash = tree_sha256(source_runtime)
        old_archive = inspect_archive() if ARCHIVE.is_file() else None
        runtime_changed = old_archive is None or source_hash != old_archive["tree_sha256"]
        errors = validate_clean_runtime(source_runtime)
        if errors:
            raise ValueError("configured runtime source is not clean: " + "; ".join(errors))
        if runtime_changed:
            existing_runs = run_artifacts()
            if existing_runs:
                raise ValueError(
                    "refusing to revise the frozen runtime after run artifacts exist:\n- "
                    + "\n- ".join(existing_runs[:20])
                )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    archive_existed = ARCHIVE.is_file()
    protected = [ARCHIVE, SOURCE_CONFIG, *metadata_paths()]
    backed_up = [path for path in protected if path.is_file()]
    try:
        with tempfile.TemporaryDirectory(prefix="ai-workflow-update-backup-") as temp_name:
            backup_root = Path(temp_name)
            for path in backed_up:
                backup = backup_root / path.relative_to(ROOT)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup)
            try:
                test_output = run_runtime_tests(source_runtime)
                (ROOT / "VALIDATION_RUNTIME_TESTS.txt").write_text(
                    test_output, encoding="utf-8", newline="\n"
                )
                run_script("sync_ai_workflow.py", "--build-from", str(source_runtime))
                run_script("generate_task_locks.py")
                run_script("generate_package_manifest.py")
                run_script("validate_repo.py")
            except (OSError, ValueError, subprocess.CalledProcessError) as exc:
                restore_on_failure(backup_root, backed_up, archive_existed)
                raise SystemExit(
                    f"runtime reconstruction failed and tracked runtime metadata was restored: {exc}"
                ) from exc
        updated = inspect_archive()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    print(
        json.dumps(
            {
                "status": "RECONSTRUCTED_FROM_CONFIGURED_SOURCE",
                "configuration": SOURCE_CONFIG.relative_to(ROOT).as_posix(),
                "source_runtime": source_runtime.relative_to(ROOT).as_posix(),
                "source_tree_changed": runtime_changed,
                "canonical_archive": ARCHIVE.relative_to(ROOT).as_posix(),
                "canonical_archive_sha256": updated["archive_sha256"],
                "runtime_tree_sha256": updated["tree_sha256"],
                "generated_runtime_copies": 8,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
