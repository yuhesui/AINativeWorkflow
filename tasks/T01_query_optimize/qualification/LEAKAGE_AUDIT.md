# Leakage audit


The agent repository contains the immutable SQLite database, task prompt, and
an editable `query.sql`.  Official tests, golden query, solution script,
baseline timing lock, and continuous-scoring implementation are physically
outside `test_repo/` under `qualification/private_eval/`.  A recursive
sensitive-name/content scan found no expected-answer or reference-solution
material in the agent workspace.  Direct materialization removes
`.ai-workflow/`; AI-Native materialization retains it.
