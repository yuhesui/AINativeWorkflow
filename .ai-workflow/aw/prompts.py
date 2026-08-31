from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .config import declared_repository_root, load_config
from .constants import (
    BACKEND_KINDS,
    DEPENDENCY_DONE,
    EVIDENCE_LEVELS,
    EXECUTION_LEVELS,
    MODEL_PROFILES,
    PROMPT_ID_RE,
    PROMPT_STATUSES,
    ROLE_GUIDES,
    TEST_PROFILES,
)
from .context import managed_context_sha256, render_context_block
from .errors import WorkflowError
from .filesystem import append_jsonl, atomic_write_json, find_root, utc_now, write_if_absent
from .models import resolve_routing
from .phase import resolve_phase


def _registry(phase: Path) -> Path:
    return phase / "artifacts" / "prompt_registry.json"


def load_registry(phase: Path) -> dict:
    path = _registry(phase)
    if not path.is_file():
        raise WorkflowError(f"Missing prompt registry: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid prompt registry: {exc}") from exc


def _save(phase: Path, registry: dict) -> None:
    atomic_write_json(_registry(phase), registry)


def _find(registry: dict, prompt_id: str) -> dict:
    for prompt in registry.get("prompts", []):
        if prompt.get("id") == prompt_id:
            return prompt
    raise WorkflowError(f"Prompt ID not found: {prompt_id}")


def _effective_dependency_done(registry: dict, dependency_id: str) -> bool:
    prompts = {p["id"]: p for p in registry.get("prompts", [])}
    current = dependency_id
    seen: set[str] = set()
    while True:
        if current in seen:
            return False
        seen.add(current)
        prompt = prompts.get(current)
        if prompt is None:
            return False
        status = prompt.get("status", "planned")
        if status in DEPENDENCY_DONE:
            return True
        if status != "superseded":
            return False
        replacement = prompt.get("superseded_by")
        if not isinstance(replacement, str) or not replacement:
            return False
        current = replacement


def _dependencies_done(registry: dict, prompt: dict) -> bool:
    return all(_effective_dependency_done(registry, dep) for dep in prompt.get("depends_on", []))


def ready_prompts(registry: dict) -> list[str]:
    ready = []
    for prompt in registry.get("prompts", []):
        if prompt.get("status") not in {"planned", "ready"}:
            continue
        if _dependencies_done(registry, prompt):
            ready.append(prompt["id"])
    return ready


def _split_csv(raw: str | None) -> list[str]:
    return [value.strip().replace("\\", "/") for value in (raw or "").split(",") if value.strip()]


def _yaml_list(name: str, values: list[str]) -> list[str]:
    return [name + ":"] + ([f'  - "{v}"' for v in values] if values else ["  []"])


