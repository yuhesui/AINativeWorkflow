#!/usr/bin/env python3
"""Run the frozen private grader against a materialized run workspace.

Private evaluator files stay outside the agent-visible workspace.  Raw reports
and a normalized grader result are written beneath runs/<RUN_ID>/evidence/.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid
import venv
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from eval_common import file_sha256, load_json


ROOT = Path(__file__).resolve().parents[1]
SLOP_TASKS = {
    "T02": {"total": 3, "entrypoint": "launch.py", "timeout": 60},
    "T03": {"total": 5, "entrypoint": "migration_tool.py", "timeout": 60},
    "T04": {"total": 8, "entrypoint": "appctl.py", "timeout": 25},
}
PYTEST_PACKAGES = (
    "pytest==9.0.3",
    "pytest-json-ctrf==0.4.1",
    "pytest-json-report==1.5.0",
    "pytest-timeout==2.4.0",
    "pyyaml",
    "uv==0.9.5",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def portable_path(value: str) -> Path:
    if os.name != "nt":
        value = value.replace("\\", "/")
    return Path(value)


def run_directory(task_root: Path, run_id: str, qualification_root: Path | None) -> Path:
    base = qualification_root.resolve() if qualification_root else task_root
    directory = base / "runs" / run_id
    if not (directory / "RUN.json").is_file():
        raise SystemExit(f"run metadata not found: {directory / 'RUN.json'}")
    return directory


def append_grade(run_path: Path, result: dict[str, object]) -> None:
    run = load_json(run_path)
    grades = run.setdefault("auto_grades", [])
    grades.append(result)
    run["latest_auto_grade"] = result
    save_json(run_path, run)


def grade_t01(task_root: Path, run_dir: Path, run: dict[str, object]) -> dict[str, object]:
    output_dir = run_dir / "evidence" / "grader"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = output_dir / "GRADER_RAW.json"
    command = [
        sys.executable,
        "-X",
        "utf8",
        str(task_root / "qualification" / "private_eval" / "score.py"),
        str(run_dir / "workspace"),
        str(raw),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    (output_dir / "GRADER_CONSOLE.txt").write_text(
        completed.stdout + completed.stderr, encoding="utf-8"
    )
    if not raw.is_file():
        raise RuntimeError(f"T01 grader produced no report (exit {completed.returncode})")
    report = load_json(raw)
    result: dict[str, object] = {
        "schema_version": 1,
        "task_id": "T01",
        "run_id": run["run_id"],
        "graded_utc": utc_now(),
        "grader_ok": True,
        "grader_exit_code": completed.returncode,
        "task_pass": bool(report.get("native_pass", False)),
        "task_completion": "PASSED" if report.get("native_pass", False) else "FAILED",
        "native_primary_metric": report.get("continuous_score"),
        "normalized_completion_score": report.get("continuous_score"),
        "raw_grader": str(raw),
        "raw_grader_sha256": file_sha256(raw),
        "metrics": str(raw),
    }
    save_json(output_dir / "GRADER_RESULT.json", result)
    return result


def venv_python(directory: Path) -> Path:
    return directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def venv_uvx(directory: Path) -> Path:
    return directory / ("Scripts/uvx.exe" if os.name == "nt" else "bin/uvx")


def pytest_command(
    python: str,
    workspace: Path,
    tests: list[Path],
    checkpoint: int,
    entrypoint: str,
    timeout: int,
    ctrf: Path,
    report: Path,
    temp_root: Path,
) -> list[str]:
    command = [
        python,
        "-m",
        "pytest",
        *(str(path) for path in tests),
        "--checkpoint",
        f"checkpoint_{checkpoint}",
        "--entrypoint",
        entrypoint,
        f"--timeout={timeout}.0",
        "--timeout-method=signal",
        f"--basetemp={temp_root}",
        f"--ctrf={ctrf}",
        "--json-report",
        f"--json-report-file={report}",
        "--json-report-omit=traceback,streams,log,collectors,warnings",
        "-p",
        "no:cacheprovider",
        "-rA",
    ]
    return command


def run_slop_posix(
    workspace: Path,
    private_tests: Path,
    tests: list[Path],
    checkpoint: int,
    entrypoint_file: str,
    timeout: int,
    output_dir: Path,
) -> tuple[int, int, str]:
    with tempfile.TemporaryDirectory(prefix="ai-native-grader-") as temporary:
        runtime = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True).create(runtime)
        python = venv_python(runtime)
        install = subprocess.run(
            [str(python), "-m", "pip", "install", "-q", *PYTEST_PACKAGES],
            text=True,
            capture_output=True,
            check=False,
        )
        if install.returncode:
            return install.returncode, -1, install.stdout + install.stderr
        ctrf = output_dir / f"GRADER_RAW_checkpoint_{checkpoint:02d}.ctrf.json"
        report = output_dir / f"pytest_report_checkpoint_{checkpoint:02d}.json"
        entrypoint = f'{shlex.quote(str(python))} {shlex.quote(entrypoint_file)}'
        graded = subprocess.run(
            pytest_command(
                str(python),
                workspace,
                tests,
                checkpoint,
                entrypoint,
                timeout,
                ctrf,
                report,
                Path(temporary) / "pytest",
            ),
            cwd=workspace,
            text=True,
            capture_output=True,
            check=False,
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPYCACHEPREFIX": str(Path(temporary) / "pycache"),
            },
        )
        scb_report = output_dir / f"scb_check_checkpoint_{checkpoint:02d}.json"
        scb_stderr = output_dir / f"scb_check_checkpoint_{checkpoint:02d}.stderr.txt"
        checked = subprocess.run(
            [
                str(venv_uvx(runtime)),
                "--from",
                "scb-check==0.1.0",
                "scb-check",
                "check",
                str(workspace),
                "--report",
                "--include-all",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        scb_report.write_text(checked.stdout, encoding="utf-8")
        scb_stderr.write_text(checked.stderr, encoding="utf-8")
        return 0, graded.returncode, graded.stdout + graded.stderr


def windows_to_wsl(path: Path) -> str:
    resolved = path.resolve()
    if not resolved.drive or not resolved.drive[0].isalpha():
        raise RuntimeError(f"cannot map path into WSL: {resolved}")
    return str(PurePosixPath("/mnt", resolved.drive[0].lower(), *resolved.parts[1:]))


def run_slop_wsl(
    workspace: Path,
    private_tests: Path,
    tests: list[Path],
    checkpoint: int,
    entrypoint_file: str,
    timeout: int,
    output_dir: Path,
) -> tuple[int, int, str]:
    token = uuid.uuid4().hex[:12]
    runtime = f"/tmp/ai-native-grader-{token}"
    workspace_wsl = windows_to_wsl(workspace)
    output_wsl = windows_to_wsl(output_dir)
    tests_wsl = [windows_to_wsl(path) for path in tests]
    private_wsl = windows_to_wsl(private_tests)
    ctrf = f"{output_wsl}/GRADER_RAW_checkpoint_{checkpoint:02d}.ctrf.json"
    report = f"{output_wsl}/pytest_report_checkpoint_{checkpoint:02d}.json"
    scb_report = f"{output_wsl}/scb_check_checkpoint_{checkpoint:02d}.json"
    scb_stderr = f"{output_wsl}/scb_check_checkpoint_{checkpoint:02d}.stderr.txt"
    rc_file = f"{output_wsl}/pytest_return_code.txt"
    packages = " ".join(shlex.quote(item) for item in PYTEST_PACKAGES)
    test_args = " ".join(shlex.quote(item) for item in tests_wsl)
    script = f"""
