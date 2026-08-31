# Leakage audit


All official tests, solutions, and checkpoints 2-8 are physically isolated
under `qualification/private_eval/`.  The initial repository exposes only
checkpoint 1 and legitimate project files.  The harness enforces the frozen
state-loss boundary after accepted checkpoint 4 and before checkpoint 5.
