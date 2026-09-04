from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from continue_run import direct_launch_command, main as continue_main  # noqa: E402
from start_run import finish_run  # noqa: E402


class ProgressiveDirectTests(unittest.TestCase):
    def test_ungraded_checkpoint_is_graded_before_any_relaunch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task_root = Path(directory) / "task"
            run_dir = task_root / "runs" / "run-test"
            state_dir = run_dir / "workspace" / ".evaluation"
            state_dir.mkdir(parents=True)
            run_path = run_dir / "RUN.json"
            run = {
                "condition": "AI_NATIVE",
                "task_id": "T03",
                "run_id": "run-test",
                "state_mode": "NORMAL",
            }
            run_path.write_text(json.dumps(run) + "\n", encoding="utf-8")
            (state_dir / "CHECKPOINT_STATE.json").write_text(
                json.dumps({"current_checkpoint": 1, "accepted": [], "revealed": [1]}) + "\n",
                encoding="utf-8",
            )
            calls: list[list[str]] = []

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                updated = json.loads(run_path.read_text(encoding="utf-8"))
                updated["latest_auto_grade"] = {
                    "checkpoint": 1,
                    "grader_ok": True,
                    "accepted_for_next_reveal": False,
                }
                run_path.write_text(json.dumps(updated) + "\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)

            argv = ["continue_run.py", str(task_root), "--run-id", "run-test"]
            with patch("continue_run.subprocess.run", side_effect=fake_run), patch.object(sys, "argv", argv):
                with self.assertRaisesRegex(SystemExit, "no executor was relaunched"):
                    continue_main()

            self.assertEqual([Path(command[3]).name for command in calls], ["grade_run.py"])

    def test_codex_continuation_requests_workspace_scoped_resume(self) -> None:
        command = direct_launch_command(
            {
                "run_id": "run-test",
                "executor": "CODEX",
                "ecosystem": "OPENAI",
            },
            ROOT / "tasks" / "T03_database_migration",
            Path("DIRECT_GOAL_CHECKPOINT_02.md"),
            None,
        )
        self.assertIn("--resume-session", command)

    def test_claude_continuation_requests_project_session_resume(self) -> None:
        command = direct_launch_command(
            {
                "run_id": "run-test",
                "executor": "CLAUDE",
                "ecosystem": "ANTHROPIC",
                "active_executor_product_visible": "claude-sonnet-5",
            },
            ROOT / "tasks" / "T03_database_migration",
            Path("AI_NATIVE_GOAL_CHECKPOINT_02.md"),
            None,
        )
        self.assertIn("--resume-session", command)

    def test_finish_run_enters_continuation_before_recording(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task_root = Path(directory) / "task"
            run_dir = task_root / "runs" / "run-test"
            run_dir.mkdir(parents=True)
            (run_dir / "RUN.json").write_text(
                json.dumps(
                    {
                        "condition": "DIRECT",
                        "task_id": "T03",
                        "latest_auto_grade": {
                            "task_completion": "INCOMPLETE_CHECKPOINTS",
                            "accepted_for_next_reveal": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            calls: list[list[str]] = []

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                return subprocess.CompletedProcess(command, 0)

            with patch("start_run.subprocess.run", side_effect=fake_run):
                result = finish_run(
                    task_root,
                    "run-test",
                    0,
                    qualification_root=None,
                    skip_auto_grade=False,
                    skip_post_run_record=False,
                )

            self.assertEqual(result, 0)
            invoked_scripts = [Path(command[3]).name for command in calls]
            self.assertEqual(invoked_scripts, ["grade_run.py", "continue_run.py"])
            self.assertNotIn("record_run.py", invoked_scripts)

    def test_ai_native_finish_uses_same_automatic_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task_root = Path(directory) / "task"
            run_dir = task_root / "runs" / "run-test"
            run_dir.mkdir(parents=True)
            (run_dir / "RUN.json").write_text(
                json.dumps(
                    {
                        "condition": "AI_NATIVE",
                        "task_id": "T03",
                        "latest_auto_grade": {
                            "task_completion": "INCOMPLETE_CHECKPOINTS",
                            "accepted_for_next_reveal": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            calls: list[list[str]] = []

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                return subprocess.CompletedProcess(command, 0)

            with patch("start_run.subprocess.run", side_effect=fake_run):
                result = finish_run(
                    task_root,
                    "run-test",
                    0,
                    qualification_root=None,
                    skip_auto_grade=False,
                    skip_post_run_record=False,
                )

            self.assertEqual(result, 0)
            invoked_scripts = [Path(command[3]).name for command in calls]
            self.assertEqual(invoked_scripts, ["grade_run.py", "continue_run.py"])

    def test_continue_command_chains_to_following_direct_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task_root = Path(directory) / "task"
            run_dir = task_root / "runs" / "run-test"
            state_dir = run_dir / "workspace" / ".evaluation"
            state_dir.mkdir(parents=True)
            run = {
                "condition": "DIRECT",
                "task_id": "T03",
                "run_id": "run-test",
                "ecosystem": "OPENAI",
                "executor": "CODEX",
                "state_mode": "NORMAL",
                "source_task_lock_sha256": "test-lock",
                "active_executor_product_visible": "gpt-5.6-terra",
                "active_executor_effort": "xhigh",
                "executor_sessions": [{"session_id": "checkpoint-1"}],
                "latest_auto_grade": {
                    "checkpoint": 1,
                    "checkpoint_total": 5,
                    "grader_ok": True,
                    "accepted_for_next_reveal": True,
                    "all_checkpoints_graded": False,
                    "task_completion": "INCOMPLETE_CHECKPOINTS",
                    "raw_grader": str(run_dir / "grader.json"),
                },
            }
            (run_dir / "RUN.json").write_text(json.dumps(run) + "\n", encoding="utf-8")
            (state_dir / "CHECKPOINT_STATE.json").write_text(
                json.dumps({"current_checkpoint": 1, "accepted": [], "revealed": [1]}) + "\n",
                encoding="utf-8",
            )
            calls: list[list[str]] = []

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                return subprocess.CompletedProcess(command, 0)

            argv = ["continue_run.py", str(task_root), "--run-id", "run-test"]
            with patch("continue_run.subprocess.run", side_effect=fake_run), patch.object(sys, "argv", argv):
                self.assertEqual(continue_main(), 0)

            invoked_scripts = [Path(command[3]).name for command in calls]
            self.assertEqual(
                invoked_scripts,
                ["reveal_checkpoint.py", "launch_direct_goal.py", "grade_run.py", "continue_run.py"],
            )
            self.assertIn("--resume-session", calls[1])
            self.assertTrue((run_dir / "EXECUTOR_RETURN_CHECKPOINT_01.md").is_file())

    def test_ai_native_checkpoint_resumes_without_another_main_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task_root = Path(directory) / "task"
            run_dir = task_root / "runs" / "run-test"
            state_dir = run_dir / "workspace" / ".evaluation"
            state_dir.mkdir(parents=True)
            run = {
                "condition": "AI_NATIVE",
                "task_id": "T03",
                "run_id": "run-test",
                "ecosystem": "OPENAI",
                "executor": "CODEX",
                "state_mode": "NORMAL",
                "main_inference_count": 1,
                "source_task_lock_sha256": "test-lock",
                "active_executor_product_visible": "gpt-5.6-terra",
                "active_executor_effort": "xhigh",
                "executor_sessions": [{"session_id": "checkpoint-1"}],
                "latest_auto_grade": {
                    "checkpoint": 1,
                    "checkpoint_total": 5,
                    "grader_ok": True,
                    "accepted_for_next_reveal": True,
                    "all_checkpoints_graded": False,
                    "task_completion": "INCOMPLETE_CHECKPOINTS",
                    "raw_grader": str(run_dir / "grader.json"),
                },
            }
            (run_dir / "RUN.json").write_text(json.dumps(run) + "\n", encoding="utf-8")
            (state_dir / "CHECKPOINT_STATE.json").write_text(
                json.dumps({"current_checkpoint": 1, "accepted": [], "revealed": [1]}) + "\n",
                encoding="utf-8",
            )
            calls: list[list[str]] = []

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                return subprocess.CompletedProcess(command, 0)

            argv = ["continue_run.py", str(task_root), "--run-id", "run-test"]
            with patch("continue_run.subprocess.run", side_effect=fake_run), patch.object(sys, "argv", argv):
                self.assertEqual(continue_main(), 0)

            invoked_scripts = [Path(command[3]).name for command in calls]
            self.assertEqual(
                invoked_scripts,
                ["reveal_checkpoint.py", "launch_direct_goal.py", "grade_run.py", "continue_run.py"],
            )
            updated = json.loads((run_dir / "RUN.json").read_text(encoding="utf-8"))
            self.assertEqual(updated["main_inference_count"], 1)
            self.assertEqual(len(updated["ai_native_continuations"]), 1)
            self.assertFalse((run_dir / "MAIN_CONTINUE_INPUT_CHECKPOINT_02.zip").exists())


if __name__ == "__main__":
    unittest.main()
