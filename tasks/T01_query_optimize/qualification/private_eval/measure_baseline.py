#!/usr/bin/env python3
"""One-time bounded T01 unoptimized/golden environment measurement."""

from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path


def run(db: Path, sql: str, timeout_s: float) -> float:
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro&immutable=1", uri=True)
    deadline = time.monotonic() + timeout_s
    con.set_progress_handler(lambda: 1 if time.monotonic() >= deadline else 0, 20_000)
    start = time.perf_counter()
    try:
        con.execute(sql).fetchall()
        return time.perf_counter() - start
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--golden-iterations", type=int, default=3)
    args = parser.parse_args()
    private = Path(__file__).resolve().parent
    db = args.repo / "oewn.sqlite"
    baseline = (args.repo / "my-sql-query.sql").read_text(encoding="utf-8")
    golden = (private / "tests" / "golden.sql").read_text(encoding="utf-8")
    golden_times = [run(db, golden, args.timeout) for _ in range(args.golden_iterations)]
    baseline_time = run(db, baseline, args.timeout)
    golden_median = statistics.median(golden_times)
    record = {
        "schema_version": 1,
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "method": "one unoptimized execution; median of three golden executions; immutable read-only SQLite",
        "host": {"platform": platform.platform(), "python": platform.python_version()},
        "timeout_s": args.timeout,
        "unoptimized_s": baseline_time,
        "golden_times_s": golden_times,
        "golden_median_s": golden_median,
        "unoptimized_to_golden_ratio": baseline_time / golden_median,
    }
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
