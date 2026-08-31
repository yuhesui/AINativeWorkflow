from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .config import declared_repository_root, load_config, save_config
from .constants import (
    DEPENDENCY_DONE,
    EXECUTION_LEVELS,
    MANAGED_CONTEXT_BEGIN,
    MANAGED_CONTEXT_END,
    MODES,
    PHASE_NAME_RE,
    RESEARCH_LEVELS,
    ROUTING_PROFILES,
    TEST_PROFILES,
)
from .context import build_context, managed_context_sha256, render_context_block
from .errors import WorkflowError
from .filesystem import (
    append_jsonl,
    append_text,
    atomic_write_json,
    find_root,
    sha256_bytes,
    utc_now,
    write_if_absent,
)
from .models import resolve_routing
from .templates import render_template, template_root
from .support_tools import check_or_install_support_tools


def _latest_phase(phases: Path) -> Path | None:
    dirs = [p for p in phases.glob("phase_*") if p.is_dir()]
    if not dirs:
        return None
    def key(path: Path):
        return tuple((0, int(x)) if x.isdigit() else (1, x.lower()) for x in re.split(r"(\d+)", path.name))
    return max(dirs, key=key)


def resolve_phase(root: Path, explicit: str | None = None, required: bool = True) -> Path | None:
    config = load_config(root)
    name = explicit or str(config.get("current_phase") or "")
    if name:
        if not PHASE_NAME_RE.fullmatch(name):
            raise WorkflowError(f"Invalid phase name: {name}")
        path = root / "phases" / name
        if path.is_dir():
            return path
        if explicit:
            raise WorkflowError(f"Phase does not exist: {path}")
    latest = _latest_phase(root / "phases")
    if latest:
        return latest
    if required:
        raise WorkflowError(f"No phase exists under: {root / 'phases'}")
    return None


def _update_manifest_current_phase(root: Path, phase_name: str) -> None:
    path = root / "agent.manifest.yaml"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if re.search(r"^current_phase\s*:", text, re.MULTILINE):
        text = re.sub(r"^current_phase\s*:.*$", f"current_phase: {phase_name}", text, flags=re.MULTILINE)
    else:
        text = text.rstrip() + f"\ncurrent_phase: {phase_name}\n"
    path.write_text(text, encoding="utf-8")


def _initialise_minor(root: Path, phase: Path, config: dict) -> Path:
    path = (phase / "minor").resolve(strict=False)
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise WorkflowError(f"Minor path escapes repository: {path}") from exc
    if str(config.get("phase_lanes", {}).get("minor", "auto")) != "on":
        return path
    (path / "logs").mkdir(parents=True, exist_ok=True)
    (path / "reports").mkdir(parents=True, exist_ok=True)
    replacements = {
        "REPO_ROOT": str(declared_repository_root(root, config, strict=False)["resolved"]),
        "PHASE_ID": phase.name,
        "WORKFLOW_CONTEXT": render_context_block(root, phase),
    }
    write_if_absent(path / "REQUESTS.md", render_template("common/MINOR_REQUESTS.md", replacements))
    write_if_absent(path / "prompt_000_minor_init.md", render_template("common/prompt_000_minor_init.md", replacements))
    (path / "events.jsonl").touch(exist_ok=True)
    return path


