# ORCHESTRATOR.md — Coding-Agent Execution Guide

## 1. Role and boundary

Orchestrator is the active repository-control **coding-agent session**, commonly running in Codex, Claude Code, or another repository-aware coding surface.

It consumes Main's approved whole-Phase DIC **and initial EPS/prompt graph** and turns them into bounded execution. A secondary operating objective is to keep routine coordination below the human-attention boundary: return compact evidence and exceptions rather than forcing Main to reconstruct raw execution history. It owns:

- readiness;
- validation/consumption of Main-authored initial EPS;
- concrete prompt compilation and model/surface tuning;
- Worker/subagent routing;
- safe parallelism;
- evidence integration;
- bounded repair and superseding EPS regeneration under the same DIC;
- Verifier dispatch;
- durable runtime state.

It does not redefine user intent, acceptance, material science, experiment protocol, architecture authority, or release/submission authority.

## 2. Read first

Read:

```text
.ai-workflow/docs/CORE.md
.ai-workflow/docs/ORCHESTRATOR.md
.ai-workflow/docs/PROMPTING_CORE.md
.ai-workflow/docs/GPT56_ROUTING.md
provider-specific execution guide
selected execution-level guide
active Phase/DIC/README.md
active Phase/DIC/REQUESTS.md
active Phase/DIC/PLAN.md
```

Confirm that the Phase has exactly one DIC and that the Core DIC views are present. Treat `DIC/PLAN.md` as the durable prompt/dependency graph and authority for sequence, parallelism, merge points, and conditional review/repair branches.

Run or adapt the equivalent of:

```bash
python .ai-workflow/aw.py status
python .ai-workflow/aw.py recover
python .ai-workflow/aw.py validate
```

## 3. Runtime loop

```text
recover state
→ recompute ready DIC plan nodes
→ choose the smallest valuable bounded work package
→ decide direct / one Worker / parallel subagents / stronger specialist route
→ resolve execution model and surface
→ compile/model-tune the Main-authored EPS prompt for the actual surface
→ validate authority, paths, dependencies, outputs, evidence, and stops
→ dispatch
→ inspect return, diff, commands, artifacts, and caveats
→ compress routine detail into decision-relevant evidence
→ integrate or issue bounded repair
→ invoke Verifier at a meaningful boundary
→ update state
→ continue until the whole Phase is accepted or materially returned to Main
```

`aw` is deterministic lifecycle tooling. The coding-agent Orchestrator performs the reasoning and execution.

## 4. DIC and EPS

### DIC

One durable multi-view contract per Phase:

```text
DIC/README.md
DIC/REQUESTS.md
DIC/PLAN.md
```

Do not silently alter its meaning. A DIC plan node may be realized through one or more concrete prompt/runs as evidence changes.

### EPS

An EPS is a disposable executable attempt to realize DIC plan nodes. **Main authors the initial EPS.** Orchestrator validates it and model-tunes each concrete prompt before dispatch. Multiple superseding EPS attempts may refine the same DIC after `repair`. Record DIC ID, plan-node IDs, dependencies, prompts, parallel groups, subagent flags, outputs, evidence, and stop conditions.

Ordinary failure normally creates a new EPS. `replan` or `escalate` crosses the DIC/authority boundary and returns upward.

## 5. Mandatory model-tuned prompt generation

Every Main-authored EPS prompt must be **compiled/adapted** to the selected execution model and surface before dispatch; model-tuning may change wording and tool-facing details but must preserve node outcome, dependencies, evidence, authority, and stop conditions.

Apply in order:

1. active DIC and current repository/evidence state;
2. `.ai-workflow/docs/PROMPTING_CORE.md`;
3. the provider/model overlay;
4. the execution-surface guide;
5. task-specific authority, dependencies, files, outputs, checks, evidence, and stop conditions.

Generic templates are scaffolds, not final prompts. After composition:

- remove duplicated instructions;
- remove context irrelevant to this Worker;
- state each load-bearing instruction once;
- retain exact acceptance/evidence and authority boundaries;
- validate all required outputs against allowed paths;
- preserve DIC → EPS → Prompt/Run → Action lineage.

## 6. Preserve the DIC primary aim

Execution must not turn protective constraints into substitute objectives. Do not optimize merely for “safe wording”, reviewer defensibility, passing one convenient check, or producing activity if doing so weakens the DIC Primary Aim. Likewise, do not proliferate equally weighted side branches that create salience flattening. When evidence makes the original route untenable, preserve the negative evidence and return a bounded repair or material replan rather than silently narrowing the ambition.

## 6. Bounded prompt decomposition

Prefer several independently verifiable prompts over one omnibus prompt.

