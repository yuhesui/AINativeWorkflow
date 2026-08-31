# Major Implementation Prompt Reference

{{WORKFLOW_CONTEXT}}

## Role and repository

Act as a bounded complex Worker under Orchestrator. Use the managed configuration block as the repository-root and routing authority.

## Objective and acceptance

<!-- State one coherent implementation outcome and map it to request IDs. -->

## Current state and dependencies

<!-- Exact prompt/run/config identities, known failures and reusable interfaces. -->

## Allowed/forbidden paths

<!-- Complete file-family contract. Required outputs must fit allowed paths. -->

## Implementation packages

A. inspect current ownership and behavior;
B. implement public contracts before adapters;
C. add failure-path and compatibility tests;
D. run risk-adaptive checks;
E. record evidence and cleanup.

## Backend/evidence

Declare real versus fixture backend and the maximum evidence this prompt can create.

## Repair and stop

Repair local implementation defects; stop for architecture/science/authority changes.

## Return

Use the full Worker return contract from `.ai-workflow/docs/WORKER.md`.
