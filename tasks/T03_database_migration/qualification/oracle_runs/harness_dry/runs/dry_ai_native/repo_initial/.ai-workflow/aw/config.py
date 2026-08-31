from __future__ import annotations

import argparse
import json
import os
import tomllib
from pathlib import Path
from typing import Any

from .constants import (
    EXECUTION_LEVELS,
    MODES,
    RESEARCH_LEVELS,
    ROUTING_PROFILES,
    SPECIFICATION_REVISION,
    TEST_PROFILES,
    VERSION,
)
from .errors import WorkflowError
from .filesystem import atomic_write_json, atomic_write_text, find_root

DEFAULT_CONFIG: dict[str, Any] = {
    "workflow_version": VERSION,
    "specification_revision": SPECIFICATION_REVISION,
    "mode": "goal",
    "execution_level": "mid",
    "research_level": "none",
    "test_profile": "affected",
    "routing_profile": "all",
    "current_phase": "",
    "auto_continue_after_go": True,
    "approval_phrase": "GO",
    "models": {
        "available": [],
        "surfaces": ["chatgpt", "claude_code", "codex", "copilot_cli"],
        "record_actual_model": True,
    },
    "repository": {
        "root_mode": "auto",
        "root": "",
        "env_var": "AW_REPO_ROOT",
        "insert_into_prompts": True,
    },
    "minor": {"approval": "auto"},
    "phase_lanes": {"minor": "auto", "research": "auto", "verification": "auto", "checkpoints": "auto"},
    "dic_views": {"readme": "on", "requests": "on", "plan": "on", "architecture": "auto", "test_matrix": "auto", "allow_custom": True},
    "templates": {
        "copy_full_set": True,
        "structured_architecture": True,
    },
    "testing": {"policy": "risk_adaptive", "default_profile": "affected"},
    "reports": {"policy": "compact_raw", "flat": True, "max_files": 10, "max_summary_files": 10, "include_key_raw_results": True},
    "update": {"prompt_statuses": ["planned", "ready"], "include_root_files": True},
}


def config_path(root: Path) -> Path:
    return root / ".ai-workflow" / "config.toml"


def _merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(root: Path) -> dict[str, Any]:
    path = config_path(root)
    if not path.is_file():
        raise WorkflowError(f"Missing workflow config: {path}")
    try:
        with path.open("rb") as handle:
            loaded = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise WorkflowError(f"Invalid workflow config TOML: {path}: {exc}") from exc
    config = _merge(DEFAULT_CONFIG, loaded)
    mode = str(config.get("mode", "goal"))
    if mode not in MODES:
        raise WorkflowError(f"Unknown workflow mode: {mode}")
    if str(config.get("execution_level")) not in EXECUTION_LEVELS:
        raise WorkflowError(f"Unknown execution_level: {config.get('execution_level')}")
    if str(config.get("research_level")) not in RESEARCH_LEVELS:
        raise WorkflowError(f"Unknown research_level: {config.get('research_level')}")
    if str(config.get("test_profile")) not in TEST_PROFILES:
        raise WorkflowError(f"Unknown test_profile: {config.get('test_profile')}")
    if str(config.get("routing_profile")) not in ROUTING_PROFILES:
        raise WorkflowError(f"Unknown routing_profile: {config.get('routing_profile')}")
    config["workflow_version"] = VERSION
    config["specification_revision"] = SPECIFICATION_REVISION
    config["mode"] = mode
    return config


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _render_toml(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_render_toml(item) for item in value) + "]"
    return _quote(str(value))


def dump_config(config: dict[str, Any]) -> str:
    ordered_top = [
        "workflow_version", "specification_revision", "mode", "execution_level",
        "research_level", "test_profile", "routing_profile", "current_phase",
        "auto_continue_after_go", "approval_phrase",
    ]
    lines = [f"{key} = {_render_toml(config.get(key, DEFAULT_CONFIG.get(key, '')))}" for key in ordered_top]
    for section in ("models", "repository", "minor", "phase_lanes", "dic_views", "templates", "testing", "reports", "update"):
        lines.append("")
        lines.append(f"[{section}]")
        for key, value in config.get(section, {}).items():
            lines.append(f"{key} = {_render_toml(value)}")
    return "\n".join(lines) + "\n"


