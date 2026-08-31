# CONFIGURATION.md — v5.6.35 Configuration

The canonical hierarchical runtime stores Plan/Phase policy in `.ai-workflow/STATE.json`. `.ai-workflow/config.toml` also exposes compatible defaults for repository-local tooling.

## Phase lanes

```toml
[phase_lanes]
minor = "auto"
research = "auto"
verification = "auto"
checkpoints = "auto"
```

Allowed values:

- `off` — prohibit the lane for that Phase;
- `auto` — lazy default; do not create until first needed;
- `on` — materialize/maintain from Phase start.

`reports` is not a toggleable lane.

## DIC views

```toml
[dic_views]
readme = "on"
requests = "on"
plan = "on"
architecture = "auto"
test_matrix = "auto"
allow_custom = true
```

`README`, `REQUESTS`, and `PLAN` are the core views of one DIC package. `ARCHITECTURE` and `TEST_MATRIX` may be materialized when relevant. Users may add arbitrary flat custom Markdown DIC views.

## Reports

```toml
[reports]
policy = "compact_raw"
flat = true
max_files = 10
max_summary_files = 10   # compatibility alias
include_key_raw_results = true
```

The runtime rejects nested directories under the canonical Phase `reports/` surface and enforces the default file cap. Raw report surfaces should preserve underlying values/results with provenance rather than silently summarize them.

## Checkpoint cadence

The hierarchical runtime default is 7 completed ordinary Phases. This is normally configured at Plan creation and is expected to be roughly 5–10 for long research programmes unless there is a reason to use another value.
