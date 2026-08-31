#!/usr/bin/env python3
"""Build the portable AI-readable explainer bundle deterministically."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reference_material" / "ai_native_workflow"
OUTPUT = BASE / "AI_NATIVE_WORKFLOW_FULL_AI_EXPLAINER.zip"
FIXED_TIME = (2026, 8, 31, 0, 0, 0)


def main() -> int:
    members: list[tuple[str, bytes]] = []
    for dirname in (".aiexplainer", "papers", "prompting"):
        for path in sorted((BASE / dirname).rglob("*"), key=lambda p: p.as_posix()):
            if path.is_file():
                members.append((path.relative_to(BASE).as_posix(), path.read_bytes()))
    manifest = {
        "schema_version": 1,
        "built_utc_date": "2026-08-31",
        "members": {name: hashlib.sha256(data).hexdigest() for name, data in members},
        "source_package": {
            "path": "source_package/AI_Native_Workflow_v5.6.35_Deadline_Experiment_Ready_Repository.zip",
            "sha256": "2df995c1eb3e0fc144e0e82555d96584d5b4bad108d916754a70ac6412873cb7",
            "included_in_bundle": False,
        },
    }
    members.append(("BUNDLE_MANIFEST.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()))
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in members:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    print(f"wrote {OUTPUT} with {len(members)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
