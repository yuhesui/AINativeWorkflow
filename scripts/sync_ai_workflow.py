#!/usr/bin/env python3
"""Build, validate, and install the single canonical AI-Native runtime ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from eval_common import file_sha256, files, tree_sha256, validate_clean_runtime


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONFIG = ROOT / "AI_WORKFLOW_RUNTIME_SOURCE.json"


def load_source_config() -> dict[str, object]:
    value = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {SOURCE_CONFIG}")
    return value


SOURCE_CONFIG_VALUE = load_source_config()
ARCHIVE = ROOT / str(SOURCE_CONFIG_VALUE["canonical_runtime_archive"])
RUNTIME_RECORD = ROOT / "RUNTIME_COPY_HASHES.json"
TASKS = (
    "T01_query_optimize",
    "T02_dag_execution",
    "T03_database_migration",
    "T04_recli",
    "T05_rlMetaMazeMisc",
    "T06_corebench_4252248",
    "T07_sequential_neural_score_estimation",
)
PREFIX = PurePosixPath(".ai-workflow")
MAX_FILES = 10_000
MAX_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def task_runtime_targets() -> list[Path]:
    return [ROOT / "tasks" / name / "test_repo" / ".ai-workflow" for name in TASKS]


def runtime_targets() -> list[Path]:
    return [ROOT / ".ai-workflow", *task_runtime_targets()]


def configured_source_runtime() -> Path:
    return (
        ROOT
        / str(SOURCE_CONFIG_VALUE["configured_source_path"])
        / str(SOURCE_CONFIG_VALUE["runtime_subpath"])
    ).resolve()


def member_relative(name: str) -> PurePosixPath | None:
    if "\\" in name or "\0" in name:
        raise ValueError(f"unsafe archive member: {name!r}")
    candidate = PurePosixPath(name)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"unsafe archive member: {name!r}")
    if not candidate.parts or candidate.parts[0] != PREFIX.name:
        raise ValueError(f"archive member is outside .ai-workflow/: {name!r}")
    if len(candidate.parts) == 1:
        return None
    relative = PurePosixPath(*candidate.parts[1:])
    if any(part in {"", ".", ".."} or ":" in part for part in relative.parts):
        raise ValueError(f"unsafe archive member: {name!r}")
    return relative


def inspect_archive(path: Path = ARCHIVE) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"missing canonical runtime archive: {path}")
    digest = hashlib.sha256()
    file_count = 0
    total_bytes = 0
    seen: set[str] = set()
    state: dict[str, object] | None = None
    try:
        with zipfile.ZipFile(path) as archive:
            infos = sorted(archive.infolist(), key=lambda item: item.filename)
            for info in infos:
                relative = member_relative(info.filename)
                if relative is None or info.is_dir():
                    continue
                unix_mode = (info.external_attr >> 16) & 0o170000
                if unix_mode == 0o120000:
                    raise ValueError(f"symbolic links are not allowed: {info.filename!r}")
                rel_text = relative.as_posix()
                collision_key = rel_text.casefold()
                if collision_key in seen:
                    raise ValueError(f"duplicate archive member: {rel_text!r}")
                seen.add(collision_key)
                file_count += 1
                total_bytes += info.file_size
                if file_count > MAX_FILES or total_bytes > MAX_UNCOMPRESSED_BYTES:
                    raise ValueError("canonical runtime archive exceeds safety limits")
                data = archive.read(info)
                digest.update(rel_text.encode("utf-8"))
                digest.update(b"\0")
                digest.update(data)
                digest.update(b"\0")
                if rel_text == "STATE.json":
                    value = json.loads(data.decode("utf-8"))
                    if not isinstance(value, dict):
                        raise ValueError("STATE.json is not a JSON object")
                    state = value
            if archive.testzip() is not None:
                raise ValueError("canonical runtime archive failed CRC validation")
    except zipfile.BadZipFile as exc:
        raise ValueError(f"invalid canonical runtime ZIP: {exc}") from exc
    if state is None:
        raise ValueError("canonical runtime archive is missing .ai-workflow/STATE.json")
    if state.get("active_plan_id") is not None or state.get("plans") != {}:
        raise ValueError("canonical runtime archive contains inherited workflow state")
    if not file_count:
        raise ValueError("canonical runtime archive contains no files")
    return {
        "archive_sha256": file_sha256(path),
        "tree_sha256": digest.hexdigest(),
        "file_count": file_count,
        "uncompressed_bytes": total_bytes,
    }


def write_deterministic_archive(source: Path, destination: Path = ARCHIVE) -> None:
    source = source.resolve()
    if not source.is_dir():
        raise ValueError(f"runtime source is not a directory: {source}")
    runtime_errors = validate_clean_runtime(source)
    if runtime_errors:
        raise ValueError("runtime source is not clean: " + "; ".join(runtime_errors))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp", delete=False
    ) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=False,
        ) as archive:
            for path in files(source):
                relative = path.relative_to(source).as_posix()
                info = zipfile.ZipInfo(f".ai-workflow/{relative}", date_time=ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                mode = 0o755 if relative.startswith("bin/") else 0o644
                info.external_attr = (0o100000 | mode) << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        inspect_archive(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def extract_archive(destination: Path, archive_path: Path = ARCHIVE) -> None:
    destination = destination.resolve()
    allowed = {path.resolve() for path in runtime_targets()}
    if destination not in allowed:
        raise ValueError(f"refusing to install outside configured runtime targets: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ai-workflow-sync-", dir=destination.parent) as temp_name:
        staged = Path(temp_name) / ".ai-workflow"
        staged.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                relative = member_relative(info.filename)
                if relative is None or info.is_dir():
                    continue
                output = staged.joinpath(*relative.parts)
                if not output.resolve().is_relative_to(staged.resolve()):
                    raise ValueError(f"unsafe archive destination: {info.filename!r}")
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(archive.read(info))
                mode = (info.external_attr >> 16) & 0o777
                if mode:
                    output.chmod(mode)
        runtime_errors = validate_clean_runtime(staged)
        if runtime_errors:
            raise ValueError("staged runtime is not clean: " + "; ".join(runtime_errors))
        expected = str(inspect_archive(archive_path)["tree_sha256"])
        if tree_sha256(staged) != expected:
            raise ValueError("staged runtime tree does not match the canonical archive")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(staged, destination)


def update_runtime_record(archive_info: dict[str, object]) -> None:
    tree_hash = str(archive_info["tree_sha256"])
    value = {
        "schema_version": 2,
        "canonical_archive": ARCHIVE.relative_to(ROOT).as_posix(),
        "canonical_archive_sha256": archive_info["archive_sha256"],
        "tree_sha256": tree_hash,
        "file_count": archive_info["file_count"],
        "uncompressed_bytes": archive_info["uncompressed_bytes"],
        "repository_default": tree_hash,
        "tasks": {name: tree_hash for name in TASKS},
    }
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if not RUNTIME_RECORD.is_file() or RUNTIME_RECORD.read_text(encoding="utf-8") != rendered:
        RUNTIME_RECORD.write_text(rendered, encoding="utf-8")


def check_targets(expected_hash: str) -> list[str]:
    errors: list[str] = []
    for target in runtime_targets():
        label = target.relative_to(ROOT).as_posix()
        if not target.is_dir():
            errors.append(f"missing generated runtime: {label}")
            continue
        runtime_errors = validate_clean_runtime(target)
        if runtime_errors:
            errors.extend(f"{label}: {error}" for error in runtime_errors)
            continue
        actual_hash = tree_sha256(target)
        if actual_hash != expected_hash:
            errors.append(f"runtime differs from canonical archive: {label}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify the archive and all expanded copies")
    parser.add_argument(
        "--ensure",
        action="store_true",
        help="install missing copies, but refuse to overwrite a differing existing copy",
    )
    parser.add_argument(
        "--build-from",
        type=Path,
        metavar="RUNTIME_DIR",
        help="maintenance only: rebuild the canonical archive from one clean runtime, then sync",
    )
    args = parser.parse_args()
    if sum((args.check, args.ensure, args.build_from is not None)) > 1:
        parser.error("choose at most one of --check, --ensure, or --build-from")

    try:
        if args.build_from is not None:
            write_deterministic_archive(args.build_from)
        elif not ARCHIVE.is_file():
            if args.check:
                raise ValueError(
                    "generated runtime archive is absent; run scripts/update_ai_workflow.py "
                    "or scripts/sync_ai_workflow.py to reconstruct it"
                )
            write_deterministic_archive(configured_source_runtime())
        archive_info = inspect_archive()
        expected_hash = str(archive_info["tree_sha256"])
        if args.check:
            errors = check_targets(expected_hash)
            if errors:
                raise ValueError("\n- ".join(("runtime synchronization check failed", *errors)))
        elif args.ensure:
            errors: list[str] = []
            for target in runtime_targets():
                if not target.exists():
                    extract_archive(target)
                elif tree_sha256(target) != expected_hash:
                    errors.append(target.relative_to(ROOT).as_posix())
            if errors:
                raise ValueError(
                    "existing runtime differs from canonical archive; review it, then run the explicit "
                    "sync command if replacement is intended:\n- " + "\n- ".join(errors)
                )
        else:
            for target in runtime_targets():
                extract_archive(target)
        if not args.check:
            update_runtime_record(archive_info)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    print(
        json.dumps(
            {
                "archive": ARCHIVE.relative_to(ROOT).as_posix(),
                **archive_info,
                "expanded_copies": len(runtime_targets()),
                "mode": "check" if args.check else "ensure" if args.ensure else "sync",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
