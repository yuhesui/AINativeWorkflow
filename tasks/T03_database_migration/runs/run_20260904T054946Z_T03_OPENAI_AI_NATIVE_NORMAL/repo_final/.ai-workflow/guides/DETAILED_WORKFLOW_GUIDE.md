# AI Native Workflow v5.6.39 — Detailed Workflow Guide

## Distribution note

This is the complete human and maintainer operating guide. It is intentionally detailed and is **not** loaded wholesale into ordinary Worker/subagent prompts.

The machine-installable runtime is only:

```text
.ai-workflow/
```

Ordinary model sessions should read the compact role-specific files under `.ai-workflow/docs/` plus the active project contract. This guide is an on-demand reference for:

- researchers adapting the workflow;
- maintainers changing the runtime;
- Main when a user asks for deeper explanation;
- complex planning where the compact docs are insufficient;
- training and Education-track material;
- migration or debugging of package semantics.

The long-form technical report explains the scientific rationale, literature, formal theory, evidence boundary, and evaluation programme. This guide explains **how to operate the workflow**.

---

# 1. Core Operating Principle

AI Native Workflow formalizes the multi-tool AI workflow many researchers already use informally.

A common informal pattern is:

```text
persistent ChatGPT / Claude chat
    -> planning / interpretation
research surface
    -> literature / novelty / external evidence
Codex / Claude Code
    -> repository implementation / experiments
persistent chat
    -> integration / paper / next decision
```

The framework does not claim that the user previously had “no workflow.” It externalizes the parts that otherwise live in the researcher's attention:

- current objective;
- priority / salience;
- authority;
- project state;
- dependencies;
- evidence;
- acceptance;
- routing;
- repair;
- handoff.

The practical design objective is:

> **reduce human attention required per unit of verified research progress, subject to scientific quality, evidence, and authority constraints.**

This is a design and evaluation objective, **not an established empirical performance claim**.

The researcher should spend attention on the science, not on reconstructing what the agents did.

---

# 2. Runtime Boundary

Only `.ai-workflow/` is copied from the AI Native Workflow distribution into a target repository.

```text
TARGET_REPOSITORY/
├── .ai-workflow/          # operative workflow runtime
├── AGENTS.md              # project-local if used
├── agent.manifest.yaml    # project-local if used
├── phases/                # project-local Plan/Phase/DIC/EPS state
├── src/
├── tests/
└── ... normal project files
```

The fuller development archive may contain:

```text
technical_report/
research/
experiments/
submissions/
slides/
history/
validation/
```

Those are development / research / publication materials about the workflow itself. They are not runtime instructions unless a Phase explicitly imports them.

## 2.1 Authority order inside a project

When sources conflict, use this order unless the project explicitly declares another:

1. exact current user correction / material human decision;
2. approved Goal / Plan / Phase / DIC state in the repository;
3. verified evidence and frozen protocols;
4. current project-local source files;
5. compact handoff / current state;
6. older reports and chat summaries;
7. remembered conversation context.

Chat memory is useful, but it is not the only source of truth.

---

# 3. Two Different Role Layers

Do not mix scientific workstreams with execution roles.

## 3.1 Core scientific workstreams

```text
Main | Theory | Experiment
```

### Main

Persistent user-facing planning and decision chat.

Owns:

- interpretation of user intent;
- programme architecture;
- Plan / Phase ownership;
- Primary Aim and salience;
- decision to request Research / Theory / Experiment;
- one whole-Phase DIC;
- integration of specialist evidence;
- material scientific / architectural decisions;
- publication / release framing;
- Phase closure and next Phase.

Main should **not** become a terminal-heavy coding session.

### Theory

Specialist reasoning workstream activated when useful.

Owns:

- formal definitions;
- mathematical derivation;
- theorem / proposition development;
- counterexamples;
- hostile mathematical audit;
- theory-relevant literature / novelty;
- conceptual interpretation.

Theory returns evidence and claim-status recommendations to Main.

### Experiment

Specialist methodological workstream activated when useful.

Owns:

- estimands;
- benchmark design;
- controls;
- frozen protocols;
- seed / data namespaces;
- statistical units;
- analysis plans;
- evidence ceilings;
- empirical interpretation.

Experiment may delegate implementation through the coding-agent Orchestrator.

## 3.2 Research capability

Research is a cross-cutting decision-support capability, not a mandatory permanent fourth session.

Typical route:

```text
Main question
  -> Research
  -> Main reconciliation
  -> binding Phase / DIC decision
  -> execution if needed
```

Research is used when external evidence can materially change:

- method;
- architecture;
- data choice;
- benchmark;
- implementation decision;
- scientific claim;
- venue;
- release / submission decision.

Research is advisory. It does not acquire mutation authority merely by finding a persuasive source.

## 3.3 Machine execution roles

```text
coding-agent Orchestrator
  -> bounded Workers / subagents
  -> tools / actions
```

