# Controlled experiment package

The experiment directory is ready for a dedicated Experiment workstream but contains no confirmatory agent-performance result. Start with `FROZEN_CANDIDATE_PROTOCOL.md`, `EXPERIMENT_HANDOFF.md`, and `config/frozen_candidate.json`.

`runner.py` is a condition-neutral record-and-validation harness. Plug condition adapters into `adapters/` and task families into `tasks/`; do not fork separate runners whose logging differs. Every run writes one schema-compatible JSON record and artifact hashes. `task_graph_generator.py` creates dependency graphs without model calls. `analyse.py` produces descriptive paired summaries and, when optional scientific Python dependencies are installed, a declared condition-by-horizon model.

Evidence levels are `smoke`, `pilot`, `confirmatory`, and `post_hoc`. Only the dedicated Experiment workstream may move the protocol from candidate to frozen after grader leakage and budget checks.
