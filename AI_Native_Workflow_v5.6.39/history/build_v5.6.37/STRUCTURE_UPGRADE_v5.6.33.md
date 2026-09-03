# v5.6.33 Phase/DIC/EPS restructuring validation

This pass changes the package architecture rather than the scientific objective.

## Adopted semantics

- One multi-view DIC package per Phase.
- `README.md`: general summary/orientation.
- `REQUESTS.md`: specific goals/requirements.
- `PLAN.md`: durable execution plan containing prompt IDs, dependencies, parallel/subagent batches, merge points and conditional branches.
- `ARCHITECTURE.md`: target repository/system architecture when changed.
- `TEST_MATRIX.md`: actual software/experiment/theory-audit matrices.
- Registered custom flat Markdown DIC views are allowed.
- EPS is disposable/JIT and instantiates/refines DIC/PLAN nodes for the current state/attempt.
- Optional lanes `minor`, `research`, `verification`, `checkpoints` support `off|auto|on`.
- `reports/` is mandatory, flat, and capped at 10 files by default; it includes human synthesis plus losslessly merged key raw results.

## Migration

The nine completed v5.6.32 Phase records were migrated structurally. Since the older runtime stored only coarse execution nodes for those Phases, the migration preserves those recorded nodes and marks their plans as reconstructed; it does not fabricate a detailed historical 10-100-prompt graph. Future Phases use the richer plan graph natively.

## Validation

- 55 tests passed.
- Package-only recovery: ok, schema 5.6.33.
- Nine Phase report surfaces validated as flat and <=10 files.
- Technical report and all three workshop manuscript/scaffold PDFs rebuilt after source synchronization.
