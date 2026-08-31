"""Shared deterministic hashing and capsule/workspace validation helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

TRANSIENT_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
SENSITIVE_NAMES = {"expected_answer.json", "golden.sql", "rubric.json", "test_outputs.py"}
SENSITIVE_PARTS = {"private_eval", "oracle_runs", "solution"}
SENSITIVE_MARKERS = (b"terminal-bench-canary GUID", b'"expected_answer": 0.4929241')


def files(root: Path, *, include_transient: bool = False) -> Iterable[Path]:
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        try:
            is_file = path.is_file()
        except OSError:
            # Qualification restores can contain upstream Linux symlinks that
            # are intentionally broken on the Windows host. They carry no file
            # content here and are excluded from portable content-tree hashes.
            continue
        if not is_file:
            continue
        rel = path.relative_to(root)
        if ".git" in rel.parts:
            continue
        if not include_transient and any(part in TRANSIENT_DIRS for part in rel.parts):
            continue
        yield path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(root: Path, *, include_transient: bool = False) -> str:
    digest = hashlib.sha256()
    for path in files(root, include_transient=include_transient):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def validate_clean_runtime(runtime: Path) -> list[str]:
    errors: list[str] = []
    state_path = runtime / "STATE.json"
    if not state_path.is_file():
        return ["AI-Native runtime is missing STATE.json"]
    try:
        state = load_json(state_path)
        if state.get("active_plan_id") is not None or state.get("plans") != {}:
            errors.append("AI-Native runtime inherited non-clean plan state")
    except Exception as exc:
        errors.append(f"invalid AI-Native STATE.json: {exc}")
    debris = [
        p.relative_to(runtime).as_posix()
        for p in runtime.rglob("*")
        if any(part in TRANSIENT_DIRS for part in p.relative_to(runtime).parts)
    ]
    if debris:
        errors.append(f"AI-Native runtime contains generated cache debris: {debris[:5]}")
    return errors


def sensitive_leaks(workspace: Path) -> list[str]:
    leaks: list[str] = []
    for path in files(workspace, include_transient=True):
        rel = path.relative_to(workspace)
        lower_parts = {part.lower() for part in rel.parts}
        if path.name.lower() in SENSITIVE_NAMES or lower_parts.intersection(SENSITIVE_PARTS):
            leaks.append(rel.as_posix())
            continue
        if path.stat().st_size <= 2 * 1024 * 1024:
            data = path.read_bytes()
            if any(marker in data for marker in SENSITIVE_MARKERS):
                leaks.append(rel.as_posix())
    return sorted(set(leaks))


def validate_reference_mounts(task_root: Path, workspace: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = task_root / "reference_material" / "VISIBILITY_MANIFEST.json"
    if not manifest_path.is_file():
        return ["missing reference visibility manifest"]
    manifest = load_json(manifest_path)
    for entry in manifest.get("agent_visible", []):
        if not isinstance(entry, dict) or "mounted_at" not in entry:
            continue
        source_text = str(entry.get("path", ""))
        mounted_text = str(entry["mounted_at"])
        if "**" in source_text or "**" in mounted_text:
            source_root = task_root / "reference_material" / source_text.split("**", 1)[0]
            mounted_declared = task_root / mounted_text.split("**", 1)[0]
            try:
                mounted_root = workspace / mounted_declared.resolve().relative_to((task_root / "test_repo").resolve())
            except ValueError:
                mounted_root = mounted_declared
            if not source_root.exists() or not mounted_root.exists():
                errors.append(f"missing visible reference tree: {source_text} -> {mounted_text}")
            elif tree_sha256(source_root) != tree_sha256(mounted_root):
                errors.append(f"visible reference tree differs: {source_text} -> {mounted_text}")
            continue
        source = (task_root / "reference_material" / source_text).resolve()
        mounted_declared = (task_root / mounted_text).resolve()
        try:
            mounted = workspace / mounted_declared.relative_to((task_root / "test_repo").resolve())
        except ValueError:
            mounted = mounted_declared
        if not source.is_file() or not mounted.is_file():
            errors.append(f"missing visible reference: {source_text} -> {mounted_text}")
        elif file_sha256(source) != file_sha256(mounted):
            errors.append(f"visible reference differs: {source_text} -> {mounted_text}")
    return errors


def validate_workspace(task_root: Path, workspace: Path, condition: str) -> list[str]:
    errors: list[str] = []
    runtime = workspace / ".ai-workflow"
    if condition == "DIRECT" and runtime.exists():
        errors.append("Direct workspace contains .ai-workflow")
    if condition == "AI_NATIVE":
        if not runtime.is_dir():
            errors.append("AI-Native workspace is missing .ai-workflow")
        else:
            errors.extend(validate_clean_runtime(runtime))
    leaks = sensitive_leaks(workspace)
    if leaks:
        errors.append(f"hidden evaluator/reference-solution leakage: {leaks[:20]}")
    errors.extend(validate_reference_mounts(task_root, workspace))
    return errors
