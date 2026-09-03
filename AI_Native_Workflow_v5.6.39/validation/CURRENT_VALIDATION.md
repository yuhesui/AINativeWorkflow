# Current Validation — AI Native Workflow v5.6.39

**Date:** 3 September 2026  
**Status:** release candidate validated

## Runtime

- **19/19 runtime/documentation/template tests passed**.
- `python .ai-workflow/aw.py validate`: `ok=true`, schema `5.6.39`, no errors or warnings.
- `python .ai-workflow/aw.py recover`: `ok=true`, schema `5.6.39`, no errors or warnings.
- Fresh Phase scaffold test confirms creation of root `phases/<phase_id>/` with `DIC/`, `EPS/`, `reports/`, `results/`, `evidence/`, `artifacts/`, and `logs/` plus the human-facing Phase summary/evidence manifest.
- Main-authored initial EPS persistence test passes, including EPS manifest/prompt materialization and `ORCHESTRATOR_START.md`.
- Safe `aw phase import <zip>` test passes: required DIC views and `PHASE_MANIFEST.json` are validated, unsafe paths/symlinks are rejected by the importer, the Phase is registered into `STATE.json`, and fresh recovery succeeds.
- Deterministic demo remains `repair -> accept`; one stable DIC across two EPS attempts; changed key `normalized`; declared downstream impact cone `experiment, table, paper, release`; unaffected `collect` and `theory` retained; fresh recovery succeeds at schema `5.6.39`.

## Documentation

- Technical report: **59 pages**, A4, detailed long-form reference.
- Technical-report source: **2002 lines**.
- Detailed workflow guide: **1968 lines**.
- NeurIPS Education slide plan: **20-slide, 18–20 minute prepared plan**, with explicit ~15-minute and emergency cuts.
- Presenter in the Education plan: **Yuhe Sui, Quantitative Research Society @ NTU**.

## Current semantic boundary

- Main authors one whole-Phase DIC **and the initial EPS/prompt graph**.
- `DIC/PLAN.md` remains the durable semantic/dependency graph.
- The initial EPS is Main's first executable prompt graph.
- Orchestrator validates and compiles/model-tunes those prompts for the actual execution model/surface, schedules/executes Workers/subagents, integrates evidence, and may issue bounded superseding repair EPS revisions under the unchanged DIC.
- A material change to Primary Aim, scientific method, acceptance, or authority returns to Main rather than becoming an execution-local repair.

## Phase evidence surface

Default Phase material is project-local at root `phases/<phase_id>/`.

- `reports/PHASE_SUMMARY.md`: compact current human-readable state.
- `reports/FINAL_HANDOFF.md`: required at terminal handoff.
- `results/KEY_RESULTS.json`: required when key findings are naturally structured.
- `results/KEY_RESULTS.csv`: used when a tabular representation is natural.
- `evidence/EVIDENCE_MANIFEST.json`: machine-readable index of decisive evidence and lineage.
- raw logs/artifacts remain separate from human-facing reports.

## Submission surfaces

- **Meta-Agents:** Full Paper; current rendered draft **7 physical pages**; semantics updated to Main-authored initial EPS.
- **NeurIPS Education:** updated full AI Native Workflow for Research slide plan and starter; embedded runtime version `5.6.39`.
- **Who Verifies:** retained as a frozen demo-paper artifact rather than silently rewritten.

## Claim boundary

- Human-attention intensity is an **evaluation target**, not an already demonstrated empirical advantage.
- Constraint–objective inversion/defensive drift and salience flattening are workflow failure modes/design motivations, not universal empirical laws of LLMs.
- The deterministic repair demo is structural/runtime evidence, not comparative agent-performance evidence.
- No external submission, public release, paid action, credentialed action, or repository push was performed by this build.
