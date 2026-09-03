# Main report — Hierarchical Research Upgrade and Workshop Submission Programme

**Authoritative state:** `.ai-workflow/STATE.json`  
**Package version:** 5.6.37  
**External submissions/actions:** none  
**Automated release blockers:** 0 for this local restructuring/build pass (see `build/BUILD_STATUS.md`)

## 1. Architecture and attention-objective changes

The canonical refinement chain remains **Goal → Plan → Phase → DIC → EPS → Prompt/Run → Action**. The operative runtime is only `.ai-workflow/`. Main is the persistent user-facing planning/decision chat; Theory and Experiment are optional specialist reasoning workstreams; Research is advisory and returns to Main; a repository-aware coding-agent Orchestrator realizes approved DIC plan nodes through model-tuned EPS prompts and bounded Workers/subagents.

The package now states its practical objective more precisely: **reduce human attention required per unit of verified research progress**, subject to scientific quality, evidence, and authority. This is an evaluation target rather than an established empirical gain. Routine routing, context reconstruction, prompt management, local repair, and evidence bookkeeping should stay below the human boundary; human attention should concentrate on primary scientific aims, surprising evidence, material methodological changes, claim boundaries, and external responsibility.

Each Phase has exactly one multi-view DIC. `DIC/README.md` now foregrounds one **Primary Aim** and priority/salience structure; `DIC/REQUESTS.md` prioritizes observable outcomes; `DIC/PLAN.md` remains the durable dependency/parallelism/merge/repair graph. The DIC is therefore both a machine contract and a human-intelligibility interface: machine execution may become complex without requiring the researcher to reconstruct raw prompt histories or terminal logs.

The guidance also names two semantic failure patterns observed in long-horizon AI-assisted research: **constraint–objective inversion / defensive drift**, where a safeguard such as “avoid unsupported claims” becomes the effective objective, and **salience flattening**, where many reasonable branches acquire similar weight and the research loses a central contribution. These are workflow failure modes, not claimed universal empirical properties of language models.

## 2. Strongest surviving theory

The strongest mechanism-specific result is the **dependency-local recovery theorem with worst-case tightness**. Under complete read/write declarations, complete dependency edges, version-bound evidence, and deterministic-or-reverified phase semantics, a repair changing keys `Δ` need invalidate only the dynamic impact cone `Reach({v : R_v ∩ Δ ≠ ∅})`. Every node in that cone can be necessary in a compatible worst case, so no uniformly smaller safe set follows from footprint information alone.

Two supporting results survive: a conditional verifier miss bound gives fault-survival probability at most `α^k` after `k` observable gates and expected detection delay at most `1/(1−α)` gate intervals; a stationary cost model gives an explicit checkpoint-interval optimum. A separate evidence-aliasing proposition proves that an evidence-only verifier cannot attain both zero false acceptance and zero false rejection when its observation map merges goal-satisfying and goal-violating states.

## 3. Most serious theoretical/novelty limitation

The formal ingredients are adaptations of established contract composition, dependency/incremental-computation, checkpoint-restart, and partial-observability ideas. They clarify this agent workflow but are not presented as foundational theorem novelty. Hierarchical planning, manager/worker agents, memory externalization, reflection, verifier calls, and automated harness optimization are already known. The defensible candidate contribution is their integrated, package-resident operationalization as **persistent intent + hierarchical refinement + bounded execution + evidence-gated verification + local repair/upward replanning**. That system-level novelty remains provisional until a fresh hostile literature review and controlled comparative evidence exclude materially equivalent systems.

## 4. Implementation and test status

- Active runtime schema/version: **5.6.37**.
- Core runtime tests re-run after the attention/salience guidance changes.
- Exactly one DIC per Phase remains enforced; three Core DIC views are required; DIC graphs must be acyclic.
- Model-executed EPS nodes still require recorded model/surface and prompt-tuning provenance before Actions can be recorded.
- The long-form technical report was synchronized to the current Main-chat / coding-Orchestrator realization and rebuilt successfully.
- Engineering validation establishes state-machine/package conformance only; it does not establish agent-performance or human-attention savings.

