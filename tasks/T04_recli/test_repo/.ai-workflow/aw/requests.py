from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .constants import GOAL_LINE_RE, REQUEST_ID_RE, REQUEST_LINE_RE
from .errors import WorkflowError
from .filesystem import append_jsonl, atomic_write_text, find_root, utc_now
from .phase import resolve_phase

REQUESTS_HEADER = "# Requests\n\n## Checklist\n"


def parse_requests(path: Path, *, required: bool = True) -> list[dict]:
    if not path.is_file():
        if required:
            raise WorkflowError(f"Missing REQUESTS.md: {path}")
        return []
    items = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        match = REQUEST_LINE_RE.match(line)
        if not match:
            continue
        checked, request_id, text = match.groups()
        acceptance: list[str] = []
        cursor = index + 1
        while cursor < len(lines):
            raw = lines[cursor]
            if REQUEST_LINE_RE.match(raw) or re.match(r"^##\s+", raw):
                break
            stripped = raw.strip()
            if stripped.startswith("- Acceptance:"):
                value = stripped.removeprefix("- Acceptance:").strip()
                if value:
                    acceptance.append(value)
            elif stripped.startswith("- ") and acceptance:
                acceptance.append(stripped[2:].strip())
            cursor += 1
        items.append({
            "id": request_id,
            "text": text.strip(),
            "acceptance": acceptance,
            "verified": checked.lower() == "x",
            "line": index,
        })
    return items


def parse_goal_acceptance(path: Path) -> list[dict]:
    if not path.is_file():
        raise WorkflowError(f"Missing GOAL.md: {path}")
    items: list[dict] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        match = GOAL_LINE_RE.match(line)
        if not match:
            continue
        checked, goal_id, text = match.groups()
        acceptance: list[str] = []
        cursor = index + 1
        while cursor < len(lines):
            raw = lines[cursor]
            if GOAL_LINE_RE.match(raw) or re.match(r"^##\s+", raw):
                break
            stripped = raw.strip()
            if stripped.startswith("- Acceptance:"):
                value = stripped.removeprefix("- Acceptance:").strip()
                if value:
                    acceptance.append(value)
            elif stripped.startswith("- ") and acceptance:
                acceptance.append(stripped[2:].strip())
            cursor += 1
        items.append({
            "goal_id": goal_id,
            "text": text.strip(),
            "acceptance": acceptance,
            "checked": checked.lower() == "x",
        })
    return items


def materialize_goal_requests(phase: Path) -> list[dict]:
    target = phase / "REQUESTS.md"
    if target.is_file() and parse_requests(target, required=False):
        return parse_requests(target)
    goals = parse_goal_acceptance(phase / "GOAL.md")
    if not goals:
        raise WorkflowError("Goal Mode requires at least one G-### acceptance item in GOAL.md before GO")
    missing = [item["goal_id"] for item in goals if not item["acceptance"]]
    if missing:
        raise WorkflowError(f"Every Goal acceptance item needs an Acceptance line before GO: {missing}")
    lines = [
        "# Requests",
        "",
        "This file was materialized from `GOAL.md` by `aw go`. Verifier owns completion.",
        "",
        "## Checklist",
        "",
    ]
    for index, item in enumerate(goals, 1):
        request_id = f"RQ-{index:03d}"
        lines.append(f"- [ ] {request_id} — {item['text']}")
        for acceptance in item["acceptance"]:
            lines.append(f"  - Acceptance: {acceptance}")
        lines.append(f"  - Source goal: {item['goal_id']}")
        lines.append("")
    atomic_write_text(target, "\n".join(lines).rstrip() + "\n")
    return parse_requests(target)


def load_request_events(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    events = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"Invalid request event JSONL {path}:{number}: {exc}") from exc
    return events


def request_states(phase: Path) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for event in load_request_events(phase / "artifacts" / "request_events.jsonl"):
        request_id = event.get("request_id")
        if request_id:
            latest[str(request_id)] = event
    return latest


def request_summary(phase: Path) -> dict:
    items = parse_requests(phase / "REQUESTS.md", required=False)
    states = request_states(phase)
    rows = []
    for item in items:
        event = states.get(item["id"], {})
        if item["verified"]:
            status = "verified"
        elif event.get("event") == "blocked":
            status = "blocked"
        else:
            status = "open"
        rows.append({**item, "status": status, "latest_event": event})
    return {
        "total": len(rows),
        "verified": sum(r["status"] == "verified" for r in rows),
        "blocked": [r["id"] for r in rows if r["status"] == "blocked"],
        "open": [r["id"] for r in rows if r["status"] == "open"],
        "items": rows,
        "materialized": (phase / "REQUESTS.md").is_file(),
    }


