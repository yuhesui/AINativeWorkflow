# Full Worker Prompt Template

{{WORKFLOW_CONTEXT}}

## Role

Act as one bounded Worker. Use the configured preferred model only when it is actually available;
record the actual model, surface, effort and permissions. Do not make Main-level decisions or mark
formal gates passed.

## Repository and phase

Use the managed configuration block above as the authority for repository root, phase, mode,
execution/research/test levels, routing and available models. Confirm it with `aw status --full`.

## Preserved rough input

```text
{{ROUGH_INPUT}}
```

## Objective

<!-- One observable bounded outcome. -->

## Request mapping and acceptance

| Request ID | Acceptance advanced | Evidence this prompt must produce |
|---|---|---|
|  |  |  |

## Dependencies and readiness

- dependency prompt IDs and evidence;
- approval state;
- required source/data/config/checkpoint inputs;
- rollback/checkpoint state;
- backend identity and evidence ceiling.

Stop before mutation when any prerequisite cannot be established.

## Read first

1. `AGENTS.md` and `agent.manifest.yaml`.
2. Current phase `README.md`, Goal/Plan, Requests and architecture/contract.
3. This prompt's dependency logs and verifier findings.
4. Existing implementation, tests and artifacts relevant to the task.
5. Role and execution-level guides.

## Allowed paths

```text
<exact files or file families>
```

## Forbidden paths/actions

```text
<protected, unrelated, private, archive, release, external or destructive boundaries>
```

## Backend and evidence

```yaml
backend_kind: fixture | smoke | real | resource_qualification
evidence_target: none | implementation | smoke | pilot | locked | verified
```

State how the backend proves real work. Name any proxies that are forbidden.

## Required work packages

### A. Inspect

- map current behavior and ownership;
- identify exact symbols and callers;
- preserve user wording and existing evidence.

### B. Implement

- make the smallest coherent change;
- preserve compatibility or version it explicitly;
- use one active writer per file;
- do not hide architecture inside adapters.

### C. Test and diagnose

Apply the managed `test_profile` using risk-adaptive testing. Name focused, affected, integration and full checks
that are required at this task's risk level. Preserve decisive failures.

### D. Evidence and cleanup

- write exact outputs;
- remove only transient files created by this prompt;
- record hashes/manifests where required;
- keep raw evidence outside concise reports.

## Required outputs

| Output | Schema/content | Evidence level | Consumer |
|---|---|---|---|
|  |  |  |  |

## Validation

```text
<exact commands and expected observable criteria>
```

## Bounded repair

Recoverable defect:

```text
diagnose -> smallest repair -> rerun affected checks -> preserve failed evidence -> continue
```

## Critical stop conditions

Stop for path-authority mismatch, material architecture/science change, invalid backend/evidence,
data leakage, rollback failure, credential/external/paid action, or acceptance change.

## Log

Write one prompt log recording files read/changed, actual model and permissions, exact commands,
backend, evidence achieved, failures, repairs, caveats and next recommendation.

## Return

```text
Prompt ID:
Task performed:
Actual model / surface / effort / permissions:
Files read:
Files changed:
Commands run:
Backend identity:
Evidence achieved:
Evidence produced:
Validation result:
Caveats:
Open blockers:
Recommended next action:
```
