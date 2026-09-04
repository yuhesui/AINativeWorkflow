# P05 required test command

Required frozen-environment test command:

```text
python .evaluation/run_in_env.py exec-self -- uv run --project /app python -m unittest -v tests.test_migration_tool
```

Host invocation (with the repository-required `rtk` prefix):

```text
rtk python .evaluation/run_in_env.py exec-self -- uv run --project /app python -m unittest -v tests.test_migration_tool
```

First attempt output:

```text
the task environment sidecar is not running; launch through start_run.py
```

The exact same command was retried once with escalated command permission as the continuation Goal directs. Its output was identical:

```text
the task environment sidecar is not running; launch through start_run.py
```

No additional wrapper, sidecar, Docker, WSL, or environment operation was attempted. The visible cumulative suite remains unverified in the required frozen environment.
