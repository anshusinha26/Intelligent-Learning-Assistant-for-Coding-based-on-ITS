import json
import tempfile
import unittest
from pathlib import Path

from scripts.phase4_adaptive_validation import SimulationConfig, run_phase4_validation


class Phase4AdaptiveValidationTests(unittest.TestCase):
    def test_phase4_small_run_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "phase4.json"
            config = SimulationConfig(
                seed=7,
                learners_per_archetype=2,
                stress_learner_count=20,
                core_attempts_per_user=8,
                stress_attempts_per_user=2,
                minimum_submissions=60,
                report_path=out,
                bank_path=Path("data/premium/problem_bank.json"),
            )
            report = run_phase4_validation(config)
            self.assertIn("quality_gate", report)
            self.assertIn("part_2_longitudinal_simulation", report)
            self.assertGreaterEqual(report["part_2_longitudinal_simulation"]["submission_rows"], 60)
            self.assertGreaterEqual(report["configuration"]["total_learners"], 40)
            self.assertIn("part_7_stress_test", report)
            self.assertIn("learner_update_latency_ms", report["part_7_stress_test"])

    def test_phase4_counts_and_quality_gate(self):
        config = SimulationConfig(
            seed=11,
            learners_per_archetype=1,
            stress_learner_count=5,
            core_attempts_per_user=6,
            stress_attempts_per_user=2,
            minimum_submissions=20,
            bank_path=Path("data/premium/problem_bank.json"),
        )
        report = run_phase4_validation(config)
        part1 = report["part_1_synthetic_learners"]
        quality = report["quality_gate"]
        self.assertEqual(part1["archetype_counts"]["Beginner"], 1)
        self.assertGreaterEqual(report["part_2_longitudinal_simulation"]["attempt_rows"], 20)
        for key in (
            "learning_quality_score",
            "recommendation_quality_score",
            "revision_quality_score",
            "personalization_quality_score",
            "its_quality_score",
        ):
            self.assertGreaterEqual(quality[key], 0.0)
            self.assertLessEqual(quality[key], 10.0)
        json.dumps(report)


if __name__ == "__main__":
    unittest.main()
