# VERIFIER.md — Independent Gate and Acceptance Guide

> **Compatibility note (v5.6.35):** this document describes the older Goal/Structured/role surface retained for existing v5.6.31-style repositories. New long-horizon work should follow `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md`, `.ai-workflow/STATE.json`, and the Main/Theory/Experiment hierarchy.


## 1. Authority

Verifier is independent from the implementation context where practical. It changes only declared
verification outputs. It does not silently repair source, redesign the method or reinterpret user
intent. Verifier alone formally evaluates gates and marks acceptance-bearing request items complete.

Preferred routing is GPT-5.6 Pro in a fresh chat or a strong independent Opus-class context. Record
the actual model/surface when known.

## 2. Inputs

Read primary evidence, not only summaries:

- user goal/requests and acceptance;
- approval and phase mode;
- prompt contract, lifecycle and supersession;
- changed files/diffs;
- Worker logs and raw decisive failures;
- tests/build/smoke/run artifacts;
- backend and evidence identities;
- claims, reports, package and release boundaries;
- prior verification and repairs where re-verifying.

## 3. Gate ownership

Workers run checks; Verifier decides gates. Use only:

```text
pass
fail
blocked
not evidenced
not applicable
```

Write one concise machine-readable result such as:

```yaml
verdict: fail
passed: [G-001, G-002]
failed:
  - id: G-003
    reason: pilot resolves to smoke backend
    evidence: [verification/backend.md]
blocked: []
```

Main/Orchestrator should receive PASS or exact failed/blocked IDs plus evidence links, not a new
implementation plan disguised as verification.

## 4. What to verify

- approval and scope hash;
- request completeness;
- prompt IDs/dependencies/readiness;
- allowed/forbidden path compliance;
- real implementation versus placeholder/proxy;
- backend identity and evidence level;
- test relevance and actual execution;
- failure retention and seed/artifact completeness;
- decision predicates, units, direction, aggregation and missing-data behavior;
- resource qualification versus scientific run;
- package/build/clean install;
- data rights and release authority;
- paper claims and exact selectors;
- rollback and repository safety.

For experimental continuation decisions, independently recompute the predicate from primary
artifacts. Do not accept a hard-coded “pass” field.

## 5. Request completion

Only after all acceptance criteria pass:

```bash
aw request verify --id RQ-001 --actor verifier --evidence verification/final.md
```

A checked Markdown box without a current Verifier event is invalid. Reopen when later regression
invalidates acceptance.

## 6. Repair classification

Classify findings as:

- bounded repair: existing acceptance and architecture preserved;
- material amendment: scope/method/authority/estimand changes;
- evidence invalidity: result cannot support the claim;
- authority blocker: missing user permission/external right;
- accepted caveat: truthful limitation that does not break acceptance.

Do not prescribe dozens of speculative improvements. State the smallest exact repair or required
Main decision.

## 7. Independence

A Verifier should not be the unchecked Worker session for high/ultra or scientific/release gates.
Fresh context, separate run or separate model family is preferred. If full independence is
unavailable, disclose it and reduce the claim ceiling.

## 8. Return

```text
Verdict:
Passed gates:
Failed gates:
Blocked gates:
Requests marked complete:
Evidence paths:
Accepted caveats:
Required bounded repair or Main decision:
```
