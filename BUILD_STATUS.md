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

- representative AI-Native runtime v5.6.36 tests: 17/17 passed under UTF-8 mode;
- seven clean runtime trees byte-identical, hash
  `9e1cad74da9c6495ea555e65dab75e8443418964d8a1dcfecdda50f592919798`;
- Direct and AI-Native non-scored materialization and leakage checks passed;
- progressive reveal, checkpoint and research-task state-loss snapshots passed;
- full-final-repository archive and separate raw/metric result attachment passed;
- task/environment lock checks and `scripts/validate_repo.py` passed;
- no valid Main handoff import, executor session, finalization, score, or executed scored
  trajectory exists. One older Direct materialization is explicitly
  `INVALIDATED_PRE_TRAJECTORY`; one operator-created AI-Native materialization
  remains `AWAITING_MAIN`. Both preserve their audit metadata.

See `SETUP_REPORT.md` for exact evidence and blockers and
`READY_FOR_SCORED_RUNS.md` for the human/Main operational loop.