set -u
python3 -m venv {shlex.quote(runtime)}
{shlex.quote(runtime + '/bin/pip')} install -q {packages}
cd {shlex.quote(workspace_wsl)}
set +e
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX={shlex.quote(runtime + '/pycache')} \\
  {shlex.quote(runtime + '/bin/python')} -m pytest {test_args} \\
  --checkpoint {shlex.quote(f'checkpoint_{checkpoint}')} \\
  --entrypoint {shlex.quote(runtime + '/bin/python ' + entrypoint_file)} \\
  --timeout={timeout}.0 --timeout-method=signal \\
  --basetemp={shlex.quote(runtime + '/pytest')} \\
  --ctrf={shlex.quote(ctrf)} --json-report --json-report-file={shlex.quote(report)} \\
  --json-report-omit=traceback,streams,log,collectors,warnings -p no:cacheprovider -rA
pytest_rc=$?
printf '%s\\n' "$pytest_rc" > {shlex.quote(rc_file)}
{shlex.quote(runtime + '/bin/uvx')} --from scb-check==0.1.0 scb-check check \\
  {shlex.quote(workspace_wsl)} --report --include-all \\
  > {shlex.quote(scb_report)} 2> {shlex.quote(scb_stderr)}
exit 0
"""
    completed = subprocess.run(
        ["wsl", "bash", "-lc", script], text=True, capture_output=True, check=False
    )
    pytest_rc = -1
    rc_path = output_dir / "pytest_return_code.txt"
    if rc_path.is_file():
        try:
            pytest_rc = int(rc_path.read_text(encoding="utf-8").strip())
        except ValueError:
            pass
    if pytest_rc < 0:
        report_path = output_dir / f"pytest_report_checkpoint_{checkpoint:02d}.json"
        if report_path.is_file():
            try:
                report_data = load_json(report_path)
                report_exit = report_data.get("exitcode")
                if isinstance(report_exit, int):
                    pytest_rc = report_exit
            except (json.JSONDecodeError, OSError):
                pass
    return completed.returncode, pytest_rc, completed.stdout + completed.stderr


def grade_slop(task_root: Path, run_dir: Path, run: dict[str, object]) -> dict[str, object]:
    task_id = str(run["task_id"])
    spec = SLOP_TASKS[task_id]
    state_path = run_dir / "workspace" / ".evaluation" / "CHECKPOINT_STATE.json"
    if not state_path.is_file():
        raise RuntimeError("checkpoint state is missing from the materialized workspace")
    state = load_json(state_path)
    checkpoint = int(state["current_checkpoint"])
    private_tests = task_root / "qualification" / "private_eval" / "tests"
    tests = [private_tests / f"test_checkpoint_{number}.py" for number in range(1, checkpoint + 1)]
    missing = [path for path in tests if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing private checkpoint tests: {missing}")
    output_dir = run_dir / "evidence" / "grader" / f"checkpoint_{checkpoint:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        infrastructure_rc, pytest_rc, console = run_slop_wsl(
            run_dir / "workspace",
            private_tests,
            tests,
            checkpoint,
            str(spec["entrypoint"]),
            int(spec["timeout"]),
            output_dir,
        )
        runtime = "WSL2"
    else:
        infrastructure_rc, pytest_rc, console = run_slop_posix(
            run_dir / "workspace",
            private_tests,
            tests,
            checkpoint,
            str(spec["entrypoint"]),
            int(spec["timeout"]),
            output_dir,
        )
        runtime = "POSIX"
    (output_dir / "GRADER_CONSOLE.txt").write_text(console, encoding="utf-8")
    ctrf = output_dir / f"GRADER_RAW_checkpoint_{checkpoint:02d}.ctrf.json"
    report = output_dir / f"pytest_report_checkpoint_{checkpoint:02d}.json"
    if infrastructure_rc or not ctrf.is_file() or not report.is_file() or pytest_rc < 0:
        raise RuntimeError(
            f"private grader infrastructure failed (runtime={runtime}, rc={infrastructure_rc}, "
            f"pytest_rc={pytest_rc})"
        )

    scb_report = output_dir / f"scb_check_checkpoint_{checkpoint:02d}.json"
    scb_rc = 0 if scb_report.is_file() and scb_report.stat().st_size else 1
    reward_dir = output_dir / "native_reward"
    history = run_dir / "evidence" / "grader" / "scb-check-history.jsonl"
    shim = private_tests / "_ctrf_to_reward.py"
    shim_command = [
        sys.executable,
        "-X",
        "utf8",
        str(shim),
        "--ctrf",
        str(ctrf),
        "--pytest-report",
        str(report),
        "--current-checkpoint",
        f"checkpoint_{checkpoint}",
        "--pytest-rc",
        str(pytest_rc),
        "--scb-check-rc",
        str(scb_rc),
        "--scb-check-history",
        str(history),
        "--out-dir",
        str(reward_dir),
    ]
    if scb_rc == 0:
        shim_command.extend(("--scb-check-report", str(scb_report)))
    shim_result = subprocess.run(shim_command, cwd=ROOT, text=True, capture_output=True, check=False)
    with (output_dir / "GRADER_CONSOLE.txt").open("a", encoding="utf-8") as stream:
        stream.write(shim_result.stdout + shim_result.stderr)
    details_path = reward_dir / "reward_details.json"
    if shim_result.returncode or not details_path.is_file():
        raise RuntimeError(f"native reward parser failed (exit {shim_result.returncode})")
    details = load_json(details_path)

    previous = []
    for grade in run.get("auto_grades", []):
        if isinstance(grade, dict) and grade.get("task_id") == task_id:
            previous.append(grade)
    by_checkpoint = {
        int(grade["checkpoint"]): grade
        for grade in previous
        if isinstance(grade.get("checkpoint"), int)
    }
    checkpoint_score = 100.0 * float(details["strict_pass_rate"])
    by_checkpoint[checkpoint] = {"checkpoint_primary_score": checkpoint_score}
    total = int(spec["total"])
    complete = all(number in by_checkpoint for number in range(1, total + 1))
    primary = None
    if complete:
        primary = sum(
            float(by_checkpoint[number]["checkpoint_primary_score"])
            for number in range(1, total + 1)
        ) / total
    result: dict[str, object] = {
        "schema_version": 1,
        "task_id": task_id,
        "run_id": run["run_id"],
        "graded_utc": utc_now(),
        "grader_ok": True,
        "grader_runtime": runtime,
        "pytest_exit_code": pytest_rc,
        "checkpoint": checkpoint,
        "checkpoint_total": total,
        "checkpoint_primary_score": checkpoint_score,
        "core_pass_rate": details.get("core_pass_rate"),
        "isolated_pass_rate": details.get("isolated_pass_rate"),
        "strict_pass_rate": details.get("strict_pass_rate"),
        "native_primary_metric": primary,
        "normalized_completion_score": primary,
        "all_checkpoints_graded": complete,
        "task_completion": "COMPLETE" if complete else "INCOMPLETE_CHECKPOINTS",
        "raw_grader": str(ctrf),
        "raw_grader_sha256": file_sha256(ctrf),
        "metrics": str(details_path),
        "accepted_for_next_reveal": True,
    }
    save_json(output_dir / "GRADER_RESULT.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a task's frozen private grader.")
    parser.add_argument("task_root", type=portable_path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--qualification-root", type=portable_path)
    args = parser.parse_args()

    task_root = args.task_root.resolve()
    run_dir = run_directory(task_root, args.run_id, args.qualification_root)
    run_path = run_dir / "RUN.json"
    run = load_json(run_path)
    if run.get("status") == "FINALIZED":
        raise SystemExit("cannot grade a finalized run")
    task_id = str(run.get("task_id", ""))
    try:
        if task_id == "T01":
            result = grade_t01(task_root, run_dir, run)
        elif task_id in SLOP_TASKS:
            result = grade_slop(task_root, run_dir, run)
        else:
            raise RuntimeError(f"automatic grader adapter is not implemented for {task_id}")
    except Exception as exc:
        failure = {
            "schema_version": 1,
            "task_id": task_id,
            "run_id": args.run_id,
            "graded_utc": utc_now(),
            "grader_ok": False,
            "infrastructure_error": f"{type(exc).__name__}: {exc}",
        }
        append_grade(run_path, failure)
        print(json.dumps(failure, indent=2, sort_keys=True))
        return 2
    append_grade(run_path, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if task_id in SLOP_TASKS and not result["all_checkpoints_graded"]:
        checkpoint = int(result["checkpoint"])
        print(
            "\nCheckpoint graded. Reveal the next checkpoint with:\n"
            f"{sys.executable} -X utf8 scripts/reveal_checkpoint.py {task_root} "
            f"{args.run_id} --checkpoint {checkpoint + 1} "
            f"--accepted-grader-raw {result['raw_grader']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
