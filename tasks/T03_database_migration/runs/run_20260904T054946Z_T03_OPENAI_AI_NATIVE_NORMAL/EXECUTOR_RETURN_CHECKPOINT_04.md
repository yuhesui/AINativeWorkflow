# Checkpoint evidence

```json
{
  "capture_mode": "durable_workspace_and_session_metadata",
  "checkpoint": 4,
  "condition": "AI_NATIVE",
  "grader": {
    "accepted_for_next_reveal": true,
    "checkpoint": 4,
    "checkpoint_primary_score": 79.3103448275862,
    "checkpoint_total": 5,
    "core_pass_rate": 0.3333333333333333,
    "graded_utc": "2026-09-04T09:00:46.537590+00:00",
    "grader_ok": true,
    "isolated_pass_rate": 0.5333333333333333,
    "run_id": "run_20260904T054946Z_T03_OPENAI_AI_NATIVE_NORMAL",
    "schema_version": 1,
    "strict_pass_rate": 0.7931034482758621,
    "task_completion": "INCOMPLETE_CHECKPOINTS",
    "task_id": "T03"
  },
  "latest_executor_session": {
    "cli_version": "codex-cli 0.152.1",
    "ended_utc": "2026-09-04T09:00:04.263225+00:00",
    "execution_mode": "AI_NATIVE_CLI_GOAL_RESUME",
    "executor": "CODEX",
    "executor_effort": "xhigh",
    "executor_model_product_visible": "gpt-5.6-terra",
    "executor_prompt": "D:\\Projects\\AI Native Workflow\\tasks\\T03_database_migration\\runs\\run_20260904T054946Z_T03_OPENAI_AI_NATIVE_NORMAL\\AI_NATIVE_GOAL_CHECKPOINT_04.md",
    "executor_prompt_sha256": "47699759fba5ccb339083f3b85076f25a02aaf26edcfe7c365bb8a85646123bd",
    "handoff_id": null,
    "process_exit_code": 0,
    "run_id": "run_20260904T054946Z_T03_OPENAI_AI_NATIVE_NORMAL",
    "schema_version": 1,
    "session_id": "20260904T090005Z-direct-03",
    "source_bundle": null,
    "started_utc": "2026-09-04T08:45:27.468521+00:00",
    "usage": {
      "api_equivalent_cost_estimate": {
        "actual_incremental_charge_known": false,
        "billable_tokens_used": {
          "cache_creation_input": 0,
          "cached_input": 3010560,
          "output": 20017,
          "uncached_input": 72235
        },
        "components": {
          "cache_creation_input_usd": 0.0,
          "cached_input_usd": 0.602112,
          "output_usd": 0.240204,
          "uncached_input_usd": 0.14447
        },
        "estimated_cost_usd": 0.986786,
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
      "cached_input_tokens": 3010560,
      "input_tokens": 72235,
      "output_tokens": 20017,
      "reasoning_tokens": 6984,
      "total_tokens": 92252
    },
    "usage_source": "operator_transcription",
    "wall_seconds": 876.790327
  },
  "note": "The interactive CLI final response is not separately captured; the surviving workspace and session metadata are authoritative."
}
```
