#!/usr/bin/env python3
"""Validate the frozen capsule contract without materializing or running a score row."""

from __future__ import annotations

import zipfile
from pathlib import Path

from eval_common import (
    TRANSIENT_DIRS,
    file_sha256,
    files,
    is_dynamic_run_artifact,
    is_generated_runtime_archive,
    is_generated_runtime_copy,
    load_json,
    sensitive_leaks,
    tree_sha256,
    validate_clean_runtime,
    validate_reference_mounts,
)
from sync_ai_workflow import ARCHIVE as WORKFLOW_ARCHIVE
from sync_ai_workflow import inspect_archive

ROOT = Path(__file__).resolve().parents[1]
TASKS = (
    "T01_query_optimize",
    "T02_dag_execution",
    "T03_database_migration",
    "T04_recli",
    "T05_rlMetaMazeMisc",
    "T06_corebench_4252248",
    "T07_sequential_neural_score_estimation",
)
REQUIRED_TASK_PATHS = (
    "README.md",
    "TASK_SOURCE.json",
    "TASK_LOCK.json",
    "original_task",
    "test_repo/.ai-workflow/STATE.json",
    "test_repo/.ai-workflow/docs/PROMPTING_CORE.md",
    "test_repo/TASK.md",
    "test_repo/RESOURCE_POLICY.md",
    "reference_material/agent_visible",
    "reference_material/provenance_only",
    "reference_material/README.md",
    "reference_material/VISIBILITY_MANIFEST.json",
    "qualification/private_eval",
    "qualification/oracle_runs",
    "qualification/ENVIRONMENT.md",
    "qualification/LEAKAGE_AUDIT.md",
    "qualification/QUALIFICATION_REPORT.md",
    "qualification/QUALIFICATION_STATUS.json",
    "runs",
    "run_results",
)


def transient_paths(root: Path) -> list[str]:
    return [
        path.relative_to(ROOT).as_posix()
        for path in root.rglob("*")
        if any(part in TRANSIENT_DIRS for part in path.relative_to(root).parts)
    ]


