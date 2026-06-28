import json
import tempfile
import unittest
from pathlib import Path

from scripts.phase3e_quality_review import run_phase3e_review


class Phase3EQualityReviewTests(unittest.TestCase):
    def test_quality_review_report_generates_and_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            curriculum = json.loads(
                Path("data/premium/curriculum/curriculum.json").read_text(encoding="utf-8")
            )
            total_curriculum = len(curriculum["problems"])
            report = run_phase3e_review(
                bank_path=Path("data/premium/problem_bank.json"),
                output_dir=Path(tmp),
            )
            self.assertEqual(report["summary"]["problems_reviewed"], total_curriculum)
            self.assertGreaterEqual(report["summary"]["average_quality_score"], 8.0)
            self.assertIsNotNone(report["summary"]["highest_scoring_problem"])
            self.assertIsNotNone(report["summary"]["lowest_scoring_problem"])

            out_json = Path(tmp) / "phase3e_quality_report.json"
            self.assertTrue(out_json.exists())
            saved = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(saved["summary"]["problems_reviewed"], total_curriculum)

    def test_generator_output_has_no_placeholder_phrases(self):
        payload = json.loads(Path("data/premium/problem_bank.json").read_text(encoding="utf-8"))
        combined = "\n".join(
            (
                problem["educational_assets"]["statement_md"]
                + "\n"
                + problem["educational_assets"]["examples_md"]
                + "\n"
                + problem["educational_assets"]["editorial_md"]
            )
            for problem in payload["problems"]
        )
        self.assertNotIn("auto-generated case", combined)
        self.assertNotIn("Implement the `solve` function exactly as described.", combined)
        self.assertNotIn("The algorithm maintains the required invariant", combined)


if __name__ == "__main__":
    unittest.main()
