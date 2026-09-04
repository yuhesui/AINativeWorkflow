Continue the same frozen run in this same Main chat. This is exactly one Main inference for the
newly revealed cumulative scope. The attached continuation ZIP is the only
authorized checkpoint input. Read `CONTINUATION_CONTEXT.json`, the newly revealed
`CHECKPOINT.md`, `PREVIOUS_EXECUTOR_RETURN.md`, `PREVIOUS_GRADER_SUMMARY.json`, and the complete
`CURRENT_WORKSPACE/` snapshot before deciding the next action.

Do not restart the task, discard accepted work, reveal or infer a later checkpoint, or expose
private evaluation material. Treat the current workspace as authoritative surviving state and the
new checkpoint as cumulative with every previously accepted checkpoint.

For AI-Native, resume the existing approved Goal and Plan from the surviving `.ai-workflow/` state.
Create or advance the next justified Phase or Phases yourself; do not assume that checkpoint number
must equal Phase number. Return the actual complete active Phase package, not an outline or partial
scaffold: the full Phase manifest, all DIC views, the complete initial EPS node graph, one substantive
prompt file for every EPS node, and the Phase `ORCHESTRATOR_START.md` as executor entrypoint. Return
one downloadable handoff ZIP containing the complete updated workflow overlay needed for import,
including durable lineage/evidence state and
`HANDOFF_MANIFEST.json`. Use a new unique `handoff_id` and preserve the frozen run bindings supplied
below.

Tune the executor prompt for the frozen executor/model/effort in `CONTINUATION_CONTEXT.json`. Make
the assignment capable of implementation, cumulative testing, bounded repair, and evidence return
in one executor session where practical. The harness starts the frozen task environment before the
executor opens. In the Orchestrator and EPS prompts, tell the executor to start substantive work
immediately and use `python .evaluation/run_in_env.py exec-self -- <command>` for task commands.
Do not add Docker/WSL/sidecar/model-route preflight or operator-confirmation gates. If a wrapper
command says the sidecar is not running, retry it once with escalated command permission; automatic
approval is enabled for this bridge. Retain its exact output and escalate only if the repeated failure blocks
a current acceptance criterion. Output only the single handoff ZIP plus a short statement
identifying its filename; do not merely describe the package contents.
