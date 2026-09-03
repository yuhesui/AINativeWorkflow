# Migration from v5.6.31

The redesign is additive and authority-preserving. Existing Goal/Structured modes, phase files, reports, and handoffs remain readable. `Orchestrator` maps to `Main`; `Researcher` maps to `Theory` by default and to `Experiment` when the bounded work is empirical. The legacy runtime is not deleted.

Run `python .ai-workflow/aw_hierarchy.py migrate`. The command indexes likely legacy authority/context files in `.ai-workflow/STATE.json` and marks them as migration sources. It does not rewrite or delete them. New work should use Plan→Phase→DIC→EPS→Action and should treat the canonical state as the conflict-resolution authority.

A legacy single-phase prompt can be represented as a one-Plan/one-Phase DIC. A legacy phase prompt can remain a prompt artifact but should be linked as EPS or evidence rather than treated as the durable contract.
