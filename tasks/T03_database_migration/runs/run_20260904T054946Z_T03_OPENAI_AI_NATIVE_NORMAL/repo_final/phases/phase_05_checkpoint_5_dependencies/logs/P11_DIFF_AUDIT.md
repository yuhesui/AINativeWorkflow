# P11 diff audit

Inspected command:

```text
rtk proxy git diff --no-index --stat --no-ext-diff -- /dev/null migration_tool.py
```

It reported the task-local `migration_tool.py` as 1670 inserted lines at audit time. Static review covered dependency field validation, JSON-directory discovery, duplicate/missing/future/cycle failures, stable topological order, non-mutating validation events, single-migration prerequisite checks, batch skip/application accounting, and visible cumulative dependency test cases. Runtime evidence remains unavailable only because the wrapper did not start the task command.
