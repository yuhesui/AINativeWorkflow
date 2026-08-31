from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .constants import MODEL_PROFILES, ROUTING_PROFILES
from .errors import WorkflowError
from .filesystem import find_root


def package_catalog_path(root: Path) -> Path:
    return root / ".ai-workflow" / "package.json"


def load_package_catalog(root: Path) -> dict[str, Any]:
    path = package_catalog_path(root)
    if not path.is_file():
        raise WorkflowError(f"Missing workflow package catalog: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid workflow package catalog: {path}: {exc}") from exc
    profiles = value.get("routing_profiles", {})
    if not isinstance(profiles, dict):
        raise WorkflowError("package.json routing_profiles must be an object")
    return value


def _available(config: dict[str, Any]) -> list[str]:
    value = config.get("models", {}).get("available", [])
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _surfaces(config: dict[str, Any]) -> list[str]:
    value = config.get("models", {}).get("surfaces", [])
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def resolve_routing(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    catalog = load_package_catalog(root)
    profile_name = str(config.get("routing_profile", "all"))
    profiles = catalog.get("routing_profiles", {})
    if profile_name not in ROUTING_PROFILES or profile_name not in profiles:
        raise WorkflowError(f"Unknown routing profile: {profile_name}")
    profile = profiles.get(profile_name, {})
    available = _available(config)
    available_folded = {item.casefold(): item for item in available}
    roles: dict[str, Any] = {}
    for role in sorted(MODEL_PROFILES):
        spec = profile.get(role, {}) if isinstance(profile, dict) else {}
        candidates = [str(x) for x in spec.get("candidates", [])]
        matched = [available_folded[c.casefold()] for c in candidates if c.casefold() in available_folded]
        selected = matched[0] if matched else (candidates[0] if candidates else None)
        availability = "declared_available" if matched else ("not_declared" if available else "unknown_not_declared")
        roles[role] = {
            "selected_preference": selected,
            "preferred_candidates": candidates,
            "declared_available_matches": matched,
            "availability": availability,
            "interface": spec.get("interface"),
            "reasoning": spec.get("reasoning"),
            "fresh_context": bool(spec.get("fresh_context", False)),
        }
    return {
        "profile": profile_name,
        "declared_available_models": available,
        "declared_surfaces": _surfaces(config),
        "availability_note": (
            "Configured availability is user/runtime-declared and must not be treated as provider verification."
        ),
        "roles": roles,
    }


def cmd_models_show(args: argparse.Namespace) -> int:
    from .config import load_config
    root = find_root(args.root)
    value = resolve_routing(root, load_config(root))
    if getattr(args, "json", False):
        print(json.dumps(value, indent=2, ensure_ascii=False))
        return 0
    print(f"Routing profile: {value['profile']}")
    print("Declared available models: " + (", ".join(value["declared_available_models"]) or "not declared"))
    print("Declared surfaces: " + (", ".join(value["declared_surfaces"]) or "not declared"))
    for role, spec in value["roles"].items():
        options = ", ".join(spec["preferred_candidates"]) or "none"
        print(
            f"{role}: preferred={spec['selected_preference'] or 'none'}; "
            f"options=[{options}]; effort={spec['reasoning'] or 'unspecified'}; "
            f"interface={spec['interface'] or 'unspecified'}; availability={spec['availability']}"
        )
    return 0


def cmd_models_profile(args: argparse.Namespace) -> int:
    from .config import load_config, save_config
    root = find_root(args.root)
    if args.profile not in ROUTING_PROFILES:
        raise WorkflowError(f"routing profile must be one of: {sorted(ROUTING_PROFILES)}")
    config = load_config(root)
    config["routing_profile"] = args.profile
    save_config(root, config)
    print(json.dumps({"routing_profile": args.profile, "root": str(root)}))
    return 0


def cmd_models_set_available(args: argparse.Namespace) -> int:
    from .config import load_config, save_config
    root = find_root(args.root)
    values: list[str] = []
    for raw in args.models:
        for item in str(raw).split(","):
            item = item.strip()
            if item and item.casefold() not in {x.casefold() for x in values}:
                values.append(item)
    config = load_config(root)
    config.setdefault("models", {})["available"] = values
    save_config(root, config)
    print(json.dumps({"available_models": values, "root": str(root)}))
    return 0


def cmd_models_set_surfaces(args: argparse.Namespace) -> int:
    from .config import load_config, save_config
    root = find_root(args.root)
    values: list[str] = []
    for raw in args.surfaces:
        for item in str(raw).split(","):
            item = item.strip()
            if item and item.casefold() not in {x.casefold() for x in values}:
                values.append(item)
    config = load_config(root)
    config.setdefault("models", {})["surfaces"] = values
    save_config(root, config)
    print(json.dumps({"surfaces": values, "root": str(root)}))
    return 0
