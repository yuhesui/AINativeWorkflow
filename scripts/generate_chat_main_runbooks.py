#!/usr/bin/env python3
"""Generate copy/paste chat-Main runbooks for the frozen T1-T4 capsules."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAME = "CHAT_MAIN_TESTING_STEPS.md"


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
        "slug": "codex",
        "guidance": (
            "Executor route for this run: Codex CLI with GPT-5.6 Terra at xhigh. "
            "Tune each executor prompt as one lean, self-contained assignment. State each "
            "instruction once and explicitly give the outcome, relevant repository context, "
            "constraints and approval boundaries, success criteria, verification evidence, and "
            "return format. Leave incidental implementation choices to the executor. Record the "
            "exact product-visible model and effort at launch; do not silently substitute."
        ),
    },
    "ANTHROPIC": {
        "main": "Claude Opus 5 — high",
        "executor": "Claude Code Sonnet 5 — high",
        "slug": "claude",
        "guidance": (
            "Executor route for this run: Claude Code CLI with Claude Sonnet 5 at high effort. "
            "Tune each executor prompt as a clear, direct, self-contained assignment: describe "
            "the outcome, point to relevant repository context, state constraints and the "
            "verification target, and name the required return artifacts. Use numbered steps only "
            "when order is semantically important; do not over-specify the implementation. Use "
            "current adaptive reasoning/effort controls, not a legacy manual thinking-token "
            "budget. Record the exact product-visible model and effort at launch; do not silently "
            "substitute."
        ),
    },
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def prompt_block(text: str) -> str:
    return f"````text\n{text.rstrip()}\n````"


def run_id(spec: TaskSpec, ecosystem: str, condition: str, state_loss: bool = False) -> str:
    mode = "STATE_LOSS" if state_loss else "NORMAL"
    return f"{spec.task_id}_{ecosystem}_{condition}_{mode}"


def materialize_block(spec: TaskSpec, ecosystem: str, condition: str, state_loss: bool = False) -> str:
    selected_run = run_id(spec, ecosystem, condition, state_loss)
    return f"""```powershell
$TaskRoot = (Resolve-Path ".\\tasks\\{spec.directory}").Path
$RunId = "{selected_run}"
$AttemptId = "attempt-01"
python -X utf8 scripts/prepare_run.py "$TaskRoot" --condition {condition} `
  --run-id $RunId --attempt-id $AttemptId --authorize-scored-materialization
$Workspace = Join-Path $TaskRoot "runs\\$RunId\\workspace"
```"""


def main_prompt(base: str, route: dict[str, str], task: str) -> str:
    return "\n\n".join(
        (
            base,
            route["guidance"],
            "Frozen task prompt follows exactly:",
            task,
        )
    )


def progressive_section(spec: TaskSpec) -> str:
    if spec.checkpoints is None:
        return """## Task/grader loop

1. Main creates a bounded handoff archive when it needs the CLI executor.
2. Import the archive, run the permitted executor, return the executor's final report, diff,
   commands, test output, and requested evidence to the same Main chat.
3. Repeat until Main declares the task ready for the private grader or the frozen budget ends.
4. Run the official private grader outside the workspace. Do not paste hidden grader code,
   expected answers, or private material into Main or the executor.
"""

    reveals = []
    for checkpoint in range(2, spec.checkpoints + 1):
        reveals.append(
            f"""After checkpoint {checkpoint - 1} is accepted, reveal checkpoint {checkpoint}:

```powershell
$GraderRaw = (Resolve-Path "<RAW_GRADER_OUTPUT_FOR_CHECKPOINT_{checkpoint - 1}>").Path
python -X utf8 scripts/reveal_checkpoint.py "$TaskRoot" "$Workspace" `
  --checkpoint {checkpoint} --accepted-grader-raw "$GraderRaw"
Get-Content -Raw "$Workspace\\CHECKPOINTS\\{checkpoint:02d}.md" | Set-Clipboard
```

Paste this preface followed by the clipboard contents into the same Main chat:

{prompt_block(f"Checkpoint {checkpoint - 1} was accepted. Continue the same cumulative task using the newly and officially revealed checkpoint {checkpoint} below. Preserve all prior requirements and tests. Do not assume access to any later checkpoint.")}
"""
        )
    return f"""## Progressive checkpoint/grader loop

Only checkpoint 1 is initially visible. At every checkpoint, Main and its executor may use the
visible repository and visible tests, but the operator alone runs the cumulative private grader.
Save raw grader output outside the workspace under `runs/<RUN_ID>/evidence/`. Never browse
`qualification/private_eval/` from Main or an executor.

