#!/usr/bin/env python3
"""Generate a self-excluding content manifest for the internal package."""

from __future__ import annotations

import json
from pathlib import Path

from eval_common import (
    file_sha256,
    files,
    is_dynamic_run_artifact,
    is_generated_runtime_archive,
    is_generated_runtime_copy,
)


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "PACKAGE_MANIFEST.json"


def main() -> int:
    entries: dict[str, dict[str, object]] = {}
    total_bytes = 0
    for path in files(ROOT):
        if path == DESTINATION:
            continue
        rel = path.relative_to(ROOT).as_posix()
        relative = path.relative_to(ROOT)
        if (
            is_dynamic_run_artifact(relative)
            or is_generated_runtime_archive(relative)
            or is_generated_runtime_copy(relative)
        ):
            continue
        size = path.stat().st_size
        entries[rel] = {"sha256": file_sha256(path), "bytes": size}
        total_bytes += size
    manifest = {
        "schema_version": 1,
        "package": "AI_Native_Workflow_Eval_v1.0_Frozen_Internal",
        "generated_utc_date": "2026-08-31",
        "self_excluded": "PACKAGE_MANIFEST.json",
        "dynamic_run_artifacts_excluded": True,
        "expanded_runtime_copies_excluded": True,
        "generated_runtime_archive_excluded": True,
        "file_count": len(entries),
        "bytes": total_bytes,
        "files": entries,
    }
    DESTINATION.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"file_count": len(entries), "bytes": total_bytes}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
