from pathlib import Path

from scripts.phase4_adaptive_validation import SimulationConfig
from scripts.phase4a_adaptive_optimization import run_phase4a


def test_phase4a_report_structure_small_run():
    config = SimulationConfig(
        seed=9,
        learners_per_archetype=2,
        stress_learner_count=20,
        core_attempts_per_user=8,
        stress_attempts_per_user=2,
        minimum_submissions=60,
        bank_path=Path("data/premium/problem_bank.json"),
    )
    report = run_phase4a(config)
    assert report["baseline_strategy"] == "legacy"
    assert report["optimized_strategy"] == "optimized"
    assert "part_1_recommendation_failure_analysis" in report
    assert "part_4_statistical_analysis" in report
    before_after = report["part_7_before_after"]
    assert isinstance(before_after["recommendation_quality_before"], (int, float))
    assert isinstance(before_after["recommendation_quality_after"], (int, float))
    assert report["part_6_repeat_simulation"]["baseline_submissions"] >= 60
    assert report["part_6_repeat_simulation"]["optimized_submissions"] >= 60
