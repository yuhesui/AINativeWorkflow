# {{PHASE_TITLE}} — Goal

{{WORKFLOW_CONTEXT}}

## Exact rough request

```text
{{ROUGH_INPUT}}
```

Preserve the user's wording. Do not silently replace it with implementation jargon.

## Main interpretation

<!-- State the user-visible outcome, material assumptions and what is only a proposed strategy. -->

## Required outcome

<!-- One concise statement of the finished result. -->

## Acceptance

Main must replace the commented example with at least one real item before GO.
`aw go` materializes these items into `REQUESTS.md`.

<!-- - [ ] G-001 — Produce the primary user-visible outcome -->
<!--   - Acceptance: The exact deliverable exists and is independently verified. -->

## Boundaries

### Allowed after GO

- private-local execution inside the declared repository and generated prompt authority;
- Orchestrator planning and execution prompt generation;
- bounded repair and risk-adaptive testing;
- formal verification at meaningful milestones.

### Not authorized without a new decision

- public release or external submission;
- paid services, credentials or external systems not named here;
- destructive work without rollback;
- material change to the objective or acceptance criteria.

## Critical stop conditions

Stop and return to Main only for a material scope change, missing authority, rollback failure,
invalid evidence, data/security issue, or formal Verifier failure requiring a new decision.

## Exact approval

```text
{{APPROVAL_PHRASE}}
```

When exact approval is supplied, Main records it immediately with `aw go`; do not ask again.
