# {{PHASE_TITLE}} — Orchestration

{{WORKFLOW_CONTEXT}}

## Phase identity

The managed configuration block above is authoritative for phase ID, mode, levels, repository root,
routing, model availability and Minor location. Re-run `aw update` after config changes.

```yaml
from_handoff: {{HANDOFF_PATH}}
status: planned_pending_main_initialization
```

## Role split

### Main

- persistent chat-style owner of user intent and major decisions;
- writes one `GOAL.md` in Goal Mode;
- writes the full contract and prompt pack in Structured Mode;
- controls exact approval, material amendments and final closure.

### Orchestrator

- computes readiness;
- creates execution plans and execution prompts in Goal Mode;
- consumes Main's prompt graph in Structured Mode;
- selects economical execution models;
- inspects returns, integrates evidence, issues bounded repairs and invokes Verifier.

### Worker and Minor

- perform one bounded assignment;
- edit only declared paths;
- run risk-adaptive checks;
- report actual backend, model, permissions, evidence and caveats;
- never self-integrate or self-verify.

### Verifier

- independently evaluates formal gates at meaningful milestones;
- reports PASS, failed gate IDs, or blockers;
- marks acceptance-bearing requests complete;
- never silently fixes implementation files.

## Runtime commands

```bash
aw status --full
aw models show
aw next
aw next --print
aw update
aw validate
aw minor status
```

## Mode-specific behavior

### Goal Mode

Main finalizes `GOAL.md`. `aw go` materializes `REQUESTS.md` from the goal acceptance list, then
hands control to Prompt 001. Orchestrator may create a working plan and prompts dynamically.

### Structured Mode

Main finalizes `REQUESTS.md`, `PLAN.md`, `USER_APPROVAL.md`, architecture or execution contract,
and the complete prompt graph before GO. Orchestrator executes and integrates the graph.

## Testing

Use the managed `test_profile`. Testing is risk-adaptive: focused during local work,
affected or integration at milestones, and full/independent at the final boundary when justified.

## Reporting

Keep only concise decisions in `reports/`. Raw evidence belongs under `logs/`, `artifacts/`,
`results/`, `research/`, `verification/`, or `paper/`.
