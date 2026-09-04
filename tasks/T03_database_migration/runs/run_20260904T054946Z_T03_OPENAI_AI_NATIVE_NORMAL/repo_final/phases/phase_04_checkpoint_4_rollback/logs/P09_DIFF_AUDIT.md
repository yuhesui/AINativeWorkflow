# P09 diff audit

Inspected command:

```text
rtk proxy git diff --no-index --stat --no-ext-diff -- /dev/null migration_tool.py
```

It reported the task-local `migration_tool.py` as 1405 inserted lines at audit time. Static review covered durable operation/explicit-rollback history, history schema upgrade, target/count selection, automatic reverse plans, foreign-key-aware rollback transaction handling, JSONL rollback events, and visible cumulative rollback test cases. Runtime evidence remains unavailable only because the wrapper did not start the task command.
