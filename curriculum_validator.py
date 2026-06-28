#!/usr/bin/env python3
import argparse
import shutil
import sqlite3
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from scripts.phase3_common import ALLOWED_DIFFICULTIES, load_inventory, write_json
from src.problem_bank import PREMIUM_DATASET_TIER
from src.database import Database
from src.learner_model import LearnerModel
from src.recommender import RecommendationEngine


DIFFICULTY_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2}


def curriculum_checks(inventory, strict_distribution: bool = False):
    issues = {"critical": [], "high": [], "medium": [], "low": []}
    is_partial_curriculum = len(inventory) < 50

    known_topics = sorted({item["topic"] for item in inventory if item["topic"]})
    known_patterns = sorted({item["pattern"] for item in inventory if item["pattern"]})

    topic_difficulty = defaultdict(Counter)
    title_counter = Counter()
    for item in inventory:
        pid = item["problem_id"]
        topic = item["topic"]
        difficulty = item["difficulty"]
        pattern = item["pattern"]
        title_norm = (item["title"] or "").strip().lower()

        title_counter[title_norm] += 1
        if difficulty not in ALLOWED_DIFFICULTIES:
            issues["critical"].append({"type": "invalid_difficulty", "problem_id": pid, "difficulty": difficulty})
            continue

        topic_difficulty[topic][difficulty] += 1

        if not topic:
            issues["high"].append({"type": "missing_topic", "problem_id": pid})
        if not pattern:
            issues["low"].append({"type": "missing_pattern", "problem_id": pid})
        elif pattern not in known_patterns:
            issues["medium"].append({"type": "unknown_pattern", "problem_id": pid, "pattern": pattern})
        if not item.get("recommendation_graph_present"):
            issues["high"].append({"type": "missing_recommendation_graph", "problem_id": pid})
        if item.get("relationship_count", 0) <= 0:
            issues["medium"].append({"type": "missing_relationship_edges", "problem_id": pid})
        graph = item.get("recommendation_graph") or {}
        if not isinstance(graph, dict):
            issues["high"].append({"type": "invalid_recommendation_graph", "problem_id": pid})
        else:
            for edge_type in ("prerequisite", "alternative", "follow_up", "review", "recovery"):
                if edge_type not in graph:
                    issues["high"].append(
                        {"type": "missing_recommendation_graph_key", "problem_id": pid, "key": edge_type}
                    )

    for title, count in title_counter.items():
        if title and count > 1:
            issues["medium"].append({"type": "duplicate_concept", "title": title, "count": count})

    for topic, distribution in topic_difficulty.items():
        if strict_distribution and (not is_partial_curriculum) and distribution["Medium"] + distribution["Hard"] > 0 and distribution["Easy"] == 0:
            issues["high"].append(
                {
                    "type": "missing_prerequisite_level",
                    "topic": topic,
                    "detail": "topic has medium/hard but no easy problems",
                }
            )
        if strict_distribution and (not is_partial_curriculum) and distribution["Hard"] > 0 and distribution["Medium"] == 0:
            issues["high"].append(
                {
                    "type": "difficulty_jump",
                    "topic": topic,
                    "detail": "topic has hard but no medium problems",
                }
            )
        if strict_distribution and (not is_partial_curriculum) and sum(distribution.values()) < 5:
            issues["low"].append(
                {"type": "curriculum_gap_sparse_topic", "topic": topic, "problem_count": sum(distribution.values())}
            )

    if not inventory:
        issues["high"].append({"type": "empty_premium_problem_bank"})

    return issues, {"known_topics": known_topics, "known_patterns_count": len(known_patterns)}


def _create_user(conn, email: str, target_level: str) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (name, email, password_hash, role, target_level, email_verified, created_at)
        VALUES (?, ?, ?, 'user', ?, 1, ?)
    """,
        (email.split("@")[0], email, "hash", target_level, datetime.utcnow().isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def _insert_attempts(conn, user_id: int, attempts):
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.executemany(
        """
        INSERT INTO attempts (user_id, problem_id, verdict, time_taken, error_type, attempted_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        [(user_id, pid, verdict, 300, err, now) for pid, verdict, err in attempts],
    )
    conn.commit()


