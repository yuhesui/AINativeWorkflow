# P01 wrapper command record

The checkpoint requires task build, test, and runtime commands to use the environment wrapper. The following required commands were attempted through that interface. Each was retried once exactly as required after the initial failure.

## Runtime lifecycle status

Host invocation (prefixed with `rtk` by repository instruction):

```text
rtk python .evaluation/run_in_env.py exec-self -- python .ai-workflow/aw.py status
```

Wrapper command:

```text
python .evaluation/run_in_env.py exec-self -- python .ai-workflow/aw.py status
```

Attempt 1 output:

```text
the task environment sidecar is not running; launch through start_run.py
```

Attempt 2 output:

```text
the task environment sidecar is not running; launch through start_run.py
```

## P01 CLI smoke entry point

Host invocation (prefixed with `rtk` by repository instruction):

```text
rtk python .evaluation/run_in_env.py exec-self -- uv run --project /app migration_tool.py --help
```

Wrapper command:

```text
python .evaluation/run_in_env.py exec-self -- uv run --project /app migration_tool.py --help
```

Attempt 1 output:

```text
the task environment sidecar is not running; launch through start_run.py
```

Attempt 2 output:

```text
the task environment sidecar is not running; launch through start_run.py
```

## Consequence

No task command ran inside the frozen Linux environment. The required wrapper is unavailable, so P01 cannot supply its required runtime create/add/skip/schema evidence. No prohibited environment-management action was attempted.
