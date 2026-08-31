from __future__ import annotations

import argparse
import sys

from .config import (
    cmd_config_set,
    cmd_config_show,
    cmd_root_auto,
    cmd_root_env,
    cmd_root_set,
    cmd_root_show,
    load_config,
)
from .constants import (
    BACKEND_KINDS,
    EVIDENCE_LEVELS,
    EXECUTION_LEVELS,
    MINOR_TERMINAL,
    MODEL_PROFILES,
    MODES,
    RESEARCH_LEVELS,
    ROUTING_PROFILES,
    TEST_PROFILES,
    VERSION,
)
from .errors import WorkflowError
from .migration import cmd_migrate
from .minor import (
    cmd_minor_add,
    cmd_minor_approve,
    cmd_minor_done,
    cmd_minor_from_user,
    cmd_minor_init,
    cmd_minor_note,
    cmd_minor_promote,
    cmd_minor_sample,
    cmd_minor_show,
    cmd_minor_status,
)
from .models import (
    cmd_models_profile,
    cmd_models_set_available,
    cmd_models_set_surfaces,
    cmd_models_show,
)
from .phase import (
    cmd_approval_record,
    cmd_approval_show,
    cmd_init,
    cmd_phase_append,
    cmd_phase_close,
    cmd_phase_current,
    cmd_phase_init,
    cmd_phase_plan_next,
    cmd_phase_use,
)
from .prompts import (
    cmd_prompt_add,
    cmd_prompt_list,
    cmd_prompt_next,
    cmd_prompt_set,
    cmd_prompt_supersede,
)
from .requests import (
    cmd_request_add,
    cmd_request_block,
    cmd_request_list,
    cmd_request_reopen,
    cmd_request_verify,
)
from .status import cmd_status
from .update import cmd_update
from .validation import cmd_validate


def cmd_go(args: argparse.Namespace) -> int:
    from .filesystem import find_root
    root = find_root(args.root)
    phrase = str(load_config(root).get("approval_phrase", "GO"))
    forwarded = argparse.Namespace(root=str(root), phase=args.phase, text=phrase, no_advance=args.no_advance)
    return cmd_approval_record(forwarded)


def cmd_help(args: argparse.Namespace) -> int:
    args.parser.print_help()
    return 0


def _normalise_global_options(argv):
    values = list(sys.argv[1:] if argv is None else argv)
    root_value = None
    cleaned = []
    index = 0
    while index < len(values):
        token = values[index]
        if token == "--root":
            if index + 1 >= len(values):
                return values
            root_value = values[index + 1]
            index += 2
            continue
        if token.startswith("--root="):
            root_value = token.split("=", 1)[1]
            index += 1
            continue
        cleaned.append(token)
        index += 1
    return (["--root", root_value, *cleaned] if root_value is not None else cleaned)


def _json(parser):
    parser.add_argument("--json", action="store_true")


