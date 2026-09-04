# Direct checkpoint evidence

```json
{
  "capture_mode": "durable_workspace_and_session_metadata",
  "checkpoint": 1,
  "grader": {
    "accepted_for_next_reveal": true,
    "checkpoint": 1,
    "checkpoint_primary_score": 100.0,
    "checkpoint_total": 5,
    "core_pass_rate": 1.0,
    "graded_utc": "2026-09-03T18:19:03.195750+00:00",
    "grader_ok": true,
    "isolated_pass_rate": 1.0,
    "run_id": "run_20260903T175401Z_T03_OPENAI_DIRECT_NORMAL",
    "schema_version": 1,
    "strict_pass_rate": 1.0,
    "task_completion": "INCOMPLETE_CHECKPOINTS",
    "task_id": "T03"
  },
  "latest_executor_session": {
    "cli_version": "codex-cli 0.152.1",
    "ended_utc": "2026-09-03T18:18:43.681144+00:00",
    "execution_mode": "DIRECT_CLI_GOAL",
    "executor": "CODEX",
    "executor_effort": "xhigh",
    "executor_model_product_visible": "gpt-5.6-terra",
    "executor_prompt": "D:\\Projects\\AI Native Workflow\\tasks\\T03_database_migration\\runs\\run_20260903T175401Z_T03_OPENAI_DIRECT_NORMAL\\DIRECT_GOAL.md",
    "executor_prompt_sha256": "78f37e3cd9d003949bfd90336fbfae849f1a81ac06a912a9988de6b2c1a8f405",
    "handoff_id": null,
    "process_exit_code": 0,
    "run_id": "run_20260903T175401Z_T03_OPENAI_DIRECT_NORMAL",
    "schema_version": 1,
    "session_id": "20260903T181849Z-direct-01",
    "source_bundle": null,
    "started_utc": "2026-09-03T17:54:06.661654+00:00",
    "usage": {
      "api_equivalent_cost_estimate": {
        "actual_incremental_charge_known": false,
        "billable_tokens_used": {
          "cache_creation_input": 0,
          "cached_input": 1263616,
          "output": 25375,
          "uncached_input": 68650
        },
        "components": {
          "cache_creation_input_usd": 0.0,
          "cached_input_usd": 0.2527232,
          "output_usd": 0.3045,
          "uncached_input_usd": 0.1373
        },
        "estimated_cost_usd": 0.6945232,
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
      "cached_input_tokens": 1263616,
      "input_tokens": 68650,
      "output_tokens": 25375,
      "reasoning_tokens": 12867,
      "total_tokens": 94025
    },
    "usage_source": "operator_transcription",
    "wall_seconds": 1477.024824
  },
  "note": "The interactive CLI final response is not separately captured."
}
```
