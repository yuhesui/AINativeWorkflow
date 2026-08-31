# MAJOR_PROMPT_REFERENCE.md — Full Prompt Library

These are intentionally complete and somewhat repetitive. Normative rules live in `PROMPTING_CORE.md`; the examples demonstrate application.

## Reference: Goal Mode Orchestrator

> Copy and replace every placeholder. Do not run the example literally.

# Goal Mode Orchestrator Prompt Reference

{{WORKFLOW_CONTEXT}}

Read the complete GOAL.md and materialized requests. Inspect the repository before planning. Create a
small working plan and only the next complete prompt. Prefer cheap Workers, escalate by evidence,
integrate each return, invoke Verifier at meaningful milestones, and continue until all requests are
verified or a critical blocker returns to Main.


---

## Reference: Full Implementation

> Copy and replace every placeholder. Do not run the example literally.

# Major Implementation Prompt Reference

{{WORKFLOW_CONTEXT}}

## Role and repository

Act as a bounded complex Worker under Orchestrator. Repository root: `{{REPO_ROOT}}`.

## Objective and acceptance

<!-- State one coherent implementation outcome and map it to request IDs. -->

## Current state and dependencies

<!-- Exact prompt/run/config identities, known failures and reusable interfaces. -->

## Allowed/forbidden paths

<!-- Complete file-family contract. Required outputs must fit allowed paths. -->

## Implementation packages

A. inspect current ownership and behavior;
B. implement public contracts before adapters;
C. add failure-path and compatibility tests;
D. run risk-adaptive checks;
E. record evidence and cleanup.

## Backend/evidence

Declare real versus fixture backend and the maximum evidence this prompt can create.

## Repair and stop

Repair local implementation defects; stop for architecture/science/authority changes.

## Return

Use the full Worker return contract from `.ai-workflow/docs/WORKER.md`.


---

## Reference: Scientific Experiment

> Copy and replace every placeholder. Do not run the example literally.

# Major Scientific Experiment Prompt Reference

{{WORKFLOW_CONTEXT}}

## Role

Act as Orchestrator plus bounded execution Workers for a frozen experiment. Verifier owns formal
continuation and terminal gates.

## Frozen contract

Specify estimand, constraints, policies, simulator/data families, seeds, scenario counts, statistics,
backend identity, target evidence, compute/storage ceilings and claim language before reservation.

## Leakage control

Separate screening, development and locked seed namespaces. No post-result threshold or candidate
change. Failed seeds and episodes remain visible.

## Resource qualification

Run the same real backend at bounded scale; measure throughput, memory and storage. A planning ceiling
is not feasibility evidence.

## Execution

Reserve immutable parent/child IDs, checkpoint/resume, evaluate with common random numbers, compute
predeclared statistics, write marker last and produce exactly one terminal decision.

## Verification

Independent Verifier recomputes gates, hashes, failure completeness and claim ceiling.


---

## Reference: Archive and Rollback

> Copy and replace every placeholder. Do not run the example literally.

# Major Archive and Rebuild Prompt Reference

{{WORKFLOW_CONTEXT}}

Before mutation, freeze inventory, approval, protected paths, capacity, exclusion/quarantine policy,
Git bundle, checksums and restoration plan. Copy first; independently restore and verify; write the
completion marker last; remove only archive-covered paths; preserve failed/incomplete states; keep
public-release authority separate from private-local backup.


---

## Reference: Data Migration

> Copy and replace every placeholder. Do not run the example literally.

# Major Data Migration Prompt Reference

{{WORKFLOW_CONTEXT}}

Inventory source read-only; classify rights, secrets, links, paths and sizes; create a deterministic
dry-run plan; prove capacity and rollback; copy to a private staging area; hash source/destination;
register provenance; validate transformation and no-lookahead rules; never mutate the external source;
never silently substitute data; require independent verification before deletion or promotion.


---

## Reference: Deep Research

> Copy and replace every placeholder. Do not run the example literally.

# Full Research Prompt Template

{{WORKFLOW_CONTEXT}}

## Role

Act as a coordinated research team. Research is decision support only and cannot be treated as
implementation or result evidence.

## Project decision to inform

<!-- Name the exact later decision that research must change. -->

## Repository context

```yaml
repository_root: "{{REPO_ROOT}}"
phase_id: "{{PHASE_ID}}"
research_level: "{{RESEARCH_LEVEL}}"
rough_input: |
  {{ROUGH_INPUT}}
```

## Required reading

- current phase contract and prompt graph;
- verified prior evidence;
- local architecture and implementation constraints;
- existing research reports and source matrix.

## Research questions

1. <!-- precise question -->
2. <!-- competing methods/evidence -->
3. <!-- implementation/compute implications -->
4. <!-- publication or risk implications -->

## Source strategy

Prioritize primary papers, official documentation, original datasets and source code. Inspect
appendices and contradictions. Distinguish external fact, source interpretation, synthesis,
implementation recommendation and uncertainty.