### Coding-agent Orchestrator

A repository-aware coding surface such as Codex or Claude Code.

Owns:

- DIC readiness;
- EPS realization;
- model / surface routing;
- final execution-prompt compilation;
- bounded Worker/subagent decomposition;
- tool execution;
- file changes;
- tests / runs;
- integration;
- bounded repair;
- evidence registration;
- verification dispatch;
- durable execution handoff.

The Orchestrator must not silently redefine the Primary Aim, scientific method, acceptance criteria, public claim, or authority boundary.

### Worker / subagent

A bounded executor.

Owns one complete work package and returns evidence to the Orchestrator.

### Verifier

Checks acceptance-bearing requests against evidence.

Returns one control outcome:

```text
accept | repair | replan | escalate
```

Verifier does not silently repair the artifact it is judging.

---

# 4. Canonical Hierarchy

```text
Goal -> Plan -> Phase -> DIC -> EPS -> Prompt/Run -> Action
```

## 4.1 Goal

Programme-scale user outcome and authority.

Typical lifetime: entire programme.

## 4.2 Plan

Human-facing strategic decomposition spanning several Phases.

A Plan should contain:

- Primary programme objective;
- Phase DAG;
- dependencies;
- owners;
- checkpoint cadence;
- material escalation rules;
- completion criteria.

The human should normally approve a Plan, not every executor prompt.

## 4.3 Phase

One coherent machine-managed milestone.

A Phase should be large enough to establish a meaningful result but small enough to have one clear Primary Aim and one DIC.

A Phase is not normally a separate human approval ceremony unless it crosses a material boundary.

## 4.4 DIC — Durable Intent Contract

Exactly one DIC per Phase.

The DIC is repair-stable unless the scientific / semantic contract changes materially.

It has two purposes:

1. machine contract;
2. human-intelligibility projection.

## 4.5 EPS — Execution Prompt Stack

Disposable executable realization of DIC plan nodes for the current attempt. **Main authors the initial EPS/prompt graph before whole-Phase handoff.**

One DIC can produce multiple EPS attempts.

```text
same DIC
  -> EPS attempt 1 -> repair
  -> EPS attempt 2 -> accept
```

Orchestrator validates and model-tunes Main's initial EPS. Ordinary execution failure normally creates a bounded superseding repair EPS under the same DIC; material semantic change returns to Main.

## 4.6 Prompt / Run

One bounded model invocation / executor task.

## 4.7 Action

Primitive operation such as:

- file read;
- edit;
- shell command;
- tool call;
- search;
- experiment;
- test;
- artifact generation.

## 4.8 Default project-local Phase filesystem

Project-specific Phase state belongs at repository root, not inside the reusable runtime:

```text
phases/<phase_id>/
├── DIC/
│   ├── README.md
│   ├── REQUESTS.md
│   └── PLAN.md
├── EPS/
│   └── <eps_id>/
│       ├── manifest.json
│       └── prompts/
├── ORCHESTRATOR_START.md
├── reports/
│   ├── PHASE_SUMMARY.md
│   ├── VERIFICATION_001.md      # when verification occurs
│   └── FINAL_HANDOFF.md         # terminal handoff
├── results/
│   ├── KEY_RESULTS.json         # when key results are naturally structured
│   └── KEY_RESULTS.csv          # when tabular results are natural
├── evidence/
│   └── EVIDENCE_MANIFEST.json
├── artifacts/
└── logs/
```

The default scaffold exists so a human or fresh Main can inspect a Phase without reverse-engineering `STATE.json` or chat history.

### Reports contract

`reports/` is the **human-attention surface**. It is intentionally concise.

- `PHASE_SUMMARY.md` is created when the Phase is created and maintained at meaningful integration points. It records the Primary Aim, current status, key findings, decisive evidence, negative/failed results, unresolved issues, material decisions, and claim boundary.
- `VERIFICATION_<NNN>.md` is required when a formal verification pass occurs and records verdict, checked requests/evidence, findings, limitations, and required repair.
- `FINAL_HANDOFF.md` is required before terminal Phase handoff/closure and states what was established, not established, decisive evidence, failed/superseded branches, DIC/EPS identities, claim/release boundary, and recommended continuation.

Reports do **not** copy raw terminal output or large result tables merely to appear complete.

### Structured results contract

When key results are naturally machine-readable, preserve them in `results/` rather than only paraphrasing them in Markdown.

- `KEY_RESULTS.json` is required when the Phase has a compact structured result set (metrics, theorem/certificate statuses, run identities, seed-level outcomes, benchmark summaries, etc.).
- `KEY_RESULTS.csv` is used when rows/columns are the natural representation. It is not mandatory for a purely theoretical or non-tabular Phase.
- More detailed run files may live below `results/` or `artifacts/`; the key-results files index the material conclusion rather than duplicating every raw output.

