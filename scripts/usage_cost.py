#!/usr/bin/env python3
"""Reproducible API-equivalent cost estimates for recorded model usage."""

from __future__ import annotations

from typing import Any


PRICING_SNAPSHOT_UTC = "2026-09-02"
PRICING: tuple[dict[str, Any], ...] = (
    {
        "key": "gpt-5.6-terra",
        "aliases": ("gpt-5.6-terra", "gpt 5.6 terra", "gpt-5.6 terra"),
        "input": 2.00,
        "cached_input": 0.20,
        "cache_creation_input": 2.50,
        "output": 12.00,
        "source": "https://developers.openai.com/api/docs/models/gpt-5.6-terra",
    },
    {
        "key": "gpt-5.6-sol",
        "aliases": ("gpt-5.6-sol", "gpt 5.6 sol", "gpt-5.6 sol"),
        "input": 4.00,
        "cached_input": 0.40,
        "cache_creation_input": 5.00,
        "output": 20.00,
        "source": "https://developers.openai.com/api/docs/models/gpt-5.6-sol",
    },
    {
        "key": "claude-sonnet-5",
        "aliases": ("claude-sonnet-5", "claude sonnet 5", "sonnet 5"),
        "input": 2.00,
        "cached_input": 0.20,
        "cache_creation_input": 2.50,
        "output": 10.00,
        "source": "https://www.anthropic.com/research/claude-sonnet-5",
    },
    {
        "key": "claude-opus-5",
        "aliases": ("claude-opus-5", "claude opus 5", "opus 5"),
        "input": 5.00,
        "cached_input": 0.50,
        "cache_creation_input": 6.25,
        "output": 25.00,
        "source": "https://www.anthropic.com/news/claude-opus-5",
    },
)


def pricing_for_model(model: object) -> dict[str, Any] | None:
    normalized = str(model or "").strip().lower().replace("—", " ")
    for pricing in PRICING:
        if any(alias in normalized for alias in pricing["aliases"]):
            return pricing
    return None


def _number(value: object) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return float(value)
    return 0.0


def estimate_api_equivalent_cost(usage: object, model: object) -> dict[str, Any] | None:
    """Estimate standard API token cost; never claim this is the product charge."""
    if not isinstance(usage, dict) or not usage:
        return None
    pricing = pricing_for_model(model)
    if pricing is None:
        return None

    uncached = _number(usage.get("input_tokens"))
    cached = _number(usage.get("cached_input_tokens"))
    if not cached:
        cached = _number(usage.get("cache_read_input_tokens"))
    cache_creation = _number(usage.get("cache_creation_input_tokens"))
    output = _number(usage.get("output_tokens"))
    components = {
        "uncached_input_usd": uncached * pricing["input"] / 1_000_000,
        "cached_input_usd": cached * pricing["cached_input"] / 1_000_000,
        "cache_creation_input_usd": (
            cache_creation * pricing["cache_creation_input"] / 1_000_000
        ),
        "output_usd": output * pricing["output"] / 1_000_000,
    }
    components = {key: round(value, 8) for key, value in components.items()}
    return {
        "kind": "standard_api_equivalent",
        "model_pricing_key": pricing["key"],
        "pricing_snapshot_utc": PRICING_SNAPSHOT_UTC,
        "pricing_source": pricing["source"],
        "rates_usd_per_million_tokens": {
            "uncached_input": pricing["input"],
            "cached_input": pricing["cached_input"],
            "cache_creation_input": pricing["cache_creation_input"],
            "output": pricing["output"],
        },
        "billable_tokens_used": {
            "uncached_input": int(uncached),
            "cached_input": int(cached),
            "cache_creation_input": int(cache_creation),
            "output": int(output),
        },
        "components": components,
        "estimated_cost_usd": round(sum(components.values()), 8),
        "actual_incremental_charge_known": False,
        "long_context_surcharge_included": False,
        "notes": (
            "API-equivalent estimate only; subscription usage may have no incremental dollar "
            "charge. Aggregate token summaries cannot determine per-request long-context pricing. "
            "Reasoning tokens are already included in output tokens and are not added again."
        ),
    }


def attach_cost_estimate(usage: dict, model: object) -> dict[str, Any] | None:
    estimate = estimate_api_equivalent_cost(usage, model)
    if estimate is not None:
        usage["api_equivalent_cost_estimate"] = estimate
    return estimate

