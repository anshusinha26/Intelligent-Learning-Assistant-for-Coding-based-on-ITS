#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase4_adaptive_validation import SimulationConfig, run_phase4_validation


def _z_test(before: Dict[str, float], after: Dict[str, float]) -> Dict[str, float]:
    m1 = float(before.get("mean", 0.0))
    s1 = float(before.get("std", 0.0))
    n1 = max(1, int(before.get("n", 1)))
    m2 = float(after.get("mean", 0.0))
    s2 = float(after.get("std", 0.0))
    n2 = max(1, int(after.get("n", 1)))
    se = math.sqrt((s1 * s1 / n1) + (s2 * s2 / n2))
    z = 0.0 if se == 0 else (m2 - m1) / se
    pooled = math.sqrt((s1 * s1 + s2 * s2) / 2.0) if (s1 > 0 or s2 > 0) else 0.0
    d = (m2 - m1) / pooled if pooled else 0.0
    return {
        "before_mean": m1,
        "after_mean": m2,
        "delta": m2 - m1,
        "z_score": z,
        "significant_at_95pct": abs(z) >= 1.96,
        "effect_size_cohens_d": d,
    }


def _failure_classification(report: Dict[str, object]) -> Dict[str, object]:
    rec = report["part_4_recommendation_engine"]
    failures = []
    if rec["difficulty_mismatch_rate"] > 0.35:
        failures.append("Wrong difficulty alignment")
    if rec["repeated_recommendation_rate"] > 0:
        failures.append("Repeated recommendations")
    if rec["progression_signal"] < 0.25:
        failures.append("Poor topic progression")
    if rec["weak_recovery_hit_rate"] < 0.45:
        failures.append("Weak recovery targeting")
    if report["part_3_learner_model"]["cold_start_recommendation_availability"] < 0.85:
        failures.append("Poor cold-start coverage")
    if rec["novelty"] < 0.5:
        failures.append("Weak exploration")
    if rec["precision_at_k"] < 0.5:
        failures.append("Weak exploitation")
    if rec["distribution"]["precision"]["std"] > 0.35:
        failures.append("Noise sensitivity")
    if report["part_6_personalization"]["cross_phase_recommendation_overlap"] > 0.7:
        failures.append("Recommendation loops")
    return {"classes": failures, "count": len(failures)}


