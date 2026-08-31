from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

from aw.config import (
    cmd_config_set,
    cmd_root_auto,
    cmd_root_env,
    cmd_root_set,
    load_config,
    save_config,
)
from aw.context import managed_context_sha256
from aw.errors import WorkflowError
from aw.minor import (
    cmd_minor_add,
    cmd_minor_approve,
    cmd_minor_done,
    cmd_minor_from_user,
    cmd_minor_promote,
    cmd_minor_sample,
    minor_summary,
)
from aw.models import resolve_routing
from aw.phase import cmd_approval_record, cmd_init, cmd_phase_close, cmd_phase_init, cmd_phase_plan_next, scope_hash
from aw.prompts import cmd_prompt_add, cmd_prompt_set, cmd_prompt_supersede, load_registry, ready_prompts
from aw.requests import cmd_request_add, cmd_request_block, cmd_request_reopen, cmd_request_verify, parse_requests
from aw.status import build_status
from aw.update import cmd_update
from aw.validation import validate_phase


def ns(**kwargs):
    return argparse.Namespace(**kwargs)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(PACKAGE, self.root / ".ai-workflow")
        with redirect_stdout(io.StringIO()):
            cmd_init(ns(
                root=str(self.root), project_name="test", phase=None,
                mode=None, execution_level=None, research_level=None,
                test_profile=None, routing_profile=None, root_mode=None,
                declared_root=None, available_model=None, surface=None,
                rough_input=None, approval_phrase=None, architecture=None,
                no_update=False,
            ))

    def tearDown(self):
        self.temp.cleanup()

    def phase(self, mode="goal", name="phase_01_test", **kwargs):
        defaults = dict(
            root=str(self.root), name=name, mode=mode, execution_level=None,
            research_level=None, test_profile=None, research=False,
            architecture=(True if mode == "structured" else False),
            copy_templates=True, activate=True, from_handoff=None,
            rough_input="preserved rough input", approval_phrase="GO",
            suppress_output=True,
        )
        defaults.update(kwargs)
        cmd_phase_init(ns(**defaults))
        return self.root / "phases" / name

    def add_goal_acceptance(self, phase: Path, text="Deliver the requested outcome", acceptance="Verifier confirms exact evidence"):
        goal = phase / "GOAL.md"
        raw = goal.read_text(encoding="utf-8")
        raw += f"\n- [ ] G-001 — {text}\n  - Acceptance: {acceptance}\n"
        goal.write_text(raw, encoding="utf-8")

    def add_structured_request(self, text="Deliver work", acceptance="Tests pass"):
        with redirect_stdout(io.StringIO()):
            cmd_request_add(ns(root=str(self.root), phase=None, id=None, text=text, acceptance=[acceptance]))

    def approve(self):
        with redirect_stdout(io.StringIO()):
            return cmd_approval_record(ns(root=str(self.root), phase=None, text="GO", no_advance=False))

    def integrate_001(self):
        phase = self.root / "phases" / "phase_01_test"
        registry = load_registry(phase)
        prompt_id = "GOAL" if any(p.get("id") == "GOAL" for p in registry.get("prompts", [])) else "000"
        evidence_path = "logs/goal.md" if prompt_id == "GOAL" else "logs/001.md"
        for status, evidence in [("running", None), ("completed", evidence_path), ("integrated", evidence_path)]:
            with redirect_stdout(io.StringIO()):
                cmd_prompt_set(ns(root=str(self.root), phase=None, id=prompt_id, status=status, actor="orchestrator", evidence=evidence, note=None))

    def prompt_args(self, **updates):
        values = dict(
            root=str(self.root), phase=None, id="02", title="Implement task",
            depends_on="GOAL", allowed="src/**,tests/**", forbidden="archive/**,.git/**",
            output=["src/task.py"], check=["pytest tests"], model_profile="worker",
            execution_level=None, test_profile=None, backend="real",
            evidence_level="implementation", rough_input="implement the task",
            no_approval=False, suppress_output=True,
        )
        values.update(updates)
        return ns(**values)

    # --- package/config/init ---

    def test_package_version_catalog_and_aw_entrypoint(self):
        catalog = json.loads((self.root / ".ai-workflow" / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["version"], "5.6.35")
        self.assertEqual(catalog["modes"], ["goal", "structured"])
        self.assertIn("all", catalog["routing_profiles"])
        pyproject = (self.root / ".ai-workflow" / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('version = "5.6.35"', pyproject)
        self.assertIn('aw = "aw.cli:main"', pyproject)
        legacy_alias = 'ai' + 'flow'
        self.assertNotIn(legacy_alias, pyproject)

    def test_init_with_phase_emits_one_json_and_inserts_context(self):
        other = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(other, ignore_errors=True))
        shutil.copytree(PACKAGE, other / ".ai-workflow")
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_init(ns(
                root=str(other), project_name="demo", phase="phase_01_demo",
                mode="goal", execution_level="high", research_level="none",
                test_profile="affected", routing_profile="all", root_mode="fixed",
                declared_root=str(other), available_model=["gpt-5.6-pro", "claude-sonnet-4.6"],
                surface=["chatgpt", "claude_code"], rough_input="rough objective",
                approval_phrase="GO", architecture=None, no_update=False,
            ))
        value = json.loads(out.getvalue())
        self.assertEqual(value["created_phase"], "phase_01_demo")
        prompt = other / "phases" / "phase_01_demo" / "GOAL.md"
        text = prompt.read_text(encoding="utf-8")
        self.assertIn(str(other), text)
        self.assertIn('routing_profile: "all"', text)
        self.assertNotIn("{{CONTEXT_SHA256}}", text)

    def test_models_all_profile_prefers_declared_available_option(self):
        config = load_config(self.root)
        config["models"]["available"] = ["claude-sonnet-4.6", "gpt-5.6-pro"]
        save_config(self.root, config)
        routing = resolve_routing(self.root, load_config(self.root))
        self.assertEqual(routing["roles"]["main"]["selected_preference"], "gpt-5.6-pro")
        self.assertEqual(routing["roles"]["orchestrator"]["selected_preference"], "claude-sonnet-4.6")

    def test_routing_profiles_chatgpt_and_claude_only(self):
        config = load_config(self.root)
        config["routing_profile"] = "chatgpt_only"
        save_config(self.root, config)
        self.assertTrue(resolve_routing(self.root, load_config(self.root))["roles"]["main"]["selected_preference"].startswith("gpt-5.6"))
        config = load_config(self.root)
        config["routing_profile"] = "claude_only"
        save_config(self.root, config)
        self.assertTrue(resolve_routing(self.root, load_config(self.root))["roles"]["main"]["selected_preference"].startswith("claude-"))

    def test_minor_location_is_not_configurable(self):
        with self.assertRaises(Exception):
            cmd_config_set(ns(root=str(self.root), key="minor.location", value="root"))
        with self.assertRaises(Exception):
            cmd_config_set(ns(root=str(self.root), key="minor.path", value="operations/minor"))

    def test_repository_root_modes(self):
        with redirect_stdout(io.StringIO()):
            cmd_root_set(ns(root=str(self.root), path=str(self.root)))
        self.assertEqual(load_config(self.root)["repository"]["root_mode"], "fixed")
        with redirect_stdout(io.StringIO()):
            cmd_root_env(ns(root=str(self.root), name="AW_TEST_ROOT"))
        self.assertEqual(load_config(self.root)["repository"]["root_mode"], "environment")
        with redirect_stdout(io.StringIO()):
            cmd_root_auto(ns(root=str(self.root)))
        self.assertEqual(load_config(self.root)["repository"]["root_mode"], "auto")

    # --- modes / GO / requests ---

    def test_goal_mode_initial_files_and_status(self):
        phase = self.phase("goal")
        self.assertTrue((phase / "GOAL.md").is_file())
        self.assertFalse((phase / "PLAN.md").exists())
        self.assertFalse((phase / "REQUESTS.md").exists())
        status = build_status(self.root)
        self.assertEqual(status["mode"], "goal")
        self.assertEqual(status["prompts"]["ready"], ["GOAL"])
        self.assertEqual(status["requests"]["total"], 0)

    def test_structured_mode_generates_full_pack_and_phase_minor(self):
        phase = self.phase("structured")
        for name in ("REQUESTS.md", "PLAN.md", "README.md", "USER_APPROVAL.md", "ARCHITECTURE.md"):
            self.assertTrue((phase / name).is_file(), name)
        self.assertFalse((phase / "minor").exists())  # auto lane is lazy; `aw minor` materializes it on first use
        self.assertTrue((phase / "templates" / "SCIENTIFIC_EXPERIMENT_PROMPT.md").is_file())
        self.assertGreater((phase / "templates" / "FULL_WORKER_PROMPT.md").stat().st_size, 3000)

    def test_goal_go_materializes_requests_and_advances(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase)
        self.approve()
        items = parse_requests(phase / "REQUESTS.md")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "RQ-001")
        registry = load_registry(phase)
        self.assertEqual(next(p for p in registry["prompts"] if p["id"] == "GOAL")["status"], "ready")

    def test_structured_go_requires_acceptance_request(self):
        self.phase("structured")
        with self.assertRaises(Exception):
            self.approve()
        self.add_structured_request(acceptance="Named verifier evidence exists")
        self.approve()

    def test_scope_hash_ignores_request_checkbox_but_detects_goal_change(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase)
        self.approve()
        approved_hash = scope_hash(phase)
        with redirect_stdout(io.StringIO()):
            cmd_request_verify(ns(root=str(self.root), phase=None, id="RQ-001", evidence="verification/final.md", actor="verifier", note=None))
        self.assertEqual(approved_hash, scope_hash(phase))
        (phase / "GOAL.md").write_text((phase / "GOAL.md").read_text(encoding="utf-8") + "\nMaterial change.\n", encoding="utf-8")
        errors, _ = validate_phase(self.root, phase)
        self.assertTrue(any("scope hash" in error for error in errors))

    def test_request_only_verifier_can_complete_and_reopen(self):
        phase = self.phase("structured")
        self.add_structured_request(acceptance="Tests pass")
        with self.assertRaises(Exception):
            cmd_request_verify(ns(root=str(self.root), phase=None, id="RQ-001", evidence="v.md", actor="worker", note=None))
        with redirect_stdout(io.StringIO()):
            cmd_request_verify(ns(root=str(self.root), phase=None, id="RQ-001", evidence="v.md", actor="verifier", note=None))
        self.assertTrue(parse_requests(phase / "REQUESTS.md")[0]["verified"])
        with redirect_stdout(io.StringIO()):
            cmd_request_reopen(ns(root=str(self.root), phase=None, id="RQ-001", reason="regression"))
        self.assertFalse(parse_requests(phase / "REQUESTS.md")[0]["verified"])

    # --- update/config-managed prompts ---

    def test_aw_update_refreshes_safe_prompt_context_from_config(self):
        phase = self.phase("goal")
        old = managed_context_sha256(self.root, phase)
        config = load_config(self.root)
        config["routing_profile"] = "chatgpt_only"
        config["models"]["available"] = ["gpt-5.6-pro", "gpt-5.6-terra"]
        save_config(self.root, config)
        self.assertNotEqual(old, managed_context_sha256(self.root, phase))
        status = build_status(self.root)
        self.assertEqual(set(status["prompts"]["stale_context"]), {"GOAL"})
        with redirect_stdout(io.StringIO()):
            cmd_update(ns(root=str(self.root), phase=None, all_phases=False, dry_run=False, include_frozen=False, no_root_files=False))
        registry = load_registry(phase)
        self.assertEqual(registry["routing_profile"], "chatgpt_only")
        self.assertEqual(registry["context_sha256"], managed_context_sha256(self.root, phase))
        text = (phase / "GOAL.md").read_text(encoding="utf-8")
        self.assertIn('routing_profile: "chatgpt_only"', text)
        self.assertNotIn('routing_profile: "all"', text)
        self.assertIn('preferred: "gpt-5.6-pro"', text)
        phase_readme = (phase / "README.md").read_text(encoding="utf-8")
        self.assertIn('routing_profile: "chatgpt_only"', phase_readme)
        errors, _ = validate_phase(self.root, phase)
        self.assertEqual(errors, [])

    def test_update_skips_terminal_prompts_by_default(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase)
        self.approve()
        self.integrate_001()
        before = (phase / "GOAL.md").read_text(encoding="utf-8")
        config = load_config(self.root); config["routing_profile"] = "claude_only"; save_config(self.root, config)
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_update(ns(root=str(self.root), phase=None, all_phases=False, dry_run=False, include_frozen=False, no_root_files=True))
        result = json.loads(out.getvalue())
        self.assertTrue(any(row["prompt_id"] == "GOAL" for row in result["phases"][0]["skipped"]))
        self.assertEqual(before, (phase / "GOAL.md").read_text(encoding="utf-8"))

    def test_update_include_frozen_refreshes_terminal_context(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve(); self.integrate_001()
        config = load_config(self.root); config["routing_profile"] = "claude_only"; save_config(self.root, config)
        with redirect_stdout(io.StringIO()):
            cmd_update(ns(root=str(self.root), phase=None, all_phases=False, dry_run=False, include_frozen=True, no_root_files=True))
        text = (phase / "GOAL.md").read_text(encoding="utf-8")
        self.assertIn('routing_profile: "claude_only"', text)

    def test_aw_update_dry_run_does_not_change_prompt(self):
        phase = self.phase("goal")
        prompt = phase / "GOAL.md"
        before = prompt.read_bytes()
        config = load_config(self.root); config["routing_profile"] = "claude_only"; save_config(self.root, config)
        with redirect_stdout(io.StringIO()):
            cmd_update(ns(root=str(self.root), phase=None, all_phases=False, dry_run=True, include_frozen=False, no_root_files=True))
        self.assertEqual(before, prompt.read_bytes())

    def test_update_refreshes_structured_copied_prompt_templates(self):
        phase = self.phase("structured")
        target = phase / "templates" / "FULL_WORKER_PROMPT.md"
        before = target.read_text(encoding="utf-8")
        self.assertIn('routing_profile: "all"', before)
        config = load_config(self.root)
        config["routing_profile"] = "claude_only"
        config["models"]["available"] = ["claude-sonnet-4.6"]
        save_config(self.root, config)
        with redirect_stdout(io.StringIO()):
            cmd_update(ns(root=str(self.root), phase=None, all_phases=False, dry_run=False, include_frozen=False, no_root_files=True))
        after = target.read_text(encoding="utf-8")
        self.assertIn('routing_profile: "claude_only"', after)
        self.assertIn('preferred: "claude-sonnet-4.6"', after)

    # --- prompt lifecycle ---

    def test_prompt_add_records_model_test_backend_evidence_and_prints(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve(); self.integrate_001()
        with redirect_stdout(io.StringIO()):
            cmd_prompt_add(self.prompt_args())
        record = next(p for p in load_registry(phase)["prompts"] if p["id"] == "02")
        self.assertEqual(record["test_profile"], "affected")
        self.assertEqual(record["backend_kind"], "real")
        self.assertEqual(record["evidence_target"], "implementation")
        self.assertTrue(record["model_options"])
        body = (phase / record["file"]).read_text(encoding="utf-8")
        self.assertIn("## Active workflow configuration", body)
        self.assertIn("Backend target: `real`", body)

    def test_prompt_lifecycle_role_enforcement(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve(); self.integrate_001()
        with redirect_stdout(io.StringIO()): cmd_prompt_add(self.prompt_args())
        with self.assertRaises(Exception):
            cmd_prompt_set(ns(root=str(self.root), phase=None, id="02", status="verified", actor="worker", evidence="v.md", note=None))
        with redirect_stdout(io.StringIO()):
            cmd_prompt_set(ns(root=str(self.root), phase=None, id="02", status="running", actor="worker", evidence=None, note=None))
            cmd_prompt_set(ns(root=str(self.root), phase=None, id="02", status="completed", actor="worker", evidence="logs/02.md", note=None))
        with self.assertRaises(Exception):
            cmd_prompt_set(ns(root=str(self.root), phase=None, id="02", status="integrated", actor="worker", evidence="logs/02.md", note=None))
        with redirect_stdout(io.StringIO()):
            cmd_prompt_set(ns(root=str(self.root), phase=None, id="02", status="integrated", actor="orchestrator", evidence="logs/02.md", note=None))
            cmd_prompt_set(ns(root=str(self.root), phase=None, id="02", status="verified", actor="verifier", evidence="verification/02.md", note=None))

    def test_prompt_supersession_dependency_waits_for_replacement(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve(); self.integrate_001()
        with redirect_stdout(io.StringIO()):
            cmd_prompt_add(self.prompt_args(id="02", title="Original"))
            cmd_prompt_add(self.prompt_args(id="02A", title="Replacement"))
            cmd_prompt_add(self.prompt_args(id="03", title="Downstream", depends_on="02", output=["src/down.py"]))
            cmd_prompt_supersede(ns(root=str(self.root), phase=None, id="02", replacement="02A", reason="contract repair"))
        self.assertNotIn("03", ready_prompts(load_registry(phase)))
        for status, evidence in [("running", None), ("completed", "logs/02A.md"), ("integrated", "logs/02A.md")]:
            with redirect_stdout(io.StringIO()):
                cmd_prompt_set(ns(root=str(self.root), phase=None, id="02A", status=status, actor="orchestrator", evidence=evidence, note=None))
        self.assertIn("03", ready_prompts(load_registry(phase)))

    def test_validator_rejects_output_outside_allowed_paths(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve(); self.integrate_001()
        with redirect_stdout(io.StringIO()):
            cmd_prompt_add(self.prompt_args(allowed="docs/**", output=["src/bad.py"]))
        errors, _ = validate_phase(self.root, phase)
        self.assertTrue(any("outside allowed paths" in e for e in errors))

    # --- Minor lane ---

    def test_minor_inherits_phase_approval_and_requires_log(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve()
        with redirect_stdout(io.StringIO()):
            cmd_minor_add(ns(root=str(self.root), phase=None, type="fix", title="Fix typo", request="Fix typo", interpretation=None, files="README.md", checks="review", approval=None, suppress_output=False))
        self.assertIn("approved_by_phase", (phase / "minor" / "REQUESTS.md").read_text(encoding="utf-8"))
        with self.assertRaises(Exception):
            cmd_minor_done(ns(root=str(self.root), phase=None, id="MF-01", status="completed", files="README.md", checks="review", log=None, caveats=None))
        with redirect_stdout(io.StringIO()):
            cmd_minor_done(ns(root=str(self.root), phase=None, id="MF-01", status="completed", files="README.md", checks="review", log="phases/phase_01_test/minor/logs/MF-01.md", caveats=None))
        self.assertEqual(minor_summary(phase / "minor")["counts"]["completed"], 1)

    def test_minor_request_specific_approval(self):
        phase = self.phase("goal")
        with redirect_stdout(io.StringIO()):
            cmd_minor_add(ns(root=str(self.root), phase=None, type="fix", title="Fix typo", request="Fix typo", interpretation=None, files="README.md", checks="review", approval="request", suppress_output=False))
        with self.assertRaises(Exception):
            cmd_minor_done(ns(root=str(self.root), phase=None, id="MF-01", status="completed", files="README.md", checks="review", log="x.md", caveats=None))
        with redirect_stdout(io.StringIO()):
            cmd_minor_approve(ns(root=str(self.root), phase=None, id="MF-01", confirmation="GO MinorFix 01"))
            cmd_minor_done(ns(root=str(self.root), phase=None, id="MF-01", status="completed", files="README.md", checks="review", log="x.md", caveats=None))
        errors, _ = validate_phase(self.root, phase)
        self.assertEqual(errors, [])

    def test_minor_from_user_splits_tasks_with_single_json(self):
        phase = self.phase("goal")
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_minor_from_user(ns(root=str(self.root), phase=None, input="fix broken links and update current status", files="README.md,reports/STATUS.md", checks="review", approval="request"))
        value = json.loads(out.getvalue())
        self.assertEqual(len(value["requests"]), 2)
        self.assertEqual([x["type"] for x in value["requests"]], ["fix", "update"])
        self.assertIn("MF-01", (phase / "minor" / "REQUESTS.md").read_text(encoding="utf-8"))
        self.assertIn("MU-01", (phase / "minor" / "REQUESTS.md").read_text(encoding="utf-8"))

    def test_minor_promote_creates_prompt_and_preserves_history(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve(); self.integrate_001()
        with redirect_stdout(io.StringIO()):
            cmd_minor_add(ns(root=str(self.root), phase=None, type="fix", title="Unexpected architecture issue", request="Repair architecture issue", interpretation="Needs source change", files="src/**", checks="pytest", approval=None, suppress_output=False))
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_minor_promote(ns(root=str(self.root), phase=None, id="MF-01", to_prompt="02A", title=None, depends_on="GOAL", output=["src/fix.py"], check=["pytest"], model_profile="worker_complex", execution_level="high", test_profile="integration", backend="real", evidence_level="implementation"))
        value = json.loads(out.getvalue())
        self.assertEqual(value["replacement_prompt"], "02A")
        self.assertIn("Promotion — MF-01", (phase / "minor" / "REQUESTS.md").read_text(encoding="utf-8"))
        self.assertTrue((phase / "prompts" / "prompt_02A_promoted_mf_01.md").is_file())

    def test_minor_samples_are_phase_local_and_full(self):
        self.phase("goal")
        for kind, approval in [("fix", "GO MinorFix 01"), ("update", "GO MinorUpdate 01"), ("report", "GO MinorReport 01")]:
            target = self.root / f"{kind}.md"
            with redirect_stdout(io.StringIO()):
                cmd_minor_sample(ns(root=str(self.root), phase=None, type=kind, rough_input="rough task", write=str(target)))
            text = target.read_text(encoding="utf-8")
            self.assertIn(str(self.root), text)
            self.assertIn("phase-local", text)
            self.assertIn(approval, text)
            self.assertIn("## Active workflow configuration", text)

    # --- next phase / CLI / validation ---

    def test_plan_next_creates_structured_phase_with_context(self):
        current = self.phase("goal")
        self.add_goal_acceptance(current); self.approve(); self.integrate_001()
        with redirect_stdout(io.StringIO()):
            cmd_request_verify(ns(root=str(self.root), phase=None, id="RQ-001", evidence="verification/final.md", actor="verifier", note=None))
            cmd_phase_close(ns(root=str(self.root), phase=None, actor="verifier", evidence="verification/final.md", note=None))
        (current / "reports" / "FINAL_HANDOFF.md").write_text("# Handoff\nVerified.\n")
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_phase_plan_next(ns(
                root=str(self.root), phase=None, name="phase_02_next", mode="structured",
                execution_level="high", research_level="mid", test_profile="integration",
                from_handoff=None, rough_input="continue verified work", architecture=True,
                copy_templates=True, activate=False, approval_phrase="GO NEXT", create=True,
            ))
        value = json.loads(out.getvalue())
        self.assertTrue(value["created"])
        created = self.root / "phases" / "phase_02_next"
        self.assertTrue((created / "PLAN.md").is_file())
        self.assertIn("continue verified work", (created / "prompts" / "prompt_000_orchestrator_init.md").read_text(encoding="utf-8"))
        errors, _ = validate_phase(self.root, created)
        self.assertEqual(errors, [])

    def test_cli_root_option_anywhere_status_update_and_models(self):
        script = self.root / ".ai-workflow" / "aw.py"
        for command in [
            ["status", "--root", str(self.root)],
            ["--root", str(self.root), "models", "show"],
            ["update", "--root", str(self.root), "--dry-run"],
        ]:
            result = subprocess.run([sys.executable, str(script), *command], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_status_without_phase_is_read_only(self):
        other = Path(tempfile.mkdtemp()); self.addCleanup(lambda: shutil.rmtree(other, ignore_errors=True))
        shutil.copytree(PACKAGE, other / ".ai-workflow")
        with redirect_stdout(io.StringIO()):
            cmd_init(ns(root=str(other), project_name="x", phase=None, mode=None, execution_level=None, research_level=None, test_profile=None, routing_profile=None, root_mode=None, declared_root=None, available_model=None, surface=None, rough_input=None, approval_phrase=None, architecture=None, no_update=False))
        before = sorted(p.relative_to(other).as_posix() for p in other.rglob("*"))
        status = build_status(other)
        after = sorted(p.relative_to(other).as_posix() for p in other.rglob("*"))
        self.assertIsNone(status["phase"])
        self.assertEqual(before, after)

    def test_reports_allow_raw_files_but_reject_nested_directories(self):
        phase = self.phase("goal")
        (phase / "reports" / "RAW_RESULTS.jsonl").write_text('{"x":1}\n')
        errors, _ = validate_phase(self.root, phase)
        self.assertFalse(any("allowlist" in e for e in errors))
        (phase / "reports" / "nested").mkdir()
        errors, _ = validate_phase(self.root, phase)
        self.assertTrue(any("must be flat" in e for e in errors))

    def test_full_phase_validation_after_goal_go(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve()
        errors, warnings = validate_phase(self.root, phase)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_structured_approval_keeps_scope_hash_valid(self):
        phase = self.phase("structured")
        self.add_structured_request(acceptance="Verifier evidence exists")
        self.approve()
        errors, _ = validate_phase(self.root, phase)
        self.assertEqual(errors, [])
        with redirect_stdout(io.StringIO()):
            cmd_approval_record(ns(root=str(self.root), phase=None, text="GO", no_advance=False))

    def test_update_after_approval_ignores_generated_context_in_scope(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve()
        approved = scope_hash(phase)
        with redirect_stdout(io.StringIO()):
            cmd_config_set(ns(root=str(self.root), key="routing_profile", value="chatgpt_only"))
            cmd_update(ns(root=str(self.root), phase=None, all_phases=False, dry_run=False, include_frozen=False, no_root_files=False))
        self.assertEqual(approved, scope_hash(phase))
        errors, _ = validate_phase(self.root, phase)
        self.assertEqual(errors, [])

    def test_active_phase_level_config_propagates_and_mode_change_is_rejected(self):
        phase = self.phase("goal")
        with redirect_stdout(io.StringIO()):
            cmd_config_set(ns(root=str(self.root), key="execution_level", value="high"))
        self.assertEqual(build_status(self.root)["execution_level"], "high")
        self.assertEqual(set(build_status(self.root)["prompts"]["stale_context"]), {"GOAL"})
        with redirect_stdout(io.StringIO()):
            cmd_update(ns(root=str(self.root), phase=None, all_phases=False, dry_run=False, include_frozen=False, no_root_files=False))
        meta = json.loads((phase / "artifacts" / "phase.json").read_text(encoding="utf-8"))
        registry = load_registry(phase)
        self.assertEqual(meta["execution_level"], "high")
        self.assertEqual(registry["execution_level"], "high")
        self.assertEqual({p["execution_level"] for p in registry["prompts"]}, {"high"})
        self.assertEqual(build_status(self.root)["execution_level"], "high")
        with self.assertRaises(WorkflowError):
            cmd_config_set(ns(root=str(self.root), key="mode", value="structured"))

    def test_blocked_request_can_be_reopened_but_not_verified_while_blocked(self):
        phase = self.phase("structured")
        self.add_structured_request()
        with redirect_stdout(io.StringIO()):
            cmd_request_block(ns(root=str(self.root), phase=None, id="RQ-001", reason="dependency"))
        self.assertEqual(build_status(self.root)["requests"]["blocked"], ["RQ-001"])
        with self.assertRaises(WorkflowError):
            cmd_request_verify(ns(root=str(self.root), phase=None, id="RQ-001", evidence="v.md", actor="verifier", note=None))
        with redirect_stdout(io.StringIO()):
            cmd_request_reopen(ns(root=str(self.root), phase=None, id="RQ-001", reason="cleared"))
        self.assertEqual(build_status(self.root)["requests"]["open"], ["RQ-001"])

    def test_phase_close_requires_verification_and_enables_next_creation(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve()
        with self.assertRaises(WorkflowError):
            cmd_phase_close(ns(root=str(self.root), phase=None, actor="verifier", evidence="v.md", note=None))
        self.integrate_001()
        with redirect_stdout(io.StringIO()):
            cmd_request_verify(ns(root=str(self.root), phase=None, id="RQ-001", evidence="v.md", actor="verifier", note=None))
            cmd_phase_close(ns(root=str(self.root), phase=None, actor="verifier", evidence="v.md", note=None))
        meta = json.loads((phase / "artifacts" / "phase.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["status"], "closed")

    def test_status_reports_red_when_validation_fails(self):
        phase = self.phase("goal")
        self.add_goal_acceptance(phase); self.approve()
        with (phase / "GOAL.md").open("a", encoding="utf-8") as handle:
            handle.write("\nMaterial semantic change.\n")
        status = build_status(self.root)
        self.assertEqual(status["health"]["level"], "RED")
        self.assertFalse(status["validation"]["ok"])

    def test_malformed_config_and_unknown_key_are_controlled(self):
        with self.assertRaises(WorkflowError):
            cmd_config_set(ns(root=str(self.root), key="unknown.section", value="value"))
        with self.assertRaises(WorkflowError):
            cmd_config_set(ns(root=str(self.root), key="repository.root", value=str(self.root / "missing")))
        (self.root / ".ai-workflow" / "config.toml").write_text("mode = [invalid\n", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            load_config(self.root)

    def test_cli_outside_repository_does_not_fall_back_to_source(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(outside, ignore_errors=True))
        result = subprocess.run(
            [sys.executable, str(PACKAGE / "aw.py"), "status"],
            cwd=outside,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Could not find .ai-workflow/config.toml", result.stderr)

    def test_template_manifest_covers_all_templates(self):
        manifest = json.loads((self.root / ".ai-workflow" / "aw" / "templates" / "manifest.json").read_text(encoding="utf-8"))
        listed = {row["file"] for row in manifest["templates"]}
        actual = {p.relative_to(self.root / ".ai-workflow" / "aw" / "templates").as_posix() for p in (self.root / ".ai-workflow" / "aw" / "templates").rglob("*.md")}
        self.assertEqual(listed, actual)


if __name__ == "__main__":
    unittest.main()
