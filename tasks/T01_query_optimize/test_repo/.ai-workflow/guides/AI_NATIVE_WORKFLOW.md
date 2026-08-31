# AI-Native Workflow v5.6.35 — Normative Human Specification

## 1. Purpose

AI-Native Workflow is a repository-centred control system for long-horizon agentic research, software and publication work. It keeps rich machine execution structure while reducing human approval ceremony.

Canonical hierarchy:

```text
Goal -> Plan -> Phase -> DIC -> EPS -> Prompt/Run -> Action
```

A human normally approves the Plan and reviews periodically after roughly 5–10 ordinary Phases. A single Phase may contain 10–100+ prompt/runs.

## 2. Persistent workstreams

- **Main** — overall authority, architecture, Plan ownership, integration, state and publication.
- **Theory** — formal reasoning, literature/novelty, propositions/counterexamples and conceptual interpretation.
- **Experiment** — empirical methodology, benchmark design, implementation delegation, statistics and evidence.

Research/search and orchestration are capabilities of the active workstream. `Orchestrator` and `Researcher` remain inexpensive compatibility aliases, not required persistent sessions.

## 3. One multi-view DIC per Phase

The Phase DIC is a directory, not one tiny JSON object and not a sequence of sub-DICs:

```text
DIC/
├── README.md
├── REQUESTS.md
├── PLAN.md
├── ARCHITECTURE.md?
├── TEST_MATRIX.md?
├── <CUSTOM>.md?
└── MANIFEST.json
```

`README.md` summarizes the Phase. `REQUESTS.md` records the specific goals to satisfy. `PLAN.md` is the durable execution plan and may enumerate tens or hundreds of prompt nodes, dependencies, parallel subagent groups, merges and conditional repair/review paths. `ARCHITECTURE.md` describes the target repository/system architecture when the Phase changes it. `TEST_MATRIX.md` records concrete test/experiment/theory-audit combinations.

Users may add arbitrary flat Markdown DIC views such as `THEOREM_MAP.md`, `EXPERIMENT_PROTOCOL.md`, `DATA_CONTRACT.md`, `VENUE_REQUIREMENTS.md`, `GRADER_SPEC.md`, or `RELEASE_CONTRACT.md`.

## 4. EPS

EPS is the disposable just-in-time instantiation of `DIC/PLAN.md` nodes against current repository state, model/context, attempt and repair history. If a prompt fails but the durable Phase objective has not changed, regenerate/repair EPS rather than rewriting the DIC.

## 5. Optional lanes

`minor/`, `research/`, `verification/`, and `checkpoints/` support `off | auto | on`. `auto` is the normal lazy default. `reports/` is always present.

## 6. Reports

Every Phase has a **flat** `reports/` directory with a default maximum of **10 files**. It contains a concise human report plus key merged raw result surfaces. Merged raw means lossless collation plus provenance, not averaging, paraphrasing, rounding or filtering failures. Full forensic evidence can remain in `logs/` and `evidence/`.

## 7. Governance

Human governance boundaries:

```text
Plan approval
-> periodic checkpoint
-> immediate material escalation when needed
```

Immediate escalation is reserved for material objective, authority, scientific-claim, frozen-protocol, destructive/external, paid-compute, credential/private-system, release or submission changes.

Local checking is automatic. Lightweight milestone rechecks may occur after prompt clusters or at DIC closure. Fresh independent review is reserved for material evidence/release boundaries.

## 8. Canonical state

`.ai-workflow/STATE.json` is the authoritative small index. Full control/evidence lineage lives under `.ai-workflow/runtime/plans/...`.

Read `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md` for exact file semantics and examples.

## 9. Compatibility

The older Goal/Structured `aw.py` CLI and legacy Orchestrator/Worker/Verifier documents remain for compatibility with v5.6.31-style repositories. They must not override the canonical hierarchical state for new work.
