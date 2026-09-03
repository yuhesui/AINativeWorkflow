#!/usr/bin/env python3
"""Build, start, use, and stop the frozen task-environment sidecar."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path


SUPPORTED_TASK_PREFIXES = ("T02_", "T03_", "T04_")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dockerfile_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment_spec(task_root: Path) -> dict | None:
    if not task_root.name.startswith(SUPPORTED_TASK_PREFIXES):
        return None
    upstream_dockerfile = task_root / "original_task" / "environment" / "Dockerfile"
    qualified_dockerfile = task_root / "qualification" / "environment" / "Dockerfile"
    dockerfile = qualified_dockerfile if qualified_dockerfile.is_file() else upstream_dockerfile
    task_toml = task_root / "original_task" / "task.toml"
    if not dockerfile.is_file() or not task_toml.is_file():
        raise RuntimeError(f"frozen task environment is incomplete: {task_root}")
    config = tomllib.loads(task_toml.read_text(encoding="utf-8"))
    environment = config.get("environment", {})
    digest = dockerfile_sha256(dockerfile)
    task_id = task_root.name.split("_", 1)[0].lower()
    return {
        "dockerfile": dockerfile,
        "build_context": dockerfile.parent,
        "dockerfile_sha256": digest,
        "upstream_dockerfile": upstream_dockerfile,
        "environment_adapted": dockerfile != upstream_dockerfile,
        "image_tag": f"ai-native-eval-{task_id}:{digest[:12]}",
        "cpus": environment.get("cpus", 1),
        "memory_mb": environment.get("memory_mb", 2048),
        "workdir": environment.get("workdir", "/app"),
        "environment": environment.get("env", {}),
    }


def container_name(run_id: str, task_root: Path) -> str:
    task_id = task_root.name.split("_", 1)[0].lower()
    suffix = hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:12]
    return f"ai-eval-{task_id}-{suffix}"


def _wsl_path(path: Path) -> str:
    converted = subprocess.run(
        ["wsl", "wslpath", "-a", str(path.resolve())],
        capture_output=True,
        text=True,
        check=False,
    )
    if converted.returncode or not converted.stdout.strip():
        raise RuntimeError(f"could not translate path for WSL: {path}\n{converted.stderr}")
    return converted.stdout.strip()


def _docker_command(arguments: list[str]) -> list[str]:
    return ["wsl", "docker", *arguments] if os.name == "nt" else ["docker", *arguments]


def _docker_path(path: Path) -> str:
    return _wsl_path(path) if os.name == "nt" else str(path.resolve())


def _docker(
    arguments: list[str],
    *,
    capture_output: bool = False,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            _docker_command(arguments),
            text=True,
            capture_output=capture_output,
            check=check,
        )
    except FileNotFoundError as exc:
        required = "WSL with Docker" if os.name == "nt" else "Docker"
        raise RuntimeError(f"{required} is required for the frozen task environment") from exc


def _inspect(kind: str, name: str, template: str) -> str | None:
    result = _docker(
        [kind, "inspect", "--format", template, name],
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def ensure_sidecar(task_root: Path, run_id: str, workspace: Path) -> dict | None:
    spec = environment_spec(task_root)
    if spec is None:
        return None
    availability = _docker(["version", "--format", "{{.Server.Version}}"], capture_output=True)
    if availability.returncode:
        detail = (availability.stderr or availability.stdout).strip()
        if os.name == "nt" and "permission denied" in detail.lower():
            raise RuntimeError(
                "WSL Docker is installed but the current WSL user cannot access "
                "/var/run/docker.sock. One-time host setup is required: add the WSL user to "
                "the docker group, restart WSL, and verify `docker version` before starting a "
                "scored run. The harness will not elevate privileges automatically."
            )
        raise RuntimeError("the frozen task environment requires a working Docker daemon: " + detail)
    image_tag = spec["image_tag"]
    image_id = _inspect("image", image_tag, "{{.Id}}")
    built = False
    if image_id is None:
        build = _docker(
            [
                "build",
                "--tag",
                image_tag,
                "--file",
                _docker_path(spec["dockerfile"]),
                _docker_path(spec["build_context"]),
            ]
        )
        if build.returncode:
            raise RuntimeError("failed to build the frozen task environment image")
        image_id = _inspect("image", image_tag, "{{.Id}}")
        built = True
    if image_id is None:
        raise RuntimeError("built task environment image could not be inspected")

    name = container_name(run_id, task_root)
    running = _inspect("container", name, "{{.State.Running}}")
    if running not in (None, "true"):
        raise RuntimeError(f"task environment container exists but is not running: {name}")
    if running is None:
        arguments = [
            "run",
            "--detach",
            "--rm",
            "--name",
            name,
            "--cpus",
            str(spec["cpus"]),
            "--memory",
            f"{spec['memory_mb']}m",
            "--volume",
            f"{_docker_path(workspace)}:{spec['workdir']}",
            "--workdir",
            str(spec["workdir"]),
        ]
        for key, value in sorted(spec["environment"].items()):
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(key)):
                raise RuntimeError(f"unsafe environment variable name in task.toml: {key!r}")
            arguments.extend(("--env", f"{key}={value}"))
        arguments.extend((image_tag, "tail", "-f", "/dev/null"))
        started = _docker(arguments, capture_output=True)
        if started.returncode:
            raise RuntimeError(
                "failed to start frozen task environment sidecar:\n" + started.stderr.strip()
            )
    return {
        "schema_version": 1,
        "kind": "docker_sidecar",
        "container_name": name,
        "container_workspace": spec["workdir"],
        "host_workspace": str(workspace),
        "dockerfile": str(spec["dockerfile"]),
        "dockerfile_sha256": spec["dockerfile_sha256"],
        "upstream_dockerfile": str(spec["upstream_dockerfile"]),
        "environment_adapted": spec["environment_adapted"],
        "image_tag": image_tag,
        "image_id": image_id,
        "image_built_this_session": built,
        "started_utc": utc_now(),
        "status": "RUNNING",
    }


def stop_sidecar(record: object) -> None:
    if not isinstance(record, dict) or record.get("kind") != "docker_sidecar":
        return
    name = str(record.get("container_name", ""))
    if not name:
        return
    result = _docker(["stop", "--timeout", "10", name], capture_output=True)
    if result.returncode and "No such container" not in result.stderr:
        raise RuntimeError(f"failed to stop task environment sidecar: {result.stderr.strip()}")
    record["status"] = "STOPPED"
    record["stopped_utc"] = utc_now()


def exec_in_sidecar(task_root: Path, run_dir: Path, command: list[str]) -> int:
    if not command:
        raise SystemExit("provide a command after --")
    run_path = run_dir / "RUN.json"
    if not run_path.is_file():
        raise SystemExit(f"missing RUN.json: {run_path}")
    run = json.loads(run_path.read_text(encoding="utf-8"))
    name = container_name(str(run.get("run_id", run_dir.name)), task_root)
    running = _inspect("container", name, "{{.State.Running}}")
    if running != "true":
        raise SystemExit(
            "the task environment sidecar is not running; launch through start_run.py"
        )
    return _docker(["exec", "-i", name, *command]).returncode


def infer_roots_from_workspace() -> tuple[Path, Path]:
    workspace = Path.cwd().resolve()
    run_dir = workspace.parent
    if workspace.name != "workspace" or run_dir.parent.name != "runs":
        raise SystemExit("exec-self must be run from a materialized run workspace")
    return run_dir.parent.parent, run_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)
    start = subparsers.add_parser("start")
    start.add_argument("task_root", type=Path)
    start.add_argument("run_dir", type=Path)
    stop = subparsers.add_parser("stop")
    stop.add_argument("run_dir", type=Path)
    execute = subparsers.add_parser("exec")
    execute.add_argument("task_root", type=Path)
    execute.add_argument("run_dir", type=Path)
    execute.add_argument("command", nargs=argparse.REMAINDER)
    execute_self = subparsers.add_parser("exec-self")
    execute_self.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.action == "start":
        run_dir = args.run_dir.resolve()
        try:
            record = ensure_sidecar(
                args.task_root.resolve(), run_dir.name, run_dir / "workspace"
            )
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        print(json.dumps(record or {"kind": "host", "status": "NOT_MANAGED"}, indent=2))
        return 0
    if args.action == "stop":
        run_path = args.run_dir.resolve() / "RUN.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))
        stop_sidecar(run.get("task_environment"))
        save_json(run_path, run)
        return 0
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if args.action == "exec-self":
        task_root, run_dir = infer_roots_from_workspace()
    else:
        task_root, run_dir = args.task_root.resolve(), args.run_dir.resolve()
    return exec_in_sidecar(task_root, run_dir, command)


if __name__ == "__main__":
    raise SystemExit(main())