def cmd_prompt_add(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    config = load_config(root)
    registry = load_registry(phase)
    if not PROMPT_ID_RE.fullmatch(args.id):
        raise WorkflowError(f"Invalid prompt ID: {args.id}")
    if any(p["id"] == args.id for p in registry.get("prompts", [])):
        raise WorkflowError(f"Duplicate prompt ID: {args.id}")
    if args.model_profile not in MODEL_PROFILES:
        raise WorkflowError(f"Unknown model profile: {args.model_profile}")
    meta = json.loads((phase / "artifacts" / "phase.json").read_text(encoding="utf-8"))
    execution_level = getattr(args, "execution_level", None) or str(meta.get("execution_level", "mid"))
    test_profile = getattr(args, "test_profile", None) or str(meta.get("test_profile", config.get("test_profile", "affected")))
    backend_kind = getattr(args, "backend", None) or "unspecified"
    evidence_target = getattr(args, "evidence_level", None) or "implementation"
    if execution_level not in EXECUTION_LEVELS:
        raise WorkflowError(f"Unknown execution level: {execution_level}")
    if test_profile not in TEST_PROFILES:
        raise WorkflowError(f"Unknown test profile: {test_profile}")
    if backend_kind not in BACKEND_KINDS:
        raise WorkflowError(f"Unknown backend kind: {backend_kind}")
    if evidence_target not in EVIDENCE_LEVELS:
        raise WorkflowError(f"Unknown evidence level: {evidence_target}")
    deps = _split_csv(args.depends_on)
    known = {p["id"] for p in registry.get("prompts", [])}
    missing = set(deps) - known
    if missing:
        raise WorkflowError(f"Unknown dependencies: {sorted(missing)}")
    slug = re.sub(r"[^a-z0-9]+", "_", args.title.lower()).strip("_") or "task"
    relative = f"prompts/prompt_{args.id}_{slug}.md"
    path = phase / relative
    allowed = _split_csv(args.allowed)
    forbidden = _split_csv(args.forbidden)
    outputs = [v.strip().replace("\\", "/") for v in (args.output or []) if v.strip()]
    checks = [v.strip() for v in (args.check or []) if v.strip()]
    repository_root = str(declared_repository_root(root, config, strict=False)["resolved"])
    role_guide = ROLE_GUIDES.get(args.model_profile, ROLE_GUIDES["worker"])
    execution_guide = f".ai-workflow/docs/execution_levels/{execution_level.upper()}.md"
    rough_input = (getattr(args, "rough_input", None) or "").strip()
    routing = resolve_routing(root, config)
    route = routing["roles"].get(args.model_profile, routing["roles"]["worker"])
    context_sha = managed_context_sha256(root, phase)
    lines = ["---", f'prompt_id: "{args.id}"', f'title: "{args.title}"']
    lines += _yaml_list("depends_on", deps)
    lines += [
        f'model_profile: "{args.model_profile}"',
        f'execution_level: "{execution_level}"',
        f'test_profile: "{test_profile}"',
        f'routing_profile: "{config.get("routing_profile", "all")}"',
        f'repository_root: "{repository_root}"',
        f'backend_kind: "{backend_kind}"',
        f'evidence_target: "{evidence_target}"',
        f'context_sha256: "{context_sha}"',
        f'role_guide: "{role_guide}"',
        f'execution_guide: "{execution_guide}"',
        f"requires_approval: {str(not args.no_approval).lower()}",
    ]
    lines += _yaml_list("allowed_paths", allowed)
    lines += _yaml_list("forbidden_paths", forbidden)
    lines += _yaml_list("required_outputs", outputs)
    lines += _yaml_list("required_checks", checks)
    lines += ["---", "", render_context_block(root, phase).rstrip(), "", f"# Prompt {args.id} — {args.title}", "", "## Role", "", f"Act as the bounded `{args.model_profile}` role. Read `{role_guide}` and `{execution_guide}` before acting.", "", "Configured route:", "", "```yaml", f'preferred_model: "{route.get("selected_preference") or "none"}"', f'reasoning: "{route.get("reasoning") or "unspecified"}"', f'interface: "{route.get("interface") or "unspecified"}"', "```", "", "The configured model is a preference, not proof of actual availability. Record the actual model and permissions when exposed.", "", "## Repository", "", f"- Repository root: `{repository_root}`", f"- Phase: `{phase.name}`", f"- Backend target: `{backend_kind}`", f"- Evidence target: `{evidence_target}`", f"- Test profile: `{test_profile}`", "- Work only inside the resolved repository and declared path authority.", "", "## Rough input / user wording", "", rough_input or "<!-- Preserve the exact rough input or request fragment that motivated this prompt. -->", "", "## Objective", "", "<!-- One observable outcome. State what must exist or work when the task is complete. -->", "", "## Requirement mapping", "", "<!-- List the REQUESTS.md IDs and acceptance criteria this prompt advances. -->", "", "## Read first", "", "1. Repository `AGENTS.md` and `agent.manifest.yaml`.", "2. Current phase `README.md`, and `GOAL.md` or `PLAN.md`.", "3. `REQUESTS.md` when it exists or after Goal Mode materialization.", "4. Dependency logs/evidence named above.", "5. Existing implementation and tests relevant to this bounded task.", "", "## Preconditions and readiness", "", "- Confirm every dependency is integrated with evidence.", "- Confirm phase approval when required.", "- Confirm required inputs, permissions, backend identity and rollback state.", "- Stop before mutation when readiness cannot be established.", "", "## Allowed changes", ""]
    lines += ([f"- `{v}`" for v in allowed] if allowed else ["- No product-path change is authorized until Orchestrator fills this section."])
    lines += ["", "## Forbidden changes", ""]
    lines += ([f"- `{v}`" for v in forbidden] if forbidden else ["- Do not broaden scope, alter unrelated files, or cross external/destructive/costly boundaries."])
    lines += ["", "## Required work", "", "1. Inspect the current implementation before editing.", "2. Make the smallest coherent change that satisfies the objective.", "3. Preserve compatibility and historical evidence unless supersession is explicit.", "4. Add or update tests according to the configured risk-adaptive test profile.", "5. Preserve decisive failures and clean temporary files.", "", "## Required outputs", ""]
    lines += ([f"- `{v}`" for v in outputs] if outputs else ["- Define exact output paths before running."])
    lines += ["", "## Validation", ""]
    lines += ([f"- `{v}`" for v in checks] if checks else [f"- Apply the `{test_profile}` risk-adaptive test profile and define deterministic checks before running."])
    lines += ["", "## Evidence and logging", "", f"- Write the declared prompt log under `{phase.name}/logs/` or the registry log path.", "- Record files read, files changed, exact commands, results, artifacts and caveats.", "- Record actual model/interface/effort/permissions when available.", "- Distinguish configured, implemented, smoke, pilot, locked and independently verified evidence.", "- Preserve decisive raw failures or a recoverable path to them.", "", "## Recovery and stop conditions", "", "- Recoverable local defect: diagnose, bounded repair, rerun and continue.", "- Stop and escalate on path-authority mismatch, semantic contract conflict, backend mismatch, data leakage, destructive risk, new external/costly action, or material acceptance change.", "- Do not claim completion when a required output or check is missing.", "", "## Return contract", "", "```text", f"Prompt ID: {args.id}", "Task performed:", "Actual model / interface / effort / permissions:", "Files read:", "Files changed:", "Commands run:", "Backend identity:", "Evidence level achieved:", "Evidence produced:", "Validation result:", "Caveats:", "Open blockers:", "Recommended next action:", "```", ""]
    if write_if_absent(path, "\n".join(lines)) == "skipped":
        raise WorkflowError(f"Prompt file already exists: {path}")
    record = {
        "id": args.id, "file": relative, "title": args.title, "depends_on": deps,
        "status": "planned", "requires_approval": not args.no_approval,
        "model_profile": args.model_profile, "execution_level": execution_level,
        "test_profile": test_profile, "routing_profile": str(config.get("routing_profile", "all")),
        "repository_root": repository_root, "backend_kind": backend_kind,
        "evidence_target": evidence_target, "context_sha256": context_sha,
        "model_options": route.get("preferred_candidates", []),
        "preferred_model": route.get("selected_preference"),
        "role_guide": role_guide, "execution_guide": execution_guide,
        "allowed_paths": allowed, "forbidden_paths": forbidden,
        "required_outputs": outputs, "required_checks": checks, "evidence": [],
    }
    registry.setdefault("prompts", []).append(record)
    _save(phase, registry)
    append_jsonl(phase / "artifacts" / "prompt_events.jsonl", {
        "event": "added", "prompt_id": args.id, "record": record,
        "actor": "orchestrator", "at": utc_now(),
    })
    if not getattr(args, "suppress_output", False):
        print(json.dumps({
            "prompt_id": args.id, "file": relative, "execution_level": execution_level,
            "test_profile": test_profile, "preferred_model": route.get("selected_preference"),
        }, ensure_ascii=False))
    return 0


_ALLOWED_TRANSITIONS = {
    "planned": {"ready", "running", "blocked", "superseded"},
    "ready": {"running", "blocked", "superseded"},
    "running": {"completed", "blocked", "failed"},
    "completed": {"integrated", "blocked", "failed"},
    "integrated": {"verified", "blocked", "superseded"},
    "verified": {"superseded"},
    "blocked": {"ready", "running", "failed", "superseded"},
    "failed": {"ready", "running", "superseded"},
    "superseded": set(),
}


def cmd_prompt_set(args: argparse.Namespace) -> int:
    if args.status not in PROMPT_STATUSES:
        raise WorkflowError(f"Invalid prompt status: {args.status}")
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    registry = load_registry(phase)
    prompt = _find(registry, args.id)
    current = prompt.get("status", "planned")
    actor = (args.actor or "orchestrator").strip().lower()
    if args.status != current and args.status not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise WorkflowError(f"Illegal prompt transition: {args.id} {current} -> {args.status}")
    if args.status == "running" and not _dependencies_done(registry, prompt):
        raise WorkflowError(f"Prompt dependencies are not integrated: {args.id}")
    if prompt.get("requires_approval") and args.status in {"running", "completed", "integrated", "verified"}:
        approval = json.loads((phase / "artifacts" / "approval.json").read_text(encoding="utf-8"))
        if approval.get("status") != "approved":
            raise WorkflowError(f"Prompt {args.id} requires approved phase GO")
    if args.status in {"completed", "integrated", "verified"} and not args.evidence:
        raise WorkflowError(f"Evidence is required for prompt status {args.status}")
    if args.status == "verified" and actor != "verifier":
        raise WorkflowError("Only actor 'verifier' may set prompt status verified")
    if args.status == "integrated" and actor not in {"orchestrator", "main"}:
        raise WorkflowError("Only Main or Orchestrator may integrate a prompt")
    prompt["status"] = args.status
    if args.evidence:
        prompt.setdefault("evidence", []).append(args.evidence)
    if args.note:
        prompt["note"] = args.note
    _save(phase, registry)
    append_jsonl(phase / "artifacts" / "prompt_events.jsonl", {
        "event": "status", "prompt_id": args.id, "previous_status": current,
        "status": args.status, "actor": actor, "evidence": args.evidence,
        "note": args.note, "at": utc_now(),
    })
    print(json.dumps({"prompt_id": args.id, "status": args.status, "actor": actor}))
    return 0


def cmd_prompt_supersede(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    registry = load_registry(phase)
    prompt = _find(registry, args.id)
    replacement = _find(registry, args.replacement)
    if prompt["id"] == replacement["id"]:
        raise WorkflowError("A prompt cannot supersede itself")
    if prompt.get("status") == "superseded":
        raise WorkflowError(f"Prompt already superseded: {args.id}")
    previous = prompt.get("status", "planned")
    prompt.update({"status": "superseded", "superseded_by": args.replacement, "supersession_reason": args.reason})
    _save(phase, registry)
    append_jsonl(phase / "artifacts" / "prompt_events.jsonl", {
        "event": "superseded", "prompt_id": args.id, "previous_status": previous,
        "replacement": args.replacement, "reason": args.reason,
        "actor": "orchestrator", "at": utc_now(),
    })
    print(json.dumps({"prompt_id": args.id, "status": "superseded", "replacement": args.replacement}))
    return 0


def cmd_prompt_list(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    registry = load_registry(phase)
    if args.json:
        print(json.dumps(registry.get("prompts", []), indent=2))
    else:
        ready = set(ready_prompts(registry))
        for prompt in registry.get("prompts", []):
            suffix = " (ready)" if prompt["id"] in ready else ""
            replacement = f" -> {prompt.get('superseded_by')}" if prompt.get("superseded_by") else ""
            model = prompt.get("preferred_model") or "unresolved"
            print(f"{prompt['id']}: {prompt.get('status', 'planned')}{suffix}{replacement} — {prompt.get('title', '')} [{model}]")
    return 0


def cmd_prompt_next(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    registry = load_registry(phase)
    ready_ids = ready_prompts(registry)
    ready_records = [_find(registry, prompt_id) for prompt_id in ready_ids]
    value = {
        "phase": phase.name,
        "mode": registry.get("mode"),
        "repository_root": json.loads((phase / "artifacts" / "phase.json").read_text(encoding="utf-8")).get("repository", {}).get("resolved", str(root)),
        "routing_profile": registry.get("routing_profile"),
        "ready": ready_records,
    }
    if getattr(args, "print_prompt", False):
        if not ready_records:
            print("none")
            return 0
        if len(ready_records) > 1 and not getattr(args, "id", None):
            raise WorkflowError("Multiple prompts are ready; use --id with --print")
        selected = _find(registry, args.id) if getattr(args, "id", None) else ready_records[0]
        if selected["id"] not in ready_ids:
            raise WorkflowError(f"Prompt is not ready: {selected['id']}")
        print((phase / selected["file"]).read_text(encoding="utf-8"), end="")
        return 0
    if args.json:
        print(json.dumps(value, indent=2, ensure_ascii=False))
    else:
        if not ready_records:
            print("none")
        for prompt in ready_records:
            options = ", ".join(prompt.get("model_options", [])) or "not configured"
            print(
                f"{prompt['id']} | {prompt['file']} | profile={prompt.get('model_profile')} | "
                f"preferred={prompt.get('preferred_model') or 'unresolved'} | options={options} | "
                f"test={prompt.get('test_profile')} | backend={prompt.get('backend_kind')} | evidence={prompt.get('evidence_target')}"
            )
    return 0
