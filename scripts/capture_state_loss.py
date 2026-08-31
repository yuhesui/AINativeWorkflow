#!/usr/bin/env python3
"""Capture the exact surviving repository and a transcript-free recovery packet."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from eval_common import file_sha256, tree_sha256

HALF_BUDGET_HOURS = {"T05": 6.0, "T06": 4.0, "T07": 12.0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_root", type=Path)
    parser.add_argument("run_id")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--accepted-grader-raw", type=Path)
    parser.add_argument("--elapsed-hours", type=float)
    parser.add_argument("--stable-handoff-evidence", type=Path)
    parser.add_argument(
        "--qualification-root",
        type=Path,
        help="write a structural dry-run snapshot outside the scored runs surface",
    )
    args = parser.parse_args()
    task_root, workspace = args.task_root.resolve(), args.workspace.resolve()
    task_id = task_root.name[:3]
    if task_id in ("T03", "T04"):
        required = 3 if task_id == "T03" else 4
        state_path = workspace / ".evaluation" / "CHECKPOINT_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        accepted = [x["checkpoint"] for x in state["accepted"]]
        if state["current_checkpoint"] != required or required in accepted:
            raise SystemExit(f"{task_id} loss requires checkpoint {required} current and the next checkpoint unrevealed")
        if not args.accepted_grader_raw or not args.accepted_grader_raw.is_file():
            raise SystemExit("checkpoint-loss capture requires the accepted checkpoint grader output")
        evidence_dir = workspace / ".evaluation" / "acceptance_evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_copy = evidence_dir / f"checkpoint_{required:02d}_grader_raw{args.accepted_grader_raw.suffix}"
        shutil.copy2(args.accepted_grader_raw, evidence_copy)
        state["accepted"].append({
            "checkpoint": required,
            "grader_raw": evidence_copy.relative_to(workspace).as_posix(),
            "grader_raw_sha256": file_sha256(evidence_copy),
        })
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif task_id in HALF_BUDGET_HOURS:
        if args.elapsed_hours is None or args.elapsed_hours < HALF_BUDGET_HOURS[task_id]:
            raise SystemExit(f"{task_id} loss cannot occur before {HALF_BUDGET_HOURS[task_id]} hours")
        if not args.stable_handoff_evidence or not args.stable_handoff_evidence.is_file():
            raise SystemExit("research-task loss requires stable handoff evidence")
    else:
        raise SystemExit("state loss is frozen only for T03-T07 modified variants")

    run_base = args.qualification_root.resolve() if args.qualification_root else task_root
    loss_root = run_base / "runs" / args.run_id / "state_loss"
    if not (loss_root.parent / "RUN.json").is_file():
        raise SystemExit(f"missing run metadata: {loss_root.parent / 'RUN.json'}")
    snapshot = loss_root / "repo_surviving"
    if snapshot.exists():
        raise SystemExit("state-loss snapshot already exists")
    shutil.copytree(workspace, snapshot)
    recovery = loss_root / "recovery_input"
    recovery.mkdir(parents=True)
    shutil.copy2(task_root / "TASK.md", recovery / "ORIGINAL_TASK.md")
    shutil.copy2(task_root / "RESOURCE_POLICY.md", recovery / "RESOURCE_POLICY.md")
    global_recovery = task_root.parents[1] / "prompts" / "common" / "STATE_LOSS_RECOVERY.md"
    shutil.copy2(global_recovery, recovery / "RECOVERY_INSTRUCTION.md")
    handoff_copy = None
    if args.stable_handoff_evidence:
        evidence_dir = loss_root / "evidence"
        evidence_dir.mkdir()
        handoff_copy = evidence_dir / f"stable_handoff{''.join(args.stable_handoff_evidence.suffixes)}"
        shutil.copy2(args.stable_handoff_evidence, handoff_copy)
    record = {
        "schema_version": 1,
        "task_id": task_id,
        "run_id": args.run_id,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_hours": args.elapsed_hours,
        "repo_surviving_tree_sha256": tree_sha256(snapshot),
        "old_main_transcript_transferred": False,
        "stable_handoff_evidence": str(handoff_copy) if handoff_copy else None,
        "stable_handoff_evidence_sha256": file_sha256(handoff_copy) if handoff_copy else None,
        "recovery_files": {p.name: file_sha256(p) for p in sorted(recovery.iterdir()) if p.is_file()},
    }
    (loss_root / "STATE_LOSS.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
