#!/usr/bin/env python3
"""Open or resume one CLI session on a frozen Direct or AI-Native Goal."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from eval_common import file_sha256, load_json
from launch_executor import parse_usage, save_json, usage_totals, utc_now
from task_environment import ensure_sidecar, environment_spec, stop_sidecar
from usage_cost import attach_cost_estimate


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch or resume one frozen CLI Goal run.")
    parser.add_argument("task_root", type=Path)
    parser.add_argument("run_id")
    parser.add_argument("--executor", choices=("CODEX", "CLAUDE"), required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--claude-model")
    parser.add_argument("--codex-model")
    parser.add_argument("--codex-effort", choices=("medium", "high", "xhigh"))
    parser.add_argument("--usage-json", type=Path)
    parser.add_argument("--skip-usage-prompt", action="store_true")
    parser.add_argument(
        "--resume-session",
        action="store_true",
        help="resume the most recent CLI session scoped to this run workspace",
    )
    parser.add_argument("--qualification-root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    task_root = args.task_root.resolve()
    run_base = args.qualification_root.resolve() if args.qualification_root else task_root
    run_dir = run_base / "runs" / args.run_id
    run_path = run_dir / "RUN.json"
    workspace = run_dir / "workspace"
    prompt = args.prompt.resolve()
    if not run_path.is_file() or not workspace.is_dir():
        raise SystemExit("run must already contain RUN.json and workspace/")
    if not prompt.is_file() or prompt.parent != run_dir:
        raise SystemExit("--prompt must be a file stored directly in this run folder")
    run = load_json(run_path)
    condition = str(run.get("condition"))
    if condition not in {"DIRECT", "AI_NATIVE"}:
        raise SystemExit("run condition must be DIRECT or AI_NATIVE")
    if run.get("status") == "FINALIZED":
        raise SystemExit("cannot launch an executor for a finalized run")
    if condition == "DIRECT" and (workspace / ".ai-workflow").exists():
        raise SystemExit("Direct workspace must not contain .ai-workflow")
    if condition == "AI_NATIVE" and not (workspace / ".ai-workflow").is_dir():
        raise SystemExit("AI-Native workspace must contain .ai-workflow")

    required_effort = (args.codex_effort or "xhigh") if args.executor == "CODEX" else "high"
    if args.executor == "CODEX":
        executor_model = args.codex_model or "gpt-5.6-terra"
    else:
        executor_model = (args.claude_model or "").strip()
        if not executor_model and not args.dry_run:
            executor_model = input("Exact product-visible Claude Sonnet 5 CLI model ID: ").strip()
        if not executor_model:
            executor_model = "<EXACT_CLAUDE_SONNET_5_MODEL_ID>"

    condition_label = "Direct baseline" if condition == "DIRECT" else "AI-Native run"
    bootstrap = (
        f"Treat the assignment below as the approved Goal continuation for this {condition_label}. Work "
        "autonomously from the current repository root in one CLI session, implement the complete "
        "currently revealed task, test and repair it, and preserve concise evidence. Do not read "
        "outside this repository or access private evaluator material.\n\n"
        + prompt.read_text(encoding="utf-8")
    )
    if environment_spec(task_root) is not None:
        bootstrap += (
            "\n\nUse the frozen Linux sidecar for every task build, test, and runtime command: "
            "`python .evaluation/run_in_env.py exec-self -- <command>`. The same workspace is "
            "mounted at `/app` inside that environment. If the wrapper says the sidecar is not "
            "running, retry that command once with escalated command permission; automatic "
            "approval is enabled. Do not stop for the first sandbox-limited result."
        )
    if args.executor == "CODEX":
        if args.resume_session:
            command = [
                "codex", "resume", "--last", "-C", str(workspace), "-m", executor_model,
                "-c", f'model_reasoning_effort="{required_effort}"', "--approve-for-me", bootstrap,
            ]
        else:
            command = [
                "codex", "-C", str(workspace), "-m", executor_model,
                "-c", f'model_reasoning_effort="{required_effort}"', "--approve-for-me", bootstrap,
            ]
    else:
        command = ["claude"]
        if args.resume_session:
            command.append("--continue")
        command.extend(("--model", executor_model, "--effort", "high"))
        if not args.resume_session:
            command.extend(("--name", f"{args.run_id}-{condition.lower()}-goal"))
        command.append(bootstrap)
    if args.dry_run:
        print(json.dumps({
            "status": "DRY_RUN_VALID",
            "workspace": str(workspace),
            "executor_prompt": str(prompt),
            "command": command,
        }, indent=2))
        return 0

    executable = shutil.which(command[0])
    if executable is None:
        raise SystemExit(f"executor CLI is not installed or not on PATH: {command[0]}")
    command[0] = executable
    version = subprocess.run(
        [executable, "--version"], capture_output=True, text=True, check=False
    ).stdout.strip()
    try:
        task_environment = ensure_sidecar(task_root, args.run_id, workspace)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if task_environment is not None:
        run["task_environment"] = task_environment
    started_utc = utc_now()
    run.setdefault("started_utc", started_utc)
    run["status"] = "IN_PROGRESS"
    prefix = "DIRECT" if condition == "DIRECT" else "AI_NATIVE"
    execution_mode = f"{prefix}_CLI_GOAL_RESUME" if args.resume_session else f"{prefix}_CLI_GOAL"
    run["execution_mode"] = execution_mode
    if condition == "DIRECT":
        run["main_inference_count"] = 0
    run["active_executor_product_visible"] = executor_model
    run["active_executor_effort"] = required_effort
    save_json(run_path, run)
    print(f"\nOpening {args.executor} directly in repository: {workspace}")
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
    attach_cost_estimate(usage, executor_model)
    sequence = len(run.get("executor_sessions", [])) + 1
    session = {
        "schema_version": 1,
        "session_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-direct-{sequence:02d}",
        "run_id": args.run_id,
        "handoff_id": None,
        "execution_mode": execution_mode,
        "executor": args.executor,
        "executor_model_product_visible": executor_model,
        "executor_effort": required_effort,
        "cli_version": version,
        "started_utc": started_utc,
        "ended_utc": ended_utc,
        "wall_seconds": round(wall_seconds, 6),
        "process_exit_code": result.returncode,
        "executor_prompt": str(prompt),
        "executor_prompt_sha256": file_sha256(prompt),
        "source_bundle": None,
        "usage": usage,
        "usage_source": usage_source,
    }
    run.setdefault("executor_sessions", []).append(session)
    run["usage_totals"] = usage_totals(run["executor_sessions"])
    run.setdefault("observed_executor_sessions", []).append({
        "session_id": session["session_id"],
        "executor": args.executor,
        "model": executor_model,
        "effort": required_effort,
    })
    save_json(run_path, run)
    print(json.dumps({"session_record": str(run_path), "process_exit_code": result.returncode}, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
