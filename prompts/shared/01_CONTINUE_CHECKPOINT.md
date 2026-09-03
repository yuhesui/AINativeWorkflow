Continue the same frozen run in this same Main chat. The attached continuation ZIP is the only
newly authorized checkpoint input. Read `CONTINUATION_CONTEXT.json`, the newly revealed
`CHECKPOINT.md`, `PREVIOUS_EXECUTOR_RETURN.md`, `PREVIOUS_GRADER_SUMMARY.json`, and the complete
`CURRENT_WORKSPACE/` snapshot before deciding the next action.

Do not restart the task, discard accepted work, reveal or infer a later checkpoint, or expose
private evaluation material. Treat the current workspace as authoritative surviving state and the
new checkpoint as cumulative with every previously accepted checkpoint.

For AI-Native, resume the existing approved Goal and Plan from the surviving `.ai-workflow/` state.
Create or advance the next justified Phase or Phases yourself; do not assume that checkpoint number
must equal Phase number. Prefer one coherent next active Phase, one complete DIC, and one
comprehensive just-in-time EPS/executor assignment for all currently revealed work. Return one
downloadable handoff ZIP containing the complete updated workflow overlay needed for import,
including the active Phase/DIC/EPS, exact executor prompt, durable lineage/evidence state, and
`HANDOFF_MANIFEST.json`. Use a new unique `handoff_id` and preserve the frozen run bindings supplied
below.

For Direct, continue from the surviving workspace without using or imitating AI-Native Workflow.
Return one complete ordinary executor handoff ZIP for all currently revealed work, with
`EXECUTOR_PROMPT.md`, `CONTEXT.md`, `RETURN_CONTRACT.md`, and `HANDOFF_MANIFEST.json`.

Tune the executor prompt for the frozen executor/model/effort in `CONTINUATION_CONTEXT.json`. Make
the assignment capable of implementation, cumulative testing, bounded repair, and evidence return
in one executor session where practical. Output only the single handoff ZIP plus a short statement
identifying its filename; do not merely describe the package contents.
