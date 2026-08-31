# Full Next-Phase Generation Template

{{WORKFLOW_CONTEXT}}

## Role

Act as Main for the new phase. Use the prior independently verified handoff and fresh repository
state. Do not copy unresolved assumptions forward merely because they existed previously.

## Inputs

Use the managed block as the current repository/configuration authority.

```yaml
previous_handoff: "{{HANDOFF_PATH}}"
rough_new_input: |
  {{ROUGH_INPUT}}
```

## Required procedure

1. Verify the handoff, run/config/package identities and open limitations.
2. Reinspect current branch, working tree, root, config and model availability.
3. Separate continuation, deferred work and genuinely new scope.
4. Select Goal or Structured Mode by coupling and authority needs.
5. Select execution, research and test levels.
6. Choose routing profile and record actual surfaces.
7. Define new acceptance, non-goals, approval and critical stops.
8. Create the phase with `aw phase init` or `aw phase plan-next --create`.
9. Run `aw update` so all safe prompts contain current config context.
10. Validate before requesting GO.

## Goal Mode output

Main writes one complete `GOAL.md`; Orchestrator creates the execution plan and prompts as an EPS after GO.

## Structured Mode output

Main writes `REQUESTS.md`, `PLAN.md`, `README.md`, `USER_APPROVAL.md`, architecture/execution
contract, complete prompt pack, verification prompts and handoff prompt.

## Stop conditions

Stop if prior evidence is not independently trustworthy, the new scope requires unavailable authority,
or the selected mode cannot express the necessary contract safely.
