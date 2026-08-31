# T07_sequential_neural_score_estimation — Internal evaluation capsule

This capsule separates the full upstream benchmark from the actual scored repository and from evaluator/results material.

1. `original_task/` — complete upstream task setup at the frozen revision; provenance copy.
2. `test_repo/` — **actual complete repository used for testing**; `.ai-workflow/` lives directly at this repo root for AI-Native runs.
3. `reference_material/` + `qualification/` — task papers/specifications, oracle/environment checks, hidden evaluator material, leakage audits.
4. `runs/` — one directory per trajectory, including the **complete final subrepo state**.
5. `run_results/` — normalized scores, raw grader output, metrics and recovery summaries.

Direct runs are created from `test_repo/` with `.ai-workflow/` physically removed. AI-Native runs use `test_repo/` as-is and Main creates Plan/Phase/DIC/EPS during the run.