### Evidence manifest

`evidence/EVIDENCE_MANIFEST.json` indexes decisive evidence with IDs, paths, producer/EPS lineage, evidence class, and verification status. Raw logs stay in `logs/`; generated products stay in `artifacts/`.

A full reference is in `.ai-workflow/guides/PHASE_FILESYSTEM.md`.

---

# 5. One DIC, Three Core Views

Every Phase DIC requires:

```text
DIC/
├── README.md
├── REQUESTS.md
└── PLAN.md
```

Optional views are added only when useful.

## 5.1 DIC/README.md

Human orientation and semantic center.

Recommended headings:

```markdown
# Phase README

## Primary Aim
## Why This Phase Exists
## Current Established Evidence
## Supporting Questions
## Constraints
## Optional Branches
## Non-Goals
## Authority / Human Gates
## Canonical Read Order
## Current DIC Status
```

### Primary Aim

Use one sentence.

Bad:

```text
Improve theory, improve experiments, improve paper, inspect novelty,
try new baselines, improve code, and prepare submission.
```

Better:

```text
Determine whether the proposed mechanism has stable benefit beyond
matched conventional capacity under a frozen evaluation protocol.
```

Everything else is supporting work, a constraint, or optional.

## 5.2 DIC/REQUESTS.md

Acceptance-bearing outcomes.

Use explicit salience:

```markdown
## P1 — PRIMARY
Outcome:
Acceptance:
Evidence class:

## S1 — SUPPORTING
Outcome:
Acceptance:

## O1 — OPTIONAL
Continue only if it materially strengthens or falsifies P1.
```

Avoid activity-only requests:

```text
write code
run tests
improve paper
```

Prefer observable outcomes:

```text
The locked comparison is complete for every frozen seed or visibly failed,
and paired statistics recompute from the exact manifest.
```

## 5.3 DIC/PLAN.md

The durable prompt / dependency / parallelism graph.

This is where Main explicitly plans:

- sequence;
- dependencies;
- safe parallel groups;
- specialist workstreams;
- subagent branches;
- merge nodes;
- integration barriers;
- evidence gates;
- verification points;
- conditional repair branches;
- replan / escalation triggers.

Example:

```text
A literature / novelty -----\
B theory / counterexample ---+--> D Main reconciliation --> E evidence gate
C matched experiment --------/
```

The graph is durable.

Actual EPS prompt text is not stored here.

---

# 6. DIC as a Human-Attention Interface

A long run may produce:

```text
20 prompts
8 subagents
4 research reports
3 failed experiments
2 repair attempts
hundreds of terminal lines
17 changed files
```

The researcher should not need to read all of that merely to answer:

- what is the Primary Aim?
- what is currently believed?
- what evidence is decisive?
- what remains unresolved?
- what requires my decision?

Therefore:

> **As machine execution becomes more complex, the human interface should become more compact, not less intelligible.**

The DIC and handoff are compression interfaces.

Raw evidence remains addressable by path.

## 6.1 Do not make the DIC a transcript

The DIC should not contain:

- every prompt body;
- every shell command;
- full terminal output;
- every research source excerpt;
- repeated warnings;
- old superseded execution details.

Those belong in EPS / logs / evidence / artifacts / history.

## 6.2 Human review test

A good DIC lets a human answer in a few minutes:

1. What result is this Phase trying to establish?
2. What evidence would close it?
3. What can run independently?
4. Where could a failure propagate?
5. What material decision might come back to me?

---

# 7. Protecting the Scientific Center of Gravity

## 7.1 Constraint–objective inversion / defensive drift

Failure pattern:

```text
Primary Aim:
find the strongest correct result

constraint:
do not overclaim

repeated audits
    -> more caveats
    -> more defensive edits
    -> constraint becomes effective objective

final programme:
minimize reviewer attack surface
```

Main must keep objective and constraints separate.

Use:

```text
Primary Aim:
  strongest correct and experimentally meaningful result

Hard constraints:
  no fabricated evidence
  no unsupported claim
  preserve negative results
```

Not:

```text
Primary Aim:
  make every claim impossible to criticize
```

## 7.2 Salience flattening

Failure pattern:

```text
idea A  =====
idea B  =====
idea C  =====
control ====
limitation ====
extension ====
```

Everything is reasonable; nothing is central.

Correct structure:

```text
PRIMARY RESULT  ===========
load-bearing support =====
control ================
limitation ===
optional extension =
```

Main, Theory, Experiment, Research, and writing prompts should preserve this hierarchy.

## 7.3 Optional branches are disposable

Do not keep an optional branch merely because work has already been invested in it.

Continue only if it:

- strengthens Primary Aim;
- falsifies Primary Aim;
- satisfies a required control;
- removes a real blocker;
- materially improves venue / release correctness.

Otherwise defer it.

---

# 8. Main Session Protocol

## 8.1 Read order

Main reads:

