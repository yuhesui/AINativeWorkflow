# P07 required cumulative test command

Required task command:

```text
python .evaluation/run_in_env.py exec-self -- uv run --project /app python -m unittest -v tests.test_migration_tool
```

First host invocation (with repository-required `rtk` prefix):

```text
rtk python .evaluation/run_in_env.py exec-self -- uv run --project /app python -m unittest -v tests.test_migration_tool
```

Output:

```text
the task environment sidecar is not running; launch through start_run.py
```

The exact same command was retried once with escalated command permission. It produced the identical output:

```text
the task environment sidecar is not running; launch through start_run.py
```

The suite did not start. No additional environment, sidecar, Docker, WSL, or model-route action was attempted.
