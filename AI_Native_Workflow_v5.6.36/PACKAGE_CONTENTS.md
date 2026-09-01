# Package Contents and Responsibilities

## `.ai-workflow/` — operative runtime

The only directory passed to Main and coding-agent Orchestrators in normal project use.

| Path | Purpose |
|---|---|
| `.ai-workflow/aw.py` | Short CLI entry point. |
| `.ai-workflow/aw/` | Deterministic hierarchy, evidence, recovery, impact-cone, CLI, and demo implementation. |
| `.ai-workflow/docs/` | Machine-facing role, prompting, routing, research, and execution guidance. |
| `.ai-workflow/aw/templates/` | DIC and bounded execution-prompt templates. |
| `.ai-workflow/tests/` | Runtime, recovery, prompt-policy, and deterministic-demo tests. |
| `.ai-workflow/package.json` | Runtime capabilities and version catalogue. |
| `.ai-workflow/config.toml` | Repository-local default configuration. |


## `runtime_release/` — deployable runtime archive

Contains `AI_WORKFLOW_RUNTIME_v5.6.36.zip`, whose top-level member is exactly `.ai-workflow/`. This is the convenient artifact to unzip/copy into a target repository.

## `submissions/who_verifies/` — workshop submission storage

Contains the four-page anonymous demo paper, LaTeX source, OpenReview metadata, checklist, cleaned anonymous `.ai-workflow` supplement, and a single workshop-submission bundle ZIP. This directory is not loaded into ordinary target-project agents.

## `submissions/neurips_education/` — Education Track preparation

Contains the official-requirement summary, concept positioning, learning objectives, linked-paper shortlist, materials checklist, and a compact teaching-materials starter ZIP for a future single-blind Education Track submission.

## `slides/` — teaching-material development

Contains the NeurIPS Education slide plan, modular timing cuts, visual/interaction notes, and teaching-material plan. It is development storage, not operative workflow state.

## `research/` — workflow R&D records

Contains the enhancement audit and the official prompting source lock. Research recommendations remain advisory until Main records a binding decision in a Phase/DIC.

## `technical_report/` — report amendment notes

Contains a concise update note identifying role and runtime wording that should remain synchronized with the technical report. The full historical technical report remains part of the source tracking archive, not the installed runtime.

## `source_tracking/` — provenance

Records the attached source tracking archive and the supplied Who Verifies artifacts used in this reconstruction. This section is for package-development provenance only.