1. `.ai-workflow/docs/CORE.md`;
2. `.ai-workflow/docs/MAIN.md`;
3. project-local authority files;
4. runtime state;
5. active Plan / Phase;
6. DIC Core views;
7. prior verified handoff;
8. unresolved material decisions;
9. only evidence needed for the current decision.

Do not preload every historical report.

## 8.2 Preserve exact input

Always separate:

```text
Exact user input
Main interpretation
```

Classify statements as:

- mandatory outcome;
- acceptance criterion;
- authority boundary;
- constraint;
- preference;
- example;
- proposed strategy;
- hypothesis;
- optional enhancement;
- deferred work;
- superseding correction.

Do not convert “maybe use X” into mandatory architecture.

## 8.3 Research gate

Ask:

> Could external evidence materially change the next decision?

If no:

```text
Research: not needed
```

If yes:

```text
Main -> Research -> Main reconciliation
```

## 8.4 Core workstreams

Use:

```text
Core workstreams: M yes | T yes/no | E yes/no
```

Theory / Experiment are activated only when useful.

## 8.5 Whole-Phase planning

Main plans the entire next Phase.

Main does not need to predict:

- final repair-EPS count;
- actual retry count;
- every Worker identity after runtime adaptation;
- every shell command.

Main **does** choose durable topology in `DIC/PLAN.md` **and authors the initial EPS/prompt graph** that materializes those plan nodes into bounded prompts for handoff.

## 8.6 Main status table

At Phase proposal / material revision / reconciliation:

| Main check | Required content |
|---|---|
| Plan / Phase | current programme milestone |
| Primary Aim | one sentence |
| Core workstreams | M / T / E |
| Research | not needed / requested / returned / integrated |
| DIC | one active DIC, Core views complete? |
| DIC plan | concise sequence + parallelism summary |
| Evidence target | decisive closure evidence |
| Human gate | NONE or exact material decision |

Do not expose a second Main-level prompt graph.

---

# 9. Research Protocol

## 9.1 Research should inform a decision

Bad research request:

```text
Research attention fine-tuning.
```

Better:

```text
Determine whether existing literature contains a mechanism or benchmark
that would materially change the frozen experiment design for Phase 08.
```

## 9.2 Source hierarchy

Prefer:

1. primary peer-reviewed papers;
2. official documentation / standards;
3. original datasets / code;
4. authoritative institutional reports;
5. high-quality secondary synthesis;
6. community discussion as experience evidence only.

## 9.3 Research output

Return:

- decision to inform;
- executive conclusion;
- source matrix;
- competing options;
- contradictions;
- uncertainty;
- ranked recommendation;
- fallback;
- implementation / experiment implications;
- questions that require local project evidence.

## 9.4 Preserve salience

Do not make a 40-paper literature catalogue the main deliverable when 4 papers determine the decision.

Separate:

```text
load-bearing evidence
supporting context
adjacent work
```

---

# 10. Theory Protocol

Theory should strengthen or falsify the Primary Aim.

## 10.1 Suggested decomposition for material theory

```text
A positive derivation
B hostile correctness audit
C novelty / nearest-result comparison
D parent reconciliation
```

These may run in parallel if independent.

## 10.2 Claim classes

Every theoretical statement should be labeled:

- definition;
- invariant by construction;
- lemma;
- proposition;
- theorem;
- corollary;
- conjecture;
- empirical hypothesis;
- unsupported / removed.

## 10.3 Hostile review is not the objective

A hostile audit is a correctness control.

It should not turn the research programme into:

```text
remove everything reviewers could possibly dislike
```

Return:

- strongest correct central statement;
- actual assumptions;
- counterexamples;
- what survives;
- what is load-bearing;
- what should be dropped.

---

# 11. Experiment Protocol

## 11.1 Freeze before confirmatory evidence

Freeze:

- estimand;
- method variants;
- baseline / controls;
- dataset split;
- seed set;
- evaluation metric;
- stopping rules;
- analysis plan;
- evidence ceiling.

## 11.2 Evidence classes

Use clear labels:

```text
screening
exploration
development
smoke
pilot
locked
confirmatory
verified
```

Do not rename exploratory evidence as confirmatory after seeing it.

## 11.3 Failed runs remain evidence

Record:

- failure reason;
- partial outputs;
- whether retry is allowed;
- whether protocol changes;
- whether the failure changes the claim boundary.

## 11.4 Smallest decisive evidence

Avoid expanding the benchmark matrix merely to appear comprehensive.

Ask:

> What is the smallest evidence set that can materially update the Primary Aim?

---

# 12. Coding-Agent Orchestrator Protocol

## 12.1 Read first

The Orchestrator reads:

- `.ai-workflow/docs/CORE.md`;
- `.ai-workflow/docs/ORCHESTRATOR.md`;
- active DIC Core views;
- Main-authored initial EPS / current repair-EPS and evidence state;
- relevant project files;
- provider execution guide for the actual surface.

