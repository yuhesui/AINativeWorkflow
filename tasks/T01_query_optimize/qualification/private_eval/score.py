#!/usr/bin/env python3
"""Private T01 verifier plus frozen continuous performance transform."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
import statistics
import time
from pathlib import Path

EXPECTED_DB_SHA256 = "89eab7555b6b86a74b8e0ee5a7db7beec0b2575a45cd2b22fe132eae79f5ad5a"
MAX_CHARS = 2_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def execute(db: Path, sql: str) -> tuple[tuple[str, ...], list[tuple[object, ...]]]:
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro&immutable=1", uri=True)
    try:
        cur = con.execute(sql)
        return tuple(d[0] for d in cur.description), cur.fetchall()
    finally:
        con.close()


def timed(db: Path, sql: str) -> float:
    start = time.perf_counter()
    execute(db, sql)
    return time.perf_counter() - start


def format_errors(sql: str) -> list[str]:
    errors: list[str] = []
    stripped = sql.strip()
    if len(stripped) > MAX_CHARS:
        errors.append("solution exceeds 2000 characters")
    if "--" in stripped or re.search(r"/\*.*?\*/", stripped, flags=re.DOTALL):
        errors.append("comments are forbidden")
    compact = " ".join(stripped.split())
    if not compact.endswith(";") or compact.count(";") != 1:
        errors.append("solution must contain exactly one semicolon-terminated statement")
    if not (compact.upper().startswith("SELECT") or compact.upper().startswith("WITH")):
        errors.append("solution must be a SELECT statement or CTE")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path, help="materialized candidate repository")
    parser.add_argument("output", type=Path)
    parser.add_argument("--iterations", type=int, default=7)
    args = parser.parse_args()
    private = Path(__file__).resolve().parent
    db = args.repo / "oewn.sqlite"
    candidate_path = args.repo / "sol.sql"
    baseline_path = args.repo / "my-sql-query.sql"
    golden_path = private / "tests" / "golden.sql"
    report: dict[str, object] = {
        "schema_version": 1,
        "task_id": "T01",
        "native_metric": "official verifier pass",
        "continuous_metric": "semantic-gated log-runtime progress",
        "iterations": args.iterations,
        "gates": {},
    }
    gates: dict[str, object] = report["gates"]  # type: ignore[assignment]
    try:
        gates["required_files"] = all(p.is_file() for p in (db, candidate_path, baseline_path, golden_path))
        if not gates["required_files"]:
            raise FileNotFoundError("one or more required files are absent")
        report["database_sha256"] = sha256(db)
        gates["database_integrity"] = report["database_sha256"] == EXPECTED_DB_SHA256
        candidate = candidate_path.read_text(encoding="utf-8").strip()
        golden = golden_path.read_text(encoding="utf-8").strip()
        report["candidate_sha256"] = sha256(candidate_path)
        errors = format_errors(candidate)
        gates["format"] = not errors
        report["format_errors"] = errors
        if not gates["database_integrity"] or errors:
            raise ValueError("hard integrity/format gate failed")
        try:
            cols_g, rows_g = execute(db, golden)
            cols_c, rows_c = execute(db, candidate)
            gates["valid_sql"] = True
        except sqlite3.Error as exc:
            gates["valid_sql"] = False
            raise ValueError(f"candidate SQL failed: {exc}") from exc
        gates["exact_columns"] = cols_c == cols_g
        gates["exact_rows_ordered"] = rows_c == rows_g
        gates["semantic_correctness"] = bool(gates["exact_columns"] and gates["exact_rows_ordered"])
        report["row_count"] = len(rows_c)
        if not gates["semantic_correctness"]:
            raise ValueError("semantic equality gate failed")

        # Untimed warm-up followed by an alternating order to reduce cache/order bias.
        for query in (golden, candidate):
            execute(db, query)
        times = {"golden_s": [], "candidate_s": []}
        orders = (("golden", golden), ("candidate", candidate))
        for i in range(args.iterations):
            rotated = orders[i % 2 :] + orders[: i % 2]
            for name, query in rotated:
                times[f"{name}_s"].append(timed(db, query))
        medians = {name: statistics.median(values) for name, values in times.items()}
        report["raw_timings"] = times
        report["medians"] = medians
        report["native_performance_threshold_ratio"] = 1.05
        report["native_pass"] = medians["candidate_s"] <= 1.05 * medians["golden_s"]
        baseline_lock = json.loads((private / "BASELINE_LOCK.json").read_text(encoding="utf-8"))
        ratio = float(baseline_lock["unoptimized_to_golden_ratio"])
        report["baseline_lock"] = baseline_lock
        denominator = math.log(ratio)
        baseline_equivalent = medians["golden_s"] * ratio
        report["baseline_equivalent_s"] = baseline_equivalent
        if denominator <= 0:
            progress = 1.0 if medians["candidate_s"] <= medians["golden_s"] else 0.0
            report["normalization_warning"] = "baseline was not slower than golden"
        else:
            progress = (math.log(baseline_equivalent) - math.log(medians["candidate_s"])) / denominator
        progress = max(0.0, min(1.0, progress))
        report["optimization_progress"] = progress
        report["continuous_score"] = 50.0 + 50.0 * progress
        report["valid"] = True
    except Exception as exc:  # verifier failures must still produce auditable raw output
        report["valid"] = False
        report["native_pass"] = False
        report["continuous_score"] = 0.0
        report["error"] = f"{type(exc).__name__}: {exc}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
