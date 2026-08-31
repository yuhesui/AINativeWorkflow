from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .config import load_config
from .constants import MINOR_APPROVED, MINOR_ID_RE, MINOR_PREFIX, MINOR_TERMINAL
from .context import render_context_block
from .errors import WorkflowError
from .filesystem import append_jsonl, append_text, atomic_write_text, find_root, utc_now, write_if_absent
from .phase import resolve_phase
from .templates import render_template

LEDGER_TEMPLATE = "# Minor Requests\n\nAppend-only phase-local ledger managed by `aw minor`.\n"


def resolve_minor_root(root: Path, phase_name: str | None = None, create: bool = False) -> Path:
    phase = resolve_phase(root, phase_name, required=True)
    path = (phase / "minor").resolve(strict=False)
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise WorkflowError(f"Minor path escapes repository: {path}") from exc
    if create:
        (path / "logs").mkdir(parents=True, exist_ok=True)
        (path / "reports").mkdir(parents=True, exist_ok=True)
        write_if_absent(path / "REQUESTS.md", LEDGER_TEMPLATE)
        (path / "events.jsonl").touch(exist_ok=True)
        prompt = path / "prompt_000_minor_init.md"
        if not prompt.exists():
            config = load_config(root)
            replacements = {
                "REPO_ROOT": str(root), "PHASE_ID": phase.name,
                "WORKFLOW_CONTEXT": render_context_block(root, phase),
            }
            write_if_absent(prompt, render_template("common/prompt_000_minor_init.md", replacements))
    return path


def _ledger(path: Path) -> str:
    file = path / "REQUESTS.md"
    if not file.is_file():
        raise WorkflowError(f"Minor lane is not initialized: {path}")
    return file.read_text(encoding="utf-8")


def _events(path: Path) -> list[dict]:
    events = []
    file = path / "events.jsonl"
    if not file.is_file():
        return events
    for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"Invalid Minor JSONL {file}:{number}: {exc}") from exc
    return events


def _latest_states(path: Path) -> dict[str, str]:
    states = {}
    for event in _events(path):
        request_id = event.get("id")
        status = event.get("status")
        if request_id and status:
            states[str(request_id)] = str(status)
    return states


def _next_id(text: str, kind: str) -> str:
    prefix = MINOR_PREFIX[kind]
    numbers = [int(match.group(2)) for match in re.finditer(r"^##\s+(MF|MU|MR)-(\d+)\s+—", text, flags=re.MULTILINE) if match.group(1) == prefix]
    return f"{prefix}-{max(numbers, default=0)+1:02d}"


def _confirmation(request_id: str) -> str:
    match = MINOR_ID_RE.fullmatch(request_id)
    if not match:
        raise WorkflowError(f"Invalid Minor ID: {request_id}")
    prefix, number = match.groups()
    name = {"MF": "MinorFix", "MU": "MinorUpdate", "MR": "MinorReport"}[prefix]
    return f"GO {name} {int(number):02d}"


