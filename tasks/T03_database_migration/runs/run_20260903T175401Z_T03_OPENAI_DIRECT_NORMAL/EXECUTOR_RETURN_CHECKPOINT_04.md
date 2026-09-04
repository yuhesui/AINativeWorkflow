# Checkpoint evidence

```json
{
  "capture_mode": "durable_workspace_and_session_metadata",
  "checkpoint": 4,
  "condition": "DIRECT",
  "grader": {
    "accepted_for_next_reveal": true,
    "checkpoint": 4,
    "checkpoint_primary_score": 86.20689655172413,
    "checkpoint_total": 5,
    "core_pass_rate": 0.6666666666666666,
    "graded_utc": "2026-09-04T05:12:20.377380+00:00",
    "grader_ok": true,
    "isolated_pass_rate": 0.8,
    "run_id": "run_20260903T175401Z_T03_OPENAI_DIRECT_NORMAL",
    "schema_version": 1,
    "strict_pass_rate": 0.8620689655172413,
    "task_completion": "INCOMPLETE_CHECKPOINTS",
    "task_id": "T03"
  },
  "latest_executor_session": {
    "cli_version": "codex-cli 0.152.1",
    "ended_utc": "2026-09-04T05:11:44.132199+00:00",
    "execution_mode": "DIRECT_CLI_GOAL_RESUME",
    "executor": "CODEX",
    "executor_effort": "xhigh",
    "executor_model_product_visible": "gpt-5.6-terra",
    "executor_prompt": "D:\\Projects\\AI Native Workflow\\tasks\\T03_database_migration\\runs\\run_20260903T175401Z_T03_OPENAI_DIRECT_NORMAL\\DIRECT_GOAL_CHECKPOINT_04.md",
    "executor_prompt_sha256": "b9999972f5d8ffeb6edba507ea8b5778e9335936f6fffe73061c53623bb8da73",
    "handoff_id": null,
    "process_exit_code": 0,
    "run_id": "run_20260903T175401Z_T03_OPENAI_DIRECT_NORMAL",
    "schema_version": 1,
    "session_id": "20260904T051148Z-direct-04",
    "source_bundle": null,
    "started_utc": "2026-09-03T19:09:46.301120+00:00",
    "usage": {
      "api_equivalent_cost_estimate": {
        "actual_incremental_charge_known": false,
        "billable_tokens_used": {
          "cache_creation_input": 0,
          "cached_input": 3607040,
          "output": 25177,
          "uncached_input": 68275
        },
        "components": {
          "cache_creation_input_usd": 0.0,
          "cached_input_usd": 0.721408,
          "output_usd": 0.302124,
          "uncached_input_usd": 0.13655
        },
        "estimated_cost_usd": 1.160082,
        "kind": "standard_api_equivalent",
        "long_context_surcharge_included": false,
        "model_pricing_key": "gpt-5.6-terra",
        "notes": "API-equivalent estimate only; subscription usage may have no incremental dollar charge. Aggregate token summaries cannot determine per-request long-context pricing. Reasoning tokens are already included in output tokens and are not added again.",
        "pricing_snapshot_utc": "2026-09-02",
        "pricing_source": "https://developers.openai.com/api/docs/models/gpt-5.6-terra",
        "rates_usd_per_million_tokens": {
          "cache_creation_input": 2.5,
          "cached_input": 0.2,
          "output": 12.0,
          "uncached_input": 2.0
        }
      },
      "cached_input_tokens": 3607040,
      "input_tokens": 68275,
      "output_tokens": 25177,
      "reasoning_tokens": 11337,
      "total_tokens": 93452
    },
    "usage_source": "operator_transcription",
    "wall_seconds": 36129.151604
  },
  "note": "The interactive CLI final response is not separately captured; the surviving workspace and session metadata are authoritative."
}
```
