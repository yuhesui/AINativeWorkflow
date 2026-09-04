#!/usr/bin/env python3
"""Reveal and execute the next checkpoint of an existing progressive run."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from eval_common import file_sha256, load_json, tree_sha256


ROOT = Path(__file__).resolve().parents[1]
TOTALS = {"T02": 3, "T03": 5, "T04": 8}
EXCLUDED_WORKSPACE_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}
DURATION = re.compile(r"^\s*(\d+)\s*m\s*(\d+)\s*s\s*$", re.IGNORECASE)


def portable_path(value: str) -> Path:
    if os.name != "nt":
        value = value.replace("\\", "/")
    return Path(value)


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def latest_unfinished_run(task_root: Path) -> str:
    candidates = []
    for run_path in (task_root / "runs").glob("*/RUN.json"):
        run = load_json(run_path)
        if run.get("status") != "FINALIZED":
            candidates.append((run_path.stat().st_mtime_ns, run_path.parent.name))
    if not candidates:
        raise SystemExit("no unfinished run found; supply --run-id")
    return max(candidates)[1]


def capture_executor_return(run_dir: Path, checkpoint: int, supplied: Path | None) -> Path:
    destination = run_dir / f"EXECUTOR_RETURN_CHECKPOINT_{checkpoint:02d}.md"
    if supplied is not None:
        source = supplied.resolve()
        if not source.is_file():
            raise SystemExit(f"executor return file not found: {source}")
        if source != destination.resolve():
            shutil.copy2(source, destination)
        return destination
    print("\nPaste the executor's final response/evidence below.")
    print("Enter END on a line by itself when finished.")
    while True:
        lines: list[str] = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        text = "\n".join(lines).strip()
        if text:
            destination.write_text(text + "\n", encoding="utf-8")
            return destination
        print("The executor return cannot be empty. Paste it again, then enter END.")


def record_direct_checkpoint_evidence(run_dir: Path, checkpoint: int, run: dict, grade: dict) -> Path:
    """Persist machine-captured checkpoint evidence without an operator paste step."""
    destination = run_dir / f"EXECUTOR_RETURN_CHECKPOINT_{checkpoint:02d}.md"
    sessions = run.get("executor_sessions")
    latest_session = sessions[-1] if isinstance(sessions, list) and sessions else None
    payload = {
        "checkpoint": checkpoint,
        "capture_mode": "durable_workspace_and_session_metadata",
        "condition": run.get("condition"),
        "note": "The interactive CLI final response is not separately captured; the surviving workspace and session metadata are authoritative.",
        "latest_executor_session": latest_session,
        "grader": safe_grade_summary(grade),
    }
    destination.write_text(
        "# Checkpoint evidence\n\n```json\n"
        + json.dumps(payload, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )
    return destination


def safe_grade_summary(grade: dict) -> dict:
    fields = (
        "schema_version", "task_id", "run_id", "graded_utc", "grader_ok",
        "checkpoint", "checkpoint_total", "checkpoint_primary_score",
        "core_pass_rate", "isolated_pass_rate", "strict_pass_rate",
        "accepted_for_next_reveal", "task_completion",
    )
    return {key: grade.get(key) for key in fields if key in grade}


def add_workspace(archive: zipfile.ZipFile, workspace: Path) -> None:
    for path in sorted(workspace.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(workspace)
        if any(part in EXCLUDED_WORKSPACE_PARTS for part in relative.parts):
            continue
        if relative.parts and relative.parts[0] == ".evaluation":
            continue
        archive.write(path, (Path("CURRENT_WORKSPACE") / relative).as_posix())


def build_main_input(
    run_dir: Path,
    workspace: Path,
    run: dict,
    checkpoint: int,
    previous: int,
    grade: dict,
    executor_return: Path,
) -> tuple[Path, Path]:
    context = {
        "schema_version": 1,
        "task_id": run["task_id"],
        "run_id": run["run_id"],
        "condition": run["condition"],
        "ecosystem": run.get("ecosystem"),
        "selected_executor": run.get("executor"),
        "executor_model_product_visible": run.get("active_executor_product_visible"),
        "executor_effort": run.get("active_executor_effort"),
        "main_model_product_visible": run.get("main_model_product_visible"),
        "main_effort_product_visible": run.get("main_effort_product_visible"),
        "previous_checkpoint": previous,
        "current_checkpoint": checkpoint,
        "checkpoint_total": TOTALS[run["task_id"]],
        "source_task_lock_sha256": run["source_task_lock_sha256"],
        "surviving_workspace_tree_sha256": tree_sha256(workspace, include_transient=True),
        "instruction": "Continue the same run; output one new complete handoff ZIP.",
    }
    input_zip = run_dir / f"MAIN_CONTINUE_INPUT_CHECKPOINT_{checkpoint:02d}.zip"
    checkpoint_file = workspace / "CHECKPOINTS" / f"{checkpoint:02d}.md"
    with zipfile.ZipFile(input_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(checkpoint_file, "CHECKPOINT.md")
        archive.write(executor_return, "PREVIOUS_EXECUTOR_RETURN.md")
        archive.writestr(
            "PREVIOUS_GRADER_SUMMARY.json",
            json.dumps(safe_grade_summary(grade), indent=2, sort_keys=True) + "\n",
        )
        archive.writestr(
            "CONTINUATION_CONTEXT.json",
            json.dumps(context, indent=2, sort_keys=True) + "\n",
        )
        add_workspace(archive, workspace)

    fixed = (ROOT / "prompts" / "shared" / "01_CONTINUE_CHECKPOINT.md").read_text(encoding="utf-8")
    prompt = run_dir / f"MAIN_CONTINUE_PROMPT_CHECKPOINT_{checkpoint:02d}.md"
    prompt.write_text(
        "# Main continuation prompt\n\n"
        f"Upload `{input_zip.name}` to the same Main chat, then paste this single message:\n\n"
        "````text\n"
        f"{fixed.strip()}\n\n"
        "Frozen handoff bindings for every HANDOFF_MANIFEST.json in this continuation:\n\n"
        "```json\n"
        + json.dumps({
            "task_id": run["task_id"],
            "run_id": run["run_id"],
            "task_lock_sha256": run["source_task_lock_sha256"],
        }, indent=2)
        + "\n```\n\n"
        f"The newly authorized cumulative scope ends at checkpoint {checkpoint} of {TOTALS[run['task_id']]}. "
        "Do not cross the next checkpoint gate.\n"
        "````\n",
        encoding="utf-8",
    )
    return input_zip, prompt


def prompt_handoff(run_dir: Path, checkpoint: int) -> Path:
    preferred = f"MAIN_HANDOFF_CHECKPOINT_{checkpoint:02d}.zip"
    while True:
        raw = input(
            f"Main handoff ZIP filename in the run folder [Enter for {preferred}]: "
        ).strip()
        name = raw or preferred
        candidate = (run_dir / name).resolve()
        if candidate.parent != run_dir.resolve() or candidate.suffix.lower() != ".zip":
            print("Enter only a .zip filename stored directly in the run folder.")
            continue
        if candidate.is_file():
            return candidate
        print(f"File not found: {candidate}. Save it there and try again.")


def prompt_main_minutes() -> float | None:
    while True:
        raw = input("Main continuation time as Xm Ys (blank if unavailable): ").strip()
        if not raw:
            return None
        match = DURATION.fullmatch(raw)
        if match and int(match.group(2)) < 60:
            return int(match.group(1)) + int(match.group(2)) / 60.0
        print("Invalid time. Use Xm Ys, for example 12m 34s, or leave it blank.")


def prompt_chat_url(run: dict) -> str:
    chats = run.get("main_chats") or []
    previous = chats[-1].get("url") if chats else ""
    suffix = " [Enter to reuse the previous link]" if previous else ""
    while True:
        value = input(f"Main chat link for this continuation{suffix}: ").strip()
        if value:
            return value
        if previous:
            return str(previous)
        print("A Main chat link is required.")


def launch_command(run: dict, task_root: Path, handoff: Path, chat_url: str) -> list[str]:
    executor = str(run.get("executor") or ("CODEX" if run.get("ecosystem") == "OPENAI" else "CLAUDE"))
    command = [
        sys.executable, "-X", "utf8", str(ROOT / "scripts" / "launch_executor.py"),
        str(task_root), str(run["run_id"]), "--bundle", str(handoff),
        "--executor", executor, "--main-chat-url", str(chat_url),
        "--main-model", str(run["main_model_product_visible"]),
        "--main-effort", str(run["main_effort_product_visible"]),
        "--allow-shared-chat-link",
    ]
    if executor == "CLAUDE":
        model = str(run.get("active_executor_product_visible") or "claude-sonnet-5")
        command.extend(("--claude-model", model))
    return command


def direct_launch_command(
    run: dict,
    task_root: Path,
    prompt: Path,
    qualification_root: Path | None,
) -> list[str]:
    executor = str(run.get("executor") or ("CODEX" if run.get("ecosystem") == "OPENAI" else "CLAUDE"))
    command = [
        sys.executable, "-X", "utf8", str(ROOT / "scripts" / "launch_direct_goal.py"),
        str(task_root), str(run["run_id"]), "--executor", executor, "--prompt", str(prompt),
    ]
    if executor == "CLAUDE":
        command.extend(("--claude-model", str(run.get("active_executor_product_visible") or "claude-sonnet-5")))
    command.append("--resume-session")
    if qualification_root:
        command.extend(("--qualification-root", str(qualification_root.resolve())))
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Continue one accepted progressive checkpoint run.")
    parser.add_argument("task_root", type=portable_path)
    parser.add_argument("--run-id")
    parser.add_argument("--executor-return", type=portable_path)
    parser.add_argument("--qualification-root", type=portable_path)
    args = parser.parse_args()

    task_root = args.task_root.resolve()
    run_id = args.run_id or latest_unfinished_run(task_root)
    run_base = args.qualification_root.resolve() if args.qualification_root else task_root
    run_dir = run_base / "runs" / run_id
    run_path = run_dir / "RUN.json"
    workspace = run_dir / "workspace"
    if not run_path.is_file() or not workspace.is_dir():
        raise SystemExit("run must contain RUN.json and workspace/")
    run = load_json(run_path)
    task_id = str(run.get("task_id"))
    if task_id not in TOTALS:
        raise SystemExit("continue_run.py applies only to T2, T3, and T4")
    if run.get("status") == "FINALIZED":
        raise SystemExit("cannot continue a finalized run")

    state_path = workspace / ".evaluation" / "CHECKPOINT_STATE.json"
    state = load_json(state_path)
    previous = int(state["current_checkpoint"])
    if previous >= TOTALS[task_id]:
        raise SystemExit("all checkpoints are already revealed; grade/finalize the run")
    grade = run.get("latest_auto_grade")
    if not isinstance(grade, dict) or grade.get("checkpoint") != previous:
        raise SystemExit("the current checkpoint must be graded before continuation")
    if not grade.get("grader_ok") or not grade.get("accepted_for_next_reveal"):
        raise SystemExit("the current checkpoint grader has not authorized the next reveal")
    loss_boundary = {"T03": 3, "T04": 4}.get(task_id)
    if run.get("state_mode") == "STATE_LOSS" and previous == loss_boundary:
        raise SystemExit(
            "frozen state-loss boundary reached. Do not continue the old Main chat or reveal the "
            "next checkpoint. Capture the surviving run with scripts/capture_state_loss.py and "
            "start the required fresh-Main recovery flow from READY_FOR_SCORED_RUNS.md."
        )

    executor_return = record_direct_checkpoint_evidence(run_dir, previous, run, grade)
    checkpoint = previous + 1
    reveal = [
        sys.executable, "-X", "utf8", str(ROOT / "scripts" / "reveal_checkpoint.py"),
        str(task_root), str(workspace), "--checkpoint", str(checkpoint),
        "--accepted-grader-raw", str(grade["raw_grader"]),
    ]
    result = subprocess.run(reveal, cwd=ROOT, check=False)
    if result.returncode:
        return result.returncode

    if run.get("condition") in {"DIRECT", "AI_NATIVE"}:
        is_direct = run.get("condition") == "DIRECT"
        prompt_prefix = "DIRECT_GOAL" if is_direct else "AI_NATIVE_GOAL"
        prompt = run_dir / f"{prompt_prefix}_CHECKPOINT_{checkpoint:02d}.md"
        workflow_guidance = (
            "Continue directly in the surviving repository without a Main chat or AI-Native "
            "Workflow."
            if is_direct
            else
            "Continue the same approved Goal using the surviving repository and durable "
            "`.ai-workflow/` state. Update the Plan/Phase/DIC/EPS evidence as needed; do not "
            "request another Main inference."
        )
        prompt.write_text(
            f"# {'Direct' if is_direct else 'AI-Native'} CLI Goal — continued cumulative scope\n\n"
            "Treat the updated `TASK.md` and all currently revealed checkpoint instructions as the "
            f"approved Goal. {workflow_guidance} Complete the cumulative requirements through the current checkpoint, "
            "run legitimate visible tests, repair failures, preserve prior passing behavior, and stop "
            "before any unrevealed checkpoint. The harness has already started the frozen task "
            "environment. Use `python .evaluation/run_in_env.py exec-self -- <command>` for task "
            "commands; do not perform Docker/WSL/sidecar/model-route preflight or ask the operator "
            "to confirm it. If the wrapper reports that the sidecar is not running, retry the same "
            "command once with escalated command permission; automatic approval is enabled. "
            "Escalate only if the "
            "repeated failure blocks the current acceptance criterion.\n",
            encoding="utf-8",
        )
        run = load_json(run_path)
        continuation_key = "direct_continuations" if is_direct else "ai_native_continuations"
        run.setdefault(continuation_key, []).append({
            "checkpoint": checkpoint,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "prompt": str(prompt),
            "prompt_sha256": file_sha256(prompt),
            "executor_return": str(executor_return),
            "executor_return_sha256": file_sha256(executor_return),
        })
        run["main_inference_count"] = 0 if is_direct else max(
            1, int(run.get("main_inference_count", 1))
        )
        run["status"] = "READY_EXECUTOR_CONTINUATION"
        save_json(run_path, run)
        session_count = len(run.get("executor_sessions", []))
        launched = subprocess.run(
            direct_launch_command(run, task_root, prompt, args.qualification_root),
            cwd=ROOT,
            check=False,
        )
        after_launch = load_json(run_path)
        if launched.returncode and len(after_launch.get("executor_sessions", [])) == session_count:
            after_launch["status"] = "INVALID_INFRASTRUCTURE"
            after_launch["invalidation_reason"] = "Continuation executor did not start; grading was skipped."
            after_launch["infrastructure_failure_utc"] = datetime.now(timezone.utc).isoformat()
            save_json(run_path, after_launch)
            print("Continuation did not start; marked INVALID_INFRASTRUCTURE and skipped grading.")
            return launched.returncode
        grade_command = [
            sys.executable, "-X", "utf8", str(ROOT / "scripts" / "grade_run.py"),
            str(task_root), "--run-id", run_id,
        ]
        if args.qualification_root:
            grade_command.extend(("--qualification-root", str(args.qualification_root.resolve())))
        graded = subprocess.run(
            grade_command,
            cwd=ROOT,
            check=False,
        )
        if launched.returncode == 0 and graded.returncode == 0:
            updated = load_json(run_path)
            latest = updated.get("latest_auto_grade")
            if isinstance(latest, dict) and latest.get("all_checkpoints_graded"):
                record_command = [
                    sys.executable, "-X", "utf8", str(ROOT / "scripts" / "record_run.py"),
                    str(task_root), "--run-id", run_id,
                ]
                if args.qualification_root:
                    record_command.extend(("--qualification-root", str(args.qualification_root.resolve())))
                return subprocess.run(record_command, cwd=ROOT, check=False).returncode
            loss_boundary = {"T03": 3, "T04": 4}.get(task_id)
            if run.get("state_mode") == "STATE_LOSS" and checkpoint == loss_boundary:
                print(
                    "Frozen state-loss boundary reached. Capture recovery state before revealing "
                    "the next checkpoint."
                )
                return 0
            continuation_command = [
                sys.executable, "-X", "utf8", str(Path(__file__).resolve()),
                str(task_root), "--run-id", run_id,
            ]
            if args.qualification_root:
                continuation_command.extend(
                    ("--qualification-root", str(args.qualification_root.resolve()))
                )
            print("\nCheckpoint accepted; automatically continuing the same CLI run to the next checkpoint.")
            return subprocess.run(continuation_command, cwd=ROOT, check=False).returncode
        return launched.returncode or graded.returncode

    input_zip, prompt = build_main_input(
        run_dir, workspace, run, checkpoint, previous, grade, executor_return
    )
    run = load_json(run_path)
    continuation = {
        "checkpoint": checkpoint,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "main_input": str(input_zip),
        "main_input_sha256": file_sha256(input_zip),
        "main_prompt": str(prompt),
        "main_prompt_sha256": file_sha256(prompt),
        "executor_return": str(executor_return),
        "executor_return_sha256": file_sha256(executor_return),
    }
    run.setdefault("main_continuations", []).append(continuation)
    run["main_inference_count"] = int(run.get("main_inference_count", 1)) + 1
    run["status"] = "AWAITING_MAIN_CONTINUATION"
    save_json(run_path, run)

    print(f"\nUpload to the same Main chat: {input_zip}")
    print(f"Copy/paste the single prompt from: {prompt}")
    print("Main must return one complete new handoff ZIP for this checkpoint.")
    main_minutes = prompt_main_minutes()
    chat_url = prompt_chat_url(run)
    continuation["main_chat_url"] = chat_url
    if main_minutes is not None:
        continuation["main_active_wall_seconds_reported"] = round(main_minutes * 60.0, 6)
    save_json(run_path, run)
    while True:
        handoff = prompt_handoff(run_dir, checkpoint)
        command = launch_command(load_json(run_path), task_root, handoff, chat_url)
        validation = subprocess.run(command + ["--dry-run"], cwd=ROOT, check=False)
        if validation.returncode == 0:
            break
        print("The handoff was rejected without changing the workspace. Correct it in Main and retry.")

    launched = subprocess.run(command, cwd=ROOT, check=False)
    graded = subprocess.run(
        [sys.executable, "-X", "utf8", str(ROOT / "scripts" / "grade_run.py"),
         str(task_root), "--run-id", run_id],
        cwd=ROOT,
        check=False,
    )
    if launched.returncode == 0 and graded.returncode == 0:
        updated = load_json(run_path)
        latest = updated.get("latest_auto_grade")
        if isinstance(latest, dict) and latest.get("all_checkpoints_graded"):
            return subprocess.run(
                [sys.executable, "-X", "utf8", str(ROOT / "scripts" / "record_run.py"),
                 str(task_root), "--run-id", run_id],
                cwd=ROOT,
                check=False,
            ).returncode
    return launched.returncode or graded.returncode


if __name__ == "__main__":
    raise SystemExit(main())
