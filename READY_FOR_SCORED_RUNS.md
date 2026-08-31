# Scored-run operations and readiness gates

Repository-wide qualification status: **QUALIFIED_WITH_BLOCKERS**.

T1, T2, T3, T4, and T6 have qualified environments and graders. T5 and T7
are hard-stopped and must not be scored until the blockers in `SETUP_REPORT.md`
are resolved without changing a frozen identity. This document is an operator
runbook; it is not authorization to start a row of `manifests/RUN_MATRIX.csv`.

## Before each run

1. Select exactly one frozen RUN_MATRIX row and assign its never-before-used
   run ID and attempt ID. An infrastructure rerun always receives a new ID and
   records the earlier run's invalidation reason.
2. Confirm the task's `QUALIFICATION_STATUS.json` is `QUALIFIED`, then run
   `python -X utf8 scripts/validate_repo.py` and verify the task and environment
   locks. Do not waive a `BLOCKED` status.
3. Record the exact product-visible Main and executor identifiers. For T1-T4,
   OpenAI routing is ChatGPT GPT-5.6 Sol at the highest exposed reasoning level
   with Codex GPT-5.6 Terra xhigh; Anthropic routing is Claude Opus 5 high with
   Claude Code Sonnet 5 high. Do not substitute silently. T5-T7 expose the same
   frozen mixed research resource menu to both conditions and let Main choose
   routing.
4. Confirm the matched task budget in `test_repo/RESOURCE_POLICY.md`, available
   disk, network policy, and required hardware. Do not buy compute without
   human approval.
5. Materialize a fresh workspace. This is the only supported source of both
   conditions:

   ```text
   python scripts/prepare_run.py tasks/<TASK> --condition DIRECT \
     --run-id <RUN_ID> --attempt-id <ATTEMPT_ID> \
     --authorize-scored-materialization

   python scripts/prepare_run.py tasks/<TASK> --condition AI_NATIVE \
     --run-id <RUN_ID> --attempt-id <ATTEMPT_ID> \
     --authorize-scored-materialization
   ```

   Use only the command matching the selected row. The Direct copy is the full
   `test_repo/` with `.ai-workflow/` physically excluded. The AI-Native copy is
   the full same repository including a clean `.ai-workflow/`. Never maintain a
   separate hand-edited Direct tree.

## Direct operational loop

Open a fresh Main chat on the materialized `workspace/` and give it only the
frozen task prompt and frozen resource menu. Direct may plan, write ordinary
notes, delegate, research where allowed, test, and revise. It receives no
AI-Native loader, documents, or state. Record transcripts, tool routing,
resource measurements, and grader evidence under the run's `main/`,
`executors/`, and `evidence/` directories without mounting private evaluation
material into the workspace.

For progressive tasks, an operator runs the private cumulative grader, stores
its raw record outside the workspace, and uses `scripts/reveal_checkpoint.py`
to reveal only the immediate next checkpoint after acceptance. Main must never
see later checkpoint prompts or hidden tests early.

## AI-Native operational loop

Open a fresh Main chat on the materialized `workspace/`. Supply the AI-Native
loader prompt, have Main read the root `.ai-workflow/`, then supply the frozen
task prompt. Treat the task as the approved Goal. Main itself creates the Plan,
chooses the Phase decomposition, creates each active Phase folder/DIC/EPS,
delegates bounded work, evaluates returned evidence, and accepts, repairs, or
replans. Do not pre-create task-specific plans, phase counts, DICs, EPSs, or
execution history.

Preserve every durable runtime mutation. The final AI-Native repository must
include its full final `.ai-workflow/`; the final Direct repository must not
contain that directory.

## Frozen state-loss loop

Do not transfer the old Main transcript. Preserve the exact surviving
workspace, Git state, generated files, and evidence, then invoke
`scripts/capture_state_loss.py` at only the frozen boundary:

- T3m: accepted checkpoint 3, before checkpoint 4 reveal.
- T4m: accepted checkpoint 4, before checkpoint 5 reveal.
- T5m/T6m/T7m: first stable Main-to-executor handoff after 50% of the frozen
  wall-time budget, with elapsed-time and handoff evidence supplied.

Start a fresh Main with only the original task prompt, surviving repository,
same resource menu, and frozen recovery instruction. AI-Native recovery relies
on surviving `.ai-workflow/`; Direct receives only its ordinary surviving
files. Store recovery measurements in the separate result record.

## Finish every trajectory, including failures

After stopping the workspace, run `scripts/finalize_run.py` with `VALID`,
`FAILED_TASK`, or `INVALID_INFRASTRUCTURE`. Valid/failed-task finalization also
requires `--grader-raw`; supply the native metric and structured metrics where
available. Infrastructure invalidation requires a reason. The tool copies the **entire** workspace to
`runs/<RUN_ID>/repo_final/`, hashes it, and creates the separate
`run_results/<RUN_ID>/` record skeleton. Retain raw native grader output,
checkpoint/subcomponent metrics, wall/resource data, recovery data when
applicable, and links/hashes to final repository and evidence. Never replace a
native primary metric with a composite score and never delete a failed or
interrupted trajectory.

Before releasing the run for analysis, re-run validation, confirm the condition
presence/absence rule for `.ai-workflow/`, verify hidden material never entered
the workspace, and ensure every raw record and hash is present. Analysis may
begin only after the frozen run row is finalized; task prompts and policies
must not be tuned from candidate performance.

## Current hard stops

- T5/T5m: the frozen MLGym config requests 64 evaluation environments while
  the shipped evaluator hard-codes 256. An explicit protocol revision or
  authoritative upstream resolution is required.
- T7/T7m: native PaperBench rubric judging needs an operator-supplied grader
  credential, and full GPU execution is unqualified because Docker has no
  NVIDIA runtime and the host has only 6 GiB VRAM. Do not downgrade to
  PaperBench Code-Dev.
