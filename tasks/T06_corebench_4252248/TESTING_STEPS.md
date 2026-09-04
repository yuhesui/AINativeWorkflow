# Testing steps — CORE-Bench capsule 4252248

Run from the evaluation repository root. T06 automatically selects its frozen `MIXED` matrix row and Sol control route; do not pass `--ecosystem`.

## Direct baseline

```shell
python -X utf8 scripts/start_run.py "./tasks/T06_corebench_4252248" --condition DIRECT
```

The command creates a timestamped run, excludes `.ai-workflow/`, and immediately opens Codex CLI GPT-5.6 Sol at medium reasoning in the run workspace. There is no Main chat. The single `DIRECT_GOAL.md` instructs Codex to reproduce the capsule, retain evidence, and produce `report.json` autonomously.

## AI-Native workflow

```shell
python -X utf8 scripts/start_run.py "./tasks/T06_corebench_4252248" --condition AI_NATIVE
```

Upload the printed `MAIN_INPUT.zip` and repository-root `AI_WORKFLOW_RUNTIME.zip` to a fresh ChatGPT GPT-5.6 Sol Main chat at xhigh, then paste the complete generated `MAIN_PROMPT.md`. Main returns one complete importable package for the current active Phase. The launcher validates and imports it, then opens Codex CLI GPT-5.6 Sol at medium to execute the whole Phase.

T06 has no benchmark checkpoint reveals. If a Phase returns without final `report.json`, the starter defers private grading and prints this continuation command:

```shell
python -X utf8 scripts/continue_t06_run.py "./tasks/T06_corebench_4252248" --run-id "<RUN_ID>"
```

It packages the surviving agent-visible workspace and evidence as `MAIN_CONTINUE_INPUT.zip`. Upload that archive to the same Main chat and paste the generated `MAIN_CONTINUE_PROMPT.md`. Main must accept, repair, replan, or materialize the next complete active Phase. Save the new handoff ZIP in the run folder; the command validates/imports it and opens the next Sol-medium Phase. Repeat until `report.json` and its audit evidence are complete, when the isolated native grader and recorder run normally.

Worker delegations are optional and bounded. Record every worker model, effort, wall time, and available usage separately; the Sol-medium Codex session remains the persistent orchestrator.

On macOS, use `python3` instead of `python` when that is the installed interpreter command.
