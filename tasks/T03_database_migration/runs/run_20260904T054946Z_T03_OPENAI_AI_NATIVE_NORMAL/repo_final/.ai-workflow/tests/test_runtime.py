from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from aw.demo import run_demo  # noqa: E402
from aw.impact import dependency_impact_cone  # noqa: E402
from aw.store import CORE_DIC_VIEWS, WorkflowError, WorkflowStore  # noqa: E402


class RuntimeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir(parents=True)
        source_runtime = WORKFLOW_ROOT
        shutil.copytree(source_runtime, self.root / ".ai-workflow", dirs_exist_ok=True)
        self.store = WorkflowStore(self.root)
        self.store.initialize(project_name="Test", overwrite=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @staticmethod
    def views() -> dict[str, str]:
        return {
            "README.md": "# Phase\n",
            "REQUESTS.md": "# Requests\n- [ ] observable outcome\n",
            "PLAN.md": "# Graph\nA -> B\n",
        }

    @staticmethod
    def nodes() -> dict[str, dict[str, object]]:
        return {
            "a": {"title": "A", "writes": ["x"]},
            "b": {"title": "B", "depends_on": ["a"], "reads": ["x"], "writes": ["y"]},
            "c": {"title": "C", "parallel_group": "independent", "subagent": True, "writes": ["z"]},
        }

    def make_ready(self) -> None:
        self.store.create_plan("p", title="Plan", goal="Goal")
        self.store.create_phase("p", "ph", title="Phase")
        self.store.create_dic("p", "ph", dic_id="d", views=self.views(), plan_nodes=self.nodes())
        self.store.approve_plan("p")

    def test_clean_initial_state(self) -> None:
        state = self.store.load()
        self.assertEqual(state["active_plan_id"], None)
        self.assertEqual(state["plans"], {})
        self.assertTrue(self.store.recover()["ok"])

    def test_plan_requires_phase_before_approval(self) -> None:
        self.store.create_plan("p", title="P", goal="G")
        with self.assertRaises(WorkflowError):
            self.store.approve_plan("p")

    def test_one_dic_and_core_views(self) -> None:
        self.store.create_plan("p", title="P", goal="G")
        self.store.create_phase("p", "ph", title="Phase")
        dic = self.store.create_dic("p", "ph", dic_id="d", views=self.views(), plan_nodes=self.nodes())
        self.assertEqual(tuple(dic["core_views"]), CORE_DIC_VIEWS)
        for name in CORE_DIC_VIEWS:
            self.assertTrue((self.root / dic["views"][name]).is_file())
        with self.assertRaisesRegex(WorkflowError, "exactly one DIC"):
            self.store.create_dic("p", "ph", dic_id="d2", views=self.views(), plan_nodes=self.nodes())

    def test_missing_core_view_is_rejected(self) -> None:
        self.store.create_plan("p", title="P", goal="G")
        self.store.create_phase("p", "ph", title="Phase")
        bad = self.views()
        del bad["PLAN.md"]
        with self.assertRaisesRegex(WorkflowError, "missing Core DIC views"):
            self.store.create_dic("p", "ph", dic_id="d", views=bad, plan_nodes=self.nodes())

    def test_missing_dependency_and_cycle_are_rejected(self) -> None:
        self.store.create_plan("p", title="P", goal="G")
        self.store.create_phase("p", "ph", title="Phase")
        with self.assertRaisesRegex(WorkflowError, "missing node"):
            self.store.create_dic(
                "p", "ph", dic_id="d", views=self.views(),
                plan_nodes={"a": {"depends_on": ["missing"]}},
            )
        with self.assertRaisesRegex(WorkflowError, "cycle"):
            self.store.create_dic(
                "p", "ph", dic_id="d2", views=self.views(),
                plan_nodes={"a": {"depends_on": ["b"]}, "b": {"depends_on": ["a"]}},
            )

    def test_safe_phase_zip_import(self) -> None:
        fixture = Path(self.tmp.name) / "fixture"
        (fixture / "DIC").mkdir(parents=True)
        (fixture / "EPS" / "eps_001" / "prompts").mkdir(parents=True)
        (fixture / "DIC" / "README.md").write_text("# Phase\n", encoding="utf-8")
        (fixture / "DIC" / "REQUESTS.md").write_text("# Requests\n- [ ] outcome\n", encoding="utf-8")
        (fixture / "DIC" / "PLAN.md").write_text("# Plan\nA\n", encoding="utf-8")
        manifest = {
            "plan_id": "import_plan", "plan_title": "Imported", "plan_goal": "Goal",
            "phase_id": "import_phase", "phase_title": "Imported Phase", "dic_id": "import_dic",
            "plan_nodes": {"A": {"title": "A", "depends_on": []}}, "initial_eps_id": "eps_001",
        }
        (fixture / "PHASE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        eps = {"plan_node_ids": ["A"], "nodes": {"A": {"prompt_tuned": False}}}
        (fixture / "EPS" / "eps_001" / "manifest.json").write_text(json.dumps(eps), encoding="utf-8")
        (fixture / "EPS" / "eps_001" / "prompts" / "A.md").write_text("Do A.\n", encoding="utf-8")
        archive = Path(self.tmp.name) / "phase.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            for file in fixture.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(fixture).as_posix())
        result = self.store.import_phase_zip(archive)
        self.assertTrue(result["ok"])
        self.assertTrue((self.root / "phases" / "import_phase" / "DIC" / "PLAN.md").is_file())
        self.assertTrue((self.root / "phases" / "import_phase" / "EPS" / "eps_001" / "prompts" / "A.md").is_file())
        self.assertTrue(self.store.recover()["ok"])

    def test_phase_scaffold_and_main_initial_eps(self) -> None:
        self.store.create_plan("p2", title="Plan", goal="Goal")
        self.store.create_phase("p2", "ph2", title="Phase")
        phase_dir = self.root / "phases" / "ph2"
        for rel in ("DIC", "EPS", "reports", "results", "evidence", "artifacts", "logs"):
            self.assertTrue((phase_dir / rel).is_dir())
        self.assertTrue((phase_dir / "reports" / "PHASE_SUMMARY.md").is_file())
        self.store.create_dic("p2", "ph2", dic_id="d2", views=self.views(), plan_nodes=self.nodes())
        self.store.approve_plan("p2")
        eps = self.store.create_eps(
            "p2", "ph2", eps_id="e0", plan_node_ids=["a"],
            nodes={"a": {"prompt": "Do bounded work.", "prompt_tuned": False}},
            origin="main",
        )
        self.assertEqual(eps["origin"], "main")
        self.assertTrue((phase_dir / "EPS" / "e0" / "manifest.json").is_file())
        self.assertTrue((phase_dir / "EPS" / "e0" / "prompts" / "a.md").is_file())
        self.assertTrue((phase_dir / "ORCHESTRATOR_START.md").is_file())

    def test_eps_binds_to_stable_dic(self) -> None:
        self.make_ready()
        e1 = self.store.create_eps("p", "ph", eps_id="e1", plan_node_ids=["a", "b", "c"])
        e2 = self.store.create_eps("p", "ph", eps_id="e2", plan_node_ids=["b"])
        self.assertEqual(e1["dic_id"], e2["dic_id"])
        self.assertEqual(e1["dic_hash"], e2["dic_hash"])
        self.assertEqual(e1["attempt"], 1)
        self.assertEqual(e2["attempt"], 2)

    def test_action_lineage_and_completion_gate(self) -> None:
        self.make_ready()
        self.store.create_eps(
            "p",
            "ph",
            eps_id="e",
            plan_node_ids=["a"],
            nodes={
                "a": {
                    "model_profile": "test-model",
                    "surface": "test-surface",
                    "prompt_guides": ["PROMPTING_CORE.md", "TEST_PROVIDER.md"],
                    "prompt_tuned": True,
                }
            },
        )
        evidence = self.root / "evidence.txt"
        evidence.write_text("ok\n", encoding="utf-8")
        action = self.store.record_action(
            "p", "ph", action_id="act", eps_id="e", prompt_node_id="a",
            result="done", evidence_paths=["evidence.txt"], output_versions={"x": "v1"},
        )
        self.assertEqual(action["plan_id"], "p")
        self.assertEqual(action["phase_id"], "ph")
        self.assertEqual(action["dic_id"], "d")
        with self.assertRaisesRegex(WorkflowError, "latest verification"):
            self.store.complete_phase("p", "ph")
        self.store.record_verification("p", "ph", outcome="accept", evidence_paths=["evidence.txt"])
        self.store.complete_phase("p", "ph")
        self.assertEqual(self.store.status()["phases"]["ph"]["status"], "complete")

    def test_model_node_requires_tuned_prompt_before_action(self) -> None:
        self.make_ready()
        self.store.create_eps("p", "ph", eps_id="e", plan_node_ids=["a"])
        with self.assertRaisesRegex(WorkflowError, "prompt tuning"):
            self.store.record_action(
                "p",
                "ph",
                action_id="act",
                eps_id="e",
                prompt_node_id="a",
                result="should not run",
            )

    def test_all_four_verification_outcomes(self) -> None:
        for outcome in ("accept", "repair", "replan", "escalate"):
            with self.subTest(outcome=outcome):
                root = Path(self.tmp.name) / outcome
                root.mkdir()
                store = WorkflowStore(root)
                store.initialize(overwrite=True)
                store.create_plan("p", title="P", goal="G")
                store.create_phase("p", "ph", title="Phase")
                store.create_dic("p", "ph", dic_id="d", views=self.views(), plan_nodes=self.nodes())
                record = store.record_verification("p", "ph", outcome=outcome)
                self.assertEqual(record["outcome"], outcome)

    def test_impact_cone(self) -> None:
        graph = {
            "collect": {"writes": ["raw"]},
            "normalize": {"depends_on": ["collect"], "reads": ["raw"], "writes": ["normalized"]},
            "experiment": {"depends_on": ["normalize"], "reads": ["normalized"], "writes": ["metrics"]},
            "table": {"depends_on": ["experiment"], "reads": ["metrics"], "writes": ["table"]},
            "paper": {"depends_on": ["table"], "reads": ["table"], "writes": ["paper"]},
            "release": {"depends_on": ["paper"], "reads": ["paper"]},
            "theory": {"writes": ["theory"]},
        }
        self.assertEqual(
            dependency_impact_cone(graph, {"normalized"}),
            {"experiment", "table", "paper", "release"},
        )

    def test_recovery_detects_missing_dic_view(self) -> None:
        self.make_ready()
        state = self.store.load()
        plan_path = self.root / state["plans"]["p"]["phases"]["ph"]["dic"]["views"]["PLAN.md"]
        plan_path.unlink()
        result = self.store.recover()
        self.assertFalse(result["ok"])
        self.assertTrue(any("DIC view file not found" in item for item in result["errors"]))

    def test_deterministic_demo(self) -> None:
        demo_root = Path(self.tmp.name) / "demo"
        result = run_demo(str(demo_root))
        self.assertEqual(result["verification_sequence"], ["repair", "accept"])
        self.assertTrue(result["stable_dic_across_attempts"])
        self.assertEqual(result["retained_nodes"], ["collect", "theory"])
        self.assertEqual(
            result["second_eps"]["nodes"],
            ["normalize", "experiment", "table", "paper", "release"],
        )
        self.assertTrue(result["recovery"]["ok"])


class DocumentationContractTestCase(unittest.TestCase):
    def test_main_and_orchestrator_boundaries_are_explicit(self) -> None:
        main = (WORKFLOW_ROOT / "docs" / "MAIN.md").read_text(encoding="utf-8")
        orch = (WORKFLOW_ROOT / "docs" / "ORCHESTRATOR.md").read_text(encoding="utf-8")
        self.assertIn("persistent user-facing planning and decision chat", main)
        self.assertIn("one DIC package", main)
        self.assertIn("DIC/PLAN.md", main)
        self.assertIn("coding-agent session", orch)
        self.assertIn("Main authors the initial EPS", orch)
        self.assertIn("Subagent", orch)

    def test_prompting_source_lock_and_model_tuning(self) -> None:
        core = (WORKFLOW_ROOT / "docs" / "PROMPTING_CORE.md").read_text(encoding="utf-8")
        sources = (WORKFLOW_ROOT / "docs" / "OFFICIAL_PROMPTING_SOURCES.md").read_text(encoding="utf-8")
        self.assertIn("Compile against the actual model and surface", core)
        self.assertIn("developers.openai.com", sources)
        self.assertIn("platform.claude.com", sources)


if __name__ == "__main__":
    unittest.main()
