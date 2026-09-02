1. Update All
python -X utf8 scripts/update_ai_workflow.py

2. Go to task testing steps

e.g. tasks/T02_dag_execution/TESTING_STEPS.md

3. Go to ChatGPT/ Claude (online)
Run the Main Prompt + upload required document after running the start run command

e.g.

## Direct baseline with Codex

## Direct baseline with Codex

```powershell
python -X utf8 scripts/start_run.py ".\tasks\T01_query_optimize" --condition DIRECT
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

