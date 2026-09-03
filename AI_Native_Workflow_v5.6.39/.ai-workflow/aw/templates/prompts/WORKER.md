# Bounded Worker / Subagent Prompt

## Identity

- Plan: `{{PLAN_ID}}`
- Phase: `{{PHASE_ID}}`
- DIC: `{{DIC_ID}}`
- EPS: `{{EPS_ID}}`
- Plan node: `{{PLAN_NODE_ID}}`
- Parent integration node: `{{MERGE_NODE}}`

## Primary outcome

{{PRIMARY_OUTCOME}}

## Current state and dependencies

{{CURRENT_STATE}}

## Read first

{{READ_FIRST}}

## Allowed writes

{{ALLOWED_WRITES}}

## Forbidden scope

{{FORBIDDEN_SCOPE}}

## Work packages

1. {{WORK_PACKAGE_1}}
2. {{WORK_PACKAGE_2}}
3. {{WORK_PACKAGE_3}}

Delete unused packages. A prompt should normally contain only one primary outcome and one to three tightly coupled packages.

## Outputs and evidence

{{OUTPUTS_AND_EVIDENCE}}

## Checks

{{CHECKS}}

## Stop / return upward

{{STOP_CONDITIONS}}

## Return

- files read;
- files changed;
- commands/checks and exact outcomes;
- artifacts/evidence paths;
- caveats/failures;
- terminal status;
- concise parent-integration note.
