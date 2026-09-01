# `.ai-workflow/` Runtime

This is the only operative part of the surrounding development package.

- Main is a persistent planning/decision chat.
- Each Phase has exactly one multi-view DIC with `README.md`, `REQUESTS.md`, and `PLAN.md`.
- `DIC/PLAN.md` stores the durable sequence, dependencies, parallelism, subagent branches, merge nodes, and conditional repair/review graph.
- Orchestrator is a coding-agent session that realizes DIC nodes as JIT, model-tuned EPS prompts and manages Workers/subagents.
- Research is advisory: `Main → Research → Main reconciliation → DIC/execution`.

Start with `docs/CORE.md` and the relevant role guide.
