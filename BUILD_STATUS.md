# Build status - frozen internal evaluation capsules v1.0

Status: **QUALIFIED_WITH_BLOCKERS / NO SCORED RUNS**

The frozen scientific design and T1-T7 identities are unchanged. All seven
capsules now contain populated upstream, test-repository, reference,
qualification, run, and result surfaces. Authoritative revisions and hashes are
in `TASK_SOURCE.json`, per-task `TASK_LOCK.json`, and
`manifests/TASK_LOCK.json`.

Qualified for scored materialization after explicit human authorization: T1,
T2, T3, T4, and T6. T5 and T7 remain `BLOCKED` and must not be scored until the
documented technical blockers are resolved under the frozen protocol.

Validation completed:

- representative AI-Native runtime tests: 55/55 passed under UTF-8 mode;
- seven clean runtime trees byte-identical, hash
  `3ca9872b60db0ab6a8107888529223ab6b380332af7faba9a4f823aca56c0dbd`;
- Direct and AI-Native non-scored materialization and leakage checks passed;
- progressive reveal, checkpoint and research-task state-loss snapshots passed;
- full-final-repository archive and separate raw/metric result attachment passed;
- task/environment lock checks and `scripts/validate_repo.py` passed;
- all scored `runs/` and `run_results/` surfaces are empty of run IDs.

See `SETUP_REPORT.md` for exact evidence and blockers and
`READY_FOR_SCORED_RUNS.md` for the human/Main operational loop.
