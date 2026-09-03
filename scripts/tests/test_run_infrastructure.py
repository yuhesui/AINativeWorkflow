from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from start_run import stop_after_infrastructure_failure  # noqa: E402
from task_environment import environment_spec  # noqa: E402


class InfrastructureFailureTests(unittest.TestCase):
    def test_ai_native_prompts_forbid_environment_preflight_gates(self) -> None:
        initial = (ROOT / "prompts" / "ai_native" / "01_START_TASK.md").read_text(
            encoding="utf-8"
        )
        continuation = (ROOT / "prompts" / "shared" / "01_CONTINUE_CHECKPOINT.md").read_text(
            encoding="utf-8"
        )
        launcher = (ROOT / "scripts" / "launch_executor.py").read_text(encoding="utf-8")

        for text in (initial, continuation, launcher):
            self.assertIn("run_in_env.py exec-self", text)
            self.assertIn("Docker", text)
        self.assertIn("preflight", initial)
        self.assertIn("preflight", continuation)
        self.assertIn("already provisioned and started", launcher)
        self.assertIn("retry it once", initial.lower())
        self.assertIn("retry", continuation.lower())

    def test_pre_executor_failure_is_invalidated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_path = Path(directory) / "RUN.json"
            run_path.write_text('{"status": "READY_EXECUTOR"}\n', encoding="utf-8")

            self.assertTrue(stop_after_infrastructure_failure(run_path, 1))
            run = json.loads(run_path.read_text(encoding="utf-8"))
            self.assertEqual(run["status"], "INVALID_INFRASTRUCTURE")
            self.assertIn("Workspace was not graded", run["invalidation_reason"])

    def test_completed_executor_session_remains_gradable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_path = Path(directory) / "RUN.json"
            initial = {"status": "IN_PROGRESS", "executor_sessions": [{"exit_code": 1}]}
            run_path.write_text(json.dumps(initial) + "\n", encoding="utf-8")

            self.assertFalse(stop_after_infrastructure_failure(run_path, 1))
            self.assertEqual(json.loads(run_path.read_text(encoding="utf-8")), initial)

    def test_t03_uses_pinned_qualification_environment(self) -> None:
        spec = environment_spec(ROOT / "tasks" / "T03_database_migration")
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertTrue(spec["environment_adapted"])
        self.assertEqual(
            spec["dockerfile"],
            ROOT / "tasks" / "T03_database_migration" / "qualification" / "environment" / "Dockerfile",
        )
        dockerfile = spec["dockerfile"].read_text(encoding="utf-8")
        self.assertIn("NPM_VERSION=10.9.0", dockerfile)
        self.assertNotIn("npm@latest", dockerfile)


if __name__ == "__main__":
    unittest.main()
