# Checkpoint 2 Execution Graph

```text
P05 data-operation implementation and focused tests
  -> P06 independent cumulative verifier and phase closure
```

| Node | Outcome | Depends on | Writes | Evidence gate |
|---|---|---|---|---|
| P05 | Add validation/execution for the three revealed data operations and retain checkpoint-1 behavior. | accepted checkpoint 1 | `migration_tool.py`, visible tests, Phase evidence | transform/migrate/backfill success and rollback cases pass. |
| P06 | Independently rerun the visible cumulative suite, inspect scope, and issue `accept`, `repair`, `replan`, or `escalate`. | P05 | Phase reports/evidence; bounded repair only if required | wrapper-run suite and representative CLI behavior pass. |

The nodes are serial because they share the canonical implementation. A local code defect receives a bounded repair record; changed acceptance or unrevealed scope requires replan/escalation.