## 12.2 Readiness gate

Before mutation confirm:

- repository root;
- DIC identity;
- required dependencies;
- tool availability;
- file ownership;
- authority;
- external / destructive gates;
- model / surface availability;
- prompt-tuning profile.

## 12.3 Ready-node selection

Execute only DIC plan nodes whose declared dependencies are satisfied.

Do not use chat-memory assumptions to bypass missing edges.

## 12.4 Direct vs subagent

For every ready node choose:

```text
A direct Orchestrator execution
B one bounded Worker
C several independent subagents
D stronger / specialist model
```

Choose based on dependency structure and evidence, not the desire to maximize parallel activity.

## 12.5 Integration

Worker completion is not integration.

Parent checks:

- interface consistency;
- write ownership;
- tests;
- evidence paths;
- unexpected scope;
- stale dependencies;
- repository cleanliness.

## 12.6 Repair

Use `repair` when:

- DIC remains valid;
- defect is execution-local;
- repair stays within authority.

Create a fresh **repair EPS** under the same DIC; preserve the Main-authored initial EPS and lineage.

## 12.7 Replan

Use `replan` when:

- frozen method changes;
- acceptance changes;
- Primary Aim changes;
- evidence shows the current DIC cannot honestly deliver;
- dependency architecture changes materially.

Return to Main.

## 12.8 Escalate

Escalate for:

- human scientific judgement;
- destructive / external / paid actions;
- credentials / private systems;
- public release / submission;
- permission expansion;
- unresolved safety issue;
- material objective ambiguity.

---

# 13. Prompt Graph and Naming Standard

The **durable** graph lives in `DIC/PLAN.md`.

The **initial executable prompt graph** is Main-authored in EPS; the current execution realization may later move to an Orchestrator-authored repair EPS under the same DIC.

Do not confuse them.

## 13.1 Durable plan node IDs

Recommended semantic IDs:

```text
A
B
C
D
T1
T2
E1
R1
M1
```

or stable project-specific names.

The DIC graph should not depend on one model provider's prompt numbering.

## 13.2 EPS prompt/run IDs

Execution IDs may be sequential or namespaced, for example:

```text
EPS-03 / P01
EPS-03 / P02A
EPS-03 / P02B
EPS-03 / P03-MERGE
```

They are attempt-local.

## 13.3 Prompt metadata

Recommended:

```yaml
prompt_id: P02A
plan_node: TheoryAudit
primary_outcome: Attempt clean positive derivation
executor_profile: gpt56_sol_pro
surface: chat_or_subagent
prompt_guidance: GPT56_ROUTING
reads:
  - DIC/README.md
  - theory/current_claim.md
writes:
  - artifacts/theory/P02A.md
depends_on:
  - P01
parallel_group: theory_attack
validation:
  - parent semantic review
stop:
  - contradiction requiring DIC change
```

## 13.4 Prompt status

Use simple states:

```text
planned
ready
running
completed
failed
blocked
superseded
```

---

# 14. Prompt Compilation

Every model-executed EPS node must be adapted to the actual model / surface.

Conceptual compilation:

```text
DIC + current evidence
  -> PROMPTING_CORE
  -> provider / model overlay
  -> execution surface overlay
  -> task-specific bounded prompt
  -> prompt audit
  -> dispatch
```

## 14.1 Outcome first

State:

- one primary outcome;
- observable success;
- deliverable;
- evidence.

Do not lead with a large invented procedure unless the procedure is contractual.

## 14.2 Context

Include only context that can change the result.

## 14.3 Constraints once

Avoid repeated warnings and duplicated role prose.

## 14.4 Autonomy once

State safe local actions and separately gated actions.

## 14.5 Do not request visible chain-of-thought

Ask for:

- result;
- evidence;
- concise rationale where useful;
- uncertainties;
- changed files;
- checks.

## 14.6 Prompt decomposition smell test

Split when:

- parts can fail independently;
- parts can execute concurrently;
- expertise differs;
- tools differ;
- evidence classes differ;
- write owners differ;
- retries would otherwise rerun unrelated work.

Do **not** split merely because one prompt contains several shell commands.

---

# 15. Model / Surface Guidance

The runtime keeps provider-derived summaries, not full copied provider pages.

Use:

```text
PROMPTING_CORE.md
+ GPT56_ROUTING.md / CODEX_EXECUTION.md
or
+ CLAUDE_EXECUTION.md
```

## 15.1 OpenAI

The workflow's internal shorthand “GPT-5.6 Pro” means the strongest available GPT-5.6 Sol / Pro-style configuration on the active surface, not a claim that a literal model slug `gpt-5.6-pro` exists.

Record actual model / surface when observable.

## 15.2 Claude

Record actual Claude / Claude Code configuration where observable.

Use structured context, explicit outputs, and subagents where independent work benefits from isolated context.