{chr(10).join(reveals)}
After checkpoint {spec.checkpoints}, run the final cumulative private grader and retain its raw
native output for finalization. Do not call `reveal_checkpoint.py` again.
"""


def state_loss_section(
    spec: TaskSpec,
    recovery: str,
    task: str,
) -> str:
    if spec.loss_after is None:
        return ""
    next_checkpoint = spec.loss_after + 1
    variants = []
    for ecosystem, route in ROUTES.items():
        for condition in ("DIRECT", "AI_NATIVE"):
            recovery_prompt = "\n\n".join(
                (
                    recovery,
                    route["guidance"],
                    (
                        f"This is the {condition} recovery. Use only the surviving repository, "
                        "the original task, and this instruction. The old Main transcript is not "
                        "available. Do not ask for it or infer unstored intent."
                    ),
                    "Original frozen task prompt follows exactly:",
                    task,
                )
            )
            variants.append(
                f"""### {ecosystem} {condition} state-loss row

Materialize the state-loss row at the start of the trajectory:

{materialize_block(spec, ecosystem, condition, state_loss=True)}

After checkpoint {spec.loss_after} has passed, but before checkpoint {next_checkpoint} is revealed:

```powershell
$GraderRaw = (Resolve-Path "<RAW_GRADER_OUTPUT_FOR_CHECKPOINT_{spec.loss_after}>").Path
python -X utf8 scripts/capture_state_loss.py "$TaskRoot" "$RunId" "$Workspace" `
  --accepted-grader-raw "$GraderRaw"
```

Close the old Main chat. Open a fresh {route['main']} chat, give it access to only the surviving
workspace and the unchanged resource menu, and paste exactly:

{prompt_block(recovery_prompt)}

Do not send the AI-Native loader during recovery. In AI_NATIVE, the fresh Main recovers from the
surviving `.ai-workflow/`; in DIRECT it sees only ordinary surviving files. After recovery is
established, reveal checkpoint {next_checkpoint} with `reveal_checkpoint.py` and continue the
normal checkpoint loop.
"""
            )
    return f"""## Optional frozen state-loss rows

These rows are separate trajectories; never convert a normal row in place. The loss boundary is
after checkpoint {spec.loss_after}/{spec.checkpoints} acceptance and before checkpoint
{next_checkpoint} reveal.

{chr(10).join(variants)}"""


def executor_loop() -> str:
    return """## Chat Main to CLI executor handoff

For each handoff, Main emits one ZIP and states its archive filename plus the repository-relative
executor prompt path. Save the original ZIP under
`tasks/<TASK>/runs/<RUN_ID>/main/handoff_packages/`, then import it into the scored workspace:

```powershell
$Bundle = (Resolve-Path "<MAIN_HANDOFF_ZIP>").Path
Expand-Archive -LiteralPath "$Bundle" -DestinationPath "$Workspace" -Force
$PromptPath = Join-Path "$Workspace" "<EXECUTOR_PROMPT_PATH_REPORTED_BY_MAIN>"
```

The Direct ZIP must expand only under `executor_handoffs/<handoff-id>/` and must never contain
`.ai-workflow`, DIC, EPS, hidden tests, expected answers, or unrevealed checkpoints. The AI-Native
ZIP must carry one canonical `.ai-workflow/runtime/plans/<plan-id>/phases/<phase-id>/` subtree with
the full Phase DIC, one assigned EPS instance/prompt, and its handoff manifest. Reject a malformed
archive before launching the executor.

For Codex CLI, first record `codex --version` and confirm the configured model is exactly GPT-5.6
Terra. A locally verified noninteractive PowerShell pattern is:

```powershell
$ExecutorLog = Join-Path "$TaskRoot" "runs\\$RunId\\executors\\$(Split-Path $PromptPath -LeafBase).jsonl"
$ExecutorFinal = Join-Path "$TaskRoot" "runs\\$RunId\\executors\\$(Split-Path $PromptPath -LeafBase)-final.md"
Get-Content -Raw "$PromptPath" | codex exec -C "$Workspace" -m gpt-5.6-terra `
  -c 'model_reasoning_effort="xhigh"' --sandbox workspace-write --json `
  --output-last-message "$ExecutorFinal" - | Tee-Object -FilePath "$ExecutorLog"
```

For Claude Code, first run `claude --version` and `claude --help`, then replace the placeholder
with the exact product-visible Sonnet 5 identifier offered by the installed CLI. Do not use an
alias if it could resolve to another model:

```powershell
$ClaudeModel = "<EXACT_PRODUCT_VISIBLE_CLAUDE_SONNET_5_ID>"
$ExecutorLog = Join-Path "$TaskRoot" "runs\\$RunId\\executors\\$(Split-Path $PromptPath -LeafBase).jsonl"
Get-Content -Raw "$PromptPath" | claude -p --model "$ClaudeModel" --effort high `
  --output-format stream-json --verbose | Tee-Object -FilePath "$ExecutorLog"
```