## 5. Experiment status

No large confirmatory comparative study is claimed. The existing matched-budget programme remains the gate for performance claims. It is now augmented with **human-supervision outcomes**: intervention counts by class, logged intervention duration where feasible, manual routing/context-reconstruction events, and human-attention intensity under prespecified milestone weights. These measures are benchmark-relative and must not be interpreted as a universal productivity score.

## 6. Meta-Agents readiness

**Selected format: Full Paper.** The official workshop call permits up to 9 pages of main text and explicitly solicits meta-agent architectures, theory, evaluation, oversight, and responsible-use analysis. The current paper is an original systems/theory contribution rather than a governance-only position; compressing it to Short Paper would remove load-bearing mechanism and assumptions, while Demo Track alone would undersell the contribution. A runnable demo can still accompany the paper/poster if the portal permits supplementary material.

`submissions/meta_agents/` now contains the Full-Paper track decision, updated anonymous NeurIPS-style source, responsible-use statement, compiled PDF, and checklist. The framing now separates persistent Main-level semantic management from coding-agent Orchestration, treats the DIC as a human-attention interface, and introduces human-attention intensity only as a planned evaluation target. No confirmatory agent-performance or attention-efficiency result is fabricated.

## 7. Who Verifies readiness

`submissions/who_verifies/` contains a materially different anonymous manuscript, bibliography, verification-loop figure, checklist, build status, and compiled PDF (rebuilt successfully; 4 pages). Its center of gravity is environment-grounded evidence, unsupported completion, fault localization, local invalidation, upward replanning, imperfect verification, and observability limits.

It is a conservative theory/system draft pending the same current-rule and release checks and pending confirmatory fault-injection evidence for a strong empirical claim. It is not a renamed copy of the Meta-Agents paper.

## 8. AutoMLR eligibility/readiness

**NOT SUBMISSION-READY.** The current primary result is an agent-workflow/control system plus formalization and planned evaluation, not a separate qualifying ML research result autonomously conducted end-to-end or decisively produced by the system. `ELIGIBILITY_CHECK.md` records this gate. The 4/4/1 LaTeX scaffold is visibly watermarked/boxed, contains no invented Part I result, and marks Part II/III text requiring human authorship or rewrite. Abstract registration was not performed and no external action was taken.

## 9. Exact next tasks

### Theory

1. Conduct a fresh hostile audit of THM-LOCAL-01/02, THM-VER-01, PROP-CHK-01, PROP-CTX-01, and IMP-OBS-01, checking hidden-state, stochastic-tool, evidence-version, and conditional-miss assumptions line by line.
2. Inspect every 2025–2026 candidate in `CURRENT_PRIMARY_SOURCE_SCAN.json` and official proceedings records; search specifically for durable contract/evidence graphs, dependency-aware invalidation, and human-timescale checkpoint protocols. Update `NOV-01` only with source-level evidence.
3. Decide whether the local-recovery/tightness pair is sufficiently differentiated for the workshop papers or should be framed solely as an adaptation/analysis tool.
4. Pre-register the exact operational definition of effective horizon and the condition-by-horizon estimand before confirmatory runs.
5. After Experiment, reconcile every manuscript sentence against generated evidence and downgrade or remove claims that miss the frozen gate.

### Experiment

1. Implement objective graders and task generators independently of condition prompts for at least two task families.
2. Implement C0–C3, C1+V, and C2-extra behind the single runner; match model, tools, information, and token/call budgets.
3. Run grader leakage, contamination, and fault-injector tests; then a small pilot used only for variance and engineering failures.
4. Freeze prompts, model versions, decoding, task seeds, budgets, stopping rules, exclusions, and analysis hashes at a Main checkpoint.
5. Execute the confirmatory matrix with complete JSONL/transcript/artifact logs and paired instance analysis.
6. Generate tables directly from evidence; report negative or null horizon interactions without post-hoc reframing.

## Release boundary

- Local structure/tests/recovery/PDF builds are clean for this v5.6.33 restructuring pass.
- No external submission or registration was performed; venue-specific final checks and submission remain human-controlled.
