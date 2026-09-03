# Testing steps — recli

Run these commands in a system terminal from the evaluation repository root—not in a ChatGPT,
Codex, or Claude prompt. The starter keeps the operator flow to one command. It creates a unique UTC-dated folder under
`runs/` and opens the interactive CLI in the run's `workspace/`. Direct goes straight to the coding
CLI as one approved-Goal run. AI-Native first performs exactly one Main inference for the currently
revealed scope and imports Main's complete Phase package.

## Direct baseline with Claude Code

```shell
python -X utf8 scripts/start_run.py "./tasks/T04_recli" --condition DIRECT
```

## AI-Native workflow with Claude Code

```shell
python -X utf8 scripts/start_run.py "./tasks/T04_recli" --condition AI_NATIVE
```

On macOS, use `python3` in place of `python` if that is the installed interpreter command.

For Direct, the command immediately opens Claude Code at `workspace/` with `DIRECT_GOAL.md`. There is no
Main chat, Main input ZIP, chat link, or Main token/time prompt.

For AI-Native, the same command pauses for one Main inference:

1. Open the printed run folder.
2. Upload `MAIN_INPUT.zip` and paste `MAIN_PROMPT.md` into a fresh Main chat.
3. For AI-Native only, also upload the printed root `AI_WORKFLOW_RUNTIME.zip` as instructed by
   `MAIN_PROMPT.md`.
4. Back in the waiting command, enter Main's total time for the single inference as `Xm Ys`
   (for example, `12m 34s`).
   Invalid time or effort entries are requested again. For OpenAI effort, press Enter for `high`,
   enter `xh` or `xhigh` for `xhigh`, or enter `pro` for `pro`.
5. Paste the Main-chat link. A normal or shared Claude link is accepted by default; use
   `--reject-shared-chat-link` only when the run requires a private URL.
6. Save Main's downloaded complete Phase ZIP directly in that run folder and press Enter.
   `MAIN_HANDOFF.zip` is preferred, but a unique alternate `.zip` download name is accepted.
7. The starter validates the package before import. If rejected, overwrite it or save the corrected
   ZIP there under a new name, then press Enter; the workspace has not been changed.
8. Claude Code opens interactively, already rooted at the run's `workspace/` and pointed at the Phase
   `ORCHESTRATOR_START.md`. The package must include the full Phase manifest, all DIC views, the
   complete initial EPS graph, and one substantive prompt file per EPS node.
   The progressive coding workspace includes `.evaluation/run_in_env.py`; the launcher starts the
   frozen Linux sidecar and Claude Code routes task build/test/runtime commands through that helper, where
   the same host workspace is mounted at `/app`. Do not copy or archive a host `.venv` as setup.
9. When the CLI exits, the starter automatically runs the frozen private grader outside the
   workspace and stores its raw output under the run's `evidence/grader/` directory. For a
   progressive Direct run, an accepted incomplete grade automatically resumes Codex at the next
   authorized checkpoint; the recorder opens only after the final checkpoint. AI-Native returns to
   the operator for the next Main inference. AI-Native reuses the already recorded Main time;
   Direct does not request Main metrics. Enter any reported Main tokens when applicable and missing executor usage. Usage accepts
   either JSON or the complete product-visible `Token usage: total=...` line. When pricing is
   available, the pipeline records and prints a standard API-equivalent estimate; this is not a
   claim about the incremental charge for a ChatGPT, Codex, or Claude subscription.

Direct never creates or receives the runtime archive. AI-Native keeps `.ai-workflow/` in the scored
workspace and supplies the generated repository-root archive to Main. Main is never told to create
local paths. If the ignored archive or expanded runtimes are missing after checkout, the starter
reconstructs them from the tracked configured source package automatically;
`python -X utf8 scripts/update_ai_workflow.py` deliberately rebuilds and validates every copy.

For AI-Native, `MAIN_INPUT.zip` preserves the complete agent-visible repository tree, including ordinary
subfolders, but excludes `.ai-workflow/` in both conditions. It has no special internal JSON
schema. By contrast, Main's returned handoff ZIP is validated against the exact file and manifest
contract embedded in `MAIN_PROMPT.md`. Its package may be at ZIP root or below exactly one wrapper
folder; manifest paths remain relative to the package contents below that wrapper.

Every generated `MAIN_PROMPT.md` supplies an exact `task_id`, timestamped `run_id`, and
`task_lock_sha256`. Main must echo all three into each `HANDOFF_MANIFEST.json`; the importer rejects
missing or stale values before changing the workspace.

## Run folder

Every invocation gets a name such as
`run_20260901T153000Z_T04_ANTHROPIC_DIRECT_NORMAL`, so reruns never overwrite one another.
The Direct run root contains `RUN.json` and `DIRECT_GOAL.md`. The AI-Native run root additionally
contains `MAIN_INPUT.zip`, `MAIN_PROMPT.md`, and the downloaded whole-Phase handoff ZIP.
`RUN.json` records the hash and path of the shared workflow archive for AI-Native runs, so no
per-run runtime duplicate is created. It is the single evolving metadata record for the Main link,
model route, timestamps, executor sessions, wall time, usage, and hashes. The initial repository is
retained as a reproducible task-lock/tree-hash reference; the final repository remains a required
full directory.

This branch defaults to the frozen Anthropic route: Claude Opus 5 high as Main and Claude Code
Sonnet 5 high as executor. Add `--ecosystem OPENAI` only when deliberately materializing the frozen
OpenAI row.

## Checkpoints

This task has 8 cumulative checkpoints. Only checkpoint 1 is initially visible.
For Direct, the starter automatically grades each checkpoint, reveals exactly the next authorized
checkpoint, resumes the Codex session in the same run workspace, and repeats through checkpoint
8. No Main chat or repeated continuation command is required. If a Direct run is
interrupted after an accepted checkpoint, resume the entire remaining checkpoint loop with:

```shell
python -X utf8 scripts/continue_run.py "./tasks/T04_recli" --run-id <RUN_ID>
```

Direct captures checkpoint evidence from durable session/grader metadata and does not ask the
operator to paste the executor's final response. The continuation command keeps advancing after
each accepted Direct checkpoint until completion or the frozen state-loss boundary.

For AI-Native, run the printed continuation command after each accepted checkpoint. It requests
exactly one Main inference for that newly revealed scope, imports the returned complete active-Phase
package, opens the orchestrator, and grades the new checkpoint. Never give Main the private grader
or a later checkpoint early. A checkpoint does not force a matching Phase number: Main preserves
the existing Plan and chooses the next justified Phase decomposition itself.

## State-loss variant

Create it as a separate timestamped run by adding `--state-mode STATE_LOSS` to the same start
command. Capture loss only after checkpoint 4/8 is accepted and
before the next checkpoint is revealed. Follow `READY_FOR_SCORED_RUNS.md` for the frozen fresh-Main
recovery message; never transfer the old Main transcript.

## Finish

The starter runs the private grader automatically after the CLI exits. To grade again manually,
run:

```shell
python -X utf8 scripts/grade_run.py "./tasks/T04_recli" --run-id <RUN_ID>
```

Then use the interactive recorder when needed:

```shell
python -X utf8 scripts/record_run.py "./tasks/T04_recli"
```

It selects the latest unfinished run by default, records reported resource usage, automatically
reuses the latest grader output and score, and can finalize. Finalization retains the full
repository in `repo_final/` and writes native scoring results separately under `run_results/`.

This file is generated by `scripts/generate_chat_main_runbooks.py`. The frozen task prompt itself is
read from this task root at run creation and written verbatim into that run's `MAIN_PROMPT.md`.
