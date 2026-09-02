#!/usr/bin/env python3
"""Create one timestamped run, package Main inputs, and open its CLI executor."""

from __future__ import annotations

import argparse
import csv
import json
import os
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


def portable_path(value: str) -> Path:
    """Accept the documented Windows path spelling when invoked on POSIX too."""
    if os.name != "nt":
        value = value.replace("\\", "/")
    return Path(value)


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


def write_main_prompt(task_root: Path, run_dir: Path, condition: str, ecosystem: str) -> Path:
    route = ROUTES[ecosystem]
    task = read(task_root / "TASK.md")
    if condition == "DIRECT":
        body = main_prompt(read(ROOT / "prompts" / "direct" / "00_START_TASK.md"), route, task)
        text = f"""# Main chat prompt

Upload `MAIN_INPUT.zip`, then paste this single message:

````text
{body}
````
"""
    else:
        loader = read(ROOT / "prompts" / "ai_native" / "00_LOAD_AI_NATIVE.md")
        body = main_prompt(read(ROOT / "prompts" / "ai_native" / "01_START_TASK.md"), route, task)
        text = f"""# Main chat prompts

Before pasting either message, upload `MAIN_INPUT.zip` from the printed run folder and
`AI_WORKFLOW_RUNTIME.zip` from the evaluation repository root. The runtime archive supplies the
clean `.ai-workflow/` directory at the scored repository root.

Paste message 1:

````text
{loader}
````

After Main confirms readiness, paste message 2:

````text
{body}
````
"""
    destination = run_dir / "MAIN_PROMPT.md"
    destination.write_text(text, encoding="utf-8", newline="\n")
    return destination


def package_inputs(task_root: Path, run_dir: Path, condition: str, run: dict) -> None:
    workspace = run_dir / "workspace"
    main_input = run_dir / "MAIN_INPUT.zip"
    zip_tree(workspace, main_input, exclude_top_level={".ai-workflow"})
    run["main_input"] = {
        "path": str(main_input),
        "sha256": file_sha256(main_input),
        "contains_ai_workflow": False,
    }
    if condition == "AI_NATIVE":
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
    elif (run_dir / ".ai-workflow.zip").exists():
        raise SystemExit("Direct run must not contain a legacy .ai-workflow.zip")
    prompt = write_main_prompt(task_root, run_dir, condition, run["ecosystem"])
    run["main_prompt"] = {"path": str(prompt), "sha256": file_sha256(prompt)}
    run["status"] = "AWAITING_MAIN"
    run["inputs_packaged_utc"] = utc_now()


def required_input(message: str) -> str:
    value = ""
    while not value:
        value = input(message).strip()
    return value


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
    parser.add_argument("--ecosystem", choices=("OPENAI", "ANTHROPIC"), default="OPENAI")
    parser.add_argument("--state-mode", choices=("NORMAL", "STATE_LOSS"), default="NORMAL")
    parser.add_argument("--main-chat-url")
    parser.add_argument("--main-model")
    parser.add_argument("--main-effort")
    parser.add_argument("--main-transcript", type=Path)
    parser.add_argument("--handoff", type=Path, help="already-downloaded first Main handoff ZIP")
    parser.add_argument("--claude-model")
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
    parser.add_argument("--stop-after-package", action="store_true")
    parser.add_argument("--non-scored", action="store_true")
    parser.add_argument("--qualification-root", type=Path)
    args = parser.parse_args()

    if args.qualification_root and not args.non_scored:
        raise SystemExit("--qualification-root requires --non-scored")
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
    print(f"Main input: {run_dir / 'MAIN_INPUT.zip'}")
    if args.condition == "AI_NATIVE":
        print(f"AI workflow: {WORKFLOW_ARCHIVE}")
    print(f"Copy/paste prompt: {run_dir / 'MAIN_PROMPT.md'}")
    if args.stop_after_package:
        return 0

    main_chat_url = args.main_chat_url or required_input("\nMain chat link: ")
    handoff = wait_for_first_handoff(run_dir, args.handoff)
    route = ROUTES[args.ecosystem]
    main_model = args.main_model or route["main"]
    main_effort = args.main_effort or ("highest exposed" if args.ecosystem == "OPENAI" else "high")
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
    return result


if __name__ == "__main__":
    raise SystemExit(main())
