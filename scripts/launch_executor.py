#!/usr/bin/env python3
"""Import one downloaded Main handoff and open the frozen interactive CLI executor."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from eval_common import file_sha256, load_json, sensitive_leaks
from usage_cost import attach_cost_estimate
from task_environment import environment_spec, ensure_sidecar, stop_sidecar


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
MAX_ARCHIVE_FILES = 5000
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "total_tokens",
    "cost_usd",
)
TOKEN_USAGE_LINE = re.compile(
    r"^\s*(?:token\s+usage\s*:\s*)?"
    r"total\s*=\s*([\d,]+)\s+"
    r"input\s*=\s*([\d,]+)\s*"
    r"(?:\(\s*\+\s*([\d,]+)\s+cached\s*\)\s*)?"
    r"output\s*=\s*([\d,]+)\s*"
    r"(?:\(\s*reasoning\s+([\d,]+)\s*\))?\s*$",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_usage_input(raw: str) -> dict:
    """Accept either usage JSON or Codex's product-visible token summary line."""
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        match = TOKEN_USAGE_LINE.fullmatch(raw)
        if not match:
            raise ValueError(
                "expected usage JSON or 'Token usage: total=... input=... "
                "(+ ... cached) output=... (reasoning ...)'"
            )
        total, input_tokens, cached, output, reasoning = match.groups()

        def integer(text: str | None) -> int:
            return int(text.replace(",", "")) if text else 0

        return {
            "total_tokens": integer(total),
            "input_tokens": integer(input_tokens),
            "cached_input_tokens": integer(cached),
            "output_tokens": integer(output),
            "reasoning_tokens": integer(reasoning),
        }
    if not isinstance(value, dict):
        raise ValueError("usage input must be one JSON object")
    return value


def safe_id(value: object, label: str) -> str:
    text = str(value or "")
    if not SAFE_ID.fullmatch(text):
        raise SystemExit(f"invalid {label} in handoff manifest: {text!r}")
    return text


def archive_relative(value: object, label: str) -> Path:
    text = str(value or "").replace("\\", "/")
    pure = PurePosixPath(text)
    if not text or pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise SystemExit(f"unsafe {label} in handoff manifest: {text!r}")
    if any(":" in part for part in pure.parts):
        raise SystemExit(f"unsafe {label} in handoff manifest: {text!r}")
    return Path(*pure.parts)