def main() -> int:
    errors: list[str] = []
    aggregate_path = ROOT / "manifests" / "TASK_LOCK.json"
    aggregate = load_json(aggregate_path) if aggregate_path.is_file() else {}
    aggregate_tasks = aggregate.get("tasks", {})
    expected_task_ids = {name[:3] for name in TASKS}
    if set(aggregate_tasks) != expected_task_ids:
        errors.append("aggregate task lock does not contain exactly T01-T07")
    runtime_hashes: list[str] = []

    for name in TASKS:
        task = ROOT / "tasks" / name
        if not task.is_dir():
            errors.append(f"missing task capsule: {name}")
            continue
        for rel in REQUIRED_TASK_PATHS:
            if not (task / rel).exists():
                errors.append(f"{name}: missing {rel}")
        if (task / ".ai-workflow").exists():
            errors.append(f"{name}: obsolete capsule-root .ai-workflow")
        if not (task / "original_task").is_dir() or not any((task / "original_task").iterdir()):
            errors.append(f"{name}: original_task is empty")
        if not (task / "test_repo").is_dir() or not any((task / "test_repo").iterdir()):
            errors.append(f"{name}: test_repo is empty")

        lock_path = task / "TASK_LOCK.json"
        if lock_path.is_file():
            lock = load_json(lock_path)
            if lock.get("task_id") != name[:3]:
                errors.append(f"{name}: lock task identity mismatch")
            for key, rel in (
                ("original_task", "original_task"),
                ("test_repo", "test_repo"),
                ("reference_agent_visible", "reference_material/agent_visible"),
                ("reference_provenance_only", "reference_material/provenance_only"),
                ("private_eval", "qualification/private_eval"),
            ):
                expected = lock.get("surfaces", {}).get(key, {}).get("tree_sha256")
                path = task / rel
                if path.is_dir() and expected != tree_sha256(path):
                    errors.append(f"{name}: {key} differs from TASK_LOCK.json")
            runtime = task / "test_repo" / ".ai-workflow"
            runtime_hash = tree_sha256(runtime) if runtime.is_dir() else ""
            runtime_hashes.append(runtime_hash)
            if lock.get("runtime_tree_sha256") != runtime_hash:
                errors.append(f"{name}: runtime hash differs from TASK_LOCK.json")
            entry = aggregate_tasks.get(name[:3], {})
            if entry.get("task_lock_sha256") != file_sha256(lock_path):
                errors.append(f"{name}: aggregate TASK_LOCK.json file hash is stale")
            if entry.get("test_repo_tree_sha256") != lock.get("surfaces", {}).get("test_repo", {}).get("tree_sha256"):
                errors.append(f"{name}: aggregate task lock is stale")
            if entry.get("original_task_tree_sha256") != lock.get("surfaces", {}).get("original_task", {}).get("tree_sha256"):
                errors.append(f"{name}: aggregate original-task lock is stale")
            if entry.get("runtime_tree_sha256") != runtime_hash:
                errors.append(f"{name}: aggregate runtime lock is stale")
            qualification_path = task / "qualification" / "QUALIFICATION_STATUS.json"
            if qualification_path.is_file():
                qualification = load_json(qualification_path)
                status = qualification.get("status")
                if status not in {"QUALIFIED", "BLOCKED"}:
                    errors.append(f"{name}: non-final qualification status: {status!r}")
                if lock.get("qualification", {}).get("status") != status:
                    errors.append(f"{name}: task lock qualification status is stale")
                if entry.get("qualification_status") != status:
                    errors.append(f"{name}: aggregate qualification status is stale")
            source_path = task / "TASK_SOURCE.json"
            if source_path.is_file():
                source = load_json(source_path)
                if source.get("task_id") != name[:3] or source.get("frozen_identity") != lock.get("frozen_identity"):
                    errors.append(f"{name}: source/lock frozen identity mismatch")

        runtime = task / "test_repo" / ".ai-workflow"
        if runtime.is_dir():
            errors.extend(f"{name}: {error}" for error in validate_clean_runtime(runtime))
        leaks = sensitive_leaks(task / "test_repo")
        if leaks:
            errors.append(f"{name}: test_repo leaks private material: {leaks[:10]}")
        errors.extend(
            f"{name}: {error}"
            for error in validate_reference_mounts(task, task / "test_repo")
        )
        debris = transient_paths(task)
        if debris:
            errors.append(f"{name}: generated cache debris present: {debris[:10]}")

        for surface in ("runs", "run_results"):
            surface_path = task / surface
            unexpected: list[str] = []
            if surface_path.is_dir():
                for path in surface_path.iterdir():
                    if path.name in {"README.md", ".gitkeep"}:
                        continue
                    if surface == "runs" and path.is_dir():
                        metadata_path = path / "RUN.json"
                        if metadata_path.is_file():
                            metadata = load_json(metadata_path)
                            status = str(metadata.get("status", ""))
                            unstarted = status == "AWAITING_MAIN" and not any(
                                key in metadata
                                for key in ("main_chat", "main_handoff", "executor_session", "finalization")
                            )
                            if status == "INVALIDATED_PRE_TRAJECTORY" or unstarted:
                                continue
                    unexpected.append(path.name)
            if unexpected:
                errors.append(f"{name}: scored surface is not empty: {surface}/{unexpected[:5]}")

    if len(runtime_hashes) != len(TASKS) or len(set(runtime_hashes)) != 1:
        errors.append("the seven test_repo/.ai-workflow trees are not byte-identical")
    repository_runtime = ROOT / ".ai-workflow"
    repository_runtime_hash = tree_sha256(repository_runtime) if repository_runtime.is_dir() else ""
    if not repository_runtime_hash:
        errors.append("missing generated repository-default .ai-workflow runtime")
    elif runtime_hashes and repository_runtime_hash != runtime_hashes[0]:
        errors.append("repository-default .ai-workflow differs from task runtimes")
    archive_info: dict[str, object] = {}
    try:
        archive_info = inspect_archive(WORKFLOW_ARCHIVE)
        if runtime_hashes and archive_info.get("tree_sha256") != runtime_hashes[0]:
            errors.append("canonical AI workflow archive differs from expanded runtimes")
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        errors.append(f"canonical AI workflow archive is invalid: {exc}")
    runtime_record_path = ROOT / "RUNTIME_COPY_HASHES.json"
    if runtime_record_path.is_file() and runtime_hashes:
        runtime_record = load_json(runtime_record_path)
        if runtime_record.get("tree_sha256") != runtime_hashes[0]:
            errors.append("RUNTIME_COPY_HASHES.json is stale")
        recorded_tasks = runtime_record.get("tasks", {})
        if set(recorded_tasks) != set(TASKS) or any(value != runtime_hashes[0] for value in recorded_tasks.values()):
            errors.append("RUNTIME_COPY_HASHES.json does not record all seven identical runtimes")
        if runtime_record.get("canonical_archive") != WORKFLOW_ARCHIVE.relative_to(ROOT).as_posix():
            errors.append("RUNTIME_COPY_HASHES.json does not identify the canonical archive")
        if runtime_record.get("repository_default") != repository_runtime_hash:
            errors.append("RUNTIME_COPY_HASHES.json repository-default runtime hash is stale")
        if archive_info and runtime_record.get("canonical_archive_sha256") != archive_info.get("archive_sha256"):
            errors.append("RUNTIME_COPY_HASHES.json canonical archive hash is stale")
    if aggregate.get("status") not in {"READY", "QUALIFIED_WITH_BLOCKERS"}:
        errors.append(f"aggregate task-lock status is not final: {aggregate.get('status')!r}")

    environment_path = ROOT / "manifests" / "ENVIRONMENT_LOCK.json"
    if environment_path.is_file():
        environment = load_json(environment_path)
        if environment.get("schema_version") != 1:
            errors.append("environment lock schema is not version 1")
        host = environment.get("host", {})
        if not all(key in host for key in ("os", "docker_engine", "gpu", "docker_runtimes", "nvidia_container_runtime")):
            errors.append("environment lock is missing required host facts")
        stacks = environment.get("qualified_stacks", {})
        if set(stacks) != {"slopcodebench", "mlgym", "paperbench", "corebench_image"}:
            errors.append("environment lock qualified-stack set is incomplete")

    for rel in (
        "manifests/ENVIRONMENT_LOCK.json",
        "reference_material/ai_native_workflow/.aiexplainer/MANIFEST.yaml",
        "reference_material/ai_native_workflow/prompting/SOURCE_LOCK.json",
        "reference_material/ai_native_workflow/AI_NATIVE_WORKFLOW_FULL_AI_EXPLAINER.zip",
        "READY_FOR_SCORED_RUNS.md",
        "SETUP_REPORT.md",
        "BUILD_STATUS.md",
        "RUNTIME_COPY_HASHES.json",
        "AI_WORKFLOW_RUNTIME_SOURCE.json",
        "AI_WORKFLOW_RUNTIME.zip",
        "scripts/sync_ai_workflow.py",
        "scripts/update_ai_workflow.py",
        "VALIDATION_RUNTIME_TESTS.txt",
        "PACKAGE_MANIFEST.json",
    ):
        if not (ROOT / rel).is_file():
            errors.append(f"missing global artifact: {rel}")
    explainer = ROOT / "reference_material" / "ai_native_workflow" / "AI_NATIVE_WORKFLOW_FULL_AI_EXPLAINER.zip"
    if explainer.is_file():
        try:
            with zipfile.ZipFile(explainer) as archive:
                bad = archive.testzip()
                if bad:
                    errors.append(f"explainer ZIP has corrupt member: {bad}")
        except zipfile.BadZipFile as exc:
            errors.append(f"invalid explainer ZIP: {exc}")
    if (ROOT / ".upstream_stage").exists():
        errors.append("temporary upstream staging directory remains")

    package_path = ROOT / "PACKAGE_MANIFEST.json"
    if package_path.is_file():
        package = load_json(package_path)
        recorded = package.get("files", {})
        actual_paths = {
            path.relative_to(ROOT).as_posix(): path
            for path in files(ROOT)
            if path != package_path
            and not is_dynamic_run_artifact(path.relative_to(ROOT))
            and not is_generated_runtime_archive(path.relative_to(ROOT))
            and not is_generated_runtime_copy(path.relative_to(ROOT))
        }
        if set(recorded) != set(actual_paths):
            missing = sorted(set(actual_paths) - set(recorded))[:10]
            stale = sorted(set(recorded) - set(actual_paths))[:10]
            errors.append(f"package manifest file set differs; missing={missing}, stale={stale}")
        else:
            for rel, path in actual_paths.items():
                entry = recorded[rel]
                if entry.get("bytes") != path.stat().st_size or entry.get("sha256") != file_sha256(path):
                    errors.append(f"package manifest differs: {rel}")
                    break

    if errors:
        print("REPOSITORY VALIDATION FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(
        "OK: seven frozen capsules; locked complete surfaces; identical clean runtimes; "
        "visibility isolation; qualification records; no executed scored trajectories"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
