# AI Native Workflow — Cumulative Changelog

## 5.6.39 — Detailed Documentation and Tracking Reconstruction

- Restored the technical report to long-form reference depth (~58 pages) while preserving v5.6.37 formal theory and attention framing.
- Restored an on-demand detailed guide layer under `.ai-workflow/guides/`; `DETAILED_WORKFLOW_GUIDE.md` is ~1,900 lines.
- Kept compact machine-operational docs under `.ai-workflow/docs/` as the default execution read path.
- Formalized proper-name convention: **AI Native Workflow**; lowercase `AI-native` remains valid as a generic adjective.
- Consolidated root tracking into `CURRENT_STATE.md`, `ROADMAP.md`, and one cumulative `CHANGELOG.md`.
- Moved legacy Main reports, next-run notes, duplicate Quick Starts, per-version changelogs, and old build records into `history/`.
- Preserved one DIC per Phase with Core `README.md`, `REQUESTS.md`, `PLAN.md`; `PLAN.md` explicitly owns durable sequence/dependency/parallelism planning.
- Clarified EPS ownership: Main authors the initial EPS/prompt graph from the approved DIC; the coding-agent Orchestrator validates/model-tunes it, executes bounded subagents, integrates evidence, and may issue bounded repair EPS revisions under the unchanged DIC.
- Retained human-attention intensity, DIC-as-human-interface, Primary Aim, defensive drift, and salience-flattening concepts; expanded their rationale and measurement plans.
- Bumped runtime/schema/package version to 5.6.39.

## 5.6.37 — Human-Attention Framing

- Introduced human attention required per unit of verified research progress as a design/evaluation objective.
- Added constraint-objective inversion / defensive drift and salience flattening.
- Strengthened DIC as a human-intelligibility projection.
- Updated Meta-Agents Full Paper and Education framing.

## 5.6.36 — Main / Orchestrator / Research Clarification

- Clarified Main as persistent planning/decision chat and Orchestrator as coding-agent execution surface.
- Added model-tuned EPS prompt requirement using official-provider-derived guidance.
- Made Research an explicit Main decision-support path.
- Added Who Verifies submission package and NeurIPS Education preparation materials.

## 5.6.33 and earlier

Historical detailed changelogs and migration notes are preserved under `history/changelogs/` and `docs/`. They remain useful provenance but do not override current v5.6.39 architecture.
