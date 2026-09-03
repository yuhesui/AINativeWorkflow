#!/usr/bin/env python3
"""Record run resource usage and optionally finalize the latest unfinished run."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from eval_common import load_json
from launch_executor import TOKEN_FIELDS, parse_usage_input, usage_totals
from usage_cost import attach_cost_estimate, estimate_api_equivalent_cost


ROOT = Path(__file__).resolve().parents[1]


def portable_path(value: str) -> Path:
    if os.name != "nt":
        value = value.replace("\\", "/")
    return Path(value)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def latest_unfinished_run(run_root: Path) -> Path:
    candidates: list[tuple[str, Path]] = []
    for run_path in (run_root / "runs").glob("*/RUN.json"):
        try:
            run = load_json(run_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if run.get("status") != "FINALIZED":
            candidates.append((str(run.get("created_utc", "")), run_path.parent))
    if not candidates:
        raise SystemExit("no unfinished run with RUN.json was found")
    return max(candidates, key=lambda item: (item[0], item[1].name))[1]


def numeric_usage(value: object, label: str) -> dict[str, float | int]:
    if not isinstance(value, dict):
        raise SystemExit(f"{label} must be one JSON object")
    result: dict[str, float | int] = {}
    for field in TOKEN_FIELDS:
        number = value.get(field)
        if number is None:
            continue
        if isinstance(number, bool) or not isinstance(number, (int, float)) or number < 0:
            raise SystemExit(f"{label}.{field} must be a non-negative number")
        result[field] = number
    return result


def usage_from_file(path: Path | None, label: str) -> dict[str, float | int] | None:
    if path is None:
        return None
    if not path.is_file():
        raise SystemExit(f"missing {label}: {path}")
    return numeric_usage(json.loads(path.read_text(encoding="utf-8")), label)


def prompt_usage(label: str) -> dict[str, float | int] | None:
    raw = input(f"{label} usage JSON or token line (blank if unavailable): ").strip()
    if not raw:
        return None
    try:
        return numeric_usage(parse_usage_input(raw), label)
    except ValueError as exc:
        raise SystemExit(f"invalid {label} usage input: {exc}") from exc


def prompt_optional_float(message: str, *, non_negative: bool = False) -> float | None:
    raw = input(message).strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise SystemExit(f"expected a number, got {raw!r}") from exc
    if non_negative and value < 0:
        raise SystemExit("time values must be non-negative")
    return value


MAIN_TIME = re.compile(r"^\s*(\d+)\s*m\s*(\d+)\s*s\s*$", re.IGNORECASE)


def prompt_optional_time(message: str) -> float | None:
    """Return seconds for an interactive Xm Ys entry, retrying malformed input."""
    while True:
        raw = input(message).strip()
        if not raw:
            return None
        match = MAIN_TIME.fullmatch(raw)
        if not match:
            print("Invalid time. Use Xm Ys, for example 12m 34s, or leave it blank.")
            continue
        minutes, seconds = (int(part) for part in match.groups())
        if seconds >= 60:
            print("Invalid time. Seconds must be between 0 and 59.")
            continue
        return float(minutes * 60 + seconds)


def elapsed_seconds(created_utc: object, ended_utc: str) -> float | None:
    try:
        created = datetime.fromisoformat(str(created_utc))
        ended = datetime.fromisoformat(ended_utc)
    except ValueError:
        return None
    return round((ended - created).total_seconds(), 6)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record condition-appropriate resource use and optionally finalize a run."
    )
    parser.add_argument("task_root", type=portable_path)
    parser.add_argument("--run-id", help="default: latest unfinished run in this task")
    parser.add_argument("--qualification-root", type=portable_path)
    parser.add_argument("--main-wall-minutes", type=float, help="reported cumulative active Main time")
    parser.add_argument("--main-usage-json", type=Path, help="reported cumulative Main usage JSON")
    parser.add_argument("--main-usage-text", help="Main usage JSON or product-visible token line")
    parser.add_argument("--executor-usage-json", type=Path, help="usage for the latest executor session")
    parser.add_argument("--executor-usage-text", help="executor usage JSON or product-visible token line")
    parser.add_argument("--replace-executor-usage", action="store_true")
    parser.add_argument(
        "--update-finalized",
        action="store_true",
        help="append resource metadata without changing finalized repository or score artifacts",
    )
    parser.add_argument("--notes")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--validity", choices=("VALID", "INVALID_INFRASTRUCTURE", "FAILED_TASK"))
    parser.add_argument("--invalidation-reason")
    parser.add_argument("--grader-raw", type=Path)
    parser.add_argument("--native-primary-metric", type=float)
    parser.add_argument("--normalized-completion-score", type=float)
    parser.add_argument("--recovery-json", type=Path)
    parser.add_argument("--non-interactive", action="store_true")
    args = parser.parse_args()

    task_root = args.task_root.resolve()
    run_root = args.qualification_root.resolve() if args.qualification_root else task_root
    run_dir = run_root / "runs" / args.run_id if args.run_id else latest_unfinished_run(run_root)
    run_path = run_dir / "RUN.json"
    workspace = run_dir / "workspace"
    if not run_path.is_file() or not workspace.is_dir():
        raise SystemExit(f"run must contain RUN.json and workspace/: {run_dir}")
    run = load_json(run_path)
    if run.get("status") == "FINALIZED" and not args.update_finalized:
        raise SystemExit("run is already finalized")
    if args.update_finalized and (args.finalize or args.validity is not None):
        raise SystemExit("--update-finalized cannot be combined with finalization options")

    print(f"\nRecording run: {run_dir.name}")
    print(f"Current status: {run.get('status', 'UNKNOWN')}")
    interactive = not args.non_interactive
    has_main = (
        run.get("condition") == "AI_NATIVE"
        or int(run.get("main_inference_count", 0)) > 0
        or "main_model_product_visible" in run
    )

    main_minutes = args.main_wall_minutes
    previously_reported_main_seconds = run.get("main_active_wall_seconds_reported")
    main_time_reused_from_start = False
    if main_minutes is None and isinstance(previously_reported_main_seconds, (int, float)):
        main_minutes = float(previously_reported_main_seconds) / 60.0
        main_time_reused_from_start = True
        if interactive:
            print(
                "Using Main time recorded once before executor launch: "
                f"{int(previously_reported_main_seconds) // 60}m "
                f"{int(previously_reported_main_seconds) % 60}s"
            )
    elif main_minutes is None and interactive and has_main:
        cumulative_seconds = prompt_optional_time(
            "Cumulative Main active/compute time as Xm Ys "
            "(blank if unavailable): "
        )
        if cumulative_seconds is not None:
            main_minutes = cumulative_seconds / 60.0
    if main_minutes is not None and main_minutes < 0:
        raise SystemExit("--main-wall-minutes must be non-negative")

    main_usage = usage_from_file(args.main_usage_json, "Main usage")
    if main_usage is None and args.main_usage_text:
        try:
            main_usage = numeric_usage(parse_usage_input(args.main_usage_text), "Main usage")
        except ValueError as exc:
            raise SystemExit(f"invalid Main usage input: {exc}") from exc
    if main_usage is None and interactive and has_main:
        main_usage = prompt_usage("Main")

    executor_usage = usage_from_file(args.executor_usage_json, "executor usage")
    if executor_usage is None and args.executor_usage_text:
        try:
            executor_usage = numeric_usage(
                parse_usage_input(args.executor_usage_text), "executor usage"
            )
        except ValueError as exc:
            raise SystemExit(f"invalid executor usage input: {exc}") from exc
    sessions = run.get("executor_sessions", [])
    if not isinstance(sessions, list):
        raise SystemExit("RUN.json executor_sessions must be a list")
    latest_session = sessions[-1] if sessions else None
    for session in sessions:
        if not isinstance(session, dict) or not isinstance(session.get("usage"), dict):
            continue
        attach_cost_estimate(
            session["usage"], session.get("executor_model_product_visible")
        )
    run["usage_totals"] = usage_totals(sessions)
    existing_executor_usage = latest_session.get("usage", {}) if isinstance(latest_session, dict) else {}
    if executor_usage is None and interactive and latest_session is not None and not existing_executor_usage:
        executor_usage = prompt_usage("Latest executor")
    if executor_usage is not None:
        executor_model = (
            latest_session.get("executor_model_product_visible")
            if isinstance(latest_session, dict)
            else run.get("active_executor_product_visible")
        )
        executor_cost = attach_cost_estimate(executor_usage, executor_model)
        if executor_cost is not None:
            print(
                "Estimated standard API-equivalent executor cost: "
                f"${executor_cost['estimated_cost_usd']:.2f}"
            )
        if latest_session is None:
            run.setdefault("unattributed_executor_usage_records", []).append(
                {
                    "recorded_utc": utc_now(),
                    "usage": executor_usage,
                    "usage_source": "operator_record_run_no_session",
                }
            )
            run["usage_totals"] = usage_totals(
                [*sessions, {"usage": executor_usage, "wall_seconds": 0.0}]
            )
        else:
            if existing_executor_usage and not args.replace_executor_usage:
                raise SystemExit(
                    "latest executor session already has usage; pass --replace-executor-usage to replace it"
                )
            latest_session["usage"] = executor_usage
            latest_session["usage_source"] = "operator_record_run"
            run["usage_totals"] = usage_totals(sessions)

    notes = args.notes
    if notes is None and interactive:
        notes = input("Optional run note (blank to omit): ").strip() or None
    recorded_utc = utc_now()
    record = {
        "recorded_utc": recorded_utc,
        "main_time_reused_from_initial_record": main_time_reused_from_start,
        "main_usage_reported": main_usage or {},
        "executor_usage_reported": executor_usage or {},
        "notes": notes,
    }
    run.setdefault("operator_records", []).append(record)
    resource_summary = dict(run.get("resource_summary", {}))
    resource_summary.update(run.get("usage_totals", usage_totals(sessions)))
    if main_minutes is not None:
        cumulative_main_seconds = round(main_minutes * 60.0, 6)
        resource_summary["main_active_wall_seconds_reported"] = cumulative_main_seconds
        if not main_time_reused_from_start:
            record["main_active_wall_seconds_reported"] = cumulative_main_seconds
            run["main_active_wall_seconds_reported"] = cumulative_main_seconds
    if main_usage is not None:
        resource_summary["main_usage_reported"] = main_usage
        main_cost = estimate_api_equivalent_cost(
            main_usage, run.get("main_model_product_visible")
        )
        if main_cost is not None:
            resource_summary["main_api_equivalent_cost_estimate"] = main_cost
            print(
                "Estimated standard API-equivalent Main cost: "
                f"${main_cost['estimated_cost_usd']:.2f}"
            )
    executor_estimated = resource_summary.get(
        "executor_api_equivalent_cost_estimated_usd"
    )
    main_estimate = resource_summary.get("main_api_equivalent_cost_estimate")
    main_estimated = (
        main_estimate.get("estimated_cost_usd")
        if isinstance(main_estimate, dict)
        else None
    )
    if isinstance(executor_estimated, (int, float)) or isinstance(
        main_estimated, (int, float)
    ):
        resource_summary["combined_api_equivalent_cost_estimated_usd"] = round(
            float(executor_estimated or 0) + float(main_estimated or 0), 8
        )
        print(
            "Combined standard API-equivalent cost estimate: "
            f"${resource_summary['combined_api_equivalent_cost_estimated_usd']:.2f} "
            "(subscription charge may differ)"
        )
    observed = elapsed_seconds(run.get("created_utc"), recorded_utc)
    if observed is not None and not args.update_finalized:
        resource_summary["elapsed_since_materialization_seconds"] = observed
    run["resource_summary"] = resource_summary
    run["last_recorded_utc"] = recorded_utc
    save_json(run_path, run)
    print(f"Recorded metrics in: {run_path}")

    if args.update_finalized:
        result_root = args.qualification_root.resolve() if args.qualification_root else task_root
        metrics_path = result_root / "run_results" / run_dir.name / "METRICS.json"
        if not metrics_path.is_file():
            raise SystemExit(f"finalized run is missing METRICS.json: {metrics_path}")
        save_json(metrics_path, run)
        print(f"Updated finalized metrics: {metrics_path}")
        return 0

    finalize = args.finalize or args.validity is not None
    if interactive and not finalize:
        latest_grade = run.get("latest_auto_grade")
        incomplete = isinstance(latest_grade, dict) and (
            latest_grade.get("task_completion") == "INCOMPLETE_CHECKPOINTS"
        )
        if incomplete:
            print(
                "Automatic grading found remaining checkpoints. Answer No to continue; "
                "finalize only if this trajectory is intentionally ending as FAILED_TASK."
            )
        finalize = input("Finalize this run now? [y/N]: ").strip().lower() in {"y", "yes"}
    if not finalize:
        print("Run remains unfinalized; rerun this command after grading to finalize it.")
        return 0

    validity = args.validity
    if validity is None and interactive:
        validity = input("Validity (VALID, FAILED_TASK, or INVALID_INFRASTRUCTURE): ").strip().upper()
    if validity not in {"VALID", "FAILED_TASK", "INVALID_INFRASTRUCTURE"}:
        raise SystemExit("finalization requires a valid --validity")
    latest_grade = run.get("latest_auto_grade")
    if (
        validity == "VALID"
        and isinstance(latest_grade, dict)
        and latest_grade.get("task_completion") == "INCOMPLETE_CHECKPOINTS"
    ):
        raise SystemExit("VALID finalization is not allowed while graded checkpoints remain")

    invalidation_reason = args.invalidation_reason
    if validity == "INVALID_INFRASTRUCTURE" and not invalidation_reason and interactive:
        invalidation_reason = input("Infrastructure invalidation reason: ").strip()
    grader_raw = args.grader_raw
    latest_auto_grade = run.get("latest_auto_grade")
    if grader_raw is None and isinstance(latest_auto_grade, dict):
        automatic_raw = latest_auto_grade.get("raw_grader")
        if isinstance(automatic_raw, str) and Path(automatic_raw).is_file():
            grader_raw = Path(automatic_raw)
            if interactive:
                print(f"Using automatic grader output: {grader_raw}")
    if validity in {"VALID", "FAILED_TASK"} and grader_raw is None and interactive:
        grader_raw = portable_path(input("Native grader-output file path: ").strip())
    native_metric = args.native_primary_metric
    if native_metric is None and isinstance(latest_auto_grade, dict):
        automatic_metric = latest_auto_grade.get("native_primary_metric")
        if isinstance(automatic_metric, (int, float)):
            native_metric = float(automatic_metric)
    if native_metric is None and interactive:
        native_metric = prompt_optional_float("Native primary metric (blank if unavailable): ")
    normalized = args.normalized_completion_score
    if normalized is None and isinstance(latest_auto_grade, dict):
        automatic_normalized = latest_auto_grade.get("normalized_completion_score")
        if isinstance(automatic_normalized, (int, float)):
            normalized = float(automatic_normalized)
    if normalized is None and interactive:
        normalized = prompt_optional_float("Normalized completion score (blank if undefined): ")

    command = [
        sys.executable,
        "-X",
        "utf8",
        str(ROOT / "scripts" / "finalize_run.py"),
        str(task_root),
        run_dir.name,
        str(workspace),
        "--validity",
        validity,
        "--metrics-json",
        str(run_path),
    ]
    if invalidation_reason:
        command.extend(("--invalidation-reason", invalidation_reason))
    if grader_raw:
        command.extend(("--grader-raw", str(grader_raw.resolve())))
    if native_metric is not None:
        command.extend(("--native-primary-metric", str(native_metric)))
    if normalized is not None:
        command.extend(("--normalized-completion-score", str(normalized)))
    if args.recovery_json:
        command.extend(("--recovery-json", str(args.recovery_json.resolve())))
    if args.qualification_root:
        command.extend(("--qualification-root", str(args.qualification_root.resolve())))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