def recommendation_quality_checks(db_path: Path):
    issues = {"critical": [], "high": [], "medium": [], "low": []}
    evidence = {}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_db = Path(tmp) / "rec_quality.db"
        if db_path.exists():
            shutil.copy2(db_path, tmp_db)
        db = Database(str(tmp_db))
        conn = db.get_connection()

        cold_id = _create_user(conn, "phase3_cold@example.com", "medium")
        advanced_id = _create_user(conn, "phase3_advanced@example.com", "hard")
        weak_id = _create_user(conn, "phase3_weak@example.com", "medium")

        cursor = conn.cursor()
        problems = [
            dict(row)
            for row in cursor.execute(
                """
                SELECT problem_id, topic, difficulty
                FROM problems
                WHERE dataset_tier = ? AND is_active = 1
            """,
                (PREMIUM_DATASET_TIER,),
            ).fetchall()
        ]
        conn.close()

        recommender = RecommendationEngine(db)
        learner = LearnerModel(db)

        if not problems:
            issues["high"].append({"type": "empty_premium_problem_bank"})
            return issues, {"cold_start_count": 0, "advanced_count": 0, "weak_count": 0, "cold_after_accept_count": 0}

        # Cold start recommendations
        cold_recs = recommender.generate_recommendations(cold_id, top_k=20, refresh_pending=True)
        cold_ids = [item["problem_id"] for item in cold_recs]
        if len(cold_ids) != len(set(cold_ids)):
            issues["critical"].append({"type": "cold_start_duplicate_recommendations"})
        if not cold_ids:
            issues["high"].append({"type": "cold_start_no_recommendations"})

        # Advanced learner: many accepted attempts, expect recommendations to avoid solved
        solved_pool = [p["problem_id"] for p in problems if p["difficulty"] in {"Easy", "Medium"}][:80]
        conn = db.get_connection()
        _insert_attempts(conn, advanced_id, [(pid, "Accepted", None) for pid in solved_pool])
        conn.close()
        learner.update_learner_metrics(advanced_id)
        advanced_recs = recommender.generate_recommendations(advanced_id, top_k=20, refresh_pending=True)
        advanced_ids = [item["problem_id"] for item in advanced_recs]
        overlap = sorted(set(advanced_ids) & set(solved_pool))
        if overlap:
            issues["critical"].append(
                {"type": "solved_problem_recommended", "count": len(overlap), "examples": overlap[:10]}
            )

        # Weak-topic mapping: inject repeated WA on one topic
        weak_topic = None
        for p in problems:
            if p["topic"]:
                weak_topic = p["topic"]
                break
        weak_attempts = []
        if weak_topic:
            weak_candidates = [p["problem_id"] for p in problems if p["topic"] == weak_topic][:12]
            weak_attempts = [(pid, "Wrong Answer", "logic-error") for pid in weak_candidates]
            conn = db.get_connection()
            _insert_attempts(conn, weak_id, weak_attempts)
            conn.close()
            learner.update_learner_metrics(weak_id)
            weak_recs = recommender.generate_recommendations(weak_id, top_k=15, refresh_pending=True)
            weak_topics = [item["topic"] for item in weak_recs]
            remaining_same_topic = [p["problem_id"] for p in problems if p["topic"] == weak_topic and p["problem_id"] not in weak_candidates]
            if remaining_same_topic and weak_topic not in weak_topics[:5]:
                issues["medium"].append(
                    {
                        "type": "weak_topic_not_prioritized",
                        "weak_topic": weak_topic,
                        "top5_topics": weak_topics[:5],
                    }
                )
        else:
            weak_recs = []

        # Evolving recommendations: accept one recommended and ensure it disappears
        if cold_recs:
            accepted_problem = cold_recs[0]["problem_id"]
            conn = db.get_connection()
            _insert_attempts(conn, cold_id, [(accepted_problem, "Accepted", None)])
            conn.close()
            learner.update_learner_metrics(cold_id)
            recs_after_accept = recommender.generate_recommendations(cold_id, top_k=20, refresh_pending=True)
            ids_after_accept = [item["problem_id"] for item in recs_after_accept]
            if accepted_problem in ids_after_accept:
                issues["high"].append(
                    {
                        "type": "accepted_problem_still_recommended",
                        "problem_id": accepted_problem,
                    }
                )
        else:
            ids_after_accept = []

        evidence = {
            "cold_start_count": len(cold_recs),
            "advanced_count": len(advanced_recs),
            "weak_count": len(weak_recs),
            "cold_after_accept_count": len(ids_after_accept),
            "weak_topic": weak_topic,
        }

    return issues, evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 curriculum and recommendation quality validator.")
    parser.add_argument("--db-path", default="data/coding_assistant.db")
    parser.add_argument("--csv-path", default="data/archive/legacy_problem_bank/problem_bank_topic_pattern.csv")
    parser.add_argument("--markdown-path", default="data/archive/legacy_problem_bank/dsa_problems.md")
    parser.add_argument("--output-dir", default="reports/phase3")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory, _ = load_inventory(Path(args.db_path), Path(args.csv_path), Path(args.markdown_path))
    curriculum_issues, curriculum_meta = curriculum_checks(inventory)
    rec_issues, rec_meta = recommendation_quality_checks(Path(args.db_path))

    issues = {
        "critical": curriculum_issues["critical"] + rec_issues["critical"],
        "high": curriculum_issues["high"] + rec_issues["high"],
        "medium": curriculum_issues["medium"] + rec_issues["medium"],
        "low": curriculum_issues["low"] + rec_issues["low"],
    }

    report = {
        "summary": {
            "total_problems": len(inventory),
            "critical_issues": len(issues["critical"]),
            "high_issues": len(issues["high"]),
            "medium_issues": len(issues["medium"]),
            "low_issues": len(issues["low"]),
        },
        "curriculum_meta": curriculum_meta,
        "recommendation_meta": rec_meta,
        "issues": issues,
    }
    report_path = output_dir / "curriculum_validation_report.json"
    write_json(report_path, report)
    print(f"Report written: {report_path}")
    print(report["summary"])
    return 1 if issues["critical"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
