# Build and release status - v5.6.37

Generated: 2026-09-03

## PDFs

| Artifact | Pages | Status |
|---|---:|---|
| `AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.pdf` | 18 | rebuilt; render inspected |
| `submissions/meta_agents/main.pdf` | 7 | Full Paper; ~5 main-text pages; render inspected |
| `submissions/who_verifies/main.pdf` | 4 | retained demo-paper artifact |
| `submissions/automlr/main.pdf` | 3 | retained conditional scaffold |

## Runtime validation

- Current suite: **17 passed**.
- `aw.py validate`: **ok**, schema `5.6.37`, no errors/warnings.
- Package-only recovery: **ok**, schema `5.6.37`, no errors/warnings.
- Deterministic demo: `repair -> accept`; DIC stable across attempts.

## Conceptual consolidation

- Practical target: lower **human attention required per unit of verified research progress**.
- DIC is both machine contract and human-intelligibility interface.
- Primary Aim and salience rules resist constraint-objective inversion / defensive drift and salience flattening.
- No empirical attention-efficiency gain is claimed.

## Release blockers

- None from local runtime tests, recovery, or current PDF build.
- External submission still requires human confirmation and live venue-specific checks.
