1. Prepare a fresh checkout (run in a system terminal from the repository root)

```shell
git lfs install
git lfs pull
python3 -X utf8 scripts/sync_ai_workflow.py --ensure
python3 -X utf8 scripts/validate_repo.py
python3 -X utf8 scripts/validate_repo.py
```

On Windows, use `python` instead of `python3` when that is the installed command.

`scripts/update_ai_workflow.py` is the maintainer operation for deliberately rebuilding the
canonical runtime and refreshing locks. It is not required before an ordinary run. When needed:

```shell
python3 -X utf8 scripts/update_ai_workflow.py
```

2. Go to task testing steps

e.g. tasks/T02_dag_execution/TESTING_STEPS.md

3. Go to ChatGPT/ Claude (online)
Run the Main Prompt + upload required document after running the start run command

e.g.

## Direct baseline with Codex

## Direct baseline with Codex

```powershell
python -X utf8 scripts/start_run.py ".\tasks\T01_query_optimize" --condition DIRECT
python -X utf8 scripts/start_run.py "./tasks/T01_query_optimize" --condition DIRECT
```

## AI-Native workflow with Codex

```powershell
python -X utf8 scripts/start_run.py ".\tasks\T01_query_optimize" --condition AI_NATIVE
```

```powershell
python -X utf8 scripts/start_run.py ".\tasks\T02_dag_execution" --condition DIRECT
```

## AI-Native workflow with Codex

```powershell
python -X utf8 scripts/start_run.py ".\tasks\T02_dag_execution" --condition AI_NATIVE
```

After the executor CLI exits, `start_run.py` automatically runs the current task's frozen private
grader outside the workspace, stores raw evidence in the timestamped run folder, and opens the
resource/finalization recorder. Use `--skip-auto-grade` only for grader-infrastructure diagnosis.