## 15.3 Provider independence

The DIC is provider-independent.

If a model family changes, regenerate EPS prompts rather than editing the scientific contract merely to fit one interface.

---

# 16. Parallelism and Subagents

## 16.1 Good parallelism

Examples:

```text
literature audit
|| theory proof attack
|| frozen experiment implementation
-> parent reconciliation
```

## 16.2 Bad parallelism

```text
Agent A edits paper.tex
Agent B edits paper.tex
Agent C changes the experiment definition
```

unless the merge strategy is explicit.

## 16.3 Write ownership

Sibling subagents should normally have:

- read-only work; or
- disjoint write paths.

If they share canonical state, serialize or use a dedicated merge parent.

## 16.4 Subagent narrowing

Parent:

```text
audit candidate theorem
```

Children:

```text
A: positive derivation only
B: hostile counterexample only
C: novelty / nearest literature only
```

Parent merges A/B/C.

Do not ask three agents to “analyze the entire project independently” unless independent replication itself is the objective.

---

# 17. Evidence Model

## 17.1 Evidence categories

Recommended:

| Class | Meaning |
|---|---|
| structural / conformance | runtime behaves according to schema |
| smoke / fixture | path executes on a small deterministic case |
| pilot | preliminary empirical signal |
| locked | protocol frozen before outcome |
| confirmatory | prespecified primary evidence completed |
| formal | proof object / theorem under assumptions |
| verifier acceptance | declared acceptance predicate satisfied |
| external outcome | submission / deployment / public effect actually occurred |

## 17.2 Evidence ceiling

Never claim above the strongest evidence class actually present.

Example:

```text
55 runtime tests passed
```

supports implementation conformance.

It does **not** support:

```text
hierarchical agents outperform flat agents
```

## 17.3 Negative evidence

Keep:

- failed branches;
- negative comparisons;
- null results;
- protocol deviations;
- resource blockers.

They are useful for later decisions.

---

# 18. Verification, Repair, Replan, Escalate

## 18.1 accept

Use when current evidence satisfies acceptance.

## 18.2 repair

Use when:

- DIC remains valid;
- local execution / evidence is defective;
- correction remains within authority.

## 18.3 replan

Use when:

- current DIC route cannot deliver honestly;
- frozen method / protocol / acceptance changes;
- new evidence changes the Phase meaning.

## 18.4 escalate

Use when human/material authority is required.

## 18.5 Verifier observability

A verifier cannot certify properties absent from its evidence surface.

If success and failure states look identical to the verifier, no better prompt can guarantee correctness.

Improve evidence, weaken the claim, or preserve uncertainty.

---

# 19. Dependency-Local Recovery

The DIC plan is a dependency graph.

Each node should declare meaningful read / dependency relationships.

If repair changes keys `Delta`:

```text
direct readers = nodes whose declared reads intersect Delta
impact cone = downstream reachability from direct readers
```

Under complete declarations and version-bound evidence, nodes outside the cone can retain evidence.

## 19.1 Hidden-dependency warning

One hidden edge can invalidate the guarantee.

Therefore local recovery is conditional, not magic.

## 19.2 Example

```text
collect -> normalize -> experiment -> table -> paper -> release
                     
          theory  (independent)
```

If `normalize` changes and `experiment` reads it:

```text
rerun:
normalize
experiment
table
paper
release

retain:
collect
theory
```

---

# 20. Human-Attention Objective

## 20.1 Attention intensity

For task interval `tau`:

```text
rho_H(tau) = human supervisory attention / verified research progress
```

This is an evaluation quantity.

Do not claim it has already improved without data.

## 20.2 Intervention taxonomy

Useful classes:

```text
semantic clarification
scientific decision
manual routing
manual context transfer
context reconstruction
execution troubleshooting
evidence interpretation
claim / release decision
security / external approval
```

## 20.3 Attention quality

A workflow may be useful even if total human minutes are similar when attention shifts from:

```text
routing / reconstruction / status checking
```

toward:

```text
scientific judgement / surprising evidence / claim decisions
```

## 20.4 Anti-gaming rule

Do not reduce human attention by hiding uncertainty or weakening evidence checks.

Attention claims require equal-or-better verified progress / quality.

---

# 21. Checkpoints

Human checkpoints should occur at meaningful timescales, not after every prompt.

Typical triggers:

- periodic multi-Phase review;
- Primary Aim change;
- scientific method change;
- acceptance / evidence threshold change;
- protocol freeze / unfreeze;
- destructive / external / paid action;
- public release / submission;
- unresolved verification failure;
- resource blocker requiring human trade-off.

Routine local repairs stay below the human boundary.

---

# 22. Security and External Actions

The workflow is not a sandbox.

Use defense in depth:

