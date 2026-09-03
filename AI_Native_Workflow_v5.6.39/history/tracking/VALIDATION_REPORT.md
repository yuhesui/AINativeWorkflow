# Validation report - v5.6.37

## Runtime

- `python -m unittest discover -s .ai-workflow/tests -v`: **17 passed**.
- `python .ai-workflow/aw.py validate`: **ok=true**, schema `5.6.37`, no errors/warnings.
- `python .ai-workflow/aw.py recover`: **ok=true**, schema `5.6.37`, no errors/warnings.
- Deterministic demo: `repair -> accept`, stable DIC across two EPS attempts, unaffected `collect` and `theory` retained.

## Current semantics checked

- Main / coding-agent Orchestrator boundary is explicit.
- Exactly one DIC per Phase with Core `README.md`, `REQUESTS.md`, `PLAN.md` views.
- DIC/PLAN owns the durable dependency/parallelism/subagent/merge/repair graph.
- Model-executed EPS nodes require prompt-tuning provenance before Actions.
- Primary Aim / priority/salience and human-attention interface guidance is present.
- Human-attention intensity is an evaluation target, not an empirical claim.

## PDFs

- Technical report: **18 pages**, rendered and visually inspected after v5.6.37 update.
- Meta-Agents Full Paper: **7 physical pages**, approximately 5 pages of main text before References; rendered/visually inspected.
- Who Verifies demo paper retained: **4 pages**.
- AutoMLR scaffold retained: **3 pages**.

## Meta-Agents format

Selected **Full Paper**. The current systems/theory draft is comfortably below the 9-page main-text ceiling and contains a responsible-use statement. Demo and position-only formats were not selected as the primary category.

## Release boundary

No external submission, registration, purchase, credentialed action, or public release was performed.