def _apply_init_config(root: Path, args: argparse.Namespace) -> dict:
    config = load_config(root)
    for key in ("mode", "execution_level", "research_level", "test_profile", "routing_profile"):
        value = getattr(args, key, None)
        if value is not None:
            config[key] = value
    approval_phrase = getattr(args, "approval_phrase", None)
    if approval_phrase:
        config["approval_phrase"] = approval_phrase
    declared_root = getattr(args, "declared_root", None)
    root_mode = getattr(args, "root_mode", None)
    if root_mode:
        config["repository"]["root_mode"] = root_mode
    if declared_root:
        config["repository"]["root"] = str(Path(declared_root).expanduser().resolve(strict=False))
        if not root_mode:
            config["repository"]["root_mode"] = "fixed"
    available = getattr(args, "available_model", None)
    if available is not None:
        values: list[str] = []
        for raw in available:
            for item in str(raw).split(","):
                item = item.strip()
                if item and item.casefold() not in {x.casefold() for x in values}:
                    values.append(item)
        config["models"]["available"] = values
    surfaces = getattr(args, "surface", None)
    if surfaces is not None:
        values = []
        for raw in surfaces:
            for item in str(raw).split(","):
                item = item.strip()
                if item and item.casefold() not in {x.casefold() for x in values}:
                    values.append(item)
        config["models"]["surfaces"] = values
    if config["mode"] not in MODES:
        raise WorkflowError(f"mode must be one of: {sorted(MODES)}")
    if config["execution_level"] not in EXECUTION_LEVELS:
        raise WorkflowError(f"execution_level must be one of: {sorted(EXECUTION_LEVELS)}")
    if config["research_level"] not in RESEARCH_LEVELS:
        raise WorkflowError(f"research_level must be one of: {sorted(RESEARCH_LEVELS)}")
    if config["test_profile"] not in TEST_PROFILES:
        raise WorkflowError(f"test_profile must be one of: {sorted(TEST_PROFILES)}")
    if config["routing_profile"] not in ROUTING_PROFILES:
        raise WorkflowError(f"routing_profile must be one of: {sorted(ROUTING_PROFILES)}")
    save_config(root, config)
    return config


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root or ".").expanduser().resolve()
    aw = root / ".ai-workflow"
    if not aw.is_dir():
        raise WorkflowError(f"Copy the v5.6.35 .ai-workflow directory first: {aw}")
    config = _apply_init_config(root, args)
    project_name = getattr(args, "project_name", None) or root.name
    replacements = {
        "PROJECT_NAME": project_name,
        "REPO_ROOT": str(declared_repository_root(root, config, strict=False)["resolved"]),
        "WORKFLOW_CONTEXT": render_context_block(root, None),
        "MODE": str(config["mode"]),
        "EXECUTION_LEVEL": str(config["execution_level"]),
        "RESEARCH_LEVEL": str(config["research_level"]),
        "TEST_PROFILE": str(config["test_profile"]),
        "ROUTING_PROFILE": str(config["routing_profile"]),
    }
    write_if_absent(root / "AGENTS.md", render_template("root/AGENTS.md", replacements))
    write_if_absent(root / "agent.manifest.yaml", render_template("root/agent.manifest.yaml", replacements))
    (root / "phases").mkdir(parents=True, exist_ok=True)
    created_phase = None
    phase_name = getattr(args, "phase", None)
    if phase_name:
        phase_args = argparse.Namespace(
            root=str(root), name=phase_name, mode=config["mode"],
            execution_level=config["execution_level"], research_level=config["research_level"],
            test_profile=config["test_profile"], research=config["research_level"] != "none",
            architecture=getattr(args, "architecture", None), copy_templates=True,
            activate=True, from_handoff=None, rough_input=getattr(args, "rough_input", None),
            approval_phrase=config["approval_phrase"], suppress_output=True,
        )
        cmd_phase_init(phase_args)
        created_phase = phase_name
    support_tools = check_or_install_support_tools(root, bool(getattr(args, "install_support_tools", False)))
    result = {
        "root": str(root), "project_name": project_name,
        "mode": config["mode"], "execution_level": config["execution_level"],
        "research_level": config["research_level"], "test_profile": config["test_profile"],
        "routing_profile": config["routing_profile"], "created_phase": created_phase,
        "support_tools": {k: {"installed": v.get("after", {}).get("installed"), "attempted": bool(v.get("attempts"))} for k, v in support_tools.get("tools", {}).items()},
        "support_tools_status": ".ai-workflow/install_status.json",
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


def cmd_phase_init(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    config = load_config(root)
    name = args.name
    if not PHASE_NAME_RE.fullmatch(name):
        raise WorkflowError(f"Invalid phase name: {name}")
    mode = args.mode or str(config.get("mode", "goal"))
    if mode not in MODES:
        raise WorkflowError(f"Unknown mode: {mode}")
    execution_level = getattr(args, "execution_level", None) or str(config.get("execution_level", "mid"))
    research_level = getattr(args, "research_level", None) or str(config.get("research_level", "none"))
    test_profile = getattr(args, "test_profile", None) or str(config.get("test_profile", "affected"))
    if execution_level not in EXECUTION_LEVELS:
        raise WorkflowError(f"Unknown execution level: {execution_level}")
    if research_level not in RESEARCH_LEVELS:
        raise WorkflowError(f"Unknown research level: {research_level}")
    if test_profile not in TEST_PROFILES:
        raise WorkflowError(f"Unknown test profile: {test_profile}")
    phase = root / "phases" / name
    if phase.exists() and any(phase.iterdir()):
        raise WorkflowError(f"Phase already exists and is not empty: {phase}")
    directories = ["prompts", "logs", "reports", "artifacts"]
    lane_policy = dict(config.get("phase_lanes", {}))
    if lane_policy.get("verification", "auto") == "on":
        directories.append("verification")
    if lane_policy.get("checkpoints", "auto") == "on":
        directories.append("checkpoints")
    if args.research or research_level != "none" or lane_policy.get("research", "auto") == "on":
        directories += ["research/prompts", "research/sources", "research/reports", "research/synthesis"]
    copy_templates_arg = getattr(args, "copy_templates", None)
    copy_templates = bool(config.get("templates", {}).get("copy_full_set", True)) if copy_templates_arg is None else bool(copy_templates_arg)
    if copy_templates and mode == "structured":
        directories.append("templates")
    for directory in directories:
        (phase / directory).mkdir(parents=True, exist_ok=True)
    approval_phrase = getattr(args, "approval_phrase", None) or str(config.get("approval_phrase", "GO"))
    root_resolution = declared_repository_root(root, config, strict=False)
    displayed_root = root_resolution["resolved"] if bool(config.get("repository", {}).get("insert_into_prompts", True)) else "<resolve with aw root show>"
    handoff = getattr(args, "from_handoff", None) or "none"
    rough_input = getattr(args, "rough_input", None) or ""
    report_limit = int(config.get("reports", {}).get("max_files", config.get("reports", {}).get("max_summary_files", 10)))
    meta = {
        "schema_version": "1", "phase_id": name, "mode": mode,
        "status": "active",
        "execution_level": execution_level, "research_level": research_level,
        "test_profile": test_profile, "routing_profile": str(config.get("routing_profile", "all")),
        "approval_phrase": approval_phrase,
        "created_at": utc_now(), "from_handoff": handoff, "rough_input": rough_input,
        "repository": {"operational_root": str(root), **root_resolution},
        "templates": {"full_set_copied": copy_templates and mode == "structured", "architecture_created": False},
        "minor": {"location": "phase", "path": "minor", "mode": str(lane_policy.get("minor", "auto")), "approval": str(config.get("minor", {}).get("approval", "auto"))},
        "phase_lanes": lane_policy,
        "reports": {
            "policy": str(config.get("reports", {}).get("policy", "compact_raw")),
            "flat": True,
            "max_files": report_limit,
            "include_key_raw_results": True,
        },
    }
    atomic_write_json(phase / "artifacts" / "phase.json", meta)
    context = render_context_block(root, phase)
    context_sha = managed_context_sha256(root, phase)
    routing = resolve_routing(root, config)
    replacements = {
        "PHASE_ID": name,
        "PHASE_TITLE": name.removeprefix("phase_").replace("_", " ").title(),
        "MODE": mode,
        "APPROVAL_PHRASE": approval_phrase,
        "REPO_ROOT": str(displayed_root),
        "REPO_ROOT_MODE": str(root_resolution["mode"]),
        "EXECUTION_LEVEL": execution_level,
        "EXECUTION_LEVEL_UPPER": execution_level.upper(),
        "RESEARCH_LEVEL": research_level,
        "TEST_PROFILE": test_profile,
        "ROUTING_PROFILE": str(config.get("routing_profile", "all")),
        "HANDOFF_PATH": str(handoff),
        "ROUGH_INPUT": str(rough_input),
        "WORKFLOW_CONTEXT": context,
        "CONTEXT_SHA256": context_sha,
    }
    common = {"README.md": "common/README.md"}
    if mode == "goal":
        mode_files = {"GOAL.md": "goal/GOAL.md"}
    else:
        common.update({
            "prompts/prompt_000_orchestrator_init.md": "common/prompt_000_orchestrator_init.md",
        })
        mode_files = {
            "REQUESTS.md": "common/REQUESTS.md",
            "PLAN.md": "structured/PLAN.md",
            "USER_APPROVAL.md": "structured/USER_APPROVAL.md",
        }
        architecture_arg = getattr(args, "architecture", None)
        architecture = bool(config.get("templates", {}).get("structured_architecture", True)) if architecture_arg is None else bool(architecture_arg)
        if architecture:
            mode_files["ARCHITECTURE.md"] = "structured/ARCHITECTURE.md"
            meta["templates"]["architecture_created"] = True
            atomic_write_json(phase / "artifacts" / "phase.json", meta)
    for destination, source in {**common, **mode_files}.items():
        write_if_absent(phase / destination, render_template(source, replacements))
    if copy_templates and mode == "structured":
        for source in sorted((template_root() / "phase_full").glob("*.md")):
            write_if_absent(phase / "templates" / source.name, render_template(f"phase_full/{source.name}", replacements))
    main_route = routing["roles"]["main"]
    orchestrator_route = routing["roles"]["orchestrator"]
    if mode == "goal":
        prompt_records = [
            {
                "id": "GOAL", "file": "GOAL.md", "title": "Goal directly initializes Orchestrator",
                "depends_on": [], "status": "planned", "requires_approval": True,
                "model_profile": "orchestrator", "execution_level": execution_level, "test_profile": test_profile,
                "routing_profile": str(config.get("routing_profile", "all")),
                "repository_root": str(displayed_root), "backend_kind": "unspecified",
                "evidence_target": "implementation", "allowed_paths": [], "forbidden_paths": [],
                "required_outputs": ["rich operational DICs", "Execution Prompt Stack", "integration evidence"],
                "required_checks": ["readiness check", "acceptance mapping", "bounded execution plan"],
                "evidence": [], "context_sha256": context_sha,
                "model_options": orchestrator_route["preferred_candidates"],
                "preferred_model": orchestrator_route["selected_preference"],
            }
        ]
    else:
        prompt_records = [
            {
                "id": "000", "file": "prompts/prompt_000_orchestrator_init.md", "title": "Structured Orchestrator initialization",
                "depends_on": [], "status": "planned", "requires_approval": True,
                "model_profile": "orchestrator", "execution_level": execution_level, "test_profile": test_profile,
                "routing_profile": str(config.get("routing_profile", "all")),
                "repository_root": str(displayed_root), "backend_kind": "unspecified",
                "evidence_target": "implementation", "allowed_paths": [], "forbidden_paths": [],
                "required_outputs": [], "required_checks": [],
                "evidence": [], "context_sha256": context_sha, "model_options": orchestrator_route["preferred_candidates"],
                "preferred_model": orchestrator_route["selected_preference"],
            },
        ]
    registry = {
        "schema_version": "1", "phase_id": name, "mode": mode,
        "execution_level": execution_level, "research_level": research_level,
        "test_profile": test_profile, "routing_profile": str(config.get("routing_profile", "all")),
        "context_sha256": context_sha,
        "prompts": prompt_records,
    }
    atomic_write_json(phase / "artifacts" / "prompt_registry.json", registry)
    atomic_write_json(phase / "artifacts" / "approval.json", {
        "schema_version": "1", "status": "pending", "expected": approval_phrase,
        "recorded_at": None, "scope_sha256": None,
    })
    for name_ in ("prompt_events.jsonl", "request_events.jsonl", "phase_events.jsonl"):
        (phase / "artifacts" / name_).touch(exist_ok=True)
    activate = bool(getattr(args, "activate", True))
    if activate:
        config["current_phase"] = name
        config["mode"] = mode
        config["execution_level"] = execution_level
        config["research_level"] = research_level
        config["test_profile"] = test_profile
        save_config(root, config)
        _update_manifest_current_phase(root, name)
    minor_path = _initialise_minor(root, phase, config)
    result = {
        "phase": name, "mode": mode, "execution_level": execution_level,
        "research_level": research_level, "test_profile": test_profile,
        "routing_profile": str(config.get("routing_profile", "all")),
        "path": str(phase), "minor_path": str(minor_path),
        "repository_root": displayed_root, "activated": activate,
    }
    if not getattr(args, "suppress_output", False):
        print(json.dumps(result, ensure_ascii=False))
    return 0


def cmd_phase_current(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    print(json.dumps({"phase": phase.name, "path": str(phase)}))
    return 0


def cmd_phase_use(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.name)
    config = load_config(root)
    config["current_phase"] = phase.name
    meta = json.loads((phase / "artifacts" / "phase.json").read_text(encoding="utf-8"))
    for key in ("mode", "execution_level", "research_level", "test_profile"):
        if key in meta:
            config[key] = meta[key]
    save_config(root, config)
    _update_manifest_current_phase(root, phase.name)
    print(json.dumps({"current_phase": phase.name}))
    return 0


def cmd_phase_append(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    mapping = {
        "goal": "GOAL.md", "requests": "REQUESTS.md", "plan": "PLAN.md",
        "readme": "README.md", "architecture": "ARCHITECTURE.md", "approval": "USER_APPROVAL.md",
    }
    target = phase / mapping[args.doc]
    if not target.exists():
        raise WorkflowError(f"Phase document does not exist in this mode: {target}")
    if bool(args.body) == bool(args.body_file):
        raise WorkflowError("Use exactly one of --body or --body-file")
    body = args.body if args.body is not None else Path(args.body_file).read_text(encoding="utf-8")
    append_text(target, f"## {args.heading}\n\n- Recorded at: `{utc_now()}`\n- Appended by: `aw phase append`\n\n{body.rstrip()}\n")
    print(json.dumps({"phase": phase.name, "document": target.name}))
    return 0


def cmd_phase_plan_next(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    current = resolve_phase(root, args.phase)
    config = load_config(root)
    mode = args.mode or str(config.get("mode", "goal"))
    execution_level = args.execution_level or str(config.get("execution_level", "mid"))
    research_level = args.research_level or str(config.get("research_level", "none"))
    test_profile = getattr(args, "test_profile", None) or str(config.get("test_profile", "affected"))
    if mode not in MODES or execution_level not in EXECUTION_LEVELS or research_level not in RESEARCH_LEVELS or test_profile not in TEST_PROFILES:
        raise WorkflowError("Invalid mode/execution/research/test level for next-phase proposal")
    handoff_path = Path(args.from_handoff).expanduser() if args.from_handoff else current / "reports" / "FINAL_HANDOFF.md"
    handoff_hash = sha256_bytes(handoff_path.read_bytes()) if handoff_path.is_file() else None
    architecture_arg = getattr(args, "architecture", None)
    architecture = bool(config.get("templates", {}).get("structured_architecture", True)) if architecture_arg is None else bool(architecture_arg)
    copy_arg = getattr(args, "copy_templates", None)
    copy_templates = bool(config.get("templates", {}).get("copy_full_set", True)) if copy_arg is None else bool(copy_arg)
    approval_phrase = getattr(args, "approval_phrase", None) or str(config.get("approval_phrase", "GO"))
    activate = bool(getattr(args, "activate", True))
    rough_input = args.rough_input or ""
    if getattr(args, "create", False):
        current_meta = json.loads(
            (current / "artifacts" / "phase.json").read_text(encoding="utf-8")
        )
        if current_meta.get("status") != "closed":
            raise WorkflowError(
                f"Cannot create next phase before current phase is closed by Verifier: {current.name}"
            )
    command = [
        "aw", "phase", "init", args.name, "--mode", mode,
        "--execution-level", execution_level, "--research-level", research_level,
        "--test-profile", test_profile, "--from-handoff", str(handoff_path),
        "--approval-phrase", approval_phrase,
    ]
    if rough_input:
        command += ["--rough-input", rough_input]
    command.append("--architecture" if architecture else "--no-architecture")
    command.append("--copy-templates" if copy_templates else "--no-copy-templates")
    command.append("--activate" if activate else "--no-activate")
    proposal = {
        "schema_version": "1", "created_at": utc_now(), "current_phase": current.name,
        "next_phase": args.name, "mode": mode, "execution_level": execution_level,
        "research_level": research_level, "test_profile": test_profile,
        "handoff_path": str(handoff_path), "handoff_sha256": handoff_hash,
        "rough_input": rough_input, "architecture": architecture,
        "copy_templates": copy_templates, "activate": activate,
        "approval_phrase": approval_phrase, "repository_root": str(root),
        "recommended_command_tokens": command,
        "recommended_command": " ".join(json.dumps(token) if any(ch.isspace() for ch in token) else token for token in command),
    }
    target = current / "artifacts" / f"next_phase_proposal_{args.name}.json"
    atomic_write_json(target, proposal)
    result = {"proposal": str(target), **proposal, "created": False}
    if getattr(args, "create", False):
        init_args = argparse.Namespace(
            root=str(root), name=args.name, mode=mode, execution_level=execution_level,
            research_level=research_level, test_profile=test_profile,
            research=research_level != "none", architecture=architecture,
            copy_templates=copy_templates, activate=activate,
            from_handoff=str(handoff_path), rough_input=rough_input,
            approval_phrase=approval_phrase, suppress_output=True,
        )
        cmd_phase_init(init_args)
        result["created"] = True
        result["created_path"] = str(root / "phases" / args.name)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _normalise_requests_for_scope(text: str) -> str:
    lines = []
    for line in text.splitlines():
        lines.append(re.sub(r"^- \[[ xX]\] (RQ-\d{3,})", r"- [ ] \1", line))
    return "\n".join(lines).rstrip() + "\n"


def _normalise_generated_scope_content(text: str) -> str:
    start = text.find(MANAGED_CONTEXT_BEGIN)
    end = text.find(MANAGED_CONTEXT_END)
    if start >= 0 and end >= start:
        end += len(MANAGED_CONTEXT_END)
        text = text[:start].rstrip() + "\n\n<!-- AW:CONFIG:NORMALISED -->\n\n" + text[end:].lstrip()
    text = re.sub(
        r"\n## Approval event\n\n"
        r"- Recorded at: `[^`\n]*`\n"
        r"- Exact text: `[^\n]*`\n"
        r"- Scope SHA-256: `[0-9a-f]*`\n?",
        "\n",
        text,
    )
    return text.rstrip() + "\n"


def scope_hash(phase: Path) -> str:
    names = ["GOAL.md", "REQUESTS.md", "PLAN.md", "ARCHITECTURE.md", "EXECUTION_CONTRACT.md", "USER_APPROVAL.md"]
    payload = bytearray()
    for name in names:
        path = phase / name
        if path.is_file():
            raw = _normalise_generated_scope_content(path.read_text(encoding="utf-8"))
            if name == "REQUESTS.md":
                raw = _normalise_requests_for_scope(raw)
            payload.extend(name.encode("utf-8")); payload.extend(b"\0")
            payload.extend(raw.encode("utf-8")); payload.extend(b"\0")
    return sha256_bytes(bytes(payload))


def cmd_phase_close(args: argparse.Namespace) -> int:
    if args.actor.strip().lower() != "verifier":
        raise WorkflowError("Only actor 'verifier' may close a phase")
    if not args.evidence.strip():
        raise WorkflowError("Phase closure requires verifier evidence")
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    from .prompts import load_registry
    from .requests import request_summary
    from .validation import validate_phase

    meta_path = phase / "artifacts" / "phase.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("status") == "closed":
        raise WorkflowError(f"Phase is already closed: {phase.name}")
    approval = json.loads((phase / "artifacts" / "approval.json").read_text(encoding="utf-8"))
    if approval.get("status") != "approved":
        raise WorkflowError("Cannot close a phase before exact approval")
    requests = request_summary(phase)
    if not requests.get("total") or requests.get("verified") != requests.get("total"):
        raise WorkflowError(
            "Cannot close phase until every request is independently verified"
        )
    registry = load_registry(phase)
    allowed_terminal = {"integrated", "verified", "superseded"}
    unfinished = [
        prompt["id"]
        for prompt in registry.get("prompts", [])
        if prompt.get("status") not in allowed_terminal
    ]
    if unfinished:
        raise WorkflowError(f"Cannot close phase with unfinished prompts: {unfinished}")
    errors, _warnings = validate_phase(root, phase)
    if errors:
        raise WorkflowError(f"Cannot close invalid phase: {errors}")
    closed_at = utc_now()
    meta.update(
        {
            "status": "closed",
            "closed_at": closed_at,
            "closed_by": "verifier",
            "closure_evidence": args.evidence.strip(),
        }
    )
    atomic_write_json(meta_path, meta)
    append_jsonl(
        phase / "artifacts" / "phase_events.jsonl",
        {
            "event": "closed",
            "phase": phase.name,
            "actor": "verifier",
            "evidence": args.evidence.strip(),
            "note": args.note,
            "at": closed_at,
        },
    )
    print(
        json.dumps(
            {
                "phase": phase.name,
                "status": "closed",
                "actor": "verifier",
                "evidence": args.evidence.strip(),
                "closed_at": closed_at,
            }
        )
    )
    return 0


def _advance_after_approval(phase: Path) -> dict:
    registry_path = phase / "artifacts" / "prompt_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    prompts = {p["id"]: p for p in registry.get("prompts", [])}
    changed = []
    goal = prompts.get("GOAL")
    if goal and goal.get("status") == "planned":
        goal["status"] = "ready"
        goal.setdefault("evidence", []).append("artifacts/approval.json")
        changed.append(("GOAL", "ready"))
    prompt_000 = prompts.get("000")
    if prompt_000 and prompt_000.get("model_profile") == "orchestrator" and prompt_000.get("status") == "planned":
        prompt_000["status"] = "ready"
        prompt_000.setdefault("evidence", []).append("artifacts/approval.json")
        changed.append(("000", "ready"))
    elif prompt_000 and prompt_000.get("model_profile") == "main" and prompt_000.get("status") not in {"integrated", "verified", "superseded"}:
        prompt_000["status"] = "integrated"
        prompt_000.setdefault("evidence", []).append("artifacts/approval.json")
        changed.append(("000", "integrated"))
    if changed:
        atomic_write_json(registry_path, registry)
        for prompt_id, status in changed:
            append_jsonl(phase / "artifacts" / "prompt_events.jsonl", {
                "event": "status", "prompt_id": prompt_id, "status": status,
                "actor": "main", "evidence": "artifacts/approval.json", "at": utc_now(),
            })
    return {"advanced": [{"prompt_id": p, "status": s} for p, s in changed]}


def cmd_approval_show(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    value = json.loads((phase / "artifacts" / "approval.json").read_text(encoding="utf-8"))
    print(json.dumps(value, indent=2) if args.json else f"{value['status']} (expected: {value['expected']})")
    return 0


def cmd_approval_record(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    phase = resolve_phase(root, args.phase)
    from .requests import materialize_goal_requests, parse_requests
    meta = json.loads((phase / "artifacts" / "phase.json").read_text(encoding="utf-8"))
    if not (phase / "REQUESTS.md").is_file() and meta.get("mode") == "goal":
        materialize_goal_requests(phase)
    requests = parse_requests(phase / "REQUESTS.md")
    if not requests:
        raise WorkflowError("Cannot record GO before acceptance-bearing requests exist")
    missing_acceptance = [item["id"] for item in requests if not item.get("acceptance")]
    if missing_acceptance:
        raise WorkflowError(f"Every request needs an Acceptance criterion before GO: {missing_acceptance}")
    path = phase / "artifacts" / "approval.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    config = load_config(root)
    expected = value.get("expected", config.get("approval_phrase", "GO"))
    if args.text != expected:
        raise WorkflowError(f"Approval mismatch. Expected exactly: {expected!r}")
    current_hash = scope_hash(phase)
    if value.get("status") == "approved":
        if value.get("scope_sha256") != current_hash:
            raise WorkflowError("Phase intent scope changed after approval; record a new scoped approval")
        result = dict(value)
    else:
        value.update({"status": "approved", "text": args.text, "recorded_at": utc_now(), "scope_sha256": current_hash})
        atomic_write_json(path, value)
        result = dict(value)
        if (phase / "USER_APPROVAL.md").is_file():
            append_text(phase / "USER_APPROVAL.md", (
                f"## Approval event\n\n- Recorded at: `{value['recorded_at']}`\n"
                f"- Exact text: `{args.text}`\n- Scope SHA-256: `{current_hash}`\n"
            ))
    if config.get("auto_continue_after_go", True) and not getattr(args, "no_advance", False):
        result.update(_advance_after_approval(phase))
    else:
        result["advanced"] = []
    print(json.dumps(result))
    return 0