def _next_id(items: list[dict]) -> str:
    numbers = [int(REQUEST_ID_RE.fullmatch(item["id"]).group(1)) for item in items]
    return f"RQ-{(max(numbers, default=0)+1):03d}"


def _find_item(items: list[dict], request_id: str) -> dict:
    for item in items:
        if item["id"] == request_id:
            return item
    raise WorkflowError(f"Request ID not found: {request_id}")


def _ensure_requests_file(path: Path) -> None:
    if not path.is_file():
        atomic_write_text(path, REQUESTS_HEADER)


def cmd_request_add(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    path = phase / "REQUESTS.md"
    _ensure_requests_file(path)
    items = parse_requests(path)
    request_id = args.id or _next_id(items)
    if not REQUEST_ID_RE.fullmatch(request_id):
        raise WorkflowError(f"Invalid request ID: {request_id}")
    if any(item["id"] == request_id for item in items):
        raise WorkflowError(f"Duplicate request ID: {request_id}")
    text = path.read_text(encoding="utf-8").rstrip()
    if "## Checklist" not in text:
        text += "\n\n## Checklist\n"
    entry = f"\n- [ ] {request_id} — {args.text.strip()}"
    acceptance_values = args.acceptance or []
    if isinstance(acceptance_values, str):
        acceptance_values = [acceptance_values]
    for acceptance in acceptance_values:
        if str(acceptance).strip():
            entry += f"\n  - Acceptance: {str(acceptance).strip()}"
    atomic_write_text(path, text + entry + "\n")
    append_jsonl(phase / "artifacts" / "request_events.jsonl", {
        "event": "added", "request_id": request_id, "text": args.text.strip(),
        "acceptance": list(acceptance_values), "actor": "main", "at": utc_now(),
    })
    print(json.dumps({"request_id": request_id, "phase": phase.name}))
    return 0


def cmd_request_list(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    summary = request_summary(phase)
    if args.json:
        print(json.dumps(summary["items"], indent=2))
    else:
        if not summary["items"]:
            print("none")
        for item in summary["items"]:
            box = "[x]" if item["verified"] else "[ ]"
            suffix = f" ({item['status']})" if item["status"] != "open" else ""
            print(f"{box} {item['id']} — {item['text']}{suffix}")
    return 0


def cmd_request_verify(args: argparse.Namespace) -> int:
    if args.actor.strip().lower() != "verifier":
        raise WorkflowError("Only actor 'verifier' may mark a request complete")
    if not args.evidence.strip():
        raise WorkflowError("Verification evidence is required")
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    path = phase / "REQUESTS.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    item = _find_item(request_summary(phase)["items"], args.id)
    if item["verified"]:
        raise WorkflowError(f"Request already verified: {args.id}")
    if item.get("status") == "blocked":
        raise WorkflowError(f"Blocked request must be reopened before verification: {args.id}")
    lines[item["line"]] = re.sub(r"^- \[ \]", "- [x]", lines[item["line"]])
    atomic_write_text(path, "\n".join(lines) + "\n")
    append_jsonl(phase / "artifacts" / "request_events.jsonl", {
        "event": "verified", "request_id": args.id, "actor": "verifier",
        "evidence": args.evidence.strip(), "note": args.note, "at": utc_now(),
    })
    print(json.dumps({"request_id": args.id, "status": "verified", "evidence": args.evidence}))
    return 0


def cmd_request_block(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    item = _find_item(parse_requests(phase / "REQUESTS.md"), args.id)
    if item["verified"]:
        raise WorkflowError(f"Verified request must be reopened before blocking: {args.id}")
    append_jsonl(phase / "artifacts" / "request_events.jsonl", {
        "event": "blocked", "request_id": args.id, "reason": args.reason,
        "actor": "orchestrator", "at": utc_now(),
    })
    print(json.dumps({"request_id": args.id, "status": "blocked"}))
    return 0


def cmd_request_reopen(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    path = phase / "REQUESTS.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    item = _find_item(request_summary(phase)["items"], args.id)
    if item["verified"]:
        lines[item["line"]] = re.sub(r"^- \[[xX]\]", "- [ ]", lines[item["line"]])
        atomic_write_text(path, "\n".join(lines) + "\n")
    elif item.get("status") != "blocked":
        raise WorkflowError(f"Request is neither verified nor blocked: {args.id}")
    append_jsonl(phase / "artifacts" / "request_events.jsonl", {
        "event": "reopened", "request_id": args.id, "reason": args.reason,
        "actor": "main", "at": utc_now(),
    })
    print(json.dumps({"request_id": args.id, "status": "open"}))
    return 0
