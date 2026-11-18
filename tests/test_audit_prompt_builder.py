"""Optional tool integration checks: run with tools/audit_prompt_builder/requirements.txt installed."""
import json
import tempfile
import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/audit_prompt_builder"


@unittest.skipIf(AppTest is None, "Standalone audit tool requires Streamlit")
class AuditPromptBuilderTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(TOOL / "app.py")).run()
        self.assertFalse(self.app.exception)

    def prompt(self):
        self.assertFalse(self.app.exception)
        return self.app.code[0].value

    def test_default_review_is_bounded_and_evidence_based(self):
        text = self.prompt()
        self.assertLess(len(text.split()), 650)
        for required in ["350 words", "up to 5", "all CRITICAL",
                         "Cite both", "Missing context", "not assessable",
                         "Final score", "Matrix scoring summary", "Findings and corrections",
                         "no positive assessed weight remains"]:
            self.assertIn(required, text)
        self.assertNotIn("Finish with a short verdict", text)
        self.assertNotIn("Run two passes", text)

    def load_data(self, data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", dir=TOOL / "profiles") as f:
            json.dump(data, f)
            f.flush()
            self.app.run()
            self.app.selectbox(key="pick").set_value(Path(f.name).name).run()
            self.app.button(key="load_pick").click().run()

    def test_legacy_input_loads_and_detailed_scoring_is_optional(self):
        self.assertNotIn("vsil-v3-paper.json", self.app.selectbox(key="pick").options)
        self.load_data(json.loads((TOOL / "archive/profiles/vsil-v3-paper.json").read_text()))
        self.assertIn("V-SIL v3", self.prompt())
        self.assertEqual(self.app.number_input(key="max_words").value, 350)
        self.app.radio(key="mode").set_value("Detailed").run()
        self.assertIn("Final score (%)", self.prompt())
        self.app.checkbox(key="stage_3").uncheck().run()
        self.app.selectbox(key="fmt").set_value("JSON").run()
        text = self.prompt()
        self.assertNotIn('"final_score"', text)
        self.assertNotIn('"matrix_summary"', text)
        self.assertNotIn('"verdict"', text)

    def test_focused_json_has_only_scores_matrix_and_findings(self):
        self.app.text_area(key="docs").set_value("[PRINCIPLE] Preserve the author's intent.").run()
        self.app.selectbox(key="fmt").set_value("JSON").run()
        text = self.prompt()
        self.assertIn("[PRINCIPLE] Preserve the author's intent.", text)
        self.assertIn('"final_score"', text)
        self.assertIn('"matrix_summary"', text)
        self.assertNotIn('"limitations"', text)
        self.assertNotIn('"verdict"', text)
        self.app.checkbox(key="stage_3").uncheck().run()
        self.assertNotIn('"final_score"', self.prompt())
        self.assertNotIn('"matrix_summary"', self.prompt())
        self.assertIn('"findings"', self.prompt())

    def test_conceptual_profiles_are_short_and_focus_on_requirements(self):
        for name in ["conceptual-skill.es.json", "conceptual-skill.en.json"]:
            self.app.selectbox(key="pick").set_value(name).run()
            self.app.button(key="load_pick").click().run()
            self.assertFalse(self.app.error)
            self.assertEqual(self.app.radio(key="mode").value, "Focused")
            self.assertLess(len(self.prompt().split()), 650)
            self.assertEqual(len(self.app.session_state["checks"]), 4)
            self.assertEqual(len(self.app.session_state["dims"]), 4)
            self.assertIn("Matrix scoring summary", self.prompt())

    def test_invalid_settings_are_rejected_without_changing_loaded_state(self):
        for data in [{"mode": "invalid"}, {"output": {"max_words": 0}},
                     {"output": {"max_findings": True}}, {"output": {"max_words": 3.5}}]:
            self.load_data({**data, "context": {"title": "must not load"}})
            self.assertTrue(self.app.error)
            self.assertNotEqual(self.app.text_input(key="title").value, "must not load")

    def test_output_limits_apply_to_both_review_styles(self):
        self.load_data({"output": {"max_words": 200, "max_findings": 3}})
        for mode in ["Focused", "Detailed"]:
            self.app.radio(key="mode").set_value(mode).run()
            text = self.prompt()
            self.assertIn("200 words", text)
            self.assertIn("up to 3", text)
            self.assertIn("all CRITICAL", text)
            self.assertIn("Final score: one line", text)
            self.assertNotIn("# FINAL SUMMARY", text)
            self.assertNotIn("Put stage details", text)


if __name__ == "__main__":
    unittest.main()
