#!/usr/bin/env python3
"""Create one timestamped run and open its Direct or AI-Native CLI flow."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from eval_common import file_sha256, load_json
from generate_chat_main_runbooks import ROUTES, main_prompt, read
from sync_ai_workflow import ARCHIVE as WORKFLOW_ARCHIVE
from sync_ai_workflow import inspect_archive


ROOT = Path(__file__).resolve().parents[1]
MAIN_TIME = re.compile(r"^\s*(\d+)\s*m\s*(\d+)\s*s\s*$", re.IGNORECASE)


def portable_path(value: str) -> Path:
    """Accept the documented Windows path spelling when invoked on POSIX too."""
    if os.name != "nt":
        value = value.replace("\\", "/")
    return Path(value)


def require_executor_cli(ecosystem: str) -> str:
    """Fail before materializing a run when its frozen interactive CLI cannot launch."""
    command = "claude" if ecosystem == "ANTHROPIC" else "codex"
    executable = shutil.which(command)
    if executable is None:
        install_hint = (
            " Install and authenticate Claude Code, then ensure `claude` is on PATH."
            if command == "claude"
            else " Install and authenticate Codex CLI, then ensure `codex` is on PATH."
        )
        raise SystemExit(f"required executor CLI is not installed or not on PATH: {command}.{install_hint}")
    if command == "claude":
        help_result = subprocess.run(
            [executable, "--help"], capture_output=True, text=True, check=False
        )
        help_text = f"{help_result.stdout}\n{help_result.stderr}"
        missing = [flag for flag in ("--model", "--effort") if flag not in help_text]
        if help_result.returncode or missing:
            detail = ", ".join(missing) if missing else "a successful --help command"
            raise SystemExit(
                "Claude Code is present but does not expose the frozen launch controls "
                f"({detail}). Update Claude Code and retry."
            )
    return executable


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def find_matrix_row(task_id: str, ecosystem: str, condition: str, state_mode: str) -> dict[str, str]:
    with (ROOT / "manifests" / "RUN_MATRIX.csv").open(encoding="utf-8", newline="") as stream:
        matches = [
            row
            for row in csv.DictReader(stream)
            if row["task_id"] == task_id
            and row["ecosystem"] == ecosystem
            and row["condition"] == condition
            and row["state_mode"] == state_mode
        ]
    if len(matches) != 1:
        raise SystemExit(
            "no unique frozen RUN_MATRIX row for "
            f"{task_id}/{ecosystem}/{condition}/{state_mode}"
        )
    return matches[0]


def unique_run_id(task_root: Path, matrix_run_id: str, stamp: str) -> str:
    base = f"run_{stamp}_{matrix_run_id}"
    candidate = base
    sequence = 2
    while (task_root / "runs" / candidate).exists():
        candidate = f"{base}_{sequence:02d}"
        sequence += 1
    return candidate


def zip_tree(
    source: Path,
    destination: Path,
    *,
    archive_prefix: str = "",
    exclude_top_level: set[str] | None = None,
) -> None:
    excluded = exclude_top_level or set()
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=False,
    ) as archive:
        for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            if relative.parts and relative.parts[0] in excluded:
                continue
            name = Path(archive_prefix) / relative if archive_prefix else relative
            archive.write(path, name.as_posix())


def write_main_prompt(
    task_root: Path,
    run_dir: Path,
    condition: str,
    ecosystem: str,
    run: dict,
) -> Path:
    route = ROUTES[ecosystem]
    task = read(task_root / "TASK.md")
    binding = f"""Frozen handoff identity — copy these exact values into every HANDOFF_MANIFEST.json:

```json
{{
  "task_id": {json.dumps(run["task_id"])},
  "run_id": {json.dumps(run["run_id"])},
  "task_lock_sha256": {json.dumps(run["source_task_lock_sha256"])}
}}
```

