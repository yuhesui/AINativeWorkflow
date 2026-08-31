# <Phase title> — Execution Plan

This is the durable Phase execution design. It may contain 10–100+ prompt/run nodes.

| ID | Objective | Requests | Depends on | Parallel/subagent group | Owner/profile | Outputs | Merge/review |
|---|---|---|---|---|---|---|---|
| P01 | ... | R01 | — | — | Main/Theory/Experiment | ... | ... |
| P02A | ... | R02 | P01 | B1 / subagent | Theory | ... | P03 |
| P02B | ... | R02 | P01 | B1 / subagent | Theory | ... | P03 |
| P03 | reconcile | R02 | P02A,P02B | — | Theory | ... | milestone review |

Record conditional branches explicitly, e.g. theorem survives → independent audit; falsified → obstruction characterization.