def _phase(parser):
    parser.add_argument("--phase")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aw", description="AI-Native Workflow v5.6.35")
    parser.add_argument("--root", default=None, help="Operational repository root; otherwise AW_REPO_ROOT/upward discovery is used")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("help", help="Show top-level CLI help")
    command.set_defaults(func=cmd_help, parser=parser)

    command = sub.add_parser("init", help="Initialize repository controls and optionally create the first phase")
    command.add_argument("--project-name")
    command.add_argument("--mode", choices=sorted(MODES))
    command.add_argument("--execution-level", choices=sorted(EXECUTION_LEVELS))
    command.add_argument("--research-level", choices=sorted(RESEARCH_LEVELS))
    command.add_argument("--test-profile", choices=sorted(TEST_PROFILES))
    command.add_argument("--routing-profile", choices=sorted(ROUTING_PROFILES))
    command.add_argument("--root-mode", choices=("auto", "fixed", "environment", "cwd"))
    command.add_argument("--declared-root")
    command.add_argument("--available-model", action="append")
    command.add_argument("--surface", action="append")
    command.add_argument("--phase", help="Optionally create and activate the first phase")
    command.add_argument("--rough-input")
    command.add_argument("--approval-phrase")
    command.add_argument("--architecture", action=argparse.BooleanOptionalAction, default=None)
    command.add_argument("--install-support-tools", action="store_true", help="Best-effort install of optional RTK and Caveman support tools; failures are non-fatal and recorded")
    command.add_argument("--no-update", action="store_true")
    command.set_defaults(func=cmd_init)

    command = sub.add_parser("update", help="Refresh config-managed context in safe prompts and root controls")
    _phase(command)
    command.add_argument("--all-phases", action="store_true")
    command.add_argument("--dry-run", action="store_true")
    command.add_argument("--include-frozen", action="store_true", help="Also update terminal prompt context blocks; use only when preserving historical semantics is acceptable")
    command.add_argument("--no-root-files", action="store_true")
    command.set_defaults(func=cmd_update)

    command = sub.add_parser("status")
    _phase(command)
    _json(command)
    command.add_argument("--full", action="store_true")
    command.set_defaults(func=cmd_status)

    command = sub.add_parser("go", help="Record the configured exact GO and continue immediately")
    _phase(command)
    command.add_argument("--no-advance", action="store_true")
    command.set_defaults(func=cmd_go)

    command = sub.add_parser("next", help="Show dependency-ready prompts and configured routing")
    _phase(command)
    _json(command)
    command.add_argument("--print", dest="print_prompt", action="store_true", help="Print the ready prompt body")
    command.add_argument("--id", help="Select a ready prompt when several are ready")
    command.set_defaults(func=cmd_prompt_next)

    root = sub.add_parser("root").add_subparsers(dest="root_command", required=True)
    command = root.add_parser("show"); _json(command); command.set_defaults(func=cmd_root_show)
    command = root.add_parser("set"); command.add_argument("path"); command.set_defaults(func=cmd_root_set)
    command = root.add_parser("auto"); command.set_defaults(func=cmd_root_auto)
    command = root.add_parser("env"); command.add_argument("--name", default="AW_REPO_ROOT"); command.set_defaults(func=cmd_root_env)

    config = sub.add_parser("config").add_subparsers(dest="config_command", required=True)
    command = config.add_parser("show"); _json(command); command.set_defaults(func=cmd_config_show)
    command = config.add_parser("set"); command.add_argument("key"); command.add_argument("value"); command.set_defaults(func=cmd_config_set)

    models = sub.add_parser("models").add_subparsers(dest="models_command", required=True)
    command = models.add_parser("show"); _json(command); command.set_defaults(func=cmd_models_show)
    command = models.add_parser("profile"); command.add_argument("profile", choices=sorted(ROUTING_PROFILES)); command.set_defaults(func=cmd_models_profile)
    command = models.add_parser("set-available"); command.add_argument("models", nargs="+"); command.set_defaults(func=cmd_models_set_available)
    command = models.add_parser("set-surfaces"); command.add_argument("surfaces", nargs="+"); command.set_defaults(func=cmd_models_set_surfaces)

    phase = sub.add_parser("phase").add_subparsers(dest="phase_command", required=True)
    command = phase.add_parser("init")
    command.add_argument("name")
    command.add_argument("--mode", choices=sorted(MODES))
    command.add_argument("--execution-level", choices=sorted(EXECUTION_LEVELS))
    command.add_argument("--research-level", choices=sorted(RESEARCH_LEVELS))
    command.add_argument("--test-profile", choices=sorted(TEST_PROFILES))
    command.add_argument("--research", action="store_true")
    command.add_argument("--architecture", action=argparse.BooleanOptionalAction, default=None)
    command.add_argument("--copy-templates", action=argparse.BooleanOptionalAction, default=None)
    command.add_argument("--activate", action=argparse.BooleanOptionalAction, default=True)
    command.add_argument("--from-handoff")
    command.add_argument("--rough-input")
    command.add_argument("--approval-phrase")
    command.set_defaults(func=cmd_phase_init)
    command = phase.add_parser("current"); _phase(command); command.set_defaults(func=cmd_phase_current)
    command = phase.add_parser("use"); command.add_argument("name"); command.set_defaults(func=cmd_phase_use)
    command = phase.add_parser("close")
    _phase(command)
    command.add_argument("--actor", default="verifier")
    command.add_argument("--evidence", required=True)
    command.add_argument("--note")
    command.set_defaults(func=cmd_phase_close)
    command = phase.add_parser("append")
    _phase(command)
    command.add_argument("--doc", choices=("goal", "requests", "plan", "readme", "architecture", "approval"), required=True)
    command.add_argument("--heading", required=True)
    command.add_argument("--body")
    command.add_argument("--body-file")
    command.set_defaults(func=cmd_phase_append)
    command = phase.add_parser("plan-next")
    _phase(command)
    command.add_argument("name")
    command.add_argument("--mode", choices=sorted(MODES))
    command.add_argument("--execution-level", choices=sorted(EXECUTION_LEVELS))
    command.add_argument("--research-level", choices=sorted(RESEARCH_LEVELS))
    command.add_argument("--test-profile", choices=sorted(TEST_PROFILES))
    command.add_argument("--from-handoff")
    command.add_argument("--rough-input")
    command.add_argument("--architecture", action=argparse.BooleanOptionalAction, default=None)
    command.add_argument("--copy-templates", action=argparse.BooleanOptionalAction, default=None)
    command.add_argument("--activate", action=argparse.BooleanOptionalAction, default=True)
    command.add_argument("--approval-phrase")
    command.add_argument("--create", action="store_true")
    command.set_defaults(func=cmd_phase_plan_next)

    approval = sub.add_parser("approval").add_subparsers(dest="approval_command", required=True)
    command = approval.add_parser("show"); _phase(command); _json(command); command.set_defaults(func=cmd_approval_show)
    command = approval.add_parser("record"); _phase(command); command.add_argument("--text", required=True); command.add_argument("--no-advance", action="store_true"); command.set_defaults(func=cmd_approval_record)

    request = sub.add_parser("request").add_subparsers(dest="request_command", required=True)
    command = request.add_parser("add")
    _phase(command)
    command.add_argument("--id")
    command.add_argument("--text", required=True)
    command.add_argument("--acceptance", action="append", help="Repeat for multiple acceptance criteria")
    command.set_defaults(func=cmd_request_add)
    command = request.add_parser("list"); _phase(command); _json(command); command.set_defaults(func=cmd_request_list)
    command = request.add_parser("verify"); _phase(command); command.add_argument("--id", required=True); command.add_argument("--evidence", required=True); command.add_argument("--actor", default="verifier"); command.add_argument("--note"); command.set_defaults(func=cmd_request_verify)
    command = request.add_parser("block"); _phase(command); command.add_argument("--id", required=True); command.add_argument("--reason", required=True); command.set_defaults(func=cmd_request_block)
    command = request.add_parser("reopen"); _phase(command); command.add_argument("--id", required=True); command.add_argument("--reason", required=True); command.set_defaults(func=cmd_request_reopen)

    prompt = sub.add_parser("prompt").add_subparsers(dest="prompt_command", required=True)
    command = prompt.add_parser("add")
    _phase(command)
    command.add_argument("--id", required=True)
    command.add_argument("--title", required=True)
    command.add_argument("--depends-on")
    command.add_argument("--allowed")
    command.add_argument("--forbidden")
    command.add_argument("--output", action="append")
    command.add_argument("--check", action="append")
    command.add_argument("--model-profile", choices=sorted(MODEL_PROFILES), default="worker")
    command.add_argument("--execution-level", choices=sorted(EXECUTION_LEVELS))
    command.add_argument("--test-profile", choices=sorted(TEST_PROFILES))
    command.add_argument("--backend", choices=sorted(BACKEND_KINDS), default="unspecified")
    command.add_argument("--evidence-level", choices=sorted(EVIDENCE_LEVELS), default="implementation")
    command.add_argument("--rough-input")
    command.add_argument("--no-approval", action="store_true")
    command.set_defaults(func=cmd_prompt_add)
    command = prompt.add_parser("list"); _phase(command); _json(command); command.set_defaults(func=cmd_prompt_list)
    command = prompt.add_parser("next"); _phase(command); _json(command); command.add_argument("--print", dest="print_prompt", action="store_true"); command.add_argument("--id"); command.set_defaults(func=cmd_prompt_next)
    command = prompt.add_parser("set"); _phase(command); command.add_argument("--id", required=True); command.add_argument("--status", required=True); command.add_argument("--actor", default="orchestrator"); command.add_argument("--evidence"); command.add_argument("--note"); command.set_defaults(func=cmd_prompt_set)
    command = prompt.add_parser("supersede"); _phase(command); command.add_argument("--id", required=True); command.add_argument("--replacement", required=True); command.add_argument("--reason", required=True); command.set_defaults(func=cmd_prompt_supersede)

    minor = sub.add_parser("minor").add_subparsers(dest="minor_command", required=True)
    command = minor.add_parser("init"); _phase(command); command.set_defaults(func=cmd_minor_init)
    command = minor.add_parser("add")
    _phase(command)
    command.add_argument("--type", choices=("fix", "update", "report"), default="fix")
    command.add_argument("--title", required=True)
    command.add_argument("--request", required=True)
    command.add_argument("--interpretation")
    command.add_argument("--files")
    command.add_argument("--checks")
    command.add_argument("--approval", choices=("auto", "request", "phase", "none"))
    command.set_defaults(func=cmd_minor_add)
    command = minor.add_parser("from-user")
    _phase(command)
    command.add_argument("--input", required=True)
    command.add_argument("--files")
    command.add_argument("--checks")
    command.add_argument("--approval", choices=("auto", "request", "phase", "none"))
    command.set_defaults(func=cmd_minor_from_user)
    command = minor.add_parser("show"); _phase(command); command.add_argument("--id"); command.set_defaults(func=cmd_minor_show)
    command = minor.add_parser("note"); _phase(command); command.add_argument("--id", required=True); command.add_argument("--heading", required=True); command.add_argument("--body", required=True); command.add_argument("--actor", default="orchestrator"); command.set_defaults(func=cmd_minor_note)
    command = minor.add_parser("approve"); _phase(command); command.add_argument("--id", required=True); command.add_argument("--confirmation", required=True); command.set_defaults(func=cmd_minor_approve)
    command = minor.add_parser("done"); _phase(command); command.add_argument("--id", required=True); command.add_argument("--status", choices=sorted(MINOR_TERMINAL), default="completed"); command.add_argument("--files"); command.add_argument("--checks"); command.add_argument("--log"); command.add_argument("--caveats"); command.set_defaults(func=cmd_minor_done)
    command = minor.add_parser("promote")
    _phase(command)
    command.add_argument("--id", required=True)
    command.add_argument("--to-prompt", required=True)
    command.add_argument("--title")
    command.add_argument("--depends-on")
    command.add_argument("--output", action="append")
    command.add_argument("--check", action="append")
    command.add_argument("--model-profile", choices=sorted(MODEL_PROFILES), default="worker")
    command.add_argument("--execution-level", choices=sorted(EXECUTION_LEVELS))
    command.add_argument("--test-profile", choices=sorted(TEST_PROFILES))
    command.add_argument("--backend", choices=sorted(BACKEND_KINDS), default="unspecified")
    command.add_argument("--evidence-level", choices=sorted(EVIDENCE_LEVELS), default="implementation")
    command.set_defaults(func=cmd_minor_promote)
    command = minor.add_parser("status"); _phase(command); _json(command); command.set_defaults(func=cmd_minor_status)
    command = minor.add_parser("sample"); _phase(command); command.add_argument("--type", choices=("fix", "update", "report"), default="fix"); command.add_argument("--rough-input", default="<rough user input>"); command.add_argument("--write"); command.set_defaults(func=cmd_minor_sample)

    command = sub.add_parser("validate"); _phase(command); _json(command); command.set_defaults(func=cmd_validate)
    command = sub.add_parser("verify", help="Compatibility alias for validate"); _phase(command); _json(command); command.set_defaults(func=cmd_validate)
    command = sub.add_parser("migrate"); command.add_argument("--dry-run", action="store_true"); command.add_argument("--execute", action="store_true"); command.set_defaults(func=cmd_migrate)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(_normalise_global_options(argv))
    if getattr(args, "dry_run", False) and getattr(args, "execute", False):
        print("ERROR: use only one of --dry-run or --execute", file=sys.stderr)
        return 2
    try:
        return int(args.func(args))
    except WorkflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"FILESYSTEM ERROR: {exc}", file=sys.stderr)
        return 2
