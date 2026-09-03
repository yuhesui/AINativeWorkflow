# Experiment workstream handoff

## Authority

Read `.ai-workflow/STATE.json`, `research/CLAIM_LEDGER.json`, and `experiments/FROZEN_CANDIDATE_PROTOCOL.md`. Do not reinterpret planned hypotheses as current results. The dedicated Experiment workstream owns implementation, benchmark freeze, run logs, statistics, and evidence ingestion; Main owns claim integration.

## Immediate tasks

1. Build the task generator and objective graders independently of condition prompts.
2. Implement C0–C3 plus C1+V and C2-extra budget controls behind one runner.
3. Run contamination/leakage tests and a tiny engineering smoke set.
4. Freeze task seeds, prompts, budgets, model versions, stopping rules, and exclusions.
5. Run a pilot only to estimate variance and failure modes; do not tune on confirmatory instances.
6. Submit a protocol-freeze checkpoint to Main, then execute the confirmatory matrix.
7. Export instance-level JSONL, environment snapshots, grader outputs, token/call logs, and a generated statistical report.

## Evidence contract

Each run record must include package commit/hash, condition, model identifier, decoding parameters, tool versions, task seed, dependency graph, injected-fault metadata hidden from the agent, complete transcript pointer, artifact hashes, grader version, raw scores, cost measures, and termination reason. Never hand-copy aggregate numbers into a manuscript; generate tables from the evidence store.

## Stop/escalation conditions

Escalate protocol changes after freeze, grader defects affecting completed instances, model/API substitution, paid compute, inaccessible credentials, or evidence that the central task manipulation does not vary effective horizon. Ordinary implementation bugs before freeze are local repair.

## Current status

No large confirmatory study was run in the reconstruction session. The package includes runtime conformance tests and can include deterministic smoke fixtures; neither supports a comparative agent-performance claim.
