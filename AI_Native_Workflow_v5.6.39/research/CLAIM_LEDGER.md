# Claim ledger

Every substantial statement is classified before manuscript use. Planned and smoke evidence are not confirmatory.

## ARCH-01 — invariant_by_construction
**Status:** implemented
The canonical execution lineage is Action ≼ EPS ≼ DIC ≼ Phase ≼ Plan ≼ Goal, with package-resident identifiers and hashes.
**Assumptions:** all canonical actions are recorded by the runtime
**Evidence:** .ai-workflow/aw/hierarchy.py, .ai-workflow/tests/test_hierarchical_runtime.py
**Novelty position:** engineering invariant; not claimed as a new theorem

## ARCH-02 — invariant_by_construction
**Status:** implemented
Ordinary phases may progress autonomously inside an approved Plan; periodic and material events are separate governance boundaries.
**Assumptions:** runtime state transitions are used
**Evidence:** .ai-workflow/aw/hierarchy.py, docs/WORKFLOW_SPEC.md
**Novelty position:** workflow design contribution

## DEF-REF-01 — definition
**Status:** retained
Semantic refinement X ≼ Y means every trace admitted by X, after the declared abstraction map, is admitted by Y.
**Assumptions:** none
**Evidence:** AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex
**Novelty position:** standard trace-refinement formulation adapted to the hierarchy

## THM-COMP-01 — theorem_under_explicit_assumptions
**Status:** proved
For an acyclic Plan, phase contract satisfaction composes to goal satisfaction when pre/post compatibility, declared-frame noninterference, and a terminal goal implication all hold.
**Assumptions:** DAG execution; sound phase contracts; edge compatibility; frame/noninterference; terminal implication
**Evidence:** AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex#compositional-satisfaction
**Novelty position:** known contract-composition principle; included for precision, not claimed as theorem novelty

## THM-LOCAL-01 — theorem_under_explicit_assumptions
**Status:** proved
Under declared read/write locality, versioned evidence, and deterministic-or-reverified phase semantics, repairing keys Δ requires invalidating only the dynamic impact cone Reach({v:R_v∩Δ≠∅}); outputs outside that cone remain contract-valid.
**Assumptions:** complete read sets; complete write sets; versioned evidence; deterministic or reverified semantics; no hidden shared state
**Evidence:** AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex#dependency-local-recovery
**Novelty position:** adaptation of incremental-computation/build-system locality to agent workflow recovery

## THM-LOCAL-02 — theorem_under_explicit_assumptions
**Status:** proved
Without additional semantic information, the direct-reader seed of the dynamic impact cone is worst-case necessary: every direct reader can be made contract-invalid by some admissible phase function after Δ changes.
**Assumptions:** phase functions may depend arbitrarily on every declared read key
**Evidence:** AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex#locality-minimality
**Novelty position:** tightness characterization for the declared-footprint model

## THM-VER-01 — theorem_under_explicit_assumptions
**Status:** proved
If the conditional probability of missing a persisting fault at each verification gate is at most α, then survival through k gates is at most α^k and the expected number of gate intervals to detection is at most 1/(1−α).
**Assumptions:** conditional miss bound α<1 at every gate; fault remains observable at subsequent gates
**Evidence:** AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex#imperfect-verification
**Novelty position:** elementary reliability bound applied to evidence-gated agent execution

## PROP-CHK-01 — proposition_under_explicit_assumptions
**Status:** proved
In the stated stationary cost model, checkpoint overhead U(h)=n(c_v+βc_f)/h+λnc_r h(1+α)/(2(1−α)) is minimized at h*=sqrt(2(c_v+βc_f)(1−α)/(λc_r(1+α))).
**Assumptions:** stationary independent fault arrivals; uniform fault position within interval; constant per-phase repair cost; conditional verifier rates; continuous relaxation of h
**Evidence:** AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex#checkpoint-cost
**Novelty position:** checkpoint/restart trade-off adapted to governance cadence; not a universal prescription

## PROP-CTX-01 — proposition_under_explicit_assumptions
**Status:** proved
A phase can omit global state outside its context projection without changing its action distribution only when the projection is conditionally sufficient for that phase and referenced evidence remains resolvable.
**Assumptions:** conditional sufficiency; stable artifact identifiers; no hidden side channel
**Evidence:** AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex#context-locality
**Novelty position:** formal condition clarifying when externalized state is safe

## IMP-OBS-01 — impossibility_proposition
**Status:** proved
If a verifier observes a non-injective evidence map on which the goal predicate is not constant, no decision rule using only that evidence can have both zero false acceptance and zero false rejection.
**Assumptions:** verifier decision depends only on observed evidence
**Evidence:** AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex#observability-limit
**Novelty position:** basic partial-observability impossibility; important limit, not claimed as novel in isolation

## HYP-HORIZON-01 — empirical_hypothesis
**Status:** planned_not_tested
The relative end-to-end benefit of hierarchical execution over a flat plan increases with effective task horizon after controlling model, token budget, and tool budget.
**Assumptions:** none
**Evidence:** experiments/FROZEN_CANDIDATE_PROTOCOL.md
**Novelty position:** central empirical claim requiring confirmatory evidence

## HYP-REPAIR-01 — empirical_hypothesis
**Status:** planned_not_tested
Verification-triggered local repair reduces downstream failure propagation and rework versus hierarchy without gated repair at matched inference budget.
**Assumptions:** none
**Evidence:** experiments/FROZEN_CANDIDATE_PROTOCOL.md
**Novelty position:** mechanism claim requiring controlled faults

## EMP-RUNTIME-01 — engineering_evidence
**Status:** verified_in_current_build
The reference runtime passes its hierarchy-specific conformance tests and package recovery validation.
**Assumptions:** recorded test log is current
**Evidence:** build/logs/hierarchical_tests.txt, build/logs/recovery.json
**Novelty position:** implementation validation, not agent-performance evidence

## NOV-01 — novelty_position
**Status:** provisional_pending_external_review
The defensible system contribution is the integrated object persistent intent + hierarchical refinement + bounded execution + evidence-gated verification + local repair/upward replanning, not hierarchy alone.
**Assumptions:** literature synthesis remains current
**Evidence:** research/LITERATURE_AND_NOVELTY.md
**Novelty position:** system-level combination and operationalization

## REMOVED-01 — unsupported_and_removed
**Status:** removed
Hierarchical decomposition by itself guarantees correctness or preserves user intent in open-world execution.
**Assumptions:** none
**Evidence:** research/CLAIM_LEDGER.md
**Novelty position:** contradicted by observability and verifier limits

## REMOVED-02 — unsupported_and_removed
**Status:** removed
The current package has confirmatory evidence that it outperforms flat agents on long-horizon tasks.
**Assumptions:** none
**Evidence:** experiments/EXPERIMENT_HANDOFF.md
**Novelty position:** awaits dedicated Experiment session

