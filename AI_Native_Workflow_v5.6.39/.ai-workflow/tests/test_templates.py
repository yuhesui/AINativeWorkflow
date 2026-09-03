from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TemplateTestCase(unittest.TestCase):
    def test_template_manifest_resolves(self) -> None:
        manifest = json.loads((ROOT / "aw" / "templates" / "manifest.json").read_text(encoding="utf-8"))
        for rel in manifest["dic_core_views"] + manifest["prompt_templates"]:
            self.assertTrue((ROOT / "aw" / "templates" / rel).is_file(), rel)

    def test_plan_template_owns_graph_and_subagents(self) -> None:
        text = (ROOT / "aw" / "templates" / "dic" / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("Durable Phase Execution Graph", text)
        self.assertIn("parallel", text.lower())
        self.assertIn("subagent", text.lower())
        self.assertIn("model-tuned", text.lower())

    def test_no_unbalanced_markdown_fences(self) -> None:
        for path in ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count("```"), text.count("```") // 2 * 2, path)
            self.assertEqual(text.count("```") % 2, 0, path)


if __name__ == "__main__":
    unittest.main()
