# {{PHASE_TITLE}} — Structured Plan

{{WORKFLOW_CONTEXT}}

## 1. Phase identity

The managed configuration block above is authoritative for phase ID, mode, repository root, levels,
routing and model availability. Refresh it with `aw update` after configuration changes.

```yaml
from_handoff: {{HANDOFF_PATH}}
```

Read the execution-level guide named by the managed `execution_level` and explicitly apply its
requirements. Do not merely label the phase High/XHigh/Ultra.

## 2. Preserved rough input and intent match

### Exact rough input

```text
{{ROUGH_INPUT}}
```

### Main interpretation

Separate:

- user-visible outcome;
- proposed implementation strategy;
- mandatory constraints;
- assumptions;
- evidence needed for completion;
- decisions requiring new user authority.

### Material assumptions

| ID | Assumption | Evidence/source | Confidence | Invalidation condition | Owner |
|---|---|---|---:|---|---|
| AS-01 |  |  |  |  | Main |

## 3. Request and acceptance map

Every workstream maps to `REQUESTS.md`. Workers report evidence; Verifier formally passes gates
and marks requests complete.

| Workstream | Request IDs | Deliverables | Worker checks | Verifier gate/evidence |
|---|---|---|---|---|
|  |  |  |  |  |

## 4. Current-state assessment

Record:

- branch, revision and working-tree state;
- prior handoff and exact identity;
- existing implementation and reusable artifacts;
- available tests, builds, runs and evidence levels;
- failed attempts and superseded prompts;
- protected/immutable material;
- data provenance and rights;
- available CPU/GPU/storage/network/tool surfaces;
- declared and actually available models;
- rollback/checkpoint status.

Use source, logs and artifacts over summaries when available.

## 5. Scope

### In scope

- <!-- Named work and visible outputs. -->

### Out of scope

- <!-- Explicit exclusions. -->

### Deferred

| Item | Reason | Future gate/phase | Evidence to preserve |
|---|---|---|---|
|  |  |  |  |

## 6. Architecture and ownership

Link `ARCHITECTURE.md` or an equivalent execution contract. Identify frozen interfaces,
component owners and file families. One file has one active writer. Prompt output paths must fit
allowed paths before execution.

## 7. Prompt graph

Main creates the complete prompt pack in Structured Mode. Classify prompts as:

- frozen implementation;
- conditional repair;
- scientific/experimental;
- integration;
- independent verification;
- phase-local Minor.

| ID | Objective | Depends on | Owner/profile | Preferred options | Allowed paths | Outputs | Worker checks | Verifier milestone |
|---|---|---|---|---|---|---|---|---|
| 000 | Main initialization | — | Main | GPT-5.6 Pro chat preferred | phase control | approved contract | read-only validation | approval integrity |
| 001 | Orchestrator initialization | 000 | Orchestrator | configured route | phase runtime | ready plan/dispatch | status/registry | not normally formal |
|  |  |  |  |  |  |  |  |  |

Letter suffixes denote sibling/replacement work packages, never permanent workers.

## 8. Model and surface routing

Use `aw models show`. Record actual availability rather than assuming the preferred catalog.

| Role | Ambiguity/consequence | Preferred profile | Actual surface/model | Effort | Permissions |
|---|---|---|---|---|---|
| Main major decision | highest | main |  |  | chat/read |
| Orchestrator | high | orchestrator |  |  | repo control |
| Worker | bounded | worker/worker_complex |  |  | prompt-specific |
| Minor | low | minor |  |  | narrow files |
| Verifier | independent | verifier |  |  | read/check only |

Escalate models only after evidence that a cheaper route is insufficient.

## 9. Concurrency

Parallelize only when dependencies are satisfied, write paths are disjoint, failures are
independently recoverable and integration order is explicit.

| Concurrent set | Independence argument | Shared read-only inputs | Integration order | Conflict response |
|---|---|---|---|---|
|  |  |  |  |  |

## 10. Research plan

Research is justified only when it changes a later decision.

| Question | Source hierarchy | Synthesis output | Consuming prompt | Stop rule |
|---|---|---|---|---|
|  |  |  |  |  |

Research distinguishes external fact, source interpretation, model inference, implementation
recommendation and open uncertainty. It is not implementation evidence.

## 11. Data, permissions, safety and rollback

Document:

- protected paths and immutable evidence;
- private/restricted data and publication boundaries;
- credentials, external systems and paid services;
- destructive operations and dry-run/plan-hash requirements;
- Git and non-Git rollback;
- path containment, symlink/junction/reparse and TOCTOU controls;
- compute, time and storage ceilings;
- interruption recovery and failed-run retention.

## 12. Backend and evidence contract

Each material prompt declares:

```yaml
backend_kind: fixture | smoke | real | resource_qualification
evidence_target: none | implementation | smoke | pilot | locked | verified
```

A command name or filename cannot promote evidence. Verifier checks the actual backend and
achieved evidence.

## 13. Testing strategy

Configured default: use the managed `test_profile`.

Use risk-adaptive profiles:

```text
focused     changed function/file and one smoke
 affected    focused plus direct dependents
 integration affected plus named cross-component seams/build
 full        complete suite, clean install/package and independent checks when justified
```

Do not run the full suite after every trivial change. Expand tests when risk or Verifier findings
justify it.

## 14. Failure and repair

Recoverable:

```text
diagnose -> bounded repair prompt -> affected checks -> preserve failed evidence -> integrate -> continue
```

Critical: stop only the affected branch for data loss risk, invalid science, leakage, corrupted
evidence, missing authority, credential need, external/costly action or material acceptance change.

## 15. Verification

Workers run checks. Verifier owns formal gates at meaningful boundaries:

- destructive/rollback gate;
- scientific continuation decision;
- integration or package boundary;
- final acceptance.

Verifier returns PASS, failed gate IDs or blockers plus evidence links. Main decides continue,
bounded repair, material amendment or stop.

## 16. Reports and artifacts

Keep concise human decisions in `reports/`. Keep raw output and detailed evidence in `logs/`,
`artifacts/`, `results/`, `research/`, `verification/` and `paper/`.

## 17. Approval and continuation

Before exact `{{APPROVAL_PHRASE}}`, only read-only inspection and phase-local planning evidence are
allowed. After approval, Prompt 000 integrates and Prompt 001 becomes ready automatically unless
Main records a critical blocker.

## 18. Final handoff

Define the final handoff structure, exact identities, remaining limitations, release authority and
next phase. No new science or implementation belongs in Prompt 99.
