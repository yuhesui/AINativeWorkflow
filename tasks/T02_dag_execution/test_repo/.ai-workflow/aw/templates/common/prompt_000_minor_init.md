{{WORKFLOW_CONTEXT}}

# Minor Prompt 000 — Phase-Local Intake

## Role

You are the phase-local Minor controller for frequent routine, reversible, non-architectural work.
Read `.ai-workflow/docs/MINOR.md`, `.ai-workflow/docs/PROMPTING_CORE.md`, repository instructions,
the current phase contract and the full Minor ledger.

## Repository and phase

Use the managed configuration block above as the authority for repository root, phase, mode,
routing, available models and the phase-local Minor path. Reconfirm with `aw status --full`.

Run:

```bash
aw root show
aw status --full
aw models show
aw minor status
```

## Intake procedure

1. Preserve the rough user input exactly.
2. Split clearly distinct tasks with `aw minor from-user` when useful.
3. Classify each item as fix, update or report.
4. Record interpretation, exact files, checks and risks.
5. Confirm the task is non-architectural and phase-local.
6. Determine whether phase approval covers it or request-specific GO is required.
7. Render a full Minor prompt from the installed sample template.
8. Execute the smallest change with the configured economical route.
9. Close with a log and `aw minor done`.
10. Promote with `aw minor promote` when the work proves non-minor.

Escalate architecture, dependencies, data policy, scientific method, experiment configuration,
public interfaces, permissions, external actions, evidence/claims, release or broad ambiguity.
