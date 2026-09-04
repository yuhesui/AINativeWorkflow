#!/usr/bin/env python3
"""Return T06 Phase evidence to Main and launch the next Sol-medium Phase."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from eval_common import file_sha256, load_json
from start_run import (
    finish_run,
    handoff_zip_candidates,
    launch,
    prompt_optional_minutes,
    save_json,
    utc_now,
    wait_for_first_handoff,
    wait_for_replacement_handoff,
    zip_tree,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_root", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--main-wall-minutes", type=float)
    parser.add_argument("--skip-auto-grade", action="store_true")
    parser.add_argument("--skip-post-run-record", action="store_true")
    args = parser.parse_args()

    task_root = args.task_root.resolve()
    run_dir = task_root / "runs" / args.run_id
    run_path = run_dir / "RUN.json"
    workspace = run_dir / "workspace"
    if not run_path.is_file() or not workspace.is_dir():
        raise SystemExit("run must contain RUN.json and workspace/")
    run = load_json(run_path)
    if run.get("task_id") != "T06" or run.get("condition") != "AI_NATIVE":
        raise SystemExit("continue_t06_run.py only accepts T06 AI_NATIVE runs")
    if run.get("status") == "FINALIZED":
        raise SystemExit("cannot continue a finalized run")

    input_zip = run_dir / "MAIN_CONTINUE_INPUT.zip"
    if input_zip.exists():
        input_zip.unlink()
    zip_tree(workspace, input_zip)
    run.setdefault("main_continuation_inputs", []).append(
        {"created_utc": utc_now(), "path": str(input_zip), "sha256": file_sha256(input_zip)}
    )
    run["status"] = "AWAITING_MAIN_CONTINUATION"
    save_json(run_path, run)

    prompt = run_dir / "MAIN_CONTINUE_PROMPT.md"
    if not prompt.is_file():
        raise SystemExit(f"missing fixed continuation prompt: {prompt}")
    print(f"\nUpload to the same Main chat: {input_zip}")
    print(f"Paste the complete fixed prompt from: {prompt}")
    minutes = prompt_optional_minutes(
        args.main_wall_minutes,
        "Main active/compute time for this continuation",
    )
    if args.handoff is not None:
        handoff = wait_for_first_handoff(run_dir, args.handoff)
    else:
        existing = {path: file_sha256(path) for path in handoff_zip_candidates(run_dir)}
        print("Save Main's new handoff ZIP directly in the run folder.")
        handoff = wait_for_replacement_handoff(run_dir, existing)

    chats = run.get("main_chats", [])
    if not chats or not isinstance(chats[-1], dict) or not chats[-1].get("url"):
        raise SystemExit("RUN.json has no archived Main chat URL")
    main_url = str(chats[-1]["url"])
    main_model = str(run.get("main_model_product_visible") or "ChatGPT GPT-5.6 Sol")
    main_effort = str(run.get("main_effort_product_visible") or "xhigh")
    if main_effort != "xhigh":
        raise SystemExit("T06 Main effort must remain xhigh")

    rejected: dict[Path, str] = {}
    while True:
        validation = launch(
            task_root,
            args.run_id,
            handoff,
            ecosystem="OPENAI",
            main_chat_url=main_url,
            main_model=main_model,
            main_effort=main_effort,
            claude_model=None,
            allow_shared_chat_link=True,
            main_transcript=None,
            qualification_root=None,
            dry_run=True,
        )
        if validation == 0:
            break
        rejected[handoff.resolve()] = file_sha256(handoff)
        handoff = wait_for_replacement_handoff(run_dir, rejected)

    run = load_json(run_path)
    run["main_inference_count"] = int(run.get("main_inference_count", 1)) + 1
    if minutes is not None:
        seconds = round(minutes * 60.0, 6)
        run["main_active_wall_seconds_reported"] = round(
            float(run.get("main_active_wall_seconds_reported", 0.0)) + seconds,
            6,
        )
    save_json(run_path, run)

    result = launch(
        task_root,
        args.run_id,
        handoff,
        ecosystem="OPENAI",
        main_chat_url=main_url,
        main_model=main_model,
        main_effort=main_effort,
        claude_model=None,
        allow_shared_chat_link=True,
        main_transcript=None,
        qualification_root=None,
    )
    return finish_run(
        task_root,
        args.run_id,
        result,
        qualification_root=None,
        skip_auto_grade=args.skip_auto_grade,
        skip_post_run_record=args.skip_post_run_record,
    )


if __name__ == "__main__":
    raise SystemExit(main())
