#!/usr/bin/env python3
"""Generate concise task-local operator instructions for the coding capsules."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAME = "TESTING_STEPS.md"


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    directory: str
    checkpoints: int | None = None
    loss_after: int | None = None


TASKS = (
    TaskSpec("T01", "T01_query_optimize"),
    TaskSpec("T02", "T02_dag_execution", checkpoints=3),
    TaskSpec("T03", "T03_database_migration", checkpoints=5, loss_after=3),
    TaskSpec("T04", "T04_recli", checkpoints=8, loss_after=4),
)

ROUTES = {
    "OPENAI": {
        "main": "ChatGPT GPT-5.6 Sol — highest reasoning setting actually exposed",
        "executor": "Codex CLI GPT-5.6 Terra — xhigh",
        "guidance": (
            "Executor route for this run: Codex CLI with GPT-5.6 Terra at xhigh. "
            "In HANDOFF_MANIFEST.json use selected_executor CODEX, requested_model "
            "gpt-5.6-terra, and requested_effort xhigh. Tune each executor prompt as one "
            "lean, self-contained assignment. State each instruction once and explicitly give "
            "the outcome, relevant repository context, constraints and approval boundaries, "
            "success criteria, verification evidence, and return format. Leave incidental "
            "implementation choices to the executor. Record the exact product-visible model "
            "and effort at launch; do not silently substitute."
        ),
    },
    "ANTHROPIC": {
        "main": "Claude Opus 5 — high",
        "executor": "Claude Code Sonnet 5 — high",
        "guidance": (
            "Executor route for this run: Claude Code CLI with Claude Sonnet 5 at high effort. "
            "In HANDOFF_MANIFEST.json use selected_executor CLAUDE, requested_model Claude "
            "Sonnet 5, and requested_effort high. Tune each executor prompt as a clear, direct, "
            "self-contained assignment: describe the outcome, point to relevant repository "
            "context, state constraints and the verification target, and name the required "
            "return artifacts. Use numbered steps only when order is semantically important; "
            "do not over-specify the implementation. Use current adaptive reasoning/effort "
            "controls, not a legacy manual thinking-token budget. Record the exact "
            "product-visible model and effort at launch; do not silently substitute."
        ),
    },
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def main_prompt(base: str, route: dict[str, str], task: str) -> str:
    return "\n\n".join((base, route["guidance"], "Frozen task prompt follows exactly:", task))


def render(spec: TaskSpec) -> str:
    display_name = spec.directory.split("_", 1)[1].replace("_", " ")
    task_path = f".\\tasks\\{spec.directory}"
    progressive = ""
    if spec.checkpoints:
        progressive = f"""## Checkpoints

This task has {spec.checkpoints} cumulative checkpoints. Only checkpoint 1 is initially visible.
After the private grader accepts the current checkpoint, reveal exactly the next checkpoint with
`scripts/reveal_checkpoint.py`. Use the timestamped run folder's `workspace/`; never give Main the
private grader or a later checkpoint early.
"""
    loss = ""
    if spec.loss_after:
        loss = f"""## State-loss variant

Create it as a separate timestamped run by adding `--state-mode STATE_LOSS` to the same start
command. Capture loss only after checkpoint {spec.loss_after}/{spec.checkpoints} is accepted and
before the next checkpoint is revealed. Follow `READY_FOR_SCORED_RUNS.md` for the frozen fresh-Main
recovery message; never transfer the old Main transcript.
"""

    return f"""# Testing steps — {display_name}

The starter keeps the operator flow to one command. It creates a unique UTC-dated folder under
`runs/`, packages the Main inputs in that folder, asks for the Main-chat link and downloaded
handoff, and opens the interactive CLI in the run's `workspace/`.

## Direct baseline with Codex

```powershell
python -X utf8 scripts/start_run.py "{task_path}" --condition DIRECT
```

## AI-Native workflow with Codex

```powershell
python -X utf8 scripts/start_run.py "{task_path}" --condition AI_NATIVE
```

The command remains open while you use Main:

1. Open the printed run folder.
2. Upload `MAIN_INPUT.zip` and paste `MAIN_PROMPT.md` into a fresh Main chat.
3. For AI-Native only, also upload the printed root `AI_WORKFLOW_RUNTIME.zip` as instructed by
   `MAIN_PROMPT.md`.
4. Paste the Main-chat link back into the waiting command.
5. Save Main's downloaded executor ZIP directly in that run folder and press Enter.
   `MAIN_HANDOFF.zip` is preferred, but a unique alternate `.zip` download name is accepted.
6. The starter validates the package before import. If rejected, overwrite it or save the corrected
   ZIP there under a new name, then press Enter; the workspace has not been changed.
7. Codex opens interactively, already rooted at the run's `workspace/` and pointed at Main's prompt.

Direct never creates or receives the runtime archive. AI-Native keeps `.ai-workflow/` in the scored
workspace and supplies the generated repository-root archive to Main. Main is never told to create
local paths. If the ignored archive or expanded runtimes are missing after checkout, the starter
reconstructs them from the tracked configured source package automatically;
`python -X utf8 scripts/update_ai_workflow.py` deliberately rebuilds and validates every copy.

`MAIN_INPUT.zip` preserves the complete agent-visible repository tree, including ordinary
subfolders, but excludes `.ai-workflow/` in both conditions. It has no special internal JSON
schema. By contrast, Main's returned handoff ZIP is validated against the exact file and manifest
contract embedded in `MAIN_PROMPT.md`. Its package may be at ZIP root or below exactly one wrapper
folder; manifest paths remain relative to the package contents below that wrapper.

## Run folder

Every invocation gets a name such as
`run_20260901T153000Z_{spec.task_id}_OPENAI_DIRECT_NORMAL`, so reruns never overwrite one another.
The run root contains `RUN.json`, `MAIN_INPUT.zip`, `MAIN_PROMPT.md`, and the downloaded handoff ZIP.
`RUN.json` records the hash and path of the shared workflow archive for AI-Native runs, so no
per-run runtime duplicate is created. It is the single evolving metadata record for the Main link,
model route, timestamps, executor sessions, wall time, usage, and hashes. The initial repository is
retained as a reproducible task-lock/tree-hash reference; the final repository remains a required
full directory.

For the Anthropic row, add `--ecosystem ANTHROPIC`; the same command opens Claude Code instead of
Codex and asks for the exact installed Sonnet model identifier.

{progressive}
{loss}
## Finish

Run the private grader outside the workspace. Finalize using the timestamped folder name as the run
ID and pass that folder's `RUN.json` as `--metrics-json`. Finalization retains the full repository in
`repo_final/` and writes native scoring results separately under `run_results/`.

This file is generated by `scripts/generate_chat_main_runbooks.py`. The frozen task prompt itself is
read from this task root at run creation and written verbatim into that run's `MAIN_PROMPT.md`.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated runbooks are stale")
    args = parser.parse_args()
    stale: list[str] = []
    for spec in TASKS:
        destination = ROOT / "tasks" / spec.directory / OUTPUT_NAME
        expected = render(spec)
        if args.check:
            if not destination.is_file() or destination.read_text(encoding="utf-8") != expected:
                stale.append(destination.relative_to(ROOT).as_posix())
        else:
            destination.write_text(expected, encoding="utf-8", newline="\n")
            print(destination.relative_to(ROOT).as_posix())
    if stale:
        raise SystemExit("stale generated runbooks:\n- " + "\n- ".join(stale))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
