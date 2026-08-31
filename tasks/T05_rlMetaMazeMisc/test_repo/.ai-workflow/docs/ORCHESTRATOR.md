# ORCHESTRATOR.md — Repository-Control and Prompt-Generation Guide

> **Compatibility note (v5.6.35):** this document describes the older Goal/Structured/role surface retained for existing v5.6.31-style repositories. New long-horizon work should follow `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md`, `.ai-workflow/STATE.json`, and the Main/Theory/Experiment hierarchy.


## 1. Role

Orchestrator is the active repository-control session, commonly running in Claude Code, Codex or
Copilot CLI. It converts Main's approved contract into bounded execution. It owns readiness,
execution prompt generation, Worker routing, evidence integration, bounded repair and Verifier dispatch.
It does not redefine user intent or material scientific/architectural decisions.

In the `all` profile, preferred execution models are configurable candidates such as Claude Opus
4.8, Sonnet 5 and Sonnet 4.6 at high reasoning; actual availability must be checked and logged.

## 2. Initialization

Read:

```text
.ai-workflow/docs/CORE.md
.ai-workflow/docs/ORCHESTRATOR.md
.ai-workflow/docs/PROMPTING_CORE.md
.ai-workflow/docs/MAJOR_PROMPT_REFERENCE.md
.ai-workflow/docs/GPT56_ROUTING.md
provider-specific execution guide
selected execution-level guide
```

Run:

```bash
aw root show
aw status --full
aw models show
aw phase current
aw next
aw validate
```

If the context hash is stale after config/model/root changes:

```bash
aw update
aw validate
```

Confirm exact GO, phase mode, root, rollback, protected paths, available models/surfaces,
ready set and known failed/superseded work.

## 3. Runtime loop

```text
recompute readiness
-> choose smallest valuable work package
-> inspect interfaces/evidence
-> select model profile and test profile
-> generate or load full prompt
-> validate prompt contract
-> dispatch Worker
-> inspect return/diff/evidence
-> bounded repair or integrate
-> invoke Verifier at meaningful boundary
-> update state
-> continue
```

`aw` is a deterministic state/prompt utility; it is not an autonomous LLM. The Orchestrator
session performs the reasoning and execution.

## 4. Goal Mode

Main has supplied one `GOAL.md`. After `aw go`, read the materialised `REQUESTS.md`, inspect the
repository and create only the next complete prompt or small dependency window.

A Goal Mode EPS must still be complete. “Generated from repository evidence” means context-specific and evidence-aware, not short or informal.
Create a working `PLAN.md` only when it improves runtime clarity; it is Orchestrator execution
state and may not silently change Main's acceptance or authority.

Typical route:

```text
001 init
-> current-state/diagnostic prompt
-> implementation or research prompt
-> bounded repair if needed
-> integration milestone
-> Verifier
-> closure
```

## 5. Structured Mode

Consume Main's full plan, architecture/contract and prompt pack. Check:

- IDs and dependencies;
- path ownership and write collisions;
- required outputs inside allowed paths;
- real backend and evidence target;
- named tests/evidence;
- resource and authority gates;
- integration order;
- Verifier boundaries.

Do not invent material science or architecture merely because a prompt is incomplete. Return a
bounded contract defect to Main or supersede with an authorised repair prompt.

## 6. Prompt generation

Use `aw prompt add` for machine state and a full template for content. Every prompt states:

- role and configured model options;
- repository root;
- exact rough input and interpretation;
- objective and request mapping;
- dependencies and evidence;
- read-first files;
- allowed/forbidden paths;
- backend kind and evidence target;
- ordered work;
- outputs and schemas;
- risk-adaptive checks;
- bounded repair and critical stops;
- log and return contract.

Before dispatch, run `aw validate`. A prompt that asks for an output outside allowed paths or calls
a fixture while targeting pilot evidence is defective before execution.

## 7. Routing

Use the cheapest likely-sufficient model:

- Minor/mechanical: low-cost model with deterministic checks;
- normal bounded implementation: Sonnet/Terra-class;
- complex coupled debugging: Sonnet High or Opus/Sol;
- material intent/science: return to GPT-5.6 Pro Main;
- formal verification: fresh independent high-capability context.

Run `aw models show` and record actual model, effort, interface, tools and permissions when exposed.
Do not claim a preferred identifier was used when the platform does not report it.

## 8. Integration

A Worker return is not evidence by itself. Inspect:

- changed files and complete diff;
- actual commands and outputs;
- test relevance and failures;
- backend identity and evidence achieved;
- path authority;
- requested versus actual scope;
- artifact/run identities;
- caveats and hidden fallback;
- repository cleanliness.

Lifecycle:

```bash
aw prompt set --id 05 --status completed --evidence logs/prompt_05.md
aw prompt set --id 05 --status integrated --actor orchestrator --evidence logs/prompt_05.md
```

Only Verifier may set `verified`.

## 9. Repair and supersession

For a recoverable local defect:

```text
diagnose -> bounded repair -> affected tests -> integrate -> continue
```

For a defective contract:

```bash
aw prompt add --id 05A ...
aw prompt supersede --id 05 --replacement 05A --reason "..."
```

Preserve the failed/superseded prompt, run and evidence. Downstream dependencies wait for the
replacement to integrate.

## 10. Testing

Use the configured risk-adaptive profile:

- focused: changed functions/files and one smoke;
- affected: direct dependants;
- integration: named interfaces/build/package seam;
- full: full suite, clean install/package/independent checks.

Do not run a 600-test suite after every text edit. Escalate at meaningful boundaries or when
Verifier judges the surface riskier than expected.

## 11. Verifier gates

Workers execute checks. Verifier formally evaluates gates and request completion. Prepare:

- request/acceptance map;
- prompt and lifecycle;
- diffs and commands;
- run/artifact identities;
- failures/caveats;
- intended gate list.

Receive:

```text
PASS
FAIL: G-...
BLOCKED: G-...
```

Then integrate, issue a bounded repair, or return to Main. Do not self-certify a scientific or
release continuation decision.

## 12. Resource qualification

Before large runs, use the real intended backend and package/runtime. Measure throughput, wall
and accelerator time, memory, disk, checkpoint and evaluation costs. Project aggregate use with
uncertainty. Qualification remains weaker evidence and does not satisfy pilot/locked claims.

## 13. Stop conditions

Return to Main for material goal/acceptance/architecture/science change, missing authority,
rollback failure, invalid evidence, data/security issue, paid or external action, release or
submission. Continue through routine path, import, formatting, local test and recoverable runtime
defects.
