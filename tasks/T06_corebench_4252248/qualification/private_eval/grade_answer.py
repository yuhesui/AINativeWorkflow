#!/usr/bin/env python3
"""Deterministic single-question wrapper around CORE-Bench's numeric semantics."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

QUESTION = (
    "Report the overall AUC from the PR curve generated with the CTRPv2 "
    "sensitivity dataset, tested against ATC annotations and drug-target "
    "information from CHEMBL."
)
EXPECTED = 0.4929241


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    candidate = payload.get(QUESTION, payload.get(f"fig {QUESTION}", payload.get("answer")))
    try:
        value = float(str(candidate).replace("%", ""))
    except (TypeError, ValueError):
        value = math.nan
    passed = math.isfinite(value) and value == EXPECTED
    result = {
        "native_metric": "correct_questions",
        "correct_questions": int(passed),
        "total_questions": 1,
        "correct_tasks": int(passed),
        "total_tasks": 1,
        "reported_value": value if math.isfinite(value) else None,
        "expected_value": EXPECTED,
        "passed": passed,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