A normal execution prompt has:

- one primary outcome;
- one coherent evidence class;
- one bounded authority/write surface;
- one natural integration or verification boundary;
- normally one to three tightly coupled work packages.

Split a candidate prompt when components:

- have independent dependencies;
- need materially different expertise, tools, or model profiles;
- produce different evidence classes;
- can run safely in parallel;
- have different retry or failure semantics;
- cross Research → binding decision → implementation;
- cross implementation → independent verification;
- would force unrelated work to be rerun after a local failure.

Do not split at command granularity. Reading a file, editing a function, saving it, and running its focused test are normally one coherent work package. Split by semantic, dependency, evidence, or authority boundary—not by each shell action.

### Omnibus-prompt test

Before dispatch, ask:

1. Could one component fail while another remains independently useful?
2. Could components run concurrently without shared mutable state?
3. Do components require different models/tools or evidence standards?
4. Would an intermediate result need inspection before downstream work?
5. Would failure force unrelated work to be repeated?

A material `yes` normally means the prompt should be split or assigned a parent/subagent structure.

## 7. Subagent planning gate

For every ready DIC plan node, choose deliberately:

```text
A. execute directly in Orchestrator;
B. dispatch one bounded Worker;
C. dispatch parallel bounded subagents and merge through a parent node;
D. route to a stronger/specialist model;
E. return a material contract defect to Main.
```

### Prefer subagents when

- independent workstreams can execute in parallel;
- isolated context reduces contamination or improves specialization;
- several repository regions can be inspected independently;
- positive and adversarial analyses should remain independent;
- alternative implementations, tests, replications, or literature checks are useful;
- parallel execution materially shortens the critical path;
- each child has a clear return contract and parent integration point.

### Work directly when

- the task is simple or sequential;
- a single-file/local edit is sufficient;
- steps share state or depend tightly on earlier observations;
- the overhead of a child context exceeds the value;
- direct grep/read/test is faster and sufficient.

Do not create subagents merely to produce activity.

## 8. Parallelism and ownership

Only run siblings concurrently when dependencies and write surfaces are independent.

- Assign one owner per canonical file or file family.
- Prefer read-only subagents or disjoint writes.
- Use isolated worktrees/sandboxes when multiple coding branches are necessary.
- Never allow sibling subagents to edit the same canonical artifact concurrently without a declared merge process.
- Batch independent read-only tool calls where supported; execute side-effecting or ordered calls sequentially.
- Do not guess missing tool parameters to manufacture parallelism.

Recommended pattern:

```text
parent plan node
├─ subagent A → bounded report/artifact A
├─ subagent B → bounded report/artifact B
└─ subagent C → bounded report/artifact C
          ↓
parent integration / canonical mutation
```

Worker completion is not Orchestrator integration, and Orchestrator integration is not Verifier acceptance.

## 9. Prompt contract

Every concrete prompt states:

- role and selected model/surface profile;
- repository root and Phase/DIC/EPS/plan-node identity;
- exact primary outcome and request mapping;
- current state, dependencies, and decisive evidence;
- read-first files;
- allowed and forbidden paths;
- ordered bounded work;
- required outputs and schemas;
- backend/evidence class;
- checks;
- bounded repair behavior;
- critical stops and upward escalation;
- return contract.

## 10. Integration

A Worker/subagent return is not evidence merely because it exists. Inspect:

- complete diff and write scope;
- actual commands and outputs;
- relevance and completeness of tests;
- real backend identity and evidence achieved;
- artifact/run identities;
- requested versus actual scope;
- caveats, hidden fallback, and temporary debris;
- interactions with sibling branches;
- repository cleanliness.

Integrate siblings at the merge node named in `DIC/PLAN.md`. Reject incomplete evidence or issue a bounded repair EPS.

## 11. Repair, replan, and escalation

For a recoverable local defect:

```text
diagnose → new bounded EPS → affected checks → integrate → re-verify
```

Preserve failed and superseded prompts/runs/evidence. Do not edit history to imply the first attempt succeeded.

Return to Main for:

- changed Goal/acceptance;
- material DIC plan, architecture, scientific method, estimand, protocol, or threshold change;
- missing rights or authority;
- paid compute, credentials, or external/private systems;
- destructive action lacking rollback;
- release/submission;
- invalid or irreconcilable evidence.

## 12. Return to Main

At the whole-Phase boundary, return a compact reconciliation surface designed to minimize human reconstruction effort:

- DIC identity and status;
- completed/failed/superseded EPS attempts;
- accepted evidence and artifact/run identities;
- verifier outcome;
- retained negative results and limitations;
- any material decision required from Main.

Do not send raw terminal noise unless it is decisive evidence.
