#!/usr/bin/env python3
"""Reveal exactly one accepted SlopCodeBench checkpoint instruction."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from eval_common import file_sha256

TOTALS = {"T02": 3, "T03": 5, "T04": 8}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_root", type=Path)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--checkpoint", type=int, required=True)
    parser.add_argument("--accepted-grader-raw", type=Path, required=True)
    args = parser.parse_args()
    task_root, workspace = args.task_root.resolve(), args.workspace.resolve()
    task_id = task_root.name[:3]
    if task_id not in TOTALS or not 2 <= args.checkpoint <= TOTALS[task_id]:
        raise SystemExit("invalid task/checkpoint")
    state_path = workspace / ".evaluation" / "CHECKPOINT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if args.checkpoint != state["current_checkpoint"] + 1:
        raise SystemExit("checkpoints must be revealed exactly once and in order")
    if not args.accepted_grader_raw.is_file():
        raise SystemExit("accepted grader raw output is required before reveal")
    previous = state["current_checkpoint"]
    evidence_dir = workspace / ".evaluation" / "acceptance_evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_copy = evidence_dir / f"checkpoint_{previous:02d}_grader_raw{args.accepted_grader_raw.suffix}"
    shutil.copy2(args.accepted_grader_raw, evidence_copy)
    instruction = task_root / "qualification" / "private_eval" / "steps" / f"checkpoint_{args.checkpoint}" / "instruction.md"
    if not instruction.is_file():
        raise SystemExit(f"missing private checkpoint instruction: {instruction}")
    destination = workspace / "CHECKPOINTS" / f"{args.checkpoint:02d}.md"
    shutil.copy2(instruction, destination)
    state["accepted"].append({
        "checkpoint": previous,
        "grader_raw": evidence_copy.relative_to(workspace).as_posix(),
        "grader_raw_sha256": file_sha256(evidence_copy),
    })
    state["current_checkpoint"] = args.checkpoint
    state["revealed"].append(args.checkpoint)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"revealed": args.checkpoint, "path": str(destination)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