def run_phase4a(config: SimulationConfig) -> Dict[str, object]:
    baseline_cfg = SimulationConfig(**{**config.__dict__, "recommender_strategy": "legacy"})
    optimized_cfg = SimulationConfig(**{**config.__dict__, "recommender_strategy": "optimized"})

    baseline = run_phase4_validation(baseline_cfg)
    optimized = run_phase4_validation(optimized_cfg)

    base_rec = baseline["part_4_recommendation_engine"]
    opt_rec = optimized["part_4_recommendation_engine"]
    base_quality = baseline["quality_gate"]
    opt_quality = optimized["quality_gate"]

    stats = {
        "precision": _z_test(base_rec["distribution"]["precision"], opt_rec["distribution"]["precision"]),
        "recall": _z_test(base_rec["distribution"]["recall"], opt_rec["distribution"]["recall"]),
        "ndcg": _z_test(base_rec["distribution"]["ndcg"], opt_rec["distribution"]["ndcg"]),
        "difficulty_mismatch": _z_test(base_rec["distribution"]["difficulty_mismatch"], opt_rec["distribution"]["difficulty_mismatch"]),
        "novelty": _z_test(base_rec["distribution"]["novelty"], opt_rec["distribution"]["novelty"]),
    }

    return {
        "phase": "Phase 4A — Adaptive Algorithm Optimization",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "objective": "Evidence-driven adaptive algorithm quality improvement without scope expansion.",
        "baseline_strategy": "legacy",
        "optimized_strategy": "optimized",
        "part_1_recommendation_failure_analysis": _failure_classification(baseline),
        "part_2_learner_model_analysis": {
            "baseline": baseline["part_3_learner_model"],
            "after": optimized["part_3_learner_model"],
            "interpretation": "Learner model quality remained stable; recommendation-layer optimization was prioritized.",
        },
        "part_3_revision_scheduler_analysis": {
            "baseline": baseline["part_5_revision_engine"],
            "after": optimized["part_5_revision_engine"],
            "interpretation": "Revision quality moved marginally; no scheduler redesign was introduced.",
        },
        "part_4_statistical_analysis": stats,
        "part_5_algorithm_changes": [
            "Switched candidate filtering from attempted-exclusion to solved-exclusion to allow recovery recommendations.",
            "Added recovery-aware scoring for unsolved historical attempts with recency-aware retry damping.",
            "Added novelty weighting from global popularity to increase exploration without sacrificing precision.",
            "Strengthened prerequisite/follow-up/recovery edge weights for better progression signal.",
            "Tightened difficulty alignment penalties for mismatch-heavy recommendations.",
        ],
        "part_6_repeat_simulation": {
            "baseline_submissions": baseline["part_2_longitudinal_simulation"]["submission_rows"],
            "optimized_submissions": optimized["part_2_longitudinal_simulation"]["submission_rows"],
            "baseline_learners": baseline["configuration"]["total_learners"],
            "optimized_learners": optimized["configuration"]["total_learners"],
        },
        "part_7_before_after": {
            "recommendation_quality_before": base_quality["recommendation_quality_score"],
            "recommendation_quality_after": opt_quality["recommendation_quality_score"],
            "revision_quality_before": base_quality["revision_quality_score"],
            "revision_quality_after": opt_quality["revision_quality_score"],
            "learning_quality_before": base_quality["learning_quality_score"],
            "learning_quality_after": opt_quality["learning_quality_score"],
            "its_quality_before": base_quality["its_quality_score"],
            "its_quality_after": opt_quality["its_quality_score"],
            "recommendation_metrics_before": {
                "precision_at_k": base_rec["precision_at_k"],
                "recall_at_k": base_rec["recall_at_k"],
                "ndcg_at_k": base_rec["ndcg_at_k"],
                "novelty": base_rec["novelty"],
                "difficulty_mismatch_rate": base_rec["difficulty_mismatch_rate"],
            },
            "recommendation_metrics_after": {
                "precision_at_k": opt_rec["precision_at_k"],
                "recall_at_k": opt_rec["recall_at_k"],
                "ndcg_at_k": opt_rec["ndcg_at_k"],
                "novelty": opt_rec["novelty"],
                "difficulty_mismatch_rate": opt_rec["difficulty_mismatch_rate"],
            },
        },
        "baseline_report": baseline,
        "optimized_report": optimized,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4A adaptive recommendation optimization")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--learners-per-archetype", type=int, default=200)
    parser.add_argument("--stress-learners", type=int, default=8000)
    parser.add_argument("--core-attempts", type=int, default=45)
    parser.add_argument("--stress-attempts", type=int, default=2)
    parser.add_argument("--minimum-submissions", type=int, default=100000)
    parser.add_argument("--bank", type=Path, default=Path("data/premium/problem_bank.json"))
    parser.add_argument("--out", type=Path, default=Path("reports/phase4/phase4a_adaptive_optimization.json"))
    args = parser.parse_args(argv)

    config = SimulationConfig(
        seed=args.seed,
        learners_per_archetype=args.learners_per_archetype,
        stress_learner_count=args.stress_learners,
        core_attempts_per_user=args.core_attempts,
        stress_attempts_per_user=args.stress_attempts,
        minimum_submissions=args.minimum_submissions,
        bank_path=args.bank,
    )
    report = run_phase4a(config)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = report["part_7_before_after"]
    print(
        json.dumps(
            {
                "recommendation_quality_before": summary["recommendation_quality_before"],
                "recommendation_quality_after": summary["recommendation_quality_after"],
                "its_quality_before": summary["its_quality_before"],
                "its_quality_after": summary["its_quality_after"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
