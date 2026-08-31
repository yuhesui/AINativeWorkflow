from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from .config import declared_repository_root, load_config
from .context import managed_context_sha256, render_context_block, replace_managed_context
from .errors import WorkflowError
from .filesystem import atomic_write_json, atomic_write_text, find_root, utc_now
from .models import resolve_routing
from .phase import resolve_phase
from .prompts import load_registry

TERMINAL_PROMPT_STATUSES = {"running", "completed", "integrated", "verified", "failed", "superseded"}


def _replace_frontmatter_scalar(text: str, key: str, value: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end < 0:
        return text
    head = text[:end]
    body = text[end:]
    pattern = re.compile(rf"^{re.escape(key)}:\s*.*$", re.MULTILINE)
    rendered = f'{key}: {json.dumps(value, ensure_ascii=False)}'
    if pattern.search(head):
        head = pattern.sub(rendered, head)
    else:
        head = head.rstrip() + "\n" + rendered
    return head + body


def _update_manifest(root: Path, config: dict[str, Any]) -> bool:
    path = root / "agent.manifest.yaml"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    repository = declared_repository_root(root, config, strict=False)
    fields = {
        "workflow_version": str(config.get("workflow_version")),
        "specification_revision": str(config.get("specification_revision")),
        "repository_root": str(repository.get("resolved", root)),
        "current_phase": str(config.get("current_phase") or ""),
        "default_mode": str(config.get("mode")),
        "default_execution_level": str(config.get("execution_level")),
        "default_research_level": str(config.get("research_level")),
        "default_test_profile": str(config.get("test_profile")),
        "routing_profile": str(config.get("routing_profile")),
    }
    changed = False
    for key, value in fields.items():
        pattern = re.compile(rf"^{re.escape(key)}:\s*.*$", re.MULTILINE)
        line = f'{key}: "{value}"'
        if pattern.search(text):
            new = pattern.sub(lambda _match, replacement=line: replacement, text)
        else:
            new = text.rstrip() + "\n" + line + "\n"
        if new != text:
            changed = True
            text = new
    if changed:
        atomic_write_text(path, text)
    return changed


def _update_agents(root: Path, block: str) -> bool:
    path = root / "AGENTS.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    updated, changed = replace_managed_context(text, block)
    if changed:
        atomic_write_text(path, updated)
    return changed


def update_phase(root: Path, phase: Path, *, dry_run: bool, include_frozen: bool) -> dict[str, Any]:
    config = load_config(root)
    meta_path = phase / "artifacts" / "phase.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    registry = load_registry(phase)
    repository = declared_repository_root(root, config, strict=False)
    context_block = render_context_block(root, phase)
    context_sha = managed_context_sha256(root, phase)
    routing = resolve_routing(root, config)
    configured_statuses = config.get("update", {}).get("prompt_statuses", ["planned", "ready"])
    allowed_statuses = set(configured_statuses if isinstance(configured_statuses, list) else ["planned", "ready"])
    changed_files: list[str] = []
    skipped: list[dict[str, str]] = []
    prompt_changes: list[str] = []

    for prompt in registry.get("prompts", []):
        status = str(prompt.get("status", "planned"))
        if status not in allowed_statuses and not include_frozen:
            skipped.append({"prompt_id": prompt["id"], "status": status, "reason": "terminal_or_not_configured_for_update"})
            continue
        file = phase / str(prompt.get("file"))
        if not file.is_file():
            skipped.append({"prompt_id": prompt["id"], "status": status, "reason": "missing_prompt_file"})
            continue
        text = file.read_text(encoding="utf-8")
        updated, block_changed = replace_managed_context(text, context_block)
        updated = _replace_frontmatter_scalar(updated, "repository_root", str(repository["resolved"]))
        updated = _replace_frontmatter_scalar(updated, "routing_profile", str(config.get("routing_profile", "all")))
        updated = _replace_frontmatter_scalar(updated, "execution_level", str(meta.get("execution_level", config.get("execution_level", "mid"))))
        updated = _replace_frontmatter_scalar(updated, "test_profile", str(meta.get("test_profile", config.get("test_profile", "affected"))))
        updated = _replace_frontmatter_scalar(updated, "context_sha256", context_sha)
        role = str(prompt.get("model_profile", "worker"))
        route = routing["roles"].get(role, routing["roles"].get("worker", {}))
        prompt["repository_root"] = str(repository["resolved"])
        prompt["routing_profile"] = str(config.get("routing_profile", "all"))
        prompt["execution_level"] = str(meta.get("execution_level", config.get("execution_level", "mid")))
        prompt["test_profile"] = str(meta.get("test_profile", config.get("test_profile", "affected")))
        prompt["context_sha256"] = context_sha
        prompt["model_options"] = list(route.get("preferred_candidates", []))
        prompt["preferred_model"] = route.get("selected_preference")
        if updated != text:
            prompt_changes.append(prompt["id"])
            changed_files.append(str(file.relative_to(root)).replace("\\", "/"))
            if not dry_run:
                atomic_write_text(file, updated)

    # Refresh config-managed context in phase-local role prompts, phase contracts and copied
    # full prompt references. Only the marked block is changed, so user-authored content remains intact.
    context_targets: list[Path] = []
    goal_terminal = any(
        prompt.get("id") == "GOAL" and str(prompt.get("status", "planned")) in TERMINAL_PROMPT_STATUSES
        for prompt in registry.get("prompts", [])
    )
    for candidate in (
        phase / "GOAL.md", phase / "README.md", phase / "PLAN.md",
        phase / "ARCHITECTURE.md", phase / "EXECUTION_CONTRACT.md",
        phase / "minor" / "prompt_000_minor_init.md",
    ):
        if candidate.name == "GOAL.md" and goal_terminal and not include_frozen:
            skipped.append({"prompt_id": "GOAL", "status": "terminal", "reason": "terminal_goal_contract_context_protected"})
            continue
        if candidate.is_file():
            context_targets.append(candidate)
    templates_dir = phase / "templates"
    if templates_dir.is_dir():
        context_targets.extend(sorted(path for path in templates_dir.rglob("*.md") if path.is_file()))
    for candidate in context_targets:
        text = candidate.read_text(encoding="utf-8")
        if "<!-- AW:CONFIG:BEGIN -->" not in text and "{{WORKFLOW_CONTEXT}}" not in text:
            continue
        updated, changed = replace_managed_context(text, context_block)
        if changed:
            rel = str(candidate.relative_to(root)).replace("\\", "/")
            if rel not in changed_files:
                changed_files.append(rel)
            if not dry_run:
                atomic_write_text(candidate, updated)

    meta["repository"] = {"operational_root": str(root), **repository}
    meta["routing_profile"] = str(config.get("routing_profile", "all"))
    meta["test_profile"] = str(meta.get("test_profile", config.get("test_profile", "affected")))
    meta["context_sha256"] = context_sha
    meta["model_context"] = routing
    meta["minor"] = {"location": "phase", "path": "minor", "approval": str(config.get("minor", {}).get("approval", "auto"))}
    registry["routing_profile"] = str(config.get("routing_profile", "all"))
    registry["mode"] = str(meta.get("mode", config.get("mode", "goal")))
    registry["execution_level"] = str(meta.get("execution_level", config.get("execution_level", "mid")))
    registry["research_level"] = str(meta.get("research_level", config.get("research_level", "none")))
    registry["test_profile"] = meta["test_profile"]
    registry["context_sha256"] = context_sha
    if not dry_run:
        atomic_write_json(meta_path, meta)
        atomic_write_json(phase / "artifacts" / "prompt_registry.json", registry)
        atomic_write_json(phase / "artifacts" / "last_update.json", {
            "schema_version": "1", "updated_at": utc_now(), "context_sha256": context_sha,
            "changed_files": changed_files, "prompt_ids": prompt_changes,
            "skipped": skipped, "include_frozen": include_frozen,
        })
    return {
        "phase": phase.name,
        "context_sha256": context_sha,
        "changed_files": changed_files,
        "prompt_ids": prompt_changes,
        "skipped": skipped,
    }


def cmd_update(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    config = load_config(root)
    dry_run = bool(getattr(args, "dry_run", False))
    include_frozen = bool(getattr(args, "include_frozen", False))
    if getattr(args, "all_phases", False):
        phases = sorted(path for path in (root / "phases").glob("phase_*") if path.is_dir())
    else:
        selected = resolve_phase(root, getattr(args, "phase", None), required=False)
        phases = [selected] if selected is not None else []
    root_changes: list[str] = []
    if bool(config.get("update", {}).get("include_root_files", True)) and not getattr(args, "no_root_files", False):
        block = render_context_block(root, None)
        if dry_run:
            for name in ("AGENTS.md", "agent.manifest.yaml"):
                if (root / name).is_file():
                    root_changes.append(name)
        else:
            if _update_agents(root, block):
                root_changes.append("AGENTS.md")
            if _update_manifest(root, config):
                root_changes.append("agent.manifest.yaml")
    results = [update_phase(root, phase, dry_run=dry_run, include_frozen=include_frozen) for phase in phases]
    value = {
        "root": str(root), "dry_run": dry_run, "include_frozen": include_frozen,
        "root_files": root_changes, "phases": results,
    }
    print(json.dumps(value, indent=2, ensure_ascii=False))
    return 0
