from __future__ import annotations
import contextlib
import datetime as dt
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterator
from .errors import WorkflowError


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _candidate_starts(start: str | Path | None) -> list[Path]:
    values: list[Path] = []
    if start not in {None, ""}:
        values.append(Path(start).expanduser())
    env_root = os.environ.get("AW_REPO_ROOT")
    if env_root:
        values.append(Path(env_root).expanduser())
    values.append(Path.cwd())
    result: list[Path] = []
    seen: set[str] = set()
    for value in values:
        try:
            resolved = value.resolve()
        except OSError:
            continue
        key = str(resolved).casefold()
        if key not in seen:
            seen.add(key); result.append(resolved)
    return result


def find_root(start: str | Path | None = None) -> Path:
    searched: list[str] = []
    for initial in _candidate_starts(start):
        p = initial.parent if initial.is_file() else initial
        for candidate in [p, *p.parents]:
            searched.append(str(candidate))
            if (candidate / ".ai-workflow" / "config.toml").is_file():
                return candidate
    raise WorkflowError("Could not find .ai-workflow/config.toml; searched: " + ", ".join(searched[:12]))


def ensure_contained(path: Path, root: Path) -> Path:
    path = path.expanduser().resolve(strict=False)
    root = root.expanduser().resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise WorkflowError(f"Path escapes allowed root: {path}") from exc
    return path


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid JSON: {path}: {exc}") from exc


def write_if_absent(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_dir():
            raise WorkflowError(f"Expected file but found directory: {path}")
        return "skipped"
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return "created"


@contextlib.contextmanager
def locked_append(path: Path) -> Iterator[Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8", newline="\n")
    try:
        if os.name != "nt":
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0, os.SEEK_END)
        yield handle
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        if os.name != "nt":
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def append_text(path: Path, text: str) -> None:
    with locked_append(path) as handle:
        if handle.tell() > 0 and not text.startswith("\n"):
            handle.write("\n")
        handle.write(text.rstrip() + "\n")


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    with locked_append(path) as handle:
        handle.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())
