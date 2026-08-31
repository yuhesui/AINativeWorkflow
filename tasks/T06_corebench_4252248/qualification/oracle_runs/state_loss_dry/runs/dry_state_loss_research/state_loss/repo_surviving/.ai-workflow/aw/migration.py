from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path
from .errors import WorkflowError
from .filesystem import find_root, utc_now

LEGACY = [".ai-workflow-cli", ".ai-workflow-reference", ".ai-workflow-reference-light", ".ai-workflow-guide"]


def cmd_migrate(args: argparse.Namespace) -> int:
    root = find_root(args.root)
    present = [root / name for name in LEGACY if (root / name).exists()]
    destination = root / ".ai-workflow" / "legacy" / "pre_v5.6.30"
    plan = [{"source": str(path), "destination": str(destination / path.name)} for path in present]
    if not args.execute:
        print(json.dumps({"dry_run": True, "moves": plan, "note": "Use --execute after review"}, indent=2))
        return 0
    destination.mkdir(parents=True, exist_ok=True)
    for item in plan:
        source = Path(item["source"])
        target = Path(item["destination"])
        if target.exists():
            raise WorkflowError(f"Migration target exists: {target}")
        shutil.move(str(source), str(target))
    (destination / "MIGRATED_AT.txt").write_text(utc_now() + "\n", encoding="utf-8")
    print(json.dumps({"dry_run": False, "moves": plan, "destination": str(destination)}))
    return 0
