# GUIDE.md — Machine Operating Summary

1. Copy `.ai-workflow/` into the repository.
2. Run `aw init` with mode, levels, routing, available models/surfaces and optional first phase.
3. Run `aw status --full`, `aw models show` and `aw validate`.
4. Main completes `GOAL.md` in Goal Mode or the full pack in Structured Mode.
5. Record exact approval with `aw go`; do not ask again.
6. Orchestrator uses `aw next`, complete templates and the model-routing config.
7. Worker executes one bounded prompt and reports checks/evidence.
8. Orchestrator integrates; Verifier alone passes gates and completes requests.
9. After config/root/model changes, run `aw update` and `aw validate`.
10. Close with independent verification and a durable handoff.

Read the role guide and selected execution-level guide before acting. The long human guides explain
rationale; machine behavior is governed by package/config, active phase contracts and these role
documents.
