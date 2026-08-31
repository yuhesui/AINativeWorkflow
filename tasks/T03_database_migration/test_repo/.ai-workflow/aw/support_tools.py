
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .filesystem import utc_now


def _run(command: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "ok": completed.returncode == 0,
        }
    except Exception as exc:  # installation should never break aw init
        return {"command": command, "returncode": None, "stdout_tail": "", "stderr_tail": repr(exc), "ok": False}


def _check(binary: str) -> dict[str, Any]:
    path = shutil.which(binary)
    result = {"binary": binary, "path": path, "installed": bool(path), "version": None}
    if path:
        out = _run([binary, "--version"], timeout=20)
        result["version"] = (out.get("stdout_tail") or out.get("stderr_tail") or "").strip().splitlines()[:2]
    return result


def _install_rtk() -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    if shutil.which("brew"):
        attempts.append(_run(["brew", "install", "rtk"], timeout=240))
        if attempts[-1]["ok"]:
            return attempts
    if shutil.which("cargo"):
        attempts.append(_run(["cargo", "install", "--git", "https://github.com/rtk-ai/rtk"], timeout=600))
        if attempts[-1]["ok"]:
            return attempts
    if shutil.which("curl") and shutil.which("sh"):
        attempts.append(_run(["sh", "-c", "curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh"], timeout=300))
    return attempts


def _install_caveman() -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    system = platform.system().lower()
    if system.startswith("windows") and shutil.which("powershell"):
        attempts.append(_run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "irm https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.ps1 | iex"], timeout=300))
        return attempts
    if shutil.which("curl") and shutil.which("bash"):
        attempts.append(_run(["bash", "-c", "curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash"], timeout=300))
    elif shutil.which("npx"):
        attempts.append(_run(["npx", "-y", "github:JuliusBrussee/caveman", "--", "--all"], timeout=300))
    return attempts


def check_or_install_support_tools(root: Path, install: bool = False) -> dict[str, Any]:
    """Check optional support tools and optionally install them.

    Failure is non-fatal by design. Results are written into .ai-workflow/install_status.json.
    """
    root = Path(root)
    status: dict[str, Any] = {
        "created_at": utc_now(),
        "install_requested": bool(install),
        "tools": {},
        "notes": [
            "RTK and Caveman are optional support tools, not workflow authorities.",
            "If installation fails, continue the workflow and report the missing tools to the user.",
            "Review install scripts before use in restricted or enterprise environments.",
        ],
    }
    for tool in ("rtk", "caveman"):
        status["tools"][tool] = {"before": _check(tool), "attempts": [], "after": None}
    if install and not status["tools"]["rtk"]["before"]["installed"]:
        status["tools"]["rtk"]["attempts"] = _install_rtk()
    if install and not status["tools"]["caveman"]["before"]["installed"]:
        status["tools"]["caveman"]["attempts"] = _install_caveman()
    status["tools"]["rtk"]["after"] = _check("rtk")
    status["tools"]["caveman"]["after"] = _check("caveman")
    path = root / ".ai-workflow" / "install_status.json"
    try:
        path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        pass
    return status
