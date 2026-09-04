from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from start_run import find_matrix_row, write_direct_goal, write_main_prompt  # noqa: E402


class T06RouteTests(unittest.TestCase):
    def test_t06_matrix_row_is_mixed(self) -> None:
        row = find_matrix_row("T06", "MIXED", "DIRECT", "NORMAL")
        self.assertEqual(row["run_id"], "T06_MIXED_DIRECT_NORMAL")

    def test_t06_direct_goal_is_single_sol_medium_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = root / "task"
            run = task / "runs" / "dry"
            workspace = run / "workspace"
            workspace.mkdir(parents=True)
            (task / "TASK_LOCK.json").write_text('{"task_id":"T06"}\n', encoding="utf-8")
            (task / "TASK.md").write_text("# Frozen question\n", encoding="utf-8")
            (run / "RUN.json").write_text(
                '{"condition":"DIRECT","status":"READY_EXECUTOR"}\n', encoding="utf-8"
            )
            prompt = write_direct_goal(task, run, "MIXED")
            text = prompt.read_text(encoding="utf-8")
            self.assertIn("There is no Main chat", text)
            self.assertIn("GPT-5.6 Sol at medium", text)
            self.assertIn("# Frozen question", text)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "launch_direct_goal.py"),
                    str(task),
                    "dry",
                    "--executor",
                    "CODEX",
                    "--prompt",
                    str(prompt),
                    "--codex-model",
                    "gpt-5.6-sol",
                    "--codex-effort",
                    "medium",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("gpt-5.6-sol", payload["command"])
            self.assertIn('model_reasoning_effort="medium"', payload["command"])

    def test_t06_main_prompt_materializes_only_active_phase(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = root / "task"
            run_dir = root / "run"
            task.mkdir()
            run_dir.mkdir()
            (task / "TASK.md").write_text("# Frozen question\n", encoding="utf-8")
            run = {
                "task_id": "T06",
                "run_id": "dry-t06",
                "source_task_lock_sha256": "a" * 64,
                "control_route": "T06_SOL",
            }
            prompt = write_main_prompt(task, run_dir, "AI_NATIVE", "MIXED", run)
            text = prompt.read_text(encoding="utf-8")
            self.assertIn("fully materialize only the current active Phase", text)
            self.assertIn("requested_model: gpt-5.6-sol", text)
            self.assertIn("requested_effort: medium", text)


if __name__ == "__main__":
    unittest.main()
