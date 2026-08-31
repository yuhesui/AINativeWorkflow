from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path

from .config import load_config
from .constants import (
    BACKEND_KINDS,
    EVIDENCE_LEVELS,
    EXECUTION_LEVELS,
    MODEL_PROFILES,
    MODES,
    PROMPT_ID_RE,
    PROMPT_STATUSES,
    RESEARCH_LEVELS,
    ROUTING_PROFILES,
    TEST_PROFILES,
    VERSION,
)
from .context import managed_context_sha256
from .errors import WorkflowError
from .filesystem import find_root
from .minor import resolve_minor_root
from .models import load_package_catalog
from .phase import resolve_phase, scope_hash
from .prompts import _dependencies_done, load_registry
from .requests import load_request_events, parse_goal_acceptance, parse_requests


def _events(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    result = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"Invalid JSONL {path}:{number}: {exc}") from exc
    return result


def _scalar(value: str):
    value = value.strip()
    if value in {"[]", "{}"}:
        return [] if value == "[]" else {}
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        raise WorkflowError("Prompt lacks YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise WorkflowError("Prompt frontmatter is not terminated")
    lines = text[4:end].splitlines()
    result = {}
    current = None
    for line in lines:
        if re.match(r"^\s+-\s+", line):
            if current is None:
                raise WorkflowError("Frontmatter list item has no key")
            result.setdefault(current, []).append(_scalar(re.sub(r"^\s+-\s+", "", line)))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current = key.strip()
        parsed = _scalar(value)
        result[current] = [] if value.strip() == "" else parsed
    return result


def _path_covered(path: str, patterns: list[str]) -> bool:
    value = path.replace("\\", "/").lstrip("./")
    for pattern in patterns:
        p = pattern.replace("\\", "/").lstrip("./")
        if p in {"*", "**", "**/*"}:
            return True
        if p.endswith("/**") and (value == p[:-3].rstrip("/") or value.startswith(p[:-3])):
            return True
        if fnmatch.fnmatch(value, p):
            return True
    return False


def _validate_minor_events(path: Path, errors: list[str]) -> None:
    state = {}
    for event in _events(path / "events.jsonl"):
        request_id = event.get("id")
        if not request_id:
            continue
        status = event.get("status")
        if event.get("event") == "terminal" and state.get(request_id) not in {"approved", "approved_by_phase"}:
            errors.append(f"Minor terminal event preceded approval: {request_id}")
        if status:
            state[request_id] = status


def validate_phase(root: Path, phase: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    config = load_config(root)
    catalog = load_package_catalog(root)
    if str(catalog.get("version")) != VERSION:
        errors.append(f"package.json version differs from runtime: {catalog.get('version')} != {VERSION}")
    meta_path = phase / "artifacts" / "phase.json"
    if not meta_path.is_file():
        return ["Missing artifacts/phase.json"], warnings
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid artifacts/phase.json: {exc}"], warnings
    mode = meta.get("mode", config["mode"])
    if mode not in MODES:
        errors.append(f"Invalid phase mode: {mode}")
    approval_path = phase / "artifacts" / "approval.json"
    approval = json.loads(approval_path.read_text(encoding="utf-8")) if approval_path.is_file() else {"status": "missing"}

    required = ["README.md", "artifacts/prompt_registry.json", "artifacts/approval.json"]
    minor_mode = str(meta.get("phase_lanes", {}).get("minor", config.get("phase_lanes", {}).get("minor", "auto")))
    if minor_mode == "on":
        required += ["minor/REQUESTS.md", "minor/prompt_000_minor_init.md"]
    if mode == "goal":
        required.append("GOAL.md")
        if approval.get("status") == "approved":
            required.append("REQUESTS.md")
    else:
        required += ["prompts/prompt_000_orchestrator_init.md"]
        required += ["REQUESTS.md", "PLAN.md", "USER_APPROVAL.md"]
        if meta.get("templates", {}).get("architecture_created"):
            required.append("ARCHITECTURE.md")
    for name in required:
        if not (phase / name).is_file():
            errors.append(f"Missing required file for {mode} mode: {name}")

    if mode == "goal":
        try:
            goals = parse_goal_acceptance(phase / "GOAL.md")
        except WorkflowError as exc:
            errors.append(str(exc)); goals = []
        if not goals:
            warnings.append("GOAL.md contains no G-### acceptance items; GO cannot be recorded")
        for item in goals:
            if not item.get("acceptance"):
                errors.append(f"Goal item lacks Acceptance criterion: {item['goal_id']}")

    requests = parse_requests(phase / "REQUESTS.md", required=False)
    if mode == "structured" and not requests:
        warnings.append("REQUESTS.md contains no checklist items; GO cannot be recorded")
    if approval.get("status") == "approved" and not requests:
        errors.append("Approved phase has no materialized acceptance-bearing requests")
    request_ids = [item["id"] for item in requests]
    if len(request_ids) != len(set(request_ids)):
        errors.append("Duplicate request ID in REQUESTS.md")
    for item in requests:
        if not item.get("acceptance"):
            errors.append(f"Request lacks Acceptance criterion: {item['id']}")
    events = load_request_events(phase / "artifacts" / "request_events.jsonl")
    latest = {}
    for event in events:
        if event.get("request_id"):
            latest[event["request_id"]] = event
    for request_id in latest:
        if request_id not in set(request_ids):
            errors.append(f"Request event references unknown ID: {request_id}")
    for item in requests:
        event = latest.get(item["id"], {})
        if item["verified"]:
            if event.get("event") != "verified" or event.get("actor") != "verifier" or not event.get("evidence"):
                errors.append(f"Checked request lacks current verifier evidence: {item['id']}")
        elif event.get("event") == "verified":
            errors.append(f"Verifier event exists but request is unchecked: {item['id']}")

    try:
        registry = load_registry(phase)
    except WorkflowError as exc:
        errors.append(str(exc)); registry = {"prompts": []}
    if meta.get("execution_level") not in EXECUTION_LEVELS:
        errors.append(f"Invalid phase execution level: {meta.get('execution_level')}")
    if meta.get("research_level") not in RESEARCH_LEVELS:
        errors.append(f"Invalid phase research level: {meta.get('research_level')}")
    if meta.get("test_profile") not in TEST_PROFILES:
        errors.append(f"Invalid phase test profile: {meta.get('test_profile')}")
    if meta.get("routing_profile") not in ROUTING_PROFILES:
        errors.append(f"Invalid phase routing profile: {meta.get('routing_profile')}")
    for field in ("execution_level", "research_level", "test_profile", "routing_profile"):
        if registry.get(field, meta.get(field)) != meta.get(field):
            errors.append(f"Prompt registry {field} differs from phase metadata")
    if registry.get("mode", meta.get("mode")) != meta.get("mode"):
        errors.append("Prompt registry mode differs from phase metadata")
    prompt_ids = [prompt.get("id") for prompt in registry.get("prompts", [])]
    if len(prompt_ids) != len(set(prompt_ids)):
        errors.append("Duplicate prompt ID in registry")
    known = set(prompt_ids)
    prompt_events = _events(phase / "artifacts" / "prompt_events.jsonl")
    latest_prompt_status = {}
    latest_prompt_event = {}
    for event in prompt_events:
        if event.get("prompt_id"):
            latest_prompt_event[event["prompt_id"]] = event
            if event.get("status"):
                latest_prompt_status[event["prompt_id"]] = event.get("status")

    current_context = managed_context_sha256(root, phase)
    parity_fields = (
        "title", "depends_on", "model_profile", "execution_level", "test_profile",
        "routing_profile", "repository_root", "backend_kind", "evidence_target",
        "context_sha256", "requires_approval", "allowed_paths", "forbidden_paths",
        "required_outputs", "required_checks",
    )
    for prompt in registry.get("prompts", []):
        prompt_id = prompt.get("id")
        if not isinstance(prompt_id, str) or not PROMPT_ID_RE.fullmatch(prompt_id):
            errors.append(f"Invalid prompt ID: {prompt_id}"); continue
        if prompt.get("status") not in PROMPT_STATUSES:
            errors.append(f"Invalid prompt status for {prompt_id}: {prompt.get('status')}")
        status = prompt.get("status", "planned")
        if status in {"ready", "running", "completed", "integrated", "verified"} and not _dependencies_done(registry, prompt):
            errors.append(f"Prompt advanced before effective dependencies completed: {prompt_id}")
        if status in {"completed", "integrated", "verified"} and not prompt.get("evidence"):
            errors.append(f"Prompt status {status} lacks evidence: {prompt_id}")
        if prompt.get("model_profile") not in MODEL_PROFILES:
            errors.append(f"Invalid model profile for {prompt_id}: {prompt.get('model_profile')}")
        if prompt.get("execution_level") not in EXECUTION_LEVELS:
            errors.append(f"Invalid execution level for {prompt_id}: {prompt.get('execution_level')}")
        if prompt.get("test_profile") not in TEST_PROFILES:
            errors.append(f"Invalid test profile for {prompt_id}: {prompt.get('test_profile')}")
        if prompt.get("routing_profile") not in ROUTING_PROFILES:
            errors.append(f"Invalid routing profile for {prompt_id}: {prompt.get('routing_profile')}")
        if prompt.get("backend_kind") not in BACKEND_KINDS:
            errors.append(f"Invalid backend kind for {prompt_id}: {prompt.get('backend_kind')}")
        if prompt.get("evidence_target") not in EVIDENCE_LEVELS:
            errors.append(f"Invalid evidence target for {prompt_id}: {prompt.get('evidence_target')}")
        if not prompt.get("repository_root"):
            errors.append(f"Prompt lacks repository_root: {prompt_id}")
        missing = set(prompt.get("depends_on", [])) - known
        if missing:
            errors.append(f"Prompt {prompt_id} has missing dependencies: {sorted(missing)}")
        relative = str(prompt.get("file", ""))
        file = (phase / relative).resolve(strict=False)
        try:
            file.relative_to(phase.resolve())
        except ValueError:
            errors.append(f"Prompt file escapes phase: {prompt_id}: {relative}"); continue
        if not file.is_file():
            errors.append(f"Missing prompt file for {prompt_id}: {relative}"); continue
        if prompt_id == "GOAL" and relative == "GOAL.md":
            # In Goal Mode the approved GOAL.md is the direct Orchestrator initialization artifact.
            # It is a durable intent contract, not a YAML-frontmatter execution prompt.
            continue
        if f"prompt_{prompt_id}_" not in file.name and file.name != f"prompt_{prompt_id}.md":
            errors.append(f"Prompt filename does not contain its ID: {prompt_id}: {file.name}")
        try:
            front = _frontmatter(file.read_text(encoding="utf-8"))
        except WorkflowError as exc:
            errors.append(f"Prompt {prompt_id}: {exc}"); continue
        if str(front.get("prompt_id")) != prompt_id:
            errors.append(f"Prompt frontmatter ID mismatch: {prompt_id}")
        for field in parity_fields:
            default = [] if field.endswith("paths") or field in {"depends_on", "required_outputs", "required_checks"} else None
            expected = prompt.get(field, default)
            actual = front.get(field, default if isinstance(expected, list) else None)
            if actual != expected:
                errors.append(f"Prompt registry/frontmatter mismatch for {prompt_id}.{field}: {actual!r} != {expected!r}")
        if status in {"planned", "ready"} and prompt.get("context_sha256") != current_context:
            errors.append(f"Safe prompt context is stale; run aw update: {prompt_id}")
        allowed = list(prompt.get("allowed_paths", []))
        forbidden = list(prompt.get("forbidden_paths", []))
        for output in prompt.get("required_outputs", []):
            if not _path_covered(output, allowed):
                errors.append(f"Prompt required output is outside allowed paths: {prompt_id}: {output}")
            if _path_covered(output, forbidden):
                errors.append(f"Prompt required output is forbidden: {prompt_id}: {output}")
        if prompt.get("status") == "superseded":
            replacement = prompt.get("superseded_by")
            if replacement not in known or not prompt.get("supersession_reason"):
                errors.append(f"Superseded prompt lacks valid replacement/reason: {prompt_id}")
        if prompt_id in latest_prompt_status and latest_prompt_status[prompt_id] != prompt.get("status"):
            errors.append(f"Prompt registry/event status mismatch: {prompt_id}")
        event = latest_prompt_event.get(prompt_id, {})
        if prompt.get("status") == "verified" and (event.get("actor") != "verifier" or not event.get("evidence")):
            errors.append(f"Verified prompt lacks current independent verifier event/evidence: {prompt_id}")
        if prompt.get("status") == "integrated" and event.get("actor") not in {"main", "orchestrator"}:
            errors.append(f"Integrated prompt lacks Main/Orchestrator event: {prompt_id}")

    graph = {prompt["id"]: prompt.get("depends_on", []) for prompt in registry.get("prompts", []) if prompt.get("id")}
    state = {}
    def visit(node):
        if state.get(node) == 1:
            errors.append(f"Prompt dependency cycle at: {node}"); return
        if state.get(node) == 2:
            return
        state[node] = 1
        for dep in graph.get(node, []):
            visit(dep)
        state[node] = 2
    for node in graph:
        visit(node)

    if meta.get("status") == "closed":
        if not requests or any(not item.get("verified") for item in requests):
            errors.append("Closed phase has unverified requests")
        unfinished = [
            prompt.get("id")
            for prompt in registry.get("prompts", [])
            if prompt.get("status") not in {"integrated", "verified", "superseded"}
        ]
        if unfinished:
            errors.append(f"Closed phase has unfinished prompts: {unfinished}")
        if meta.get("closed_by") != "verifier" or not meta.get("closure_evidence"):
            errors.append("Closed phase lacks Verifier-owned closure evidence")
        phase_events = _events(phase / "artifacts" / "phase_events.jsonl")
        close_event = next((event for event in reversed(phase_events) if event.get("event") == "closed"), None)
        if not close_event or close_event.get("actor") != "verifier" or not close_event.get("evidence"):
            errors.append("Closed phase lacks current Verifier closure event/evidence")

    if approval.get("status") == "approved" and approval.get("scope_sha256") != scope_hash(phase):
        errors.append("Approved intent scope hash no longer matches core phase intent documents")
    if approval.get("status") != "approved":
        for prompt in registry.get("prompts", []):
            if prompt.get("requires_approval") and prompt.get("status") in {"running", "completed", "integrated", "verified"}:
                errors.append(f"Prompt advanced without phase approval: {prompt['id']}")

    try:
        minor = resolve_minor_root(root, phase.name, create=False)
        if minor.exists() or minor_mode == "on":
            if not (minor / "REQUESTS.md").is_file():
                errors.append(f"Missing phase-local Minor file: {minor / 'REQUESTS.md'}")
            _validate_minor_events(minor, errors)
    except WorkflowError as exc:
        errors.append(str(exc))

    reports = meta.get("reports", {})
    rdir = phase / "reports"
    if not rdir.is_dir():
        errors.append("Missing always-present reports/ directory")
    else:
        nested = sorted(p.name for p in rdir.iterdir() if p.is_dir())
        if nested:
            errors.append(f"reports/ must be flat; subdirectories found: {nested}")
        actual = {p.name for p in rdir.iterdir() if p.is_file()}
        maximum = int(reports.get("max_files", config.get("reports", {}).get("max_files", 10)))
        if len(actual) > maximum:
            errors.append(f"Report file count exceeds compact limit {maximum}: {len(actual)}")
    return errors, warnings


def cmd_validate(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    errors, warnings = validate_phase(root, phase)
    value = {"root": str(root), "phase": phase.name, "ok": not errors, "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(value, indent=2))
    else:
        print("OK" if not errors else "\n".join(errors))
        for warning in warnings:
            print(f"WARNING: {warning}")
    return 0 if not errors else 1
