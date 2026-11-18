"""Optional tool integration checks: run with tools/tools-reqs.txt installed."""
import json
import tempfile
import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(AppTest is None, "Standalone audit tool requires Streamlit")
class AuditPromptBuilderTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(ROOT / "tools/audit_prompt_builder.py")).run()
        self.assertFalse(self.app.exception)

    def prompt(self):
        self.assertFalse(self.app.exception)
        return self.app.code[0].value

    def test_default_review_is_bounded_and_evidence_based(self):
        text = self.prompt()
        self.assertLess(len(text.split()), 450)
        for required in ["600 words", "five most consequential", "every CRITICAL",
                         "cite both", "Missing context", "not assessable"]:
            self.assertIn(required, text)
        self.assertNotIn("Weighted score", text)
        self.assertNotIn("Run two passes", text)

    def test_legacy_input_loads_and_detailed_scoring_is_optional(self):
        self.app.selectbox(key="pick").set_value("V-SIl-v3-audit.json").run()
        self.app.button(key="load_pick").click().run()
        self.assertIn("V-SIL v3", self.prompt())
        self.app.radio(key="mode").set_value("Detailed").run()
        self.assertIn("Weighted score", self.prompt())
        self.app.checkbox(key="stage_3").uncheck().run()
        self.app.selectbox(key="fmt").set_value("JSON").run()
        text = self.prompt()
        self.assertNotIn("Weighted score", text)
        schema = json.loads(text.split("```json\n")[1].split("```", 1)[0])
        self.assertNotIn("scores", schema)
        self.assertNotIn("weighted_percent", schema)

    def test_focused_json_keeps_material_and_omits_scoring(self):
        self.app.text_area(key="docs").set_value("[PRINCIPLE] Preserve the author's intent.").run()
        self.app.selectbox(key="fmt").set_value("JSON").run()
        text = self.prompt()
        self.assertIn("[PRINCIPLE] Preserve the author's intent.", text)
        self.assertIn('"limitations" (array)', text)
        self.assertNotIn('"weighted_percent"', text)

    def test_conceptual_profiles_are_short_and_focus_on_requirements(self):
        for name in ["auditoria-coherencia-skill-metodologica.json",
                     "methodological-skill-coherence-audit.en.json"]:
            self.app.selectbox(key="pick").set_value(name).run()
            self.app.button(key="load_pick").click().run()
            self.assertFalse(self.app.error)
            self.assertEqual(self.app.radio(key="mode").value, "Focused")
            self.assertLess(len(self.prompt().split()), 600)
            self.assertEqual(len(self.app.session_state["checks"]), 4)
            self.assertNotIn("Weighted score", self.prompt())

    def test_invalid_mode_is_rejected_without_changing_loaded_state(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", dir=ROOT / "tools/inputs") as f:
            json.dump({"mode": "invalid", "context": {"title": "must not load"}}, f)
            f.flush()
            self.app.run()
            self.app.selectbox(key="pick").set_value(Path(f.name).name).run()
            self.app.button(key="load_pick").click().run()
            self.assertTrue(self.app.error)
            self.assertNotEqual(self.app.text_input(key="title").value, "must not load")


if __name__ == "__main__":
    unittest.main()
