# Minor continuation notes — v5.6.33

These notes are a **delta on top of v5.6.33**, not a new redesign specification.

## 1. Treat v5.6.33 as the architectural baseline

Do **not** repeat the earlier Plan/Phase/DIC/EPS restructuring unless a concrete correctness problem is found.

The canonical hierarchy is already:

```text
Goal
→ Plan
→ Phase
→ one multi-view DIC package
→ EPS
→ Prompt/Run
→ Action
```

The package already has:
- package-state authority in `.ai-workflow/STATE.json`;
- Main / Theory / Experiment as canonical persistent workstreams;
- human governance at Plan plus periodic/material checkpoints;
- multi-view DIC packages;
- `DIC/PLAN.md` as the durable prompt/dependency/parallel-subagent graph;
- EPS as disposable JIT instantiation;
- mandatory compact `reports/`;
- venue-specific Meta-Agents / Who Verifies / conditional AutoMLR drafts.

Any next session should therefore **continue from the current package**, not reconstruct these mechanisms from scratch.

## 2. Important terminology note

The earlier intuition that “DICs are the smaller steps” has been refined in v5.6.33.

There is normally **one DIC package per Phase**.

Within that package:
- `DIC/README.md` gives orientation;
- `DIC/REQUESTS.md` contains the smaller goals / requirements to resolve;
- `DIC/PLAN.md` contains the durable execution graph and may contain 10–100+ prompt/run nodes;
- EPS creates the actual JIT prompt/run instances for the current attempt.

Therefore, do not create `DIC-01`, `DIC-02`, `DIC-03` merely to represent sequential work inside one Phase. Use Requests and Plan nodes instead.

## 3. Keep human governance coarse

Stable prompt IDs, EPS attempts, repairs, and local verification are machine coordination events, not human approval boundaries.

The intended human pattern remains approximately:

```text
approve Plan
→ several ordinary Phases execute
→ review every ~5–10 Phases
→ immediate review only on material escalation
```

The runtime default and the completed research Plan use checkpoint intervals in this range. Do not add per-prompt or per-EPS human approval.

## 4. The completed research-upgrade Plan should remain historical

`.ai-workflow/STATE.json` currently records `plan-hierarchical-research-upgrade` as complete.

Do not reopen its completed Phase statuses just to continue research.

For substantial new work, create a **new continuation Plan** whose phases are larger scientific milestones. A sensible continuation is approximately:

1. Theory/novelty strengthening;
2. confirmatory Experiment programme;
3. Main publication integration.

The number of prompts inside those Phases may be large; that is what `DIC/PLAN.md` is for.

## 5. Theory: strengthen, do not restart

The current package already contains a nontrivial formal base.

The strongest surviving mechanism-specific result is the dependency-local recovery / worst-case-tightness pair, supported by:
- conditional verifier-miss bounds;
- checkpoint-cost analysis;
- an evidence-aliasing observability limitation.

The next Theory session should primarily:
- audit assumptions line by line;
- test the results against hidden state, stochastic tools, evidence versions, and imperfect observability;
- verify nearest-neighbour novelty against current primary literature;
- decide which results belong in the papers as genuine contributions versus analytical adaptations;
- patch the technical report and manuscripts directly.

Do not spend the session re-deriving definitions that are already stable unless an audit finds a problem.

## 6. Experiment is now the largest evidence gap

The package has **55 conformance tests**, but these validate runtime/package semantics rather than comparative language-agent performance.

No large confirmatory study has yet been completed.

The Experiment session should therefore receive most of the next empirical effort.

Priority:
1. objective graders and task generators;
2. condition implementation and leakage/contamination checks;
3. small pilot only for engineering/difficulty calibration;
4. protocol freeze;
5. confirmatory C0/C1/C2/C3-style runs plus matched-budget controls;
6. horizon interaction and fault-localization/recovery analysis;
7. direct evidence-to-table/figure generation.

Keep smoke, pilot, confirmatory, and post-hoc evidence explicitly separate.

## 7. Current research targets and Pro continuation

The next comprehensive GPT-5.6 Pro Main run should use `PRO_RESEARCH_CONTINUATION_PROMPT.md`.

Active research targets are now only:

- **Meta-Agents** — maintain and strengthen the existing research manuscript as the primary system/theory paper; the listed workshop submission time has passed, so do not treat this as a deadline-rush external submission task.
- **AutoMLR** — treat as a conditional scientific-eligibility route. The current package does not yet contain a qualifying autonomous ML research result; the next run should decide whether the selected empirical programme could become that result.

`submissions/who_verifies/` is retained as a historical artifact. Do not allocate new research effort to it unless the human explicitly reactivates that target.

The highest-priority output is now a **single decided experiment programme**, not additional paper variants. The Pro run must choose exact task families, conditions, model stacks, budgets/run counts, fault injections, primary metrics, freeze rules, analysis, and validity/eligibility gates and store that decision in the package.

## 8. Main / Theory / Experiment remain the only normal persistent workstreams

Do not reintroduce role proliferation.

Use:
- **Main** for authority, integration, architecture, report/paper reconciliation;
- **Theory** for formal/conceptual/literature/novelty work;
- **Experiment** for empirical methodology, implementation delegation, execution and statistics.

Research, orchestration and local verification are capabilities/lanes, not reasons to create additional persistent chats by default.

Codex / Claude Code are execution tools rather than separate sources of project authority.

## 9. Suggested model use for the continuation

- **Theory:** GPT-5.6 XHigh.
- **Experiment:** GPT-5.6 Pro, delegating code/runs to Codex and Claude Code where useful.
- **Main final integration:** return to the persistent GPT-5.6 Pro Main context when possible.
- **Claude Opus:** one compact hostile checkpoint after material Theory + Experiment evidence, not continuous re-verification.

## 10. Package authority and claim discipline

The package remains the source of truth.

A fresh session should begin with:

1. `00_READ_FIRST.md`
2. `NEXT_RUN_NOTES.md`
3. `MAIN_REPORT.md`
4. `.ai-workflow/STATE.json`
5. `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md`
6. the relevant Phase DIC/reports
7. `research/CLAIM_LEDGER.json`
8. `experiments/EXPERIMENT_HANDOFF.md`
9. relevant manuscript sources.

If chat recollection conflicts with package state, package state wins unless the human explicitly overrides it.

Do not:
- present planned experiments as completed;
- turn conformance tests into performance evidence;
- inflate established systems ideas into foundational theorem novelty;
- silently change frozen empirical protocols;
- perform external submission, paid compute, credential/private-system actions, or release changes without human authorization.
