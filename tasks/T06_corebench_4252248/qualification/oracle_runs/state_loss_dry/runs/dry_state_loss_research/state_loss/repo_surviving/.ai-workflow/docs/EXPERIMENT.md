# EXPERIMENT.md — Experiment Workstream Guide

Experiment owns empirical methodology, benchmark/task design, implementation delegation, frozen protocols, statistics and evidence.

Useful DIC views include `TEST_MATRIX.md`, `EXPERIMENT_PROTOCOL.md`, `DATA_CONTRACT.md`, and `GRADER_SPEC.md`. The execution Plan should state condition batches, dependencies, parallel runs/subagents, integration/statistical analysis nodes and failure/repair branches.

After protocol freeze, consider `minor=off` if apparently small changes could contaminate the study. Use `verification=auto` or `on` according to evidence materiality.

`reports/` should include a concise report and key merged raw run/grader/metric surfaces; full run archives remain in `logs/`/`evidence/`.
