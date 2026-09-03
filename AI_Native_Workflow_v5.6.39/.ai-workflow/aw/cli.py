"""Command-line interface for the reference runtime."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .demo import write_demo
from .store import WorkflowError, WorkflowStore


def _store(args: argparse.Namespace) -> WorkflowStore:
    return WorkflowStore(Path(args.root))


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aw", description="AI Native Workflow reference runtime")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="initialize package-local state")
    init.add_argument("--project-name", default="Project")
    init.add_argument("--overwrite", action="store_true")

    sub.add_parser("status", help="show compact workflow status")
    sub.add_parser("recover", help="reconstruct and validate hierarchy")
    sub.add_parser("validate", help="exit non-zero when recovery validation fails")

    phase = sub.add_parser("phase", help="Phase package operations")
    phase_sub = phase.add_subparsers(dest="phase_command", required=True)
    phase_import = phase_sub.add_parser("import", help="safely import a Main-authored Phase ZIP")
    phase_import.add_argument("archive", help="path to Phase ZIP")

    demo = sub.add_parser("demo", help="run deterministic repair-to-accept demo")
    demo.add_argument("--output", default="demo_trace.json")
    demo.add_argument("--workspace", default=None, help="optional persistent demo repository")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            _print(_store(args).initialize(project_name=args.project_name, overwrite=args.overwrite))
            return 0
        if args.command == "status":
            _print(_store(args).status())
            return 0
        if args.command in {"recover", "validate"}:
            result = _store(args).recover()
            _print(result)
            return 0 if result["ok"] else 1
        if args.command == "phase" and args.phase_command == "import":
            _print(_store(args).import_phase_zip(args.archive))
            return 0
        if args.command == "demo":
            result = write_demo(args.output, args.workspace)
            _print(result)
            return 0 if result["recovery"]["ok"] else 1
    except WorkflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    parser.error("unhandled command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
