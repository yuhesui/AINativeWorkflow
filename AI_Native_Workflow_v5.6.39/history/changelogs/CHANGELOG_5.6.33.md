# 5.6.33 Phase-structure refinement

v5.6.33 preserves the v5.6.32 Plan-level governance simplification while restoring the richer machine execution resolution needed for phases that routinely span 10–100+ prompts.

## Main changes

- The canonical hierarchy is now **Goal → Plan → Phase → DIC → EPS → Prompt/Run → Action**.
- A Phase has **one multi-view DIC package**, not many sequential DICs.
- Required DIC views are `README.md`, `REQUESTS.md`, and `PLAN.md`.
- `DIC/PLAN.md` is explicitly the durable execution graph: prompt IDs, dependencies, parallel subagents, merges and conditional repair/review branches.
- `ARCHITECTURE.md` means the target repository/system architecture when changed.
- `TEST_MATRIX.md` means concrete software/theory/experiment matrices or batches.
- Users may add arbitrary flat custom DIC Markdown views.
- EPS is the disposable JIT instantiation of durable Plan nodes against current state/model/context/attempt.
- `minor`, `research`, `verification`, and `checkpoints` support `off | auto | on`; `auto` is lazy.
- `reports/` is always present, must be flat, and is limited to 10 files by default.
- Reports explicitly include key merged raw results as well as human-readable synthesis. Merged raw means lossless collation plus provenance rather than aggregation or paraphrase.
- The nine existing v5.6.32 runtime phases were migrated into the new `DIC/`, `EPS/`, and `reports/` structure without inventing historical prompt detail that was not recorded.
- Hierarchy and compatibility tests were expanded to cover DIC views, custom views, parallel EPS nodes, lazy lanes and report invariants.

The older Goal/Structured `aw.py` surface remains available for compatibility, but `.ai-workflow/STATE.json` and `.ai-workflow/runtime/plans/...` are canonical for new long-horizon work.