1. exact target identity;
2. allowed / forbidden paths;
3. least privilege;
4. isolated credentials;
5. sandbox where applicable;
6. dry run;
7. snapshot / rollback;
8. telemetry / logs;
9. post-action verification;
10. explicit approval for material boundary crossing.

Never substitute a reachable target when the intended target is unavailable.

Return `blocked` or escalate.

---

# 23. Fresh-Session Recovery

A fresh session should recover without requiring chat reconstruction.

## 23.1 Main recovery

Read:

```text
CORE.md
MAIN.md
project authority files
runtime state
Plan / Phase
DIC Core views
latest verified handoff
unresolved decisions
```

## 23.2 Orchestrator recovery

Read:

```text
CORE.md
ORCHESTRATOR.md
DIC Core views
current EPS state
relevant evidence
provider execution guide
```

## 23.3 Validate

Check:

- schema version;
- Plan / Phase / DIC lineage;
- one DIC per Phase;
- required views;
- acyclic plan graph;
- EPS -> DIC bindings;
- Action lineage;
- evidence paths;
- terminal state.

Do not silently infer missing state from conversational context.

---

# 24. Runtime Layout

```text
.ai-workflow/
├── VERSION
├── STATE.json
├── config.toml
├── aw.py
├── aw/
│   ├── cli.py
│   ├── store.py
│   ├── impact.py
│   ├── demo.py
│   └── templates/
├── docs/
│   ├── CORE.md
│   ├── MAIN.md
│   ├── THEORY.md
│   ├── EXPERIMENT.md
│   ├── RESEARCH.md
│   ├── ORCHESTRATOR.md
│   ├── WORKER.md
│   ├── VERIFIER.md
│   ├── PROMPTING_CORE.md
│   ├── GPT56_ROUTING.md
│   ├── CODEX_EXECUTION.md
│   └── CLAUDE_EXECUTION.md
├── guides/
│   ├── README.md
│   ├── DETAILED_WORKFLOW_GUIDE.md
│   ├── WORKFLOW_CLI.md
│   ├── PROMPTING_AND_MODELS.md
│   ├── INSTALL_TO_REPOSITORY.md
│   ├── SECURITY_AND_EXTERNAL_ACTIONS.md
│   └── MIGRATION.md
└── tests/
```

Compact docs are execution authority.

Guides are on-demand reference.

---

# 25. CLI / Deterministic Runtime

The `aw` utility should handle deterministic state mechanics rather than semantic scientific decisions.

Typical classes of operation:

```text
status / recovery
Plan / Phase / DIC registration
EPS / run / Action lineage
verification outcome recording
impact-cone calculation
validation
runnable demo
```

Do not push objective interpretation into the CLI merely because it can be represented as JSON.

See `WORKFLOW_CLI.md` for the current command surface.

---

# 26. Tracking the AI Native Workflow Development Package

The outer development distribution has one current truth surface.

## 26.1 Canonical root files

```text
00_READ_FIRST.md
CURRENT_STATE.md
ROADMAP.md
README.md
QUICKSTART.md
VERSIONING.md
CHANGELOG.md
PACKAGE_MANIFEST.json
PACKAGE_HANDOFF.json
```

## 26.2 What each does

### 00_READ_FIRST.md

Very short authority / index.

### CURRENT_STATE.md

What is true **now**.

No future task list.

### ROADMAP.md

Future work only.

### README.md

Stable product / package explanation.

### QUICKSTART.md

Adoption path only.

### VERSIONING.md

Version policy.

### CHANGELOG.md

Cumulative historical change log.

### PACKAGE_MANIFEST.json

File inventory / hashes.

### PACKAGE_HANDOFF.json

Machine-readable recovery state.

## 26.3 History

Superseded files move to:

```text
history/
├── changelogs/
├── tracking/
├── prompts/
└── build_*/
```

Do not leave three Quick Starts and multiple competing “current reports” at root.

---

# 27. Research Example

Primary Aim:

```text
Determine whether a proposed attention compatibility mechanism has
stable benefit beyond matched conventional Q/K capacity.
```

DIC plan:

```text
A novelty audit -----\
B theory attack ------+--> D Main reconciliation --> E claim decision
C matched experiment -/
```

Possible outcomes:

```text
A: nearest prior method found
B: theoretical distinctness survives
C: matched control removes empirical gain
```

Main reconciliation:

```text
Do not claim superior method.
Preserve theoretical distinction as conditional insight.
Redesign next Phase around a regime where compatibility may be load-bearing.
```

The workflow's value is not forcing a positive result.

It is keeping the project coherent while evidence changes the route.

---

# 28. Research Example — Defensive Drift

Initial Primary Aim:

```text
Find the strongest correct theorem-supported result.
```

After repeated hostile audits an agent may begin recommending:

```text
remove mechanism claim
remove interpretation
remove ambitious experiment
emphasize only caveats
```

Main should ask:

```text
Did the evidence actually falsify these claims?
Or did “avoid criticism” become the objective?
```