def cmd_minor_init(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    path = resolve_minor_root(root, args.phase, create=True)
    print(json.dumps({"minor_path": str(path), "location": "phase"}))
    return 0


def cmd_minor_add(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    path = resolve_minor_root(root, phase.name, create=True)
    text = _ledger(path)
    request_id = _next_id(text, args.type)
    config = load_config(root)
    approval_mode = args.approval or config.get("minor", {}).get("approval", "auto")
    approval_path = phase / "artifacts" / "approval.json"
    phase_approved = approval_path.is_file() and json.loads(approval_path.read_text(encoding="utf-8")).get("status") == "approved"
    if approval_mode == "auto":
        approval_mode = "phase" if phase_approved else "request"
    if approval_mode == "phase" and not phase_approved:
        approval_mode = "request"
    status = "approved_by_phase" if approval_mode == "phase" else ("approved" if approval_mode == "none" else "awaiting_confirmation")
    confirmation = None if status != "awaiting_confirmation" else _confirmation(request_id)
    block = (
        f"## {request_id} — {args.title.strip()}\n\n"
        f"- Type: `{args.type}`\n- Status: `{status}`\n- Created at: `{utc_now()}`\n"
        f"- User request: {args.request.strip()}\n"
        f"- Interpretation: {(args.interpretation or args.request).strip()}\n"
        f"- Expected files: `{args.files or 'unknown'}`\n"
        f"- Validation: `{args.checks or 'define before completion'}`\n"
    )
    if confirmation:
        block += f"- Required confirmation: `{confirmation}`\n"
    append_text(path / "REQUESTS.md", block)
    append_jsonl(path / "events.jsonl", {
        "event": "added", "id": request_id, "type": args.type,
        "status": status, "approval_mode": approval_mode, "at": utc_now(),
    })
    if not getattr(args, "suppress_output", False):
        print(json.dumps({"id": request_id, "status": status, "confirmation": confirmation, "minor_path": str(path)}))
    return 0


def _classify_clause(text: str) -> str:
    lower = text.casefold()
    # Explicit update verbs take precedence over nouns such as "status".
    if any(word in lower for word in ("update", "sync", "refresh", "rename")):
        return "update"
    if any(word in lower for word in ("report", "summar", "status", "extract")):
        return "report"
    return "fix"


def cmd_minor_from_user(args: argparse.Namespace) -> int:
    raw = args.input.strip()
    clauses = [item.strip(" ,") for item in re.split(r"\s+(?:and|then)\s+|;", raw) if item.strip(" ,")]
    if not clauses:
        raise WorkflowError("Minor rough input is empty")
    results = []
    for clause in clauses:
        kind = _classify_clause(clause)
        title = clause[0].upper() + clause[1:] if clause else "Minor task"
        forwarded = argparse.Namespace(
            root=args.root, phase=args.phase, type=kind, title=title,
            request=raw, interpretation=clause, files=args.files,
            checks=args.checks, approval=args.approval, suppress_output=True,
        )
        # Capture the generated ID deterministically by reading before/after.
        root = find_root(args.root)
        phase = resolve_phase(root, args.phase)
        lane = resolve_minor_root(root, phase.name, create=True)
        before = set(_latest_states(lane))
        cmd_minor_add(forwarded)
        after = set(_latest_states(lane))
        request_id = sorted(after - before)[0]
        results.append({"id": request_id, "type": kind, "interpretation": clause})
    print(json.dumps({"rough_input": raw, "requests": results}, ensure_ascii=False))
    return 0


def _find_block(text: str, request_id: str) -> str:
    match = re.search(rf"^## {re.escape(request_id)} — .*?(?=^## |\Z)", text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise WorkflowError(f"Minor request not found: {request_id}")
    return match.group(0).rstrip()


def cmd_minor_show(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    path = resolve_minor_root(root, args.phase, create=False)
    text = _ledger(path)
    print(_find_block(text, args.id) if args.id else text, end="\n" if args.id else "")
    return 0


def cmd_minor_note(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    path = resolve_minor_root(root, args.phase, create=False)
    _find_block(_ledger(path), args.id)
    append_text(path / "REQUESTS.md", f"### {args.heading} — {args.id}\n\n- At: `{utc_now()}`\n\n{args.body.rstrip()}\n")
    append_jsonl(path / "events.jsonl", {
        "event": "note", "id": args.id, "heading": args.heading,
        "actor": args.actor, "at": utc_now(),
    })
    print(json.dumps({"id": args.id, "note": args.heading}))
    return 0


def cmd_minor_approve(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    path = resolve_minor_root(root, args.phase, create=False)
    _find_block(_ledger(path), args.id)
    current = _latest_states(path).get(args.id)
    expected = _confirmation(args.id)
    if args.confirmation != expected:
        raise WorkflowError(f"Confirmation mismatch. Expected exactly: {expected!r}")
    if current != "awaiting_confirmation":
        raise WorkflowError(f"Minor request is not awaiting confirmation: {args.id} ({current})")
    append_text(path / "REQUESTS.md", f"### Approval — {args.id}\n\n- Status: `approved`\n- At: `{utc_now()}`\n- Confirmation: `{args.confirmation}`\n")
    append_jsonl(path / "events.jsonl", {"event": "approved", "id": args.id, "status": "approved", "at": utc_now()})
    print(json.dumps({"id": args.id, "status": "approved"}))
    return 0


def cmd_minor_done(args: argparse.Namespace) -> int:
    if args.status not in MINOR_TERMINAL:
        raise WorkflowError(f"Invalid terminal status: {args.status}")
    root = find_root(args.root)
    path = resolve_minor_root(root, args.phase, create=False)
    _find_block(_ledger(path), args.id)
    current = _latest_states(path).get(args.id)
    if current not in MINOR_APPROVED:
        raise WorkflowError(f"Minor request is not approved: {args.id} ({current})")
    if args.status == "completed" and not args.log:
        raise WorkflowError("A completion log/evidence path is required")
    append_text(path / "REQUESTS.md", (
        f"### Terminal — {args.id}\n\n- Status: `{args.status}`\n- At: `{utc_now()}`\n"
        f"- Files: `{args.files or 'none'}`\n- Checks: `{args.checks or 'not supplied'}`\n"
        f"- Log: `{args.log or 'not supplied'}`\n- Caveats: {args.caveats or 'none'}\n"
    ))
    append_jsonl(path / "events.jsonl", {
        "event": "terminal", "id": args.id, "status": args.status,
        "at": utc_now(), "log": args.log, "checks": args.checks,
    })
    print(json.dumps({"id": args.id, "status": args.status}))
    return 0


def cmd_minor_promote(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    path = resolve_minor_root(root, phase.name, create=False)
    block = _find_block(_ledger(path), args.id)
    current = _latest_states(path).get(args.id)
    if current in MINOR_TERMINAL:
        raise WorkflowError(f"Minor request is already terminal: {args.id} ({current})")
    request_match = re.search(r"^- User request:\s*(.+)$", block, flags=re.MULTILINE)
    interpretation_match = re.search(r"^- Interpretation:\s*(.+)$", block, flags=re.MULTILINE)
    files_match = re.search(r"^- Expected files:\s*`([^`]*)`", block, flags=re.MULTILINE)
    checks_match = re.search(r"^- Validation:\s*`([^`]*)`", block, flags=re.MULTILINE)
    from .prompts import cmd_prompt_add
    cmd_prompt_add(argparse.Namespace(
        root=str(root), phase=phase.name, id=args.to_prompt,
        title=args.title or f"Promoted {args.id}", depends_on=args.depends_on,
        allowed=(files_match.group(1) if files_match else ""),
        forbidden="archive/**,.git/**", output=args.output or [],
        check=args.check or ([checks_match.group(1)] if checks_match else []),
        model_profile=args.model_profile, execution_level=args.execution_level,
        test_profile=args.test_profile, backend=args.backend,
        evidence_level=args.evidence_level,
        rough_input=(request_match.group(1) if request_match else block),
        no_approval=False, suppress_output=True,
    ))
    append_text(path / "REQUESTS.md", (
        f"### Promotion — {args.id}\n\n- Status: `escalated`\n- At: `{utc_now()}`\n"
        f"- Replacement prompt: `{args.to_prompt}`\n"
        f"- Interpretation: `{interpretation_match.group(1) if interpretation_match else 'see original block'}`\n"
    ))
    append_jsonl(path / "events.jsonl", {
        "event": "terminal", "id": args.id, "status": "escalated",
        "replacement_prompt": args.to_prompt, "at": utc_now(),
    })
    print(json.dumps({"id": args.id, "status": "escalated", "replacement_prompt": args.to_prompt}))
    return 0


def minor_summary(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "initialized": False, "counts": {}, "open": []}
    latest = _latest_states(path)
    counts: dict[str, int] = {}
    for status in latest.values():
        counts[status] = counts.get(status, 0) + 1
    open_ids = [request_id for request_id, status in latest.items() if status not in MINOR_TERMINAL]
    return {"path": str(path), "initialized": (path / "REQUESTS.md").is_file(), "counts": counts, "open": open_ids}


def cmd_minor_status(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    path = resolve_minor_root(root, args.phase, create=False)
    value = minor_summary(path)
    if args.json:
        print(json.dumps(value, indent=2))
    else:
        print(f"Minor: {path}\nInitialized: {value['initialized']}\nOpen: {', '.join(value['open']) or 'none'}\nCounts: {value['counts']}")
    return 0


def cmd_minor_sample(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase, required=True)
    repo_root = str(root)
    kind = args.type
    confirmation = {"fix": "GO MinorFix 01", "update": "GO MinorUpdate 01", "report": "GO MinorReport 01"}[kind]
    rendered = render_template(f"minor_samples/{kind}.md", {
        "REPO_ROOT": repo_root, "PHASE_ID": phase.name,
        "ROUGH_INPUT": args.rough_input, "CONFIRMATION": confirmation,
        "WORKFLOW_CONTEXT": render_context_block(root, phase),
    })
    if args.write:
        target = Path(args.write).expanduser()
        if not target.is_absolute():
            target = root / target
        try:
            target.resolve(strict=False).relative_to(root.resolve())
        except ValueError as exc:
            raise WorkflowError(f"Minor sample output escapes repository: {target}") from exc
        atomic_write_text(target, rendered)
        print(json.dumps({"sample": str(target), "type": kind, "confirmation": confirmation}))
    else:
        print(rendered, end="")
    return 0