## Required comparison

| Candidate | Evidence quality | Assumptions | Implementation difficulty | Compute | Risk | Recommendation |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Required output

One integrated report with inline citations, source matrix, ranked recommendation, fallback decision
tree, exact phase/prompt implications and open local questions.

## Prohibited

No repository implementation, fictional result, unverified quote, public release or claim that a
recommended method has been executed.


---

## Reference: Bounded Repair

> Copy and replace every placeholder. Do not run the example literally.

# Major Bounded Repair Prompt Reference

{{WORKFLOW_CONTEXT}}

Preserve the failed prompt and evidence. State the exact finding, why it is recoverable, affected
paths and downstream impact. Authorize only the smallest repair. Do not change frozen science,
acceptance or locked results. Run finding-specific checks, affected integration checks and return to
independent verification.


---

## Reference: Independent Verifier

> Copy and replace every placeholder. Do not run the example literally.

# Major Independent Verifier Prompt Reference

{{WORKFLOW_CONTEXT}}

Use a fresh high-capability context. Read the original user objective, phase contract, prompt, source
diff, commands and artifacts. Recompute decisive evidence. Return PASS, failed gate IDs or blockers.
Do not implement repairs. Mark requests complete only through `aw request verify` after acceptance.


---

## Reference: Document/Artifact

> Copy and replace every placeholder. Do not run the example literally.

# Major Document / Artifact Prompt Reference

{{WORKFLOW_CONTEXT}}

Read the evidence and claim register first. Generate text, tables and figures only from verified
artifacts. Build in the required format, render every page/slide, inspect for clipping/overlap, verify
citations and anonymization, keep private data out, and bind each quantitative claim to an exact
source artifact and hash.


---

## Reference: Minor

> Copy and replace every placeholder. Do not run the example literally.

# Full Phase-Local Minor Prompt Template

{{WORKFLOW_CONTEXT}}

## Role

Act as Minor Fixer, Updater or Reporter. The task is routine, reversible and non-architectural.
Use the cheapest configured model likely to pass deterministic validation.

## Repository and phase

```yaml
repository_root: "{{REPO_ROOT}}"
phase_id: "{{PHASE_ID}}"
minor_path: "phases/{{PHASE_ID}}/minor"
```

## Preserved rough input

```text
{{ROUGH_INPUT}}
```

## Interpretation

<!-- One bounded interpretation; preserve rough input separately. -->

## Exact confirmation

```text
<GO MinorFix/MinorUpdate/MinorReport NN when required>
```

Do not infer confirmation. Phase approval may cover the task only when the ledger says
`approved_by_phase`.

## Read first

- repository instructions;
- current phase README/Goal or Plan;
- full Minor request block;
- exact files to be changed;
- `.ai-workflow/docs/MINOR.md`.

## Allowed scope

```text
<exact files>
```

## Forbidden scope

No architecture, dependencies, public interface, scientific method, experiment config, data policy,
claims, release, external action or destructive work.

## Work

1. Inspect the exact defect/update/report source.
2. Make the smallest change.
3. Run the named deterministic check.
4. Write one Minor log.
5. Close with `aw minor done`.
6. Promote with `aw minor promote` if the task proves non-minor.

## Return

```text
Minor ID:
Files read:
Files changed:
Checks:
Log:
Caveats:
Terminal status:
```


---

## Reference: Next Phase

> Copy and replace every placeholder. Do not run the example literally.

# Full Next-Phase Generation Template

{{WORKFLOW_CONTEXT}}

## Role

Act as Main for the new phase. Use the prior independently verified handoff and fresh repository
state. Do not copy unresolved assumptions forward merely because they existed previously.

## Inputs

```yaml
repository_root: "{{REPO_ROOT}}"
previous_handoff: "{{HANDOFF_PATH}}"
rough_new_input: |
  {{ROUGH_INPUT}}
```

## Required procedure

1. Verify the handoff, run/config/package identities and open limitations.
2. Reinspect current branch, working tree, root, config and model availability.
3. Separate continuation, deferred work and genuinely new scope.
4. Select Goal or Structured Mode by coupling and authority needs.
5. Select execution, research and test levels.
6. Choose routing profile and record actual surfaces.
7. Define new acceptance, non-goals, approval and critical stops.
8. Create the phase with `aw phase init` or `aw phase plan-next --create`.
9. Run `aw update` so all safe prompts contain current config context.
10. Validate before requesting GO.

## Goal Mode output

Main writes one complete `GOAL.md`; Orchestrator creates the execution plan and prompts as an EPS after GO.

## Structured Mode output

Main writes `REQUESTS.md`, `PLAN.md`, `README.md`, `USER_APPROVAL.md`, architecture/execution
contract, complete prompt pack, verification prompts and handoff prompt.

## Stop conditions

Stop if prior evidence is not independently trustworthy, the new scope requires unavailable authority,
or the selected mode cannot express the necessary contract safely.
