# Frozen-candidate empirical protocol

## Research question

At matched model, tool access, task information, and total inference budget, does the relative benefit of explicit hierarchy increase with **effective task horizon**, and does evidence-gated local repair reduce failure propagation beyond the benefit of extra verifier inference?

## Conditions

- **C0 Direct/reactive:** no explicit cross-step plan; the agent acts from the task and current observation.
- **C1 Flat plan-and-execute:** one global plan, then sequential execution; no durable subcontracts or dependency-local invalidation.
- **C2 Hierarchical execution:** Plan→Phase→DIC→EPS with persistent package state; local checks may report failure but do not trigger the C3 recovery policy.
- **C3 Hierarchical + verification-triggered repair/replanning:** C2 plus evidence gates returning accept/repair/replan/escalate and dependency-local invalidation.

For the main comparison, C0–C3 use the same base model and tool interfaces. Match either total model tokens/calls or report a Pareto frontier. Add a **C1+V budget control** that spends C3's verifier calls on generic critique without hierarchy-local repair, and a **C2-extra** control that spends the same budget on additional generation.

## Factorial task generator

Vary independently where feasible:

1. dependency depth `d∈{2,4,8,12}`;
2. branching `b∈{1,2,4}`;
3. delayed dependency distance `ℓ∈{0,2,6}`;
4. interacting constraints `k∈{1,3,6}`;
5. injected intermediate fault type and location.

Use package-reconstruction, code/data pipeline, and evidence-synthesis task families with objective executable graders. Generate instances before freezing prompts. Avoid using raw prompt length as the only horizon manipulation. Define effective horizon from the dependency graph and minimal required state transitions.

## Fault injection

Inject faults after an otherwise valid intermediate artifact: stale schema, omitted constraint, swapped dependency version, corrupted statistic, unsupported citation pointer, or failing code path. The injector and grader know the fault; the agent is not told whether or where a fault was injected. Balance locations across depth and branch position.

## Primary outcomes

1. end-to-end graded success;
2. hard-constraint satisfaction;
3. unsupported-completion rate;
4. downstream failure-propagation size;
5. recovery locality (re-executed nodes / true impact cone);
6. fault-detection latency in actions/phases;
7. rework and invalidated artifacts.

Secondary outcomes: model/tool calls, input/output tokens, wall time, verifier calls, human checkpoints, false-rejection repair, and evidence completeness.

## Statistical plan

Pre-register one primary mixed-effects logistic model for success with condition, standardized effective horizon, their interaction, and task-family random intercepts. The central parameter is the C2/C3 by horizon interaction relative to C1. For propagation and rework use count or robust regression appropriate to observed dispersion. Report per-instance paired contrasts when conditions share the same task seed. Use family-wise correction only for the small declared primary family; label all other analyses exploratory. Report confidence intervals and raw seed/instance outcomes.

## Gates

A submission-level positive claim requires: frozen prompts/protocol; no unresolved grader leakage; all primary conditions completed; matched-budget analysis; at least two task families; and a positive interaction or clearly bounded negative result. Runtime unit tests and deterministic fixtures are smoke evidence only.
