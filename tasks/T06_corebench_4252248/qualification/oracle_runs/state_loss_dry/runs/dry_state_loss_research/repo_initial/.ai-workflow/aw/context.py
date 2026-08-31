from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import declared_repository_root, load_config
from .constants import MANAGED_CONTEXT_BEGIN, MANAGED_CONTEXT_END, VERSION
from .models import resolve_routing


def _phase_meta(phase: Path | None) -> dict[str, Any]:
    if phase is None:
        return {}
    path = phase / "artifacts" / "phase.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_context(root: Path, phase: Path | None = None) -> dict[str, Any]:
    config = load_config(root)
    meta = _phase_meta(phase)
    repository = declared_repository_root(root, config, strict=False)
    mode = str(meta.get("mode", config.get("mode", "goal")))
    execution_level = str(meta.get("execution_level", config.get("execution_level", "mid")))
    research_level = str(meta.get("research_level", config.get("research_level", "none")))
    test_profile = str(meta.get("test_profile", config.get("test_profile", config.get("testing", {}).get("default_profile", "affected"))))
    routing = resolve_routing(root, config)
    value: dict[str, Any] = {
        "workflow_version": VERSION,
        "specification_revision": str(config.get("specification_revision", "")),
        "phase_id": phase.name if phase is not None else None,
        "mode": mode,
        "execution_level": execution_level,
        "research_level": research_level,
        "test_profile": test_profile,
        "repository": {
            "operational_root": str(root),
            **repository,
        },
        "routing": routing,
        "minor": {
            "location": "phase",
            "path": f"phases/{phase.name}/minor" if phase is not None else "phases/<phase>/minor",
            "approval": str(config.get("minor", {}).get("approval", "auto")),
        },
        "approval_phrase": str(meta.get("approval_phrase", config.get("approval_phrase", "GO"))),
        "testing": dict(config.get("testing", {})),
    }
    fingerprint_basis = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    value["context_sha256"] = hashlib.sha256(fingerprint_basis).hexdigest()
    return value


def render_context_block(root: Path, phase: Path | None = None) -> str:
    value = build_context(root, phase)
    routing = value["routing"]
    lines = [
        MANAGED_CONTEXT_BEGIN,
        "## Active workflow configuration",
        "",
        "This block is generated from `.ai-workflow/config.toml`, `.ai-workflow/package.json`,",
        "and the phase metadata. Refresh safe prompts with `aw update` after configuration changes.",
        "",
        "```yaml",
        f'workflow_version: "{value["workflow_version"]}"',
        f'specification_revision: "{value["specification_revision"]}"',
        f'phase_id: "{value["phase_id"] or "none"}"',
        f'mode: "{value["mode"]}"',
        f'execution_level: "{value["execution_level"]}"',
        f'research_level: "{value["research_level"]}"',
        f'test_profile: "{value["test_profile"]}"',
        f'repository_root: "{value["repository"]["resolved"]}"',
        f'repository_root_mode: "{value["repository"]["mode"]}"',
        f'routing_profile: "{routing["profile"]}"',
        "declared_available_models:",
    ]
    if routing["declared_available_models"]:
        lines.extend(f'  - "{item}"' for item in routing["declared_available_models"])
    else:
        lines.append("  []")
    lines.append("declared_agent_surfaces:")
    if routing["declared_surfaces"]:
        lines.extend(f'  - "{item}"' for item in routing["declared_surfaces"])
    else:
        lines.append("  []")
    lines.append("role_routing:")
    for role in ("main", "orchestrator", "worker_complex", "worker", "minor", "verifier", "research"):
        spec = routing["roles"].get(role, {})
        lines.extend([
            f"  {role}:",
            f'    preferred: "{spec.get("selected_preference") or "none"}"',
            f'    reasoning: "{spec.get("reasoning") or "unspecified"}"',
            f'    interface: "{spec.get("interface") or "unspecified"}"',
            f'    availability: "{spec.get("availability") or "unknown"}"',
        ])
        candidates = spec.get("preferred_candidates", [])
        lines.append("    options:")
        if candidates:
            lines.extend(f'      - "{item}"' for item in candidates)
        else:
            lines.append("      []")
    lines.extend([
        "minor:",
        f'  path: "{value["minor"]["path"]}"',
        f'  approval: "{value["minor"]["approval"]}"',
        f'approval_phrase: "{value["approval_phrase"]}"',
        f'context_sha256: "{value["context_sha256"]}"',
        "```",
        "",
        "Model availability above is configuration/runtime-declared, not provider-verified. Record the",
        "actual model, interface, effort and permissions in the prompt log when the execution surface exposes them.",
        MANAGED_CONTEXT_END,
    ])
    return "\n".join(lines) + "\n"


def managed_context_sha256(root: Path, phase: Path | None = None) -> str:
    return str(build_context(root, phase)["context_sha256"])


def replace_managed_context(text: str, block: str) -> tuple[str, bool]:
    start = text.find(MANAGED_CONTEXT_BEGIN)
    end = text.find(MANAGED_CONTEXT_END)
    if start >= 0 and end >= start:
        end += len(MANAGED_CONTEXT_END)
        suffix = text[end:]
        if suffix.startswith("\n"):
            suffix = suffix[1:]
        updated = text[:start].rstrip() + "\n\n" + block.rstrip() + "\n\n" + suffix.lstrip("\n")
        return updated.rstrip() + "\n", updated.rstrip() != text.rstrip()
    insert_at = 0
    if text.startswith("---\n"):
        closing = text.find("\n---\n", 4)
        if closing >= 0:
            insert_at = closing + len("\n---\n")
    prefix = text[:insert_at].rstrip()
    suffix = text[insert_at:].lstrip("\n")
    updated = (prefix + "\n\n" if prefix else "") + block.rstrip() + "\n\n" + suffix
    return updated.rstrip() + "\n", True
