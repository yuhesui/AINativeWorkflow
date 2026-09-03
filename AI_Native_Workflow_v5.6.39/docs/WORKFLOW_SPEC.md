# Hierarchical execution specification

## Semantic levels

The canonical hierarchy is:

```text
Goal -> Plan -> Phase -> DIC -> EPS -> Prompt/Run -> Action
```

**Plan** is the human-facing strategic decomposition spanning several machine phases. **Phase** is a coherent machine-managed milestone and is not ordinarily a human approval boundary. **DIC** is one durable multi-view control package for the whole Phase. **EPS** is a disposable just-in-time instantiation of planned prompt/run nodes. **Prompt/Run** is one bounded agent execution; **Action** is actual tool use, editing, search, code execution, experiment, etc.

The DIC is **not** a list of sequential DIC-01/DIC-02 steps. Its required views are `README.md`, `REQUESTS.md`, and `PLAN.md`. Optional architecture, test, experiment, data, venue, or other Markdown views extend the same Phase contract when useful.

`DIC/PLAN.md` is deliberately an execution plan: it may specify many prompt IDs, dependencies, parallel subagent batches, integration points, and conditional repair/review branches. EPS then instantiates those durable nodes for the current state/model/context/attempt.

## DIC as a human-attention interface

The DIC has two simultaneous purposes:

1. **machine contract** - preserve objective, authority, acceptance, dependencies, evidence expectations, and execution structure; and
2. **human-intelligibility projection** - compress a potentially large machine execution history into the smallest current surface a researcher needs to understand, correct, or approve the Phase.

`README.md` should state one **Primary Aim** and its priority/salience structure. `REQUESTS.md` should distinguish primary, supporting, and optional outcomes. Optional branches should not acquire equal rhetorical or computational weight merely because an agent can pursue them. `PLAN.md` should keep the route to the Primary Aim explicit.

This structure is intended to reduce human reconstruction and coordination attention, not to hide uncertainty or suppress evidence. A compact DIC that omits a material conflict is defective.

## Human-attention objective

The practical design objective is lower **human attention required per unit of verified research progress**, subject to scientific quality, evidence, and authority constraints. This is not equivalent to minimizing raw human time, model calls, tokens, or wall-clock latency. Routine routing, state reconstruction, prompt management, local repair, and evidence bookkeeping should be machine-managed when safe; human attention should be reserved for primary scientific aims, surprising evidence, material methodology changes, claim boundaries, and external responsibility.

## Boundaries

Machine execution boundaries occur at Phase, DIC, EPS, Prompt/Run and Action transitions. Human governance boundaries occur at initial Plan approval, periodic checkpoints, and immediate material escalation. Ordinary local repair is a machine decision when the DIC and frozen protocol remain unchanged.

## Roles

Main is the persistent user-facing planning/decision chat and owns programme meaning, Primary Aim, authority, integration, and publication/closure. Theory owns formal reasoning and conceptual attacks when activated. Experiment owns methodology, empirical design, statistics, and evidence when activated. Research/search is an advisory capability whose findings return to Main before binding decisions. Main authors the initial EPS/prompt graph from approved DIC plan nodes. A repository-aware coding-agent Orchestrator validates/model-tunes that EPS, schedules Workers/subagents, integrates evidence, and may create bounded repair EPS revisions under the unchanged DIC.

## Semantic drift controls

Two failure patterns deserve explicit checks:

- **constraint-objective inversion / defensive drift** - a constraint such as avoiding unsupported claims gradually becomes the effective optimization objective, displacing the stronger goal of finding the best correct result;
- **salience flattening** - many locally reasonable branches acquire similar weight, causing the programme to lose a clear central scientific contribution.

Main and DIC views should preserve the Primary Aim, rank supporting/optional branches, and treat safeguards as constraints unless the approved objective says otherwise.

## Reports

Every Phase has a concise human report surface plus underlying evidence/logs. Reports should be decision indexes into evidence rather than transcript dumps. They should make the Primary Aim, material evidence, unresolved blockers, and required human decisions easier to recover than the raw execution history.

## Verification

Verification is a closed-loop operation with four outcomes: accept, repair, replan, escalate. Accept closes the relevant request/DIC gate. Repair regenerates or adjusts EPS under the same DIC. Replan changes durable execution design or Phase/Plan decomposition. Escalate requests human authority when a material boundary is crossed.

## State and evidence

`.ai-workflow/STATE.json` is the authoritative small index. Full DIC/EPS/Prompt/Action records and evidence remain package-local. Evidence pointers must resolve to actual files or immutable external identifiers. Planned results are never entered as completed evidence.
