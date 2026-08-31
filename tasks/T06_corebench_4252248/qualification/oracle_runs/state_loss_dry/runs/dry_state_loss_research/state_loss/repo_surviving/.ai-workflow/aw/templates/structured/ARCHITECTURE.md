# {{PHASE_TITLE}} — Architecture and Execution Contract

{{WORKFLOW_CONTEXT}}

## 1. Purpose

Freeze the component boundaries, shared contracts, ownership, artifact schemas, safety controls and
verification seams needed for this phase. This document must be specific enough that Workers do not
invent material architecture during execution.

## 2. Current system map

Describe the existing system before proposing changes:

```text
inputs -> preprocessing -> domain/core -> services -> adapters/CLI -> artifacts/reports
```

Identify:

- current source-of-truth modules;
- legacy or proxy paths;
- public versus private interfaces;
- active backends and fixtures;
- evidence already available;
- known dependency violations or technical debt.

## 3. Target architecture

Provide a dependency-ordered diagram and component table.

| Layer/component | Responsibility | Public inputs | Public outputs | Allowed dependencies | Forbidden dependencies | Owner |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

No domain layer imports CLI/adapters. Paper/report code consumes verified artifacts rather than
training internals. Fixtures are explicit and cannot substitute for real backends silently.

## 4. Shared contracts and schemas

For every cross-layer record define:

- namespaced schema version;
- required fields;
- shape/type/unit conventions;
- semantic hash basis;
- unknown-version behavior;
- serialization format;
- compatibility policy;
- validator and owner.

| Contract | Owner | Required fields | Invariants | Persistence | Failure behavior |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Avoid self-referential hashes. Marker-last completion must separate candidate and effective evidence.

## 5. Backend and evidence architecture

List the actual execution backends:

| Backend identity | Kind | Real work performed | Permitted evidence ceiling | Prohibited claims |
|---|---|---|---|---|
|  | fixture/smoke/real/resource qualification |  |  |  |

Every run records backend identity, code/config/input hashes, target evidence and achieved evidence.
A fixture or smoke backend may never satisfy a pilot/locked gate.

## 6. State and lifecycle

Define:

```text
planned -> reserved -> running -> interrupted/failed/completion_pending
        -> verified manifest -> marker-last COMPLETE -> effectively completed
```

Completed evidence is immutable. Resume preserves lineage. Duplicate/case-colliding IDs fail
atomically. Status text alone never proves completion.

## 7. Prompt ownership and write boundaries

| Prompt/work package | Depends on | Allowed paths | Forbidden paths | Shared interface | Owner/profile | Integration order |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Required outputs must be covered by allowed paths before execution. One file has one active writer.

## 8. Tools and permissions

For every operation classify:

```text
read-only
local mutation
external/network
credential-bearing
paid
irreversible/destructive
publication/release
```

For mutations define dry-run behavior, plan identity, containment, rollback, postconditions and
evidence.

## 9. Safety and rollback

Required topics:

- protected roots and immutable artifacts;
- Git and non-Git rollback;
- archive/snapshot manifests and restoration tests;
- secret/private-data quarantine;
- path traversal, symlink/junction/reparse and TOCTOU defenses;
- resource preflight;
- interruption recovery;
- failed evidence preservation;
- release authority separate from private-local completion.

## 10. Model and prompt architecture

The workflow configuration supplies preferred model candidates, actual availability declarations,
repository root, mode and test profile. `aw update` refreshes managed context in safe prompts.

Main owns material decisions. Orchestrator owns runtime decomposition and prompt generation. Workers
own bounded edits. Verifier owns formal gates and request completion.

## 11. Test architecture

Define test seams by risk:

| Seam | Controlled input | Observable output | Test profile | Earliest owner |
|---|---|---|---|---|
|  |  |  | focused/affected/integration/full |  |

Include failure-path and adversarial tests where a wrong pass would be more harmful than a wrong
fail. Do not make every prompt run every test.

## 12. Verification architecture

Verifier checks:

1. contract and authority;
2. implementation reality and backend identity;
3. execution evidence and failure retention;
4. artifact/claim/package integrity;
5. request acceptance.

Formal gate predicates live in the phase contract or verifier prompt, not hidden in Worker summaries.

## 13. Evidence and reporting layout

```text
logs/          raw command/execution evidence
artifacts/     machine-readable decisions and manifests
results/       runs, checkpoints, metrics and detailed tables
research/      sources and synthesis
verification/  independent checking
reports/       concise decisions only
paper/         manuscript, figures and packages
```

## 14. Change control

A material architecture change requires Main adjudication, append-only amendment, downstream impact
analysis, a new/superseding prompt ID, updated tests and independent review before execution.
Executed prompts are never silently rewritten.