def extract_zip(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARCHIVE_FILES:
            raise SystemExit("handoff archive has too many entries")
        total = sum(info.file_size for info in infos)
        if total > MAX_ARCHIVE_BYTES:
            raise SystemExit("handoff archive exceeds the 512 MiB extraction limit")
        for info in infos:
            rel = archive_relative(info.filename.rstrip("/"), "ZIP entry") if info.filename.rstrip("/") else None
            if rel is None:
                continue
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise SystemExit(f"handoff ZIP contains a symlink: {info.filename}")
            target = destination / rel
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as incoming, target.open("wb") as outgoing:
                shutil.copyfileobj(incoming, outgoing)


def find_package_root(staging: Path) -> tuple[Path, str | None]:
    """Accept files at ZIP root or beneath exactly one enclosing directory."""
    if (staging / "HANDOFF_MANIFEST.json").is_file():
        return staging, None
    files = [path for path in staging.iterdir() if path.is_file()]
    directories = [path for path in staging.iterdir() if path.is_dir()]
    if not files and len(directories) == 1:
        wrapper = directories[0]
        if (wrapper / "HANDOFF_MANIFEST.json").is_file():
            return wrapper, wrapper.name
    raise SystemExit(
        "handoff ZIP must contain HANDOFF_MANIFEST.json at archive root or beneath "
        "exactly one enclosing directory with no sibling entries"
    )


def normalize_executor(value: object) -> str:
    text = str(value or "").strip().lower()
    if text.startswith("codex"):
        return "CODEX"
    if text.startswith("claude"):
        return "CLAUDE"
    return text.upper()


def prompt_required(current: str | None, message: str) -> str:
    value = (current or "").strip()
    while not value:
        value = input(message).strip()
    return value


def validate_chat_url(value: str, allow_shared: bool) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SystemExit("Main chat locator must be an https URL")
    if parsed.username or parsed.password:
        raise SystemExit("Main chat URL must not contain credentials")
    if parsed.netloc.lower() == "chatgpt.com" and parsed.path.startswith("/share/") and not allow_shared:
        raise SystemExit(
            "ChatGPT share links are disabled for this launch; use an authenticated conversation "
            "URL or omit --reject-shared-chat-link"
        )


def validate_handoff_bindings(manifest: dict, run: dict, run_id: str) -> None:
    expected_bindings = {
        "task_id": run.get("task_id"),
        "run_id": run_id,
        "task_lock_sha256": run.get("source_task_lock_sha256"),
    }
    for field, expected in expected_bindings.items():
        if not isinstance(expected, str) or not expected:
            raise SystemExit(f"RUN.json is missing required handoff binding: {field}")
        if manifest.get(field) != expected:
            raise SystemExit(
                f"handoff {field} does not match this run; expected {expected!r}"
            )


def validate_whole_phase_overlay(overlay: Path, prompt_source: Path) -> None:
    """Require an AI-Native handoff to contain a complete executable Phase graph."""
    entries = [path.relative_to(overlay) for path in overlay.rglob("*")]
    allowed_roots = {".ai-workflow", "phases"}
    if not entries or any(not rel.parts or rel.parts[0] not in allowed_roots for rel in entries):
        raise SystemExit("AI-Native repository_overlay may contain only .ai-workflow/ and phases/")
    phase_root = overlay / "phases"
    phase_manifests = sorted(phase_root.glob("*/PHASE_MANIFEST.json")) if phase_root.is_dir() else []
    if phase_manifests:
        if prompt_source.name != "ORCHESTRATOR_START.md" or phase_root not in prompt_source.parents:
            raise SystemExit("AI-Native executor_prompt must be the active Phase ORCHESTRATOR_START.md")
        for phase_manifest_path in phase_manifests:
            current = phase_manifest_path.parent
            required = (
                current / "DIC" / "README.md",
                current / "DIC" / "REQUESTS.md",
                current / "DIC" / "PLAN.md",
                current / "ORCHESTRATOR_START.md",
            )
            missing = [str(path.relative_to(overlay).as_posix()) for path in required if not path.is_file()]
            if missing:
                raise SystemExit("whole-Phase handoff is missing: " + ", ".join(missing))
            phase_manifest = load_json(phase_manifest_path)
            eps_id = str(phase_manifest.get("initial_eps_id") or "").strip()
            if not eps_id:
                raise SystemExit("PHASE_MANIFEST.json must name initial_eps_id")
            eps_root = current / "EPS" / eps_id
            eps_manifest_path = eps_root / "manifest.json"
            if not eps_manifest_path.is_file():
                raise SystemExit("whole-Phase handoff is missing its initial EPS manifest")
            eps_manifest = load_json(eps_manifest_path)
            node_ids = eps_manifest.get("plan_node_ids")
            nodes = eps_manifest.get("nodes")
            if not isinstance(node_ids, list) or not node_ids or not isinstance(nodes, dict):
                raise SystemExit("initial EPS manifest must contain a non-empty full node graph")
            for node_id in node_ids:
                if node_id not in nodes:
                    raise SystemExit(f"initial EPS manifest lacks node metadata for {node_id!r}")
                prompt_path = eps_root / "prompts" / f"{node_id}.md"
                if not prompt_path.is_file() or not prompt_path.read_text(encoding="utf-8").strip():
                    raise SystemExit(f"initial EPS lacks a substantive prompt file for {node_id!r}")
        return
    # Compatibility with the pre-root-phases runtime. Its complete Phase state lives below
    # .ai-workflow; the controlling prompt still must be an orchestrator entrypoint, not a worker.
    if ".ai-workflow" not in prompt_source.relative_to(overlay).parts:
        raise SystemExit("AI-Native handoff contains no canonical Phase surface")


def parse_usage(path: Path | None, skip_prompt: bool) -> tuple[dict, str]:
    if path is not None:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise SystemExit("--usage-json must contain one JSON object")
        return value, str(path.resolve())
    if skip_prompt:
        return {}, "not_reported"
    print("\nIf the CLI displayed usage, paste its token line or one JSON object now.")
    print("Example: Token usage: total=168 input=123 (+ 500 cached) output=45 (reasoning 20)")
    raw = input("Usage (blank if unavailable): ").strip()
    if not raw:
        return {}, "not_reported"
    try:
        value = parse_usage_input(raw)
    except ValueError as exc:
        raise SystemExit(f"invalid usage input: {exc}") from exc
    return value, "operator_transcription"


def update_main_archive(
    run_dir: Path,
    *,
    url: str,
    model: str,
    effort: str,
    handoff_id: str,
    transcript: Path | None,
    simple_layout: bool = False,
) -> dict:
    transcript_record = None
    if transcript is not None:
        if not transcript.is_file():
            raise SystemExit(f"missing Main transcript export: {transcript}")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        if simple_layout:
            target = run_dir / f"MAIN_TRANSCRIPT_{stamp}{''.join(transcript.suffixes) or '.txt'}"
        else:
            target = run_dir / "main" / "transcripts" / f"{stamp}{''.join(transcript.suffixes) or '.txt'}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(transcript, target)
        transcript_record = {
            "path": str(target),
            "sha256": file_sha256(target),
        }
    record = {
        "recorded_utc": utc_now(),
        "url": url,
        "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
        "main_model_product_visible": model,
        "main_effort_product_visible": effort,
        "handoff_id": handoff_id,
        "transcript_export": transcript_record,
    }
    if not simple_layout:
        destination = run_dir / "main" / "MAIN_CHATS.json"
        value = load_json(destination) if destination.is_file() else {"schema_version": 1, "chats": []}
        value["chats"].append(record)
        save_json(destination, value)
    return record


def usage_totals(sessions: list[dict]) -> dict:
    totals = {"executor_wall_seconds": 0.0}
    for item in sessions:
        totals["executor_wall_seconds"] += float(item.get("wall_seconds", 0.0))
        usage = item.get("usage", {})
        for field in TOKEN_FIELDS:
            number = usage.get(field)
            if isinstance(number, (int, float)) and not isinstance(number, bool):
                totals[field] = totals.get(field, 0) + number
    totals["executor_wall_seconds"] = round(totals["executor_wall_seconds"], 6)
    estimates = [
        item.get("usage", {}).get("api_equivalent_cost_estimate")
        for item in sessions
        if isinstance(item, dict) and isinstance(item.get("usage"), dict)
    ]
    estimated_costs = [
        estimate.get("estimated_cost_usd")
        for estimate in estimates
        if isinstance(estimate, dict)
        and isinstance(estimate.get("estimated_cost_usd"), (int, float))
    ]
    if estimated_costs:
        totals["executor_api_equivalent_cost_estimated_usd"] = round(
            sum(estimated_costs), 8
        )
    return totals


def update_usage(run_dir: Path, chat_record: dict, session: dict) -> Path:
    destination = run_dir / "evidence" / "EXECUTION_USAGE.json"
    value = load_json(destination) if destination.is_file() else {
        "schema_version": 1,
        "run_id": run_dir.name,
        "main_chat_records": [],
        "executor_sessions": [],
        "totals": {},
    }
    value["main_chat_records"].append(chat_record)
    value["executor_sessions"].append(session)
    value["totals"] = usage_totals(value["executor_sessions"])
    save_json(destination, value)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_root", type=Path)
    parser.add_argument("run_id")
    parser.add_argument("--bundle", type=Path, required=True, help="ZIP downloaded from Main chat")
    parser.add_argument("--executor", choices=("CODEX", "CLAUDE"), required=True)
    parser.add_argument("--claude-model", help="exact product-visible Claude Sonnet 5 CLI model ID")
    parser.add_argument("--main-chat-url")
    parser.add_argument("--main-model")
    parser.add_argument("--main-effort")
    parser.add_argument("--main-transcript", type=Path, help="optional exported Main conversation")
    parser.add_argument("--usage-json", type=Path, help="optional executor usage JSON")
    parser.add_argument("--skip-usage-prompt", action="store_true")
    chat_link_policy = parser.add_mutually_exclusive_group()
    chat_link_policy.add_argument(
        "--allow-shared-chat-link",
        dest="allow_shared_chat_link",
        action="store_true",
        help="accept ChatGPT share links (the default)",
    )
    chat_link_policy.add_argument(
        "--reject-shared-chat-link",
        dest="allow_shared_chat_link",
        action="store_false",
        help="require a non-share HTTPS Main chat URL",
    )
    parser.set_defaults(allow_shared_chat_link=True)
    parser.add_argument("--qualification-root", type=Path, help="non-scored run root used for qualification")
    parser.add_argument("--dry-run", action="store_true", help="validate and print without importing or launching")
    args = parser.parse_args()

    task_root = args.task_root.resolve()
    run_base = args.qualification_root.resolve() if args.qualification_root else task_root
    run_dir = run_base / "runs" / args.run_id
    run_path = run_dir / "RUN.json"
    workspace = run_dir / "workspace"
    bundle = args.bundle.resolve()
    if not run_path.is_file() or not workspace.is_dir():
        raise SystemExit("run must already be materialized with RUN.json and workspace/")
    if not bundle.is_file() or bundle.suffix.lower() != ".zip":
        raise SystemExit("--bundle must be a downloaded ZIP file")
    run = load_json(run_path)
    simple_layout = str(run.get("layout_version", "")).startswith("simple-")
    if run.get("status") == "FINALIZED":
        raise SystemExit("cannot launch an executor for a finalized run")

    with tempfile.TemporaryDirectory(prefix="ai-eval-handoff-") as temp_name:
        staging = Path(temp_name)
        extract_zip(bundle, staging)
        package_root, package_wrapper = find_package_root(staging)
        manifest_path = package_root / "HANDOFF_MANIFEST.json"
        manifest = load_json(manifest_path)
        validate_handoff_bindings(manifest, run, args.run_id)
        handoff_id = safe_id(manifest.get("handoff_id"), "handoff_id")
        manifest_condition = str(manifest.get("condition", "")).upper().replace("-", "_")
        if manifest_condition != run["condition"]:
            raise SystemExit("handoff condition does not match RUN.json")
        if normalize_executor(manifest.get("selected_executor")) != args.executor:
            raise SystemExit("handoff selected_executor does not match --executor")
        required_effort = "xhigh" if args.executor == "CODEX" else "high"
        if str(manifest.get("requested_effort", "")).lower() != required_effort:
            raise SystemExit(f"handoff requested_effort must be {required_effort}")
        prompt_rel = archive_relative(manifest.get("executor_prompt"), "executor_prompt")
        prompt_source = package_root / prompt_rel
        if not prompt_source.is_file():
            raise SystemExit(f"missing executor prompt declared by manifest: {prompt_rel}")
        declared_files_raw = manifest.get("archived_files")
        if not isinstance(declared_files_raw, list):
            raise SystemExit("HANDOFF_MANIFEST.json must contain archived_files as a list")
        declared_files = {
            archive_relative(item, "archived_files entry").as_posix()
            for item in declared_files_raw
        }
        actual_files = {
            path.relative_to(package_root).as_posix()
            for path in package_root.rglob("*")
            if path.is_file()
        }
        if declared_files != actual_files:
            missing = sorted(actual_files - declared_files)
            extra = sorted(declared_files - actual_files)
            raise SystemExit(
                f"handoff archived_files mismatch; undeclared={missing[:10]} missing={extra[:10]}"
            )
        leaks = sensitive_leaks(package_root)
        if leaks:
            raise SystemExit("handoff contains hidden evaluator/solution material: " + ", ".join(leaks[:20]))

        if args.executor == "CODEX":
            requested_model = str(manifest.get("requested_model", "")).lower()
            if "gpt-5.6-terra" not in requested_model:
                raise SystemExit("Codex handoff must request GPT-5.6 Terra")
            executor_model = "gpt-5.6-terra"
        else:
            requested_model = str(manifest.get("requested_model", "")).lower()
            if "sonnet 5" not in requested_model and "sonnet-5" not in requested_model:
                raise SystemExit("Claude handoff must request Claude Sonnet 5")
            executor_model = (args.claude_model or "").strip()
            if not executor_model and not args.dry_run:
                executor_model = prompt_required(None, "Exact product-visible Claude Sonnet 5 CLI model ID: ")
            if not executor_model:
                executor_model = "<EXACT_CLAUDE_SONNET_5_MODEL_ID>"

        overlay = None
        prompt_inside_overlay = None
        if run["condition"] == "DIRECT":
            required_direct = {
                "EXECUTOR_PROMPT.md",
                "CONTEXT.md",
                "RETURN_CONTRACT.md",
                "HANDOFF_MANIFEST.json",
            }
            if not required_direct.issubset(actual_files):
                raise SystemExit(
                    "Direct handoff is missing required root files: "
                    + ", ".join(sorted(required_direct - actual_files))
                )
            if prompt_rel.as_posix() != "EXECUTOR_PROMPT.md":
                raise SystemExit("Direct executor_prompt must be root EXECUTOR_PROMPT.md")
            if any(
                ".ai-workflow" in path.relative_to(package_root).parts
                for path in package_root.rglob("*")
            ):
                raise SystemExit("Direct handoff contains .ai-workflow")
            planned_import_root = workspace / "executor_handoffs" / handoff_id
            planned_prompt_target = planned_import_root / prompt_rel
        else:
            overlay_rel = archive_relative(manifest.get("repository_overlay"), "repository_overlay")
            overlay = package_root / overlay_rel
            if not overlay.is_dir():
                raise SystemExit("AI-Native handoff repository_overlay is missing")
            validate_whole_phase_overlay(overlay, prompt_source)
            unexpected_files = [
                path.relative_to(package_root).as_posix()
                for path in package_root.rglob("*")
                if path.is_file() and path != manifest_path and overlay not in path.parents
            ]
            if unexpected_files:
                raise SystemExit(
                    "AI-Native handoff contains files outside repository_overlay: "
                    + ", ".join(unexpected_files[:20])
                )
            try:
                prompt_inside_overlay = prompt_source.relative_to(overlay)
            except ValueError as exc:
                raise SystemExit("AI-Native executor prompt must be inside repository_overlay") from exc
            if not (workspace / ".ai-workflow").is_dir():
                raise SystemExit("AI-Native workspace is missing .ai-workflow before import")
            planned_prompt_target = workspace / prompt_inside_overlay

        prompt_target = planned_prompt_target
        if simple_layout:
            archive_destination = run_dir / f"HANDOFF_{handoff_id}.zip"
            source_bundle_destination = archive_destination
        else:
            archive_destination = run_dir / "main" / "handoff_packages" / handoff_id
            source_bundle_destination = archive_destination / "SOURCE.zip"
        prompt_workspace_rel = prompt_target.relative_to(workspace).as_posix()
        bootstrap = (
            f"Work from the current repository root. Read and execute the complete bounded assignment "
            f"in `{prompt_workspace_rel}`. Treat that file as the controlling executor prompt. Do not "
            "read outside this repository or access private evaluator material. Preserve the requested "
            "commands, tests, diffs, failures, and return evidence."
        )
        if environment_spec(task_root) is not None:
            bootstrap += (
                " This repository uses its frozen Linux task environment through the approved "
                "sidecar. Run every task build, test, and runtime command through "
                "`python .evaluation/run_in_env.py exec-self -- <command>`. The host repository "
                "is bind-mounted at `/app` inside that environment; do not create or copy a host "
                "virtual environment."
            )
        if args.executor == "CODEX":
            command = [
                "codex", "-C", str(workspace), "-m", executor_model,
                "-c", 'model_reasoning_effort="xhigh"', "--sandbox", "workspace-write", bootstrap,
            ]
        else:
            command = [
                "claude", "--model", executor_model, "--effort", "high",
                "--name", f"{args.run_id}-{handoff_id}", bootstrap,
            ]

        if args.dry_run:
            print(json.dumps({
                "status": "DRY_RUN_VALID",
                "workspace": str(workspace),
                "archive_destination": str(archive_destination),
                "package_wrapper": package_wrapper,
                "executor_prompt": str(prompt_target),
                "command": command,
            }, indent=2))
            return 0

        executable = shutil.which(command[0])
        if executable is None:
            raise SystemExit(f"executor CLI is not installed or not on PATH: {command[0]}")
        command[0] = executable
        version = subprocess.run(
            [executable, "--version"], capture_output=True, text=True, check=False,
        ).stdout.strip()
        chat_url = prompt_required(
            args.main_chat_url,
            "Main chat URL (authenticated conversation or ChatGPT share link): ",
        )
        validate_chat_url(chat_url, args.allow_shared_chat_link)
        main_model = prompt_required(args.main_model, "Exact product-visible Main model: ")
        main_effort = prompt_required(args.main_effort, "Exact product-visible Main effort setting: ")
        for field, observed in (
            ("main_model_product_visible", main_model),
            ("main_effort_product_visible", main_effort),
        ):
            existing = run.get(field)
            if existing is not None and existing != observed:
                raise SystemExit(f"{field} differs from the value already recorded in RUN.json")
        transcript_source = args.main_transcript.resolve() if args.main_transcript else None
        if transcript_source is not None and not transcript_source.is_file():
            raise SystemExit(f"missing Main transcript export: {transcript_source}")

        if archive_destination.exists():
            raise SystemExit(f"handoff ID already imported: {archive_destination}")
        if simple_layout:
            shutil.copy2(bundle, source_bundle_destination)
        else:
            archive_destination.mkdir(parents=True)
            shutil.copy2(bundle, source_bundle_destination)
            shutil.copytree(staging, archive_destination / "UNPACKED")
        if run["condition"] == "DIRECT":
            import_root = workspace / "executor_handoffs" / handoff_id
            shutil.copytree(package_root, import_root)
            prompt_target = import_root / prompt_rel
        else:
            runtime = workspace / ".ai-workflow"
            if not simple_layout:
                shutil.copytree(runtime, archive_destination / "PRE_IMPORT_AI_WORKFLOW")
            assert overlay is not None and prompt_inside_overlay is not None
            shutil.copytree(overlay, workspace, dirs_exist_ok=True)
            prompt_target = workspace / prompt_inside_overlay
        if not prompt_target.is_file():
            raise SystemExit("executor prompt was not present after handoff import")

        chat_record = update_main_archive(
            run_dir,
            url=chat_url,
            model=main_model,
            effort=main_effort,
            handoff_id=handoff_id,
            transcript=transcript_source,
            simple_layout=simple_layout,
        )

        transcript_hint = (
            run_dir / f"EXECUTOR_TRANSCRIPT_{handoff_id}.txt"
            if simple_layout
            else run_dir / "executors" / f"{args.run_id}-{handoff_id}-transcript.txt"
        )
        try:
            task_environment = ensure_sidecar(task_root, args.run_id, workspace)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        if task_environment is not None:
            run["task_environment"] = task_environment
        started_utc = utc_now()
        if "started_utc" not in run:
            run["started_utc"] = started_utc
        run["status"] = "IN_PROGRESS"
        run["main_model_product_visible"] = main_model
        run["main_effort_product_visible"] = main_effort
        run["main_inference_count"] = max(1, int(run.get("main_inference_count", 0)))
        run["active_executor_product_visible"] = executor_model
        run["active_executor_effort"] = required_effort
        if simple_layout:
            main_chats = run.setdefault("main_chats", [])
            if not any(
                isinstance(existing, dict)
                and existing.get("url_sha256") == chat_record["url_sha256"]
                for existing in main_chats
            ):
                main_chats.append(chat_record)
        save_json(run_path, run)
        print(f"\nOpening {args.executor} in repository: {workspace}")
        if args.executor == "CLAUDE":
            print(f"Before exiting Claude Code, run /usage and /export {transcript_hint}")
        else:
            print("Before exiting Codex, preserve any product-visible usage summary for the prompt below.")
        started = time.monotonic()
        try:
            result = subprocess.run(command, cwd=workspace, check=False)
        finally:
            try:
                stop_sidecar(run.get("task_environment"))
            except RuntimeError as exc:
                print(f"WARNING: {exc}", file=sys.stderr)
        wall_seconds = time.monotonic() - started
        ended_utc = utc_now()
        usage, usage_source = parse_usage(args.usage_json, args.skip_usage_prompt)
        cost_estimate = attach_cost_estimate(usage, executor_model)
        if cost_estimate is not None:
            print(
                "Estimated standard API-equivalent executor cost: "
                f"${cost_estimate['estimated_cost_usd']:.2f} "
                "(not necessarily an actual subscription charge)"
            )
        session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{handoff_id}"
        session = {
            "schema_version": 1,
            "session_id": session_id,
            "run_id": args.run_id,
            "handoff_id": handoff_id,
            "executor": args.executor,
            "executor_model_product_visible": executor_model,
            "executor_effort": required_effort,
            "cli_version": version,
            "started_utc": started_utc,
            "ended_utc": ended_utc,
            "wall_seconds": round(wall_seconds, 6),
            "process_exit_code": result.returncode,
            "executor_prompt": str(prompt_target),
            "executor_prompt_sha256": file_sha256(prompt_target),
            "source_bundle": str(source_bundle_destination),
            "source_bundle_sha256": file_sha256(source_bundle_destination),
            "usage": usage,
            "usage_source": usage_source,
            "local_transcript_expected": str(transcript_hint) if args.executor == "CLAUDE" else None,
        }
        if simple_layout:
            run.setdefault("executor_sessions", []).append(session)
            run["usage_totals"] = usage_totals(run["executor_sessions"])
            metrics_path = run_path
            session_record = run_path
        else:
            session_record = run_dir / "executors" / f"{session_id}.json"
            save_json(session_record, session)
            metrics_path = update_usage(run_dir, chat_record, session)
        run.setdefault("observed_executor_sessions", []).append({
            "session_id": session_id,
            "executor": args.executor,
            "model": executor_model,
            "effort": required_effort,
        })
        save_json(run_path, run)
        print(json.dumps({
            "session_record": str(session_record),
            "metrics": str(metrics_path),
            "process_exit_code": result.returncode,
        }, indent=2))
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