def save_config(root: Path, config: dict[str, Any]) -> None:
    config["workflow_version"] = VERSION
    config["specification_revision"] = SPECIFICATION_REVISION
    atomic_write_text(config_path(root), dump_config(config))


def _parse_value(raw: str) -> Any:
    text = raw.strip()
    lower = text.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if text.startswith("[") or text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    try:
        return int(text)
    except ValueError:
        return text


def _set_dotted(config: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cursor = config
    for part in parts[:-1]:
        current = cursor.get(part)
        if not isinstance(current, dict):
            current = {}
            cursor[part] = current
        cursor = current
    cursor[parts[-1]] = value


def _dotted_exists(config: dict[str, Any], dotted: str) -> bool:
    cursor: Any = config
    for part in dotted.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return False
        cursor = cursor[part]
    return True


def _sync_active_phase_field(root: Path, config: dict[str, Any], key: str, value: Any) -> None:
    if key not in {"execution_level", "research_level", "test_profile"}:
        return
    phase_name = str(config.get("current_phase") or "")
    meta_path = root / "phases" / phase_name / "artifacts" / "phase.json"
    if not phase_name or not meta_path.is_file():
        return
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid active phase metadata: {meta_path}: {exc}") from exc
    meta[key] = value
    atomic_write_json(meta_path, meta)


def declared_repository_root(actual_root: Path, config: dict[str, Any], *, strict: bool = False) -> dict[str, Any]:
    repo = dict(config.get("repository", {}))
    mode = str(repo.get("root_mode", "auto"))
    env_var = str(repo.get("env_var", "AW_REPO_ROOT"))
    configured = str(repo.get("root", ""))
    status = "resolved"
    if mode == "auto":
        value = actual_root
    elif mode == "fixed":
        if not configured:
            if strict:
                raise WorkflowError("repository.root_mode=fixed requires repository.root")
            value = actual_root
            status = "fallback_auto_missing_fixed_root"
        else:
            value = Path(configured).expanduser().resolve(strict=False)
    elif mode == "environment":
        raw = os.environ.get(env_var)
        if not raw:
            if strict:
                raise WorkflowError(f"Repository root environment variable is unset: {env_var}")
            return {
                "mode": mode, "configured": configured, "env_var": env_var,
                "resolved": f"${{{env_var}}}", "status": "unresolved_environment",
            }
        value = Path(raw).expanduser().resolve(strict=False)
    elif mode == "cwd":
        value = Path.cwd().resolve()
    else:
        raise WorkflowError(f"Unknown repository.root_mode: {mode}")
    if strict and not (value / ".ai-workflow" / "config.toml").is_file():
        raise WorkflowError(f"Configured repository root lacks .ai-workflow/config.toml: {value}")
    return {"mode": mode, "configured": configured, "env_var": env_var, "resolved": str(value), "status": status}


def cmd_config_show(args: argparse.Namespace) -> int:
    from .models import resolve_routing
    root = find_root(args.root)
    config = load_config(root)
    if args.json:
        value = dict(config)
        value["repository_resolution"] = declared_repository_root(root, config, strict=False)
        value["resolved_routing"] = resolve_routing(root, config)
        print(json.dumps(value, indent=2, ensure_ascii=False))
    else:
        print(dump_config(config), end="")
    return 0


def cmd_config_set(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    config = load_config(root)
    value = _parse_value(args.value)
    if args.key == "mode" and value not in MODES:
        raise WorkflowError(f"mode must be one of: {sorted(MODES)}")
    if args.key == "execution_level" and value not in EXECUTION_LEVELS:
        raise WorkflowError(f"execution_level must be one of: {sorted(EXECUTION_LEVELS)}")
    if args.key == "research_level" and value not in RESEARCH_LEVELS:
        raise WorkflowError(f"research_level must be one of: {sorted(RESEARCH_LEVELS)}")
    if args.key in {"test_profile", "testing.default_profile"} and value not in TEST_PROFILES:
        raise WorkflowError(f"test profile must be one of: {sorted(TEST_PROFILES)}")
    if args.key == "routing_profile" and value not in ROUTING_PROFILES:
        raise WorkflowError(f"routing_profile must be one of: {sorted(ROUTING_PROFILES)}")
    if args.key == "repository.root_mode" and value not in {"auto", "fixed", "environment", "cwd"}:
        raise WorkflowError("repository.root_mode must be auto, fixed, environment, or cwd")
    if args.key == "repository.root" and value:
        target = Path(str(value)).expanduser().resolve(strict=False)
        if not (target / ".ai-workflow" / "config.toml").is_file():
            raise WorkflowError(f"Target is not an initialized workflow repository: {target}")
        value = str(target)
    if args.key == "minor.approval" and value not in {"auto", "request", "phase", "none"}:
        raise WorkflowError("minor.approval must be auto, request, phase, or none")
    if args.key.startswith("phase_lanes.") and value not in {"off", "auto", "on"}:
        raise WorkflowError("phase lane mode must be off, auto, or on")
    if args.key.startswith("dic_views.") and args.key != "dic_views.allow_custom" and value not in {"off", "auto", "on"}:
        raise WorkflowError("DIC view mode must be off, auto, or on")
    if args.key in {"minor.location", "minor.path"}:
        raise WorkflowError("Compatibility Minor is phase-local only; minor.location/path are not configurable")
    if not _dotted_exists(DEFAULT_CONFIG, args.key):
        raise WorkflowError(f"Unknown configuration key: {args.key}")
    if args.key == "mode":
        phase_name = str(config.get("current_phase") or "")
        meta_path = root / "phases" / phase_name / "artifacts" / "phase.json"
        if phase_name and meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            current_mode = str(meta.get("mode", config.get("mode", "goal")))
            if value != current_mode:
                raise WorkflowError(
                    "Cannot change mode of an existing active phase; create or activate a phase "
                    f"with mode {value!r} instead"
                )
    _set_dotted(config, args.key, value)
    save_config(root, config)
    _sync_active_phase_field(root, config, args.key, value)
    print(json.dumps({"root": str(root), "key": args.key, "value": value}, ensure_ascii=False))
    return 0


def cmd_root_show(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    config = load_config(root)
    value = {"operational_root": str(root), **declared_repository_root(root, config, strict=False)}
    print(json.dumps(value, indent=2) if args.json else "\n".join(f"{k}: {v}" for k, v in value.items()))
    return 0


def cmd_root_set(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    target = Path(args.path).expanduser().resolve(strict=False)
    if not (target / ".ai-workflow" / "config.toml").is_file():
        raise WorkflowError(f"Target is not an initialized workflow repository: {target}")
    config = load_config(root)
    config["repository"]["root_mode"] = "fixed"
    config["repository"]["root"] = str(target)
    save_config(root, config)
    print(json.dumps({"root_mode": "fixed", "root": str(target)}))
    return 0


def cmd_root_auto(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    config = load_config(root)
    config["repository"]["root_mode"] = "auto"
    config["repository"]["root"] = ""
    save_config(root, config)
    print(json.dumps({"root_mode": "auto", "root": str(root)}))
    return 0


def cmd_root_env(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    config = load_config(root)
    config["repository"]["root_mode"] = "environment"
    config["repository"]["env_var"] = args.name
    save_config(root, config)
    print(json.dumps({"root_mode": "environment", "env_var": args.name, "current_value": os.environ.get(args.name)}))
    return 0
