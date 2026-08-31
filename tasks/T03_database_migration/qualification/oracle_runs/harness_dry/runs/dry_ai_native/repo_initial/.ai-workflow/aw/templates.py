from __future__ import annotations
from pathlib import Path
from .errors import WorkflowError


def template_root() -> Path:
    return Path(__file__).resolve().parent / "templates"


def render_template(relative: str, replacements: dict[str, str] | None = None) -> str:
    path = template_root() / relative
    if not path.is_file():
        raise WorkflowError(f"Missing installed template: {path}")
    text = path.read_text(encoding="utf-8")
    for key, value in (replacements or {}).items():
        text = text.replace("{{" + key + "}}", value)
    return text
