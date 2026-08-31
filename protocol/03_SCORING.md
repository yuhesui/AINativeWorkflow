# Scoring

Primary outcomes must remain native/continuous where possible.

- **T1:** 0–100 score with semantic correctness as a hard prerequisite for optimization credit; final exact formula is locked during environment qualification before scoring.
- **T2–T4:** `100 × strict_pass_rate_mean` as the primary completion score; retain core/isolated pass rate, regression/erosion, checkpoint curves, wall time, and interaction counts.
- **T5:** native held-out MetaMaze reward is primary. Also report delta from frozen baseline, cross-seed variation, reproducibility, and a separately declared 0–100 research-completion diagnostic.
- **T6:** native CORE-Bench graded score/item accuracy is primary; retain reproduction/environment/evidence milestones.
- **T7:** native PaperBench hierarchical rubric percentage is primary; retain Code Development, Code Execution, and Result Analysis components.

For state loss, the key paired quantity is `normal_score - state_loss_score`. Also record duplicated work, retained valid work, recovery latency, contradictions, and unnecessary reruns.
