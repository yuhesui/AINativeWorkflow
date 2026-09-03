# `.ai-workflow/` Runtime

This is the only operative part of the surrounding development package. It can be adopted wholesale or used to formalize an existing ChatGPT/Claude + research + coding-agent workflow.

- Main is a persistent planning/decision chat.
- Each Phase has exactly one multi-view DIC with `README.md`, `REQUESTS.md`, and `PLAN.md`.
- `DIC/PLAN.md` stores the durable sequence, dependencies, parallelism, subagent branches, merge nodes, and conditional repair/review graph.
- Main authors the initial EPS/prompt graph from the DIC. Orchestrator is a coding-agent session that validates/model-tunes that EPS for the actual surface, manages Workers/subagents, integrates evidence, and may issue bounded repair EPS revisions.
- Research is advisory: `Main → Research → Main reconciliation → DIC/execution`.

Phase material lives at repository root `phases/<phase_id>/`; `.ai-workflow/` remains reusable runtime code/guidance. A Main-authored Phase ZIP can be imported with `python .ai-workflow/aw.py --root . phase import <zip>`.

Start with `docs/CORE.md` and the relevant role guide.


## Practical objective

Reduce human attention spent on routine coordination, context reconstruction, and execution supervision per unit of verified progress. Preserve human attention for scientific objectives, surprising evidence, material method changes, claim boundaries, and external responsibility. This is a target for evaluation, not an already-proven performance gain.


## Detailed guides

Compact normative instructions live under `docs/`. Human/maintainer references live under `guides/`; ordinary Workers should not load the full detailed guide unless the task requires it.
