# Leakage audit


Every official test, solution, and checkpoints 2-3 prompt is physically
isolated under `qualification/private_eval/`.  `test_repo/` contains only the
greenfield repository, checkpoint-1 instructions, resource policy, and clean
runtime.  `reveal_checkpoint.py` permits only the immediate next checkpoint
after an accepted cumulative grader record.