Correct response:

- preserve falsified claims as removed;
- retain surviving ambitious claims under actual assumptions;
- do not restore overclaims;
- do not flatten the paper into only limitations.

---

# 29. Research Example — Salience Flattening

Bad Phase output:

```text
5 datasets
7 metrics
4 side theorems
3 architecture variants
6 future directions
```

but no primary answer.

Repair by Main:

1. restate Primary Aim;
2. classify every branch;
3. keep only load-bearing controls;
4. defer interesting but non-decisive work;
5. rewrite DIC / paper around the central result.

---

# 30. General Technical Example

Task:

```text
Introduce a new feature family across data ingestion,
model code, frozen evaluation, documentation, and package release.
```

DIC plan:

```text
schema freeze
    -> model integration
    -> frozen baseline / comparison
    -> report / docs
    -> package validation
```

Parallelize docs only after artifact paths stabilize.

Do not let a documentation Worker redefine the experiment.

---

# 31. When the Workflow Is Worth It

Good fit:

- multi-session;
- multi-artifact;
- multiple AI surfaces;
- evidence-sensitive;
- expensive failure propagation;
- parallel branches;
- research + code + writing;
- public claims / submission;
- repeated fresh sessions.

Poor fit:

- one paragraph rewrite;
- one obvious local code edit;
- one low-risk question;
- work where process overhead exceeds coordination risk.

Use proportional control.

---

# 32. Phase Closure

Close only when:

- Primary requests are accepted or visibly terminal-negative / blocked;
- evidence is current;
- verifier state is `accept` for successful completion;
- failed branches remain visible;
- DIC identity resolves;
- terminal EPS / run identities resolve;
- release / submission state is explicit;
- handoff is current;
- next Phase is proposed only from verified state.

Valid terminal states include:

```text
complete
blocked
resource-blocked
negative-result
superseded
abandoned
```

Do not force every Phase into a positive scientific result.

---

# 33. Main Handoff

A compact handoff should contain:

```text
Phase
Primary Aim
terminal status
DIC identity
verified / negative evidence
failed / superseded branches
material decisions
claim boundary
human / release state
next Phase recommendation
```

It should not paste every Worker log.

---

# 34. Documentation Layering

## Runtime docs

Small and normative.

```text
.ai-workflow/docs/
```

## Detailed guides

Operational / maintainer explanation.

```text
.ai-workflow/guides/
```

## Technical report

Scientific rationale, literature, formal theory, evaluation, limitations.

```text
technical_report/
```

## Current tracking

Compact package state.

```text
CURRENT_STATE.md
ROADMAP.md
```

Do not merge all four purposes into one giant “master.md”.

---

# 35. Glossary

**Action** — primitive tool/edit/search/test/experiment operation.

**DIC** — Durable Intent Contract; one durable multi-view semantic contract per Phase.

**EPS** — Execution Prompt Stack; disposable operational realization of DIC plan nodes for one attempt.

**Experiment** — specialist empirical methodology / interpretation workstream.

**Goal** — programme-scale outcome and authority.

**Main** — persistent planning / decision chat and semantic center.

**Orchestrator** — repository-aware coding-agent operational center.

**Phase** — coherent milestone under a Plan.

**Plan** — strategic multi-Phase decomposition.

**Primary Aim** — one central result a Phase exists to establish.

**Prompt/Run** — one bounded executor invocation.

**Research** — external evidence capability returning to Main.

**Theory** — specialist formal / conceptual reasoning workstream.

**Verifier** — independent acceptance evaluator returning accept / repair / replan / escalate.

**Worker/subagent** — bounded executor under an Orchestrator / parent.

---

# 36. Maintenance Rules

When changing the workflow itself:

1. update compact docs first if runtime semantics change;
2. update templates / schema / tests;
3. update this detailed guide;
4. update the technical report if rationale / theory / public framing changes;
5. update `CURRENT_STATE.md`;
6. add cumulative `CHANGELOG.md` entry;
7. update package manifests and handoff;
8. run tests / validation / demo;
9. rebuild runtime ZIP and full package;
10. preserve superseded tracking material under `history/`.

Do not update only the report while leaving executable runtime semantics stale.

---

# 37. Final Operating Summary

```text
Researcher
  -> Main persistent chat
      -> Research if decision-relevant
      -> Theory / Experiment if useful
      -> one whole Phase
      -> one DIC
          README / REQUESTS / PLAN
          durable sequence + parallelism graph
  -> coding-agent Orchestrator
      -> JIT model-tuned EPS
      -> bounded prompts / subagents
      -> actions / evidence
      -> integration
      -> verifier
          accept / repair / replan / escalate
  -> Main reconciliation / closure / next Phase
```

The system should make machine execution more autonomous **without making the researcher's understanding of the project less clear**.

The researcher should spend attention on the Primary Aim and the science, not on reconstructing agent activity.
