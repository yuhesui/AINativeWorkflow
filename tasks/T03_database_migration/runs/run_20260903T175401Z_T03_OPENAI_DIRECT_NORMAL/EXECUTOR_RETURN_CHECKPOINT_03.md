# Direct checkpoint evidence

```json
{
  "capture_mode": "durable_workspace_and_session_metadata",
  "checkpoint": 3,
  "grader": {
    "accepted_for_next_reveal": true,
    "checkpoint": 3,
    "checkpoint_primary_score": 88.37209302325581,
    "checkpoint_total": 5,
    "core_pass_rate": 1.0,
    "graded_utc": "2026-09-03T19:09:43.898297+00:00",
    "grader_ok": true,
    "isolated_pass_rate": 1.0,
    "run_id": "run_20260903T175401Z_T03_OPENAI_DIRECT_NORMAL",
    "schema_version": 1,
    "strict_pass_rate": 0.8837209302325582,
    "task_completion": "INCOMPLETE_CHECKPOINTS",
    "task_id": "T03"
  },
  "latest_executor_session": {
    "cli_version": "codex-cli 0.152.1",
    "ended_utc": "2026-09-03T19:09:19.778669+00:00",
    "execution_mode": "DIRECT_CLI_GOAL_RESUME",
    "executor": "CODEX",
    "executor_effort": "xhigh",
    "executor_model_product_visible": "gpt-5.6-terra",
    "executor_prompt": "D:\\Projects\\AI Native Workflow\\tasks\\T03_database_migration\\runs\\run_20260903T175401Z_T03_OPENAI_DIRECT_NORMAL\\DIRECT_GOAL_CHECKPOINT_03.md",
    "executor_prompt_sha256": "b9999972f5d8ffeb6edba507ea8b5778e9335936f6fffe73061c53623bb8da73",
    "handoff_id": null,
    "process_exit_code": 0,
    "run_id": "run_20260903T175401Z_T03_OPENAI_DIRECT_NORMAL",
    "schema_version": 1,
    "session_id": "20260903T190921Z-direct-03",
    "source_bundle": null,
    "started_utc": "2026-09-03T18:54:17.771044+00:00",
    "usage": {
      "api_equivalent_cost_estimate": {
        "actual_incremental_charge_known": false,
        "billable_tokens_used": {
          "cache_creation_input": 0,
          "cached_input": 2906112,
          "output": 33685,
          "uncached_input": 63853
        },
        "components": {
          "cache_creation_input_usd": 0.0,
          "cached_input_usd": 0.5812224,
          "output_usd": 0.40422,
          "uncached_input_usd": 0.127706
        },
        "estimated_cost_usd": 1.1131484,
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
      "cached_input_tokens": 2906112,
      "input_tokens": 63853,
      "output_tokens": 33685,
      "reasoning_tokens": 15403,
      "total_tokens": 97538
    },
    "usage_source": "operator_transcription",
    "wall_seconds": 902.005041
  },
  "note": "The interactive CLI final response is not separately captured."
}
```