Use only the permissions and network access allowed by `RESOURCE_POLICY.md`; never enable a broad
bypass mode merely to avoid a permission prompt. After execution, give Main the executor's concise
final report, exact changed-file/diff evidence, commands/tests and failures. Do not give Main the
private grader implementation. Main then accepts, repairs, replans, or emits the next handoff ZIP.
"""


def finalization_section() -> str:
    return """## Finalize the trajectory

Stop all Main/executor activity before grading/finalization. Preserve failures. Supply the actual
grader and metrics files; the placeholders below are deliberately not guessed:

```powershell
$GraderRaw = (Resolve-Path "<FINAL_NATIVE_GRADER_RAW_FILE>").Path
$Metrics = (Resolve-Path "<STRUCTURED_METRICS_JSON>").Path
python -X utf8 scripts/finalize_run.py "$TaskRoot" "$RunId" "$Workspace" `
  --validity VALID --grader-raw "$GraderRaw" --metrics-json "$Metrics" `
  --native-primary-metric <NATIVE_METRIC>
```

For a task failure use `--validity FAILED_TASK`. For infrastructure invalidation use
`--validity INVALID_INFRASTRUCTURE --invalidation-reason "<EXACT_REASON>"`; allocate a new run and
attempt identifier for any rerun. Finalization must retain the entire final repository. Do not run
or compare another matrix row as part of the same trajectory.
"""


def render(spec: TaskSpec) -> str:
    task_root = ROOT / "tasks" / spec.directory
    task = read(task_root / "TASK.md")
    direct = read(ROOT / "prompts" / "direct" / "00_START_TASK.md")
    loader = read(ROOT / "prompts" / "ai_native" / "00_LOAD_AI_NATIVE.md")
    ai_start = read(ROOT / "prompts" / "ai_native" / "01_START_TASK.md")
    recovery = read(ROOT / "prompts" / "common" / "STATE_LOSS_RECOVERY.md")

    recipe_parts = []
    for ecosystem, route in ROUTES.items():
        recipe_parts.append(
            f"""## {ecosystem} Direct

Main: **{route['main']}**. Executor: **{route['executor']}**.

{materialize_block(spec, ecosystem, 'DIRECT')}

Open a fresh Main chat with access to the materialized workspace and unchanged resource policy.
Paste this as the first and only task-start message:

{prompt_block(main_prompt(direct, route, task))}

Do not send the AI-Native loader or expose any global workflow reference material.

## {ecosystem} AI-Native

Main: **{route['main']}**. Executor: **{route['executor']}**.

{materialize_block(spec, ecosystem, 'AI_NATIVE')}

Open a fresh Main chat with access to the materialized workspace. Paste loader message 1 exactly:

{prompt_block(loader)}

Wait only for the requested ready confirmation. Then paste task-start message 2 exactly:

{prompt_block(main_prompt(ai_start, route, task))}

Main chooses the Plan and number of Phases after task start; the operator does not pre-create them.
"""
        )

    rows = []
    for ecosystem in ROUTES:
        for condition in ("DIRECT", "AI_NATIVE"):
            rows.append(f"| `{run_id(spec, ecosystem, condition)}` | {ecosystem} | {condition} |")

    return f"""# {spec.task_id} chat-Main testing steps

Generated by `scripts/generate_chat_main_runbooks.py`. This is an operator runbook outside the
scored repository; it does not replace or modify the frozen `TASK.md`. It materializes no run and
authorizes no scored execution by itself.

## Fixed scope and routes

| Normal run ID | Ecosystem | Condition |
|---|---|---|
{chr(10).join(rows)}

The Main surface is a fresh persistent **chat** in both conditions. The CLI is only a bounded
executor. Record exact product-visible identifiers and effort settings in `RUN.json` at launch.

The frozen matched budget and access rules are in this task root's `RESOURCE_POLICY.md`. Enforce
that file exactly and give the same limits to both conditions.

Before selecting one row, run `python -X utf8 scripts/validate_repo.py`, confirm this task is
`QUALIFIED`, and confirm no scored run directory already uses the selected ID. Run exactly one row.

{chr(10).join(recipe_parts)}

{executor_loop()}

{progressive_section(spec)}

{state_loss_section(spec, recovery, task)}

{finalization_section()}

## Prompt-shaping provenance

The executor route text follows the repository's locked runtime guidance and current official
provider guidance: OpenAI's `Using GPT-5.6` guide, Anthropic's `Prompting best practices`, and
Anthropic's `Best practices for Claude Code`. Provider webpages are not copied into the scored
workspace. Recheck installed CLI help at run time because command flags and exact product-visible
model identifiers can change; never change the frozen model policy silently.
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
