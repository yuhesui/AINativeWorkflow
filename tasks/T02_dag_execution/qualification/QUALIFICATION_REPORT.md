# Qualification report

Status: **QUALIFIED**


The official final checkpoint-3 reference implementation ran and parsed: 49
passed, 2 failed; strict pass rate 49/51 (0.960784...), core 3/3, isolated
10/10.  The same two failures (`test_branch_if` and
`test_stderr_validation`) occur in the official checkpoint-1 reference (31
passed, 2 failed), so this is a frozen upstream oracle defect rather than
checkpoint erosion.  No benchmark semantics or grader were changed.  The
environment is qualified with that explicit caveat; raw reports for both
checkpoints are retained under `oracle_runs/`.