A package with missing or different binding values will be rejected before import.
"""
    interaction_guidance = """Interaction policy: use exactly one Main inference for the complete currently revealed scope. Return one complete whole-Phase package whose Orchestrator entrypoint executes the full initial EPS prompt graph. A single ZIP is a transport boundary, not permission to collapse independently verifiable EPS nodes into one prompt. Never cross an unrevealed-checkpoint gate."""
    loader = read(ROOT / "prompts" / "ai_native" / "00_LOAD_AI_NATIVE.md")
    body = main_prompt(read(ROOT / "prompts" / "ai_native" / "01_START_TASK.md"), route, task)
    text = f"""# Main chat prompt

Upload `MAIN_INPUT.zip` from the printed run folder and
`AI_WORKFLOW_RUNTIME.zip` from the evaluation repository root. The runtime archive supplies the
clean `.ai-workflow/` directory at the scored repository root.

Then paste this single complete message:

````text
{loader}

{binding}

{interaction_guidance}

{body}
````
"""
    destination = run_dir / "MAIN_PROMPT.md"
    destination.write_text(text, encoding="utf-8", newline="\n")
    return destination


def write_direct_goal(task_root: Path, run_dir: Path, ecosystem: str) -> Path:
    route = ROUTES[ecosystem]
    task = read(task_root / "TASK.md")
    destination = run_dir / "DIRECT_GOAL.md"
    destination.write_text(
        "# Direct CLI Goal\n\n"
        + read(ROOT / "prompts" / "direct" / "00_START_TASK.md")
        + "\n\nFrozen executor route: " + route["executor"] + ". Do not silently substitute.\n\n"
        + "Frozen task prompt follows exactly:\n\n" + task + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


def package_inputs(task_root: Path, run_dir: Path, condition: str, run: dict) -> None:
    workspace = run_dir / "workspace"
    if condition == "DIRECT":
        if (workspace / ".ai-workflow").exists():
            raise SystemExit("Direct workspace must not contain .ai-workflow")
        prompt = write_direct_goal(task_root, run_dir, run["ecosystem"])
        run["direct_goal_prompt"] = {"path": str(prompt), "sha256": file_sha256(prompt)}
        run["main_inference_count"] = 0
        run["status"] = "READY_EXECUTOR"
        run["inputs_packaged_utc"] = utc_now()
        return
    main_input = run_dir / "MAIN_INPUT.zip"
    zip_tree(workspace, main_input, exclude_top_level={".ai-workflow"})
    run["main_input"] = {
        "path": str(main_input),
        "sha256": file_sha256(main_input),
        "contains_ai_workflow": False,
    }
    workflow = workspace / ".ai-workflow"
    if not workflow.is_dir():
        raise SystemExit("AI-Native workspace is missing .ai-workflow")
    archive_info = inspect_archive()
    run["ai_workflow_input"] = {
        "path": str(WORKFLOW_ARCHIVE),
        "sha256": archive_info["archive_sha256"],
        "runtime_tree_sha256": archive_info["tree_sha256"],
        "shared_canonical_archive": True,
    }
    prompt = write_main_prompt(task_root, run_dir, condition, run["ecosystem"], run)
    run["main_prompt"] = {"path": str(prompt), "sha256": file_sha256(prompt)}
    run["status"] = "AWAITING_MAIN"
    run["main_inference_count"] = 1
    run["inputs_packaged_utc"] = utc_now()


def required_input(message: str) -> str:
    value = ""
    while not value:
        value = input(message).strip()
    return value


def prompt_main_effort(current: str | None, ecosystem: str) -> str:
    if current:
        raw = current.strip().lower()
        interactive = False
    else:
        raw = ""
        interactive = True
    aliases = {
        "": "high",
        "h": "high",
        "high": "high",
        "xh": "xhigh",
        "xhigh": "xhigh",
        "pro": "pro",
    }
    while True:
        if interactive:
            message = (
                "Main compute/effort [Press Enter for high; xh/xhigh for xhigh; pro for pro]: "
                if ecosystem == "OPENAI"
                else "Main compute/effort [Press Enter for high]: "
            )
            raw = input(message).strip().lower()
        if raw in aliases:
            return aliases[raw]
        if not interactive:
            raise SystemExit("Main effort must be high (or blank), xh/xhigh, or pro")
        print("Invalid effort. Please try again: press Enter for high, or enter xh, xhigh, or pro.")


def prompt_optional_minutes(current: float | None, label: str) -> float | None:
    if current is not None:
        if current < 0:
            raise SystemExit("--main-wall-minutes must be non-negative")
        return current
    while True:
        raw = input(
            f"{label} as Xm Ys, e.g. 12m 34s "
            "(blank if unavailable): "
        ).strip()
        if not raw:
            return None
        match = MAIN_TIME.fullmatch(raw)
        if not match:
            print("Invalid time. Use Xm Ys, for example 12m 34s, or leave it blank.")
            continue
        minutes, seconds = (int(part) for part in match.groups())
        if seconds >= 60:
            print("Invalid time. Seconds must be between 0 and 59.")
            continue
        return minutes + seconds / 60.0


def handoff_zip_candidates(run_dir: Path) -> list[Path]:
    """Return unimported ZIPs stored directly in the run folder."""
    reserved = {"main_input.zip", ".ai-workflow.zip"}
    return sorted(
        (
            path.resolve()
            for path in run_dir.glob("*.zip")
            if path.is_file()
            and path.name.lower() not in reserved
            and not path.name.lower().startswith("handoff_")
        ),
        key=lambda path: path.name.lower(),
    )


def select_handoff_zip(
    run_dir: Path,
    *,
    rejected: dict[Path, str] | None = None,
) -> Path | None:
    """Select an exact-name or unique alternate-name handoff ZIP.

    During replacement, unchanged rejected archives are ignored. This lets the
    operator either overwrite one or download the corrected package under a new name.
    """
    candidates = handoff_zip_candidates(run_dir)
    if rejected:
        candidates = [
            path
            for path in candidates
            if path not in rejected or file_sha256(path) != rejected[path]
        ]
    preferred = [path for path in candidates if path.name.lower() == "main_handoff.zip"]
    if preferred:
        return preferred[0]
    if len(candidates) == 1:
        print(f"Using alternate handoff ZIP name: {candidates[0].name}")
        return candidates[0]
    if len(candidates) > 1:
        print("Multiple possible handoff ZIPs are present:")
        for path in candidates:
            print(f"  - {path.name}")
        selected = input("Type the exact ZIP filename to use (or press Enter to rescan): ").strip()
        if selected:
            matches = [path for path in candidates if path.name.lower() == selected.lower()]
            if len(matches) == 1:
                return matches[0]
            print("That filename is not one of the listed handoff ZIPs.")
    return None


def wait_for_first_handoff(run_dir: Path, supplied: Path | None) -> Path:
    if supplied is not None:
        handoff = supplied.resolve()
        while not handoff.is_file():
            input(f"Press Enter after the handoff ZIP has been saved at {handoff}: ")
        return handoff
    print(
        "\nSave Main's downloaded handoff ZIP directly in this run folder "
        f"(MAIN_HANDOFF.zip preferred; a unique alternate .zip name is accepted):\n{run_dir}"
    )
    while True:
        handoff = select_handoff_zip(run_dir)
        if handoff is not None:
            return handoff
        input("Press Enter after the handoff ZIP has been saved there: ")


def wait_for_replacement_handoff(run_dir: Path, rejected: dict[Path, str]) -> Path:
    print(
        "\nReplace the rejected ZIP, or save the corrected ZIP under another name "
        f"directly in:\n{run_dir}"
    )
    while True:
        input("Press Enter to discover and validate the replacement, or Ctrl+C to stop: ")
        replacement = select_handoff_zip(run_dir, rejected=rejected)
        if replacement is not None:
            return replacement
        print("No new or changed handoff ZIP was found in the run folder.")


def launch(
    task_root: Path,
    run_id: str,
    handoff: Path,
    *,
    ecosystem: str,
    main_chat_url: str,
    main_model: str,
    main_effort: str,
    claude_model: str | None,
    allow_shared_chat_link: bool,
    main_transcript: Path | None,
    qualification_root: Path | None,
    dry_run: bool = False,
) -> int:
    executor = "CODEX" if ecosystem == "OPENAI" else "CLAUDE"
    command = [
        sys.executable,
        "-X",
        "utf8",
        str(ROOT / "scripts" / "launch_executor.py"),
        str(task_root),
        run_id,
        "--executor",
        executor,
        "--bundle",
        str(handoff),
        "--main-chat-url",
        main_chat_url,
        "--main-model",
        main_model,
        "--main-effort",
        main_effort,
    ]
    if claude_model:
        command.extend(("--claude-model", claude_model))
    command.append(
        "--allow-shared-chat-link" if allow_shared_chat_link else "--reject-shared-chat-link"
    )
    if main_transcript:
        command.extend(("--main-transcript", str(main_transcript.resolve())))
    if qualification_root:
        command.extend(("--qualification-root", str(qualification_root.resolve())))
    if dry_run:
        command.append("--dry-run")
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def launch_direct(
    task_root: Path,
    run_id: str,
    prompt: Path,
    *,
    ecosystem: str,
    claude_model: str | None,
    qualification_root: Path | None,
) -> int:
    command = [
        sys.executable, "-X", "utf8", str(ROOT / "scripts" / "launch_direct_goal.py"),
        str(task_root), run_id, "--executor", "CODEX" if ecosystem == "OPENAI" else "CLAUDE",
        "--prompt", str(prompt),
    ]
    if claude_model:
        command.extend(("--claude-model", claude_model))
    if qualification_root:
        command.extend(("--qualification-root", str(qualification_root.resolve())))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def finish_run(
    task_root: Path,
    run_id: str,
    result: int,
    *,
    qualification_root: Path | None,
    skip_auto_grade: bool,
    skip_post_run_record: bool,
) -> int:
    grade_result = 0
    if not skip_auto_grade:
        grade_command = [
            sys.executable, "-X", "utf8", str(ROOT / "scripts" / "grade_run.py"),
            str(task_root), "--run-id", run_id,
        ]
        if qualification_root:
            grade_command.extend(("--qualification-root", str(qualification_root.resolve())))
        print("\nRunning frozen private grader...")
        grade_result = subprocess.run(grade_command, cwd=ROOT, check=False).returncode
    if not skip_post_run_record:
        record_command = [
            sys.executable, "-X", "utf8", str(ROOT / "scripts" / "record_run.py"),
            str(task_root), "--run-id", run_id,
        ]
        if qualification_root:
            record_command.extend(("--qualification-root", str(qualification_root.resolve())))
        record_result = subprocess.run(record_command, cwd=ROOT, check=False).returncode
        if result == 0 and grade_result == 0:
            return record_result
    return result or grade_result


def record_handoff_validation(run_path: Path, handoff: Path, return_code: int) -> None:
    run = load_json(run_path)
    attempts = run.setdefault("handoff_validation_attempts", [])
    attempts.append(
        {
            "attempt": len(attempts) + 1,
            "checked_utc": utc_now(),
            "bundle": str(handoff),
            "bundle_sha256": file_sha256(handoff) if handoff.is_file() else None,
            "valid": return_code == 0,
            "validator_return_code": return_code,
        }
    )
    save_json(run_path, run)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_root", type=portable_path)
    parser.add_argument("--condition", choices=("DIRECT", "AI_NATIVE"), required=True)
    parser.add_argument(
        "--ecosystem",
        choices=("OPENAI", "ANTHROPIC"),
        default="ANTHROPIC",
        help="routing ecosystem (default on this branch: ANTHROPIC)",
    )
    parser.add_argument("--state-mode", choices=("NORMAL", "STATE_LOSS"), default="NORMAL")
    parser.add_argument("--main-chat-url")
    parser.add_argument("--main-model")
    parser.add_argument(
        "--main-effort", help="Main setting: high (default), xh/xhigh, or pro"
    )
    parser.add_argument(
        "--main-wall-minutes", type=float, help="reported active Main-chat time"
    )
    parser.add_argument("--main-transcript", type=Path)
    parser.add_argument("--handoff", type=Path, help="already-downloaded first Main handoff ZIP")
    parser.add_argument(
        "--claude-model",
        default="claude-sonnet-5",
        help="Claude Code executor model (default: claude-sonnet-5)",
    )
    chat_link_policy = parser.add_mutually_exclusive_group()
    chat_link_policy.add_argument(
        "--allow-shared-chat-link",
        dest="allow_shared_chat_link",
        action="store_true",
        help="accept ChatGPT or Claude share links (the default)",
    )
    chat_link_policy.add_argument(
        "--reject-shared-chat-link",
        dest="allow_shared_chat_link",
        action="store_false",
        help="require a non-share HTTPS Main chat URL",
    )
    parser.set_defaults(allow_shared_chat_link=True)
    parser.add_argument("--stop-after-package", action="store_true")
    parser.add_argument(
        "--skip-post-run-record",
        action="store_true",
        help="do not open the metric/finalization recorder after the executor exits",
    )
    parser.add_argument(
        "--skip-auto-grade",
        action="store_true",
        help="do not run the frozen private grader after the executor exits",
    )
    parser.add_argument("--non-scored", action="store_true")
    parser.add_argument("--qualification-root", type=Path)
    args = parser.parse_args()

    if args.qualification_root and not args.non_scored:
        raise SystemExit("--qualification-root requires --non-scored")
    if not args.stop_after_package:
        executor_cli = require_executor_cli(args.ecosystem)
        print(f"Executor preflight: {executor_cli}")
    synced = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(ROOT / "scripts" / "sync_ai_workflow.py"),
            "--ensure",
        ],
        cwd=ROOT,
        check=False,
    )
    if synced.returncode:
        return synced.returncode
    task_root = args.task_root.resolve()
    lock_path = task_root / "TASK_LOCK.json"
    if not lock_path.is_file():
        raise SystemExit("task_root must contain TASK_LOCK.json")
    task_id = str(load_json(lock_path).get("task_id", ""))
    row = find_matrix_row(task_id, args.ecosystem, args.condition, args.state_mode)
    stamp = timestamp_slug()
    run_base = args.qualification_root.resolve() if args.qualification_root else task_root
    run_id = unique_run_id(run_base, row["run_id"], stamp)
    attempt_id = f"attempt-{stamp}"

    prepare = [
        sys.executable,
        "-X",
        "utf8",
        str(ROOT / "scripts" / "prepare_run.py"),
        str(task_root),
        "--condition",
        args.condition,
        "--run-id",
        run_id,
        "--attempt-id",
        attempt_id,
        "--simple-layout",
    ]
    if args.non_scored:
        prepare.append("--non-scored")
        if args.qualification_root:
            prepare.extend(("--qualification-root", str(args.qualification_root.resolve())))
    else:
        prepare.append("--authorize-scored-materialization")
    prepared = subprocess.run(prepare, cwd=ROOT, check=False)
    if prepared.returncode:
        return prepared.returncode

    run_dir = run_base / "runs" / run_id
    run_path = run_dir / "RUN.json"
    run = load_json(run_path)
    run.update(
        {
            "matrix_run_id": row["run_id"],
            "ecosystem": args.ecosystem,
            "state_mode": args.state_mode,
            "run_folder_timestamp_utc": stamp,
            "metadata_file": str(run_path),
            "executor": "CODEX" if args.ecosystem == "OPENAI" else "CLAUDE",
        }
    )
    package_inputs(task_root, run_dir, args.condition, run)
    save_json(run_path, run)

    print("\nRUN READY")
    print(f"Run folder: {run_dir}")
    if args.condition == "DIRECT":
        print(f"Direct Goal: {run_dir / 'DIRECT_GOAL.md'}")
    else:
        print(f"Main input: {run_dir / 'MAIN_INPUT.zip'}")
        print(f"AI workflow: {WORKFLOW_ARCHIVE}")
        print(f"Copy/paste prompt: {run_dir / 'MAIN_PROMPT.md'}")
    if args.stop_after_package:
        return 0

    if args.condition == "DIRECT":
        result = launch_direct(
            task_root,
            run_id,
            run_dir / "DIRECT_GOAL.md",
            ecosystem=args.ecosystem,
            claude_model=args.claude_model,
            qualification_root=args.qualification_root,
        )
        print(f"\nRun metadata: {run_path}")
        return finish_run(
            task_root,
            run_id,
            result,
            qualification_root=args.qualification_root,
            skip_auto_grade=args.skip_auto_grade,
            skip_post_run_record=args.skip_post_run_record,
        )

    route = ROUTES[args.ecosystem]
    main_model = args.main_model or route["main"]
    print("\nIn a fresh Main chat, upload:")
    print(f"  - {run_dir / 'MAIN_INPUT.zip'}")
    if args.condition == "AI_NATIVE":
        print(f"  - {WORKFLOW_ARCHIVE}")
    print(f"Then paste the instructions from: {run_dir / 'MAIN_PROMPT.md'}")
    print("When Main has produced the handoff ZIP, return here to archive its run details.")
    main_minutes = prompt_optional_minutes(
        args.main_wall_minutes,
        "Main total active/compute time for this prompt and handoff",
    )
    main_effort = prompt_main_effort(args.main_effort, args.ecosystem)
    provider = "Claude" if args.ecosystem == "ANTHROPIC" else "ChatGPT"
    main_chat_url = args.main_chat_url or required_input(
        f"Main chat link (normal or shared {provider} URL): "
    )
    handoff = wait_for_first_handoff(run_dir, args.handoff)
    run = load_json(run_path)
    run["main_model_product_visible"] = main_model
    run["main_effort_product_visible"] = main_effort
    if main_minutes is not None:
        main_seconds = round(main_minutes * 60.0, 6)
        run["main_initial_prompt_wall_seconds_reported"] = main_seconds
        run["main_active_wall_seconds_reported"] = main_seconds
    save_json(run_path, run)
    rejected_handoffs: dict[Path, str] = {}
    while True:
        validation_result = launch(
            task_root,
            run_id,
            handoff,
            ecosystem=args.ecosystem,
            main_chat_url=main_chat_url,
            main_model=main_model,
            main_effort=main_effort,
            claude_model=args.claude_model,
            allow_shared_chat_link=args.allow_shared_chat_link,
            main_transcript=args.main_transcript,
            qualification_root=args.qualification_root,
            dry_run=True,
        )
        record_handoff_validation(run_path, handoff, validation_result)
        if validation_result == 0:
            break
        print(f"\nMain handoff validation failed before import: {handoff.name}")
        if handoff.is_file():
            rejected_handoffs[handoff.resolve()] = file_sha256(handoff)
        handoff = wait_for_replacement_handoff(run_dir, rejected_handoffs)
    result = launch(
        task_root,
        run_id,
        handoff,
        ecosystem=args.ecosystem,
        main_chat_url=main_chat_url,
        main_model=main_model,
        main_effort=main_effort,
        claude_model=args.claude_model,
        allow_shared_chat_link=args.allow_shared_chat_link,
        main_transcript=args.main_transcript,
        qualification_root=args.qualification_root,
    )
    print(f"\nRun metadata: {run_path}")
    return finish_run(
        task_root,
        run_id,
        result,
        qualification_root=args.qualification_root,
        skip_auto_grade=args.skip_auto_grade,
        skip_post_run_record=args.skip_post_run_record,
    )


if __name__ == "__main__":
    raise SystemExit(main())
