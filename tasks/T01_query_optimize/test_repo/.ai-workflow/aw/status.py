from __future__ import annotations

import argparse
import json
from collections import Counter

from .config import declared_repository_root, load_config
from .context import managed_context_sha256
from .filesystem import find_root
from .minor import minor_summary, resolve_minor_root
from .models import resolve_routing
from .phase import resolve_phase
from .prompts import load_registry, ready_prompts
from .requests import request_summary


def build_status(root, phase_name=None):
    config = load_config(root)
    root_resolution = declared_repository_root(root, config, strict=False)
    routing = resolve_routing(root, config)
    phase = resolve_phase(root, phase_name, required=False)
    base = {
        "root": str(root),
        "workflow_version": config["workflow_version"],
        "specification_revision": config.get("specification_revision"),
        "repository": root_resolution,
        "mode_default": config.get("mode"),
        "execution_level_default": config.get("execution_level"),
        "research_level_default": config.get("research_level"),
        "test_profile_default": config.get("test_profile"),
        "routing": routing,
        "auto_continue_after_go": config.get("auto_continue_after_go", True),
    }
    if phase is None:
        return {**base, "phase": None}
    approval = json.loads((phase / "artifacts" / "approval.json").read_text(encoding="utf-8"))
    requests = request_summary(phase)
    registry = load_registry(phase)
    meta = json.loads((phase / "artifacts" / "phase.json").read_text(encoding="utf-8"))
    prompt_counts = Counter(prompt.get("status", "planned") for prompt in registry.get("prompts", []))
    minor = minor_summary(resolve_minor_root(root, phase.name, create=False))
    current_context = managed_context_sha256(root, phase)
    stale = [
        prompt["id"] for prompt in registry.get("prompts", [])
        if prompt.get("status") in {"planned", "ready"} and prompt.get("context_sha256") != current_context
    ]
    health = "GREEN"
    reasons = []
    if stale:
        health = "YELLOW"; reasons.append("safe prompts have stale config context")
    if approval.get("status") != "approved":
        health = "YELLOW"; reasons.append("phase approval pending")
    if requests.get("blocked"):
        health = "YELLOW"; reasons.append("one or more requests are blocked")
    if prompt_counts.get("failed") or prompt_counts.get("blocked"):
        health = "YELLOW"; reasons.append("one or more prompts are blocked or failed")
    from .validation import validate_phase
    validation_errors, validation_warnings = validate_phase(root, phase)
    if validation_errors:
        health = "RED"
        reasons.extend(validation_errors)
    elif validation_warnings and health == "GREEN":
        health = "YELLOW"
        reasons.extend(validation_warnings)
    return {
        **base,
        "phase": phase.name,
        "phase_status": meta.get("status", "active"),
        "mode": meta.get("mode", registry.get("mode", config["mode"])),
        "execution_level": meta.get("execution_level", registry.get("execution_level", config.get("execution_level"))),
        "research_level": meta.get("research_level", registry.get("research_level", config.get("research_level"))),
        "test_profile": meta.get("test_profile", registry.get("test_profile", config.get("test_profile"))),
        "repository": meta.get("repository", root_resolution),
        "approval": approval,
        "requests": {k: v for k, v in requests.items() if k != "items"},
        "prompts": {"counts": dict(prompt_counts), "ready": ready_prompts(registry), "stale_context": stale},
        "minor": minor,
        "context_sha256": current_context,
        "health": {"level": health, "reasons": reasons},
        "validation": {"ok": not validation_errors, "errors": validation_errors, "warnings": validation_warnings},
    }


def cmd_status(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    value = build_status(root, args.phase)
    if args.json:
        print(json.dumps(value, indent=2, ensure_ascii=False))
        return 0
    print(f"Workflow: {value['workflow_version']} ({value.get('specification_revision')})")
    print(f"Operational root: {value['root']}")
    repo = value.get("repository", {})
    print(f"Declared root: {repo.get('resolved', value['root'])} ({repo.get('mode', 'auto')}; {repo.get('status', 'resolved')})")
    print(f"Routing profile: {value['routing']['profile']}")
    print("Declared available models: " + (", ".join(value['routing']['declared_available_models']) or "not declared"))
    if not value.get("phase"):
        print(f"Default mode: {value.get('mode_default')}; execution={value.get('execution_level_default')}; research={value.get('research_level_default')}; test={value.get('test_profile_default')}")
        print("Phase: none")
        return 0
    print(f"Phase: {value['phase']} ({value['mode']}; {value.get('phase_status', 'active')})")
    print(f"Levels: execution={value['execution_level']}; research={value['research_level']}; test={value['test_profile']}")
    print(f"Health: {value['health']['level']}" + (" — " + "; ".join(value['health']['reasons']) if value['health']['reasons'] else ""))
    print(f"Approval: {value['approval']['status']}")
    print(f"Requests: {value['requests']['verified']}/{value['requests']['total']} verified; blocked {', '.join(value['requests']['blocked']) or 'none'}; open {', '.join(value['requests']['open']) or 'none'}")
    print(f"Prompts: {value['prompts']['counts']}")
    print(f"Ready: {', '.join(value['prompts']['ready']) or 'none'}")
    print(f"Stale prompt contexts: {', '.join(value['prompts']['stale_context']) or 'none'}")
    print(f"Minor: {value['minor']['path']}; initialized={value['minor']['initialized']}; open {', '.join(value['minor']['open']) or 'none'}")
    if getattr(args, "full", False):
        print("Role routing:")
        for role, spec in value["routing"]["roles"].items():
            print(
                f"  {role}: preferred={spec.get('selected_preference') or 'none'}; "
                f"effort={spec.get('reasoning') or 'unspecified'}; interface={spec.get('interface') or 'unspecified'}; "
                f"options={', '.join(spec.get('preferred_candidates', [])) or 'none'}"
            )
    return 0
