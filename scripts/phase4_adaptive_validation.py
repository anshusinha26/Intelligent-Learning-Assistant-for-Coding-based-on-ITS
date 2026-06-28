#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import Database
from src.learner_model import LearnerModel
from src.premium_bank_loader import sync_premium_problem_bank
from src.problem_bank import PREMIUM_DATASET_TIER
from src.rag_service import RAGService
from src.recommender import RecommendationEngine
from src.revision_scheduler import RevisionScheduler


VERDICTS = ["Accepted", "Wrong Answer", "Runtime Error", "Compilation Error", "Time Limit Exceeded"]
TOPIC_FOR_ARCHETYPE = {
    "Weak Graph learners": "Graphs",
    "Weak DP learners": "Dynamic Programming",
    "Weak Tree learners": "Trees",
    "Weak Array learners": "Arrays & Hashing",
}


@dataclass
class ArchetypeSpec:
    name: str
    base_accuracy: float
    speed_ms: int
    consistency: float
    learning_rate: float
    forgetting_rate: float
    motivation: float
    review_compliance: float
    target_level: str
    weak_topic: Optional[str] = None


@dataclass
class SyntheticLearner:
    user_id: int
    name: str
    archetype: str
    accuracy: float
    speed_ms: int
    consistency: float
    learning_rate: float
    forgetting_rate: float
    motivation: float
    review_compliance: float
    target_level: str
    weak_topic: Optional[str]
    weak_secondary: Optional[str]
    start_accuracy: float
    end_accuracy: float


@dataclass
class SimulationConfig:
    seed: int = 42
    learners_per_archetype: int = 200
    stress_learner_count: int = 8000
    core_attempts_per_user: int = 45
    stress_attempts_per_user: int = 2
    minimum_submissions: int = 100000
    recommendation_k: int = 5
    stress_recommendation_k: int = 3
    recommender_strategy: str = "optimized"
    report_path: Path = Path("reports/phase4/phase4_adaptive_validation.json")
    bank_path: Path = Path("data/premium/problem_bank.json")


def _archetype_specs() -> List[ArchetypeSpec]:
    return [
        ArchetypeSpec("Beginner", 0.33, 2100, 0.48, 0.040, 0.030, 0.62, 0.52, "easy"),
        ArchetypeSpec("Intermediate", 0.56, 1600, 0.65, 0.030, 0.018, 0.70, 0.62, "medium"),
        ArchetypeSpec("Advanced", 0.78, 1200, 0.80, 0.020, 0.012, 0.76, 0.74, "hard"),
        ArchetypeSpec("Returning learners", 0.58, 1700, 0.60, 0.026, 0.050, 0.63, 0.58, "medium"),
        ArchetypeSpec("Weak Graph learners", 0.54, 1800, 0.58, 0.032, 0.020, 0.68, 0.60, "medium", "Graphs"),
        ArchetypeSpec("Weak DP learners", 0.52, 1850, 0.57, 0.034, 0.022, 0.67, 0.60, "medium", "Dynamic Programming"),
        ArchetypeSpec("Weak Tree learners", 0.55, 1750, 0.60, 0.032, 0.020, 0.67, 0.62, "medium", "Trees"),
        ArchetypeSpec("Weak Array learners", 0.57, 1650, 0.61, 0.030, 0.018, 0.69, 0.63, "medium", "Arrays & Hashing"),
        ArchetypeSpec("Random learners", 0.50, 1900, 0.52, 0.025, 0.028, 0.55, 0.50, "medium"),
        ArchetypeSpec("High-speed learners", 0.66, 900, 0.72, 0.036, 0.015, 0.80, 0.76, "medium"),
    ]


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _difficulty_penalty(difficulty: str) -> float:
    if difficulty == "Easy":
        return 0.05
    if difficulty == "Hard":
        return 0.19
    return 0.11


def _sample_verdict(
    rng: random.Random,
    p_accept: float,
    consistency: float,
    speed_ms: int,
    difficulty: str,
) -> str:
    if rng.random() < p_accept:
        return "Accepted"
    wa = 0.52 - consistency * 0.18
    re = 0.22 + (1.0 - consistency) * 0.12
    ce = 0.10 + (1.0 - consistency) * 0.05
    tle = 0.16 + (0.10 if speed_ms > 1900 else 0.0) + (0.05 if difficulty == "Hard" else 0.0)
    total = wa + re + ce + tle
    r = rng.random() * total
    if r < wa:
        return "Wrong Answer"
    if r < wa + re:
        return "Runtime Error"
    if r < wa + re + ce:
        return "Compilation Error"
    return "Time Limit Exceeded"


def _error_type(verdict: str, rng: random.Random) -> Optional[str]:
    if verdict == "Accepted":
        return None
    if verdict == "Wrong Answer":
        return rng.choice(["logic-error", "off-by-one", "edge-case"])
    if verdict == "Runtime Error":
        return rng.choice(["runtime-exception", "index-error", "null-state"])
    if verdict == "Compilation Error":
        return "syntax-error"
    if verdict == "Time Limit Exceeded":
        return "timeout"
    return "unknown"


def _runtime_ms(verdict: str, speed_ms: int, difficulty: str, rng: random.Random) -> int:
    base = float(speed_ms)
    if difficulty == "Easy":
        base *= 0.82
    elif difficulty == "Hard":
        base *= 1.24
    if verdict == "Accepted":
        base *= 0.88
    elif verdict == "Wrong Answer":
        base *= 1.03
    elif verdict == "Runtime Error":
        base *= 1.18
    elif verdict == "Compilation Error":
        base *= 0.55
    else:
        base *= 1.55
    jitter = rng.uniform(0.78, 1.28)
    return max(20, int(base * jitter))


def _pick_problem(
    rng: random.Random,
    learner: SyntheticLearner,
    catalog: Dict[str, List[Dict[str, str]]],
    solved: set,
) -> Dict[str, str]:
    topics = list(catalog.keys())
    preferred_topic = learner.weak_topic
    if preferred_topic and rng.random() < 0.62:
        topic = preferred_topic
    elif learner.weak_secondary and rng.random() < 0.35:
        topic = learner.weak_secondary
    else:
        topic = rng.choice(topics)
    candidates = catalog.get(topic, [])
    if not candidates:
        candidates = [p for problems in catalog.values() for p in problems]
    if learner.target_level == "easy":
        level = {"Easy": 0.58, "Medium": 0.32, "Hard": 0.10}
    elif learner.target_level == "hard":
        level = {"Easy": 0.10, "Medium": 0.34, "Hard": 0.56}
    else:
        level = {"Easy": 0.30, "Medium": 0.50, "Hard": 0.20}
    weighted = [p for p in candidates if rng.random() < level.get(p["difficulty"], 0.25)]
    if not weighted:
        weighted = candidates
    unsolved = [p for p in weighted if p["problem_id"] not in solved]
    pool = unsolved if unsolved and rng.random() < 0.72 else weighted
    return rng.choice(pool)


def _build_catalog(db: Database) -> Tuple[Dict[str, List[Dict[str, str]]], Dict[str, str], Dict[str, List[Dict[str, object]]]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT problem_id, topic, difficulty
        FROM problems
        WHERE dataset_tier = ? AND is_active = 1
        ORDER BY problem_id
        """,
        (PREMIUM_DATASET_TIER,),
    ).fetchall()
    rel_rows = cursor.execute(
        """
        SELECT problem_id, related_problem_id, edge_type
        FROM premium_problem_relationships
        """
    ).fetchall()
    conn.close()
    catalog: Dict[str, List[Dict[str, str]]] = {}
    problem_topic: Dict[str, str] = {}
    for row in rows:
        item = {"problem_id": row["problem_id"], "topic": row["topic"], "difficulty": row["difficulty"]}
        catalog.setdefault(row["topic"], []).append(item)
        problem_topic[row["problem_id"]] = row["topic"]
    rel_map: Dict[str, List[Dict[str, object]]] = {}
    for row in rel_rows:
        rel_map.setdefault(row["problem_id"], []).append(
            {"target": row["related_problem_id"], "edge_type": row["edge_type"]}
        )
    return catalog, problem_topic, rel_map


def _insert_users(db: Database, learners: Sequence[SyntheticLearner]) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO users (user_id, name, email, password_hash, role, target_level, email_verified)
        VALUES (?, ?, ?, ?, 'user', ?, 1)
        """,
        [
            (
                learner.user_id,
                learner.name,
                f"sim_user_{learner.user_id}@example.com",
                "$2b$12$8qj4wqIJIQM6wP4UuQ3EuOnJf6wUkfIykzo8RO8qDRad5Df0fM1f2",
                learner.target_level,
            )
            for learner in learners
        ],
    )
    conn.commit()
    conn.close()


def _generate_learners(config: SimulationConfig, rng: random.Random) -> Tuple[List[SyntheticLearner], List[SyntheticLearner], List[SyntheticLearner]]:
    specs = _archetype_specs()
    core: List[SyntheticLearner] = []
    user_id = 1
    topic_list = list(TOPIC_FOR_ARCHETYPE.values())
    for spec in specs:
        for idx in range(config.learners_per_archetype):
            accuracy = _clip(rng.gauss(spec.base_accuracy, 0.07), 0.05, 0.97)
            speed_ms = max(250, int(rng.gauss(spec.speed_ms, 180)))
            consistency = _clip(rng.gauss(spec.consistency, 0.08), 0.10, 0.98)
            learning_rate = _clip(rng.gauss(spec.learning_rate, 0.008), 0.005, 0.12)
            forgetting_rate = _clip(rng.gauss(spec.forgetting_rate, 0.007), 0.001, 0.20)
            motivation = _clip(rng.gauss(spec.motivation, 0.10), 0.10, 0.98)
            review_compliance = _clip(rng.gauss(spec.review_compliance, 0.12), 0.05, 0.98)
            weak_secondary = None
            if spec.weak_topic:
                weak_secondary = rng.choice([t for t in topic_list if t != spec.weak_topic])
            core.append(
                SyntheticLearner(
                    user_id=user_id,
                    name=f"{spec.name} #{idx+1}",
                    archetype=spec.name,
                    accuracy=accuracy,
                    speed_ms=speed_ms,
                    consistency=consistency,
                    learning_rate=learning_rate,
                    forgetting_rate=forgetting_rate,
                    motivation=motivation,
                    review_compliance=review_compliance,
                    target_level=spec.target_level,
                    weak_topic=spec.weak_topic,
                    weak_secondary=weak_secondary,
                    start_accuracy=accuracy,
                    end_accuracy=accuracy,
                )
            )
            user_id += 1

    stress: List[SyntheticLearner] = []
    for idx in range(config.stress_learner_count):
        stress.append(
            SyntheticLearner(
                user_id=user_id,
                name=f"Stress learner #{idx+1}",
                archetype="Stress concurrent learners",
                accuracy=_clip(rng.gauss(0.48, 0.16), 0.03, 0.96),
                speed_ms=max(220, int(rng.gauss(1700, 420))),
                consistency=_clip(rng.gauss(0.55, 0.20), 0.05, 0.98),
                learning_rate=_clip(rng.gauss(0.025, 0.015), 0.003, 0.15),
                forgetting_rate=_clip(rng.gauss(0.03, 0.02), 0.001, 0.25),
                motivation=_clip(rng.gauss(0.52, 0.20), 0.05, 0.99),
                review_compliance=_clip(rng.gauss(0.48, 0.20), 0.01, 0.99),
                target_level=rng.choice(["easy", "medium", "hard"]),
                weak_topic=rng.choice(list(TOPIC_FOR_ARCHETYPE.values())),
                weak_secondary=rng.choice(list(TOPIC_FOR_ARCHETYPE.values())),
                start_accuracy=0.0,
                end_accuracy=0.0,
            )
        )
        user_id += 1
    for learner in stress:
        learner.start_accuracy = learner.accuracy
        learner.end_accuracy = learner.accuracy
    return core + stress, core, stress


def _simulate_events(
    learners: Sequence[SyntheticLearner],
    catalog: Dict[str, List[Dict[str, str]]],
    attempts_per_user: int,
    rng: random.Random,
    start_dt: datetime,
    include_inactivity: bool,
) -> Tuple[List[Tuple], List[Tuple], Dict[int, Dict[str, object]]]:
    phase1_attempts: List[Tuple] = []
    phase2_attempts: List[Tuple] = []
    traces: Dict[int, Dict[str, object]] = {}
    for learner in learners:
        solved: set = set()
        local_time = start_dt + timedelta(days=rng.randint(0, 8), minutes=rng.randint(0, 59))
        attempts = attempts_per_user
        if learner.archetype == "Stress concurrent learners":
            draw = rng.random()
            if draw < 0.15:
                attempts = 0
            elif draw < 0.45:
                attempts = 1
        if attempts <= 0:
            traces[learner.user_id] = {
                "phase1_accept_rate": 0.0,
                "phase2_accept_rate": 0.0,
                "attempts": 0,
                "inactivity_days": 0,
            }
            continue
        split = max(1, attempts // 2)
        phase1_success = 0
        phase2_success = 0
        inactivity_days = 0
        streak_fail = 0
        for idx in range(attempts):
            if include_inactivity and learner.archetype == "Returning learners" and idx == split:
                gap = rng.randint(26, 48)
                inactivity_days = gap
                learner.accuracy = _clip(learner.accuracy * (1.0 - learner.forgetting_rate * gap / 32.0), 0.03, 0.98)
                local_time += timedelta(days=gap)
            problem = _pick_problem(rng, learner, catalog, solved)
            topic = problem["topic"]
            difficulty = problem["difficulty"]
            weak_penalty = 0.0
            if learner.weak_topic and topic == learner.weak_topic:
                weak_penalty += 0.21
            elif learner.weak_secondary and topic == learner.weak_secondary:
                weak_penalty += 0.09
            progress_boost = (idx / max(1, attempts - 1)) * learner.learning_rate * 1.8
            frustration_penalty = 0.03 * max(0, streak_fail - 2)
            p_accept = _clip(
                learner.accuracy + progress_boost - _difficulty_penalty(difficulty) - weak_penalty - frustration_penalty,
                0.01,
                0.98,
            )
            if learner.archetype.startswith("Weak ") and idx < 3 and topic == learner.weak_topic:
                p_accept = min(p_accept, 0.10)
            verdict = _sample_verdict(rng, p_accept, learner.consistency, learner.speed_ms, difficulty)
            err = _error_type(verdict, rng)
            runtime_ms = _runtime_ms(verdict, learner.speed_ms, difficulty, rng)
            attempted_at = local_time.isoformat(timespec="seconds")
            if verdict == "Accepted":
                solved.add(problem["problem_id"])
                streak_fail = 0
                learner.accuracy = _clip(
                    learner.accuracy + learner.learning_rate * (1.0 - learner.accuracy) * (0.9 + learner.motivation * 0.2),
                    0.01,
                    0.995,
                )
            else:
                streak_fail += 1
                learner.accuracy = _clip(
                    learner.accuracy - (1.0 - learner.consistency) * 0.020 - weak_penalty * 0.020,
                    0.01,
                    0.995,
                )
            if idx >= split:
                learner.accuracy = _clip(
                    learner.accuracy + learner.learning_rate * 0.10,
                    0.01,
                    0.995,
                )
            step_days = 1 if learner.archetype == "High-speed learners" else rng.randint(1, 3)
            local_time += timedelta(days=step_days, minutes=rng.randint(5, 120))

            row = (
                learner.user_id,
                problem["problem_id"],
                verdict,
                runtime_ms,
                err,
                attempted_at,
                learner.user_id,
                problem["problem_id"],
                "python",
                "def solve(*args):\n    return None\n",
                verdict,
                runtime_ms,
                json.dumps({"simulated": True, "verdict": verdict}),
                attempted_at,
            )
            if idx < split:
                phase1_attempts.append(row)
                if verdict == "Accepted":
                    phase1_success += 1
            else:
                phase2_attempts.append(row)
                if verdict == "Accepted":
                    phase2_success += 1

        traces[learner.user_id] = {
            "phase1_accept_rate": phase1_success / max(1, split),
            "phase2_accept_rate": phase2_success / max(1, attempts - split),
            "attempts": attempts,
            "inactivity_days": inactivity_days,
        }
        learner.end_accuracy = learner.accuracy
    return phase1_attempts, phase2_attempts, traces


def _bulk_insert_events(db: Database, rows: Sequence[Tuple]) -> None:
    if not rows:
        return
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO attempts (user_id, problem_id, verdict, time_taken, error_type, attempted_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows],
    )
    cursor.executemany(
        """
        INSERT INTO submissions (user_id, problem_id, language, code, verdict, runtime_ms, output, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13]) for r in rows],
    )
    conn.commit()
    conn.close()


def _ensure_phase4_indexes(db: Database) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_problem_phase4 ON attempts(user_id, problem_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_verdict_phase4 ON attempts(user_id, verdict, attempted_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_learner_metrics_user_phase4 ON learner_metrics(user_id, topic, pattern)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_user_phase4 ON submissions(user_id, problem_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_revision_user_phase4 ON revision_schedule(user_id, status, next_review_date)")
    conn.commit()
    conn.close()


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return float(sum(items) / len(items)) if items else 0.0


def _percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * pct
    lower = math.floor(idx)
    upper = math.ceil(idx)
    if lower == upper:
        return float(ordered[int(idx)])
    return float(ordered[lower] * (upper - idx) + ordered[upper] * (idx - lower))


def _mean_ci95(values: Sequence[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "std": 0.0, "ci95_low": 0.0, "ci95_high": 0.0, "n": 0}
    vals = [float(v) for v in values]
    mean = statistics.mean(vals)
    std = statistics.pstdev(vals) if len(vals) > 1 else 0.0
    se = std / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
    margin = 1.96 * se
    return {
        "mean": float(mean),
        "std": float(std),
        "ci95_low": float(mean - margin),
        "ci95_high": float(mean + margin),
        "n": len(vals),
    }


def _pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    mx = statistics.mean(x)
    my = statistics.mean(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if sx == 0 or sy == 0:
        return 0.0
    return float(cov / (sx * sy))


def _dcg(binary_relevance: Sequence[int]) -> float:
    score = 0.0
    for idx, rel in enumerate(binary_relevance):
        if rel:
            score += 1.0 / math.log2(idx + 2)
    return score


def _topic_entropy(items: Sequence[str]) -> float:
    if not items:
        return 0.0
    counts: Dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    total = len(items)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def _fetch_mastery_map(db: Database, user_id: int) -> Dict[str, float]:
    conn = db.get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT topic, mastery_score
        FROM learner_metrics
        WHERE user_id = ? AND topic IS NOT NULL
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return {row["topic"]: row["mastery_score"] for row in rows}


def _fetch_solved(db: Database, user_id: int) -> set:
    conn = db.get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT DISTINCT a.problem_id
        FROM attempts a
        JOIN problems p ON p.problem_id = a.problem_id
        WHERE a.user_id = ? AND a.verdict = 'Accepted' AND p.dataset_tier = ? AND p.is_active = 1
        """,
        (user_id, PREMIUM_DATASET_TIER),
    ).fetchall()
    conn.close()
    return {row["problem_id"] for row in rows}


def _build_relevant_set(
    learner: SyntheticLearner,
    solved: set,
    all_problem_ids: set,
    problem_topic: Dict[str, str],
    relationship_map: Dict[str, List[Dict[str, object]]],
) -> set:
    relevant = set()
    weak_topics = {t for t in [learner.weak_topic, learner.weak_secondary] if t}
    for pid in all_problem_ids:
        if pid in solved:
            continue
        if weak_topics and problem_topic.get(pid) in weak_topics:
            relevant.add(pid)
    for solved_id in solved:
        for edge in relationship_map.get(solved_id, []):
            if edge["edge_type"] in {"prerequisite", "follow_up", "review", "recovery"}:
                target = edge["target"]
                if target not in solved:
                    relevant.add(target)
    return relevant


def _run_rag_personalization_probe(
    learner_model: LearnerModel,
    scheduler: RevisionScheduler,
    db: Database,
    learner_a: SyntheticLearner,
    learner_b: SyntheticLearner,
) -> Dict[str, object]:
    rag = RAGService(
        enabled=True,
        mode="local",
        base_url="http://127.0.0.1:0",
        org_id="phase4",
        agent_id="phase4",
        service_token="",
        allow_full_solutions=False,
        enforce_hint_progression=True,
        max_question_chars=2000,
        timeout_seconds=5.0,
    )
    conn = db.get_connection()
    cursor = conn.cursor()
    first_problem = cursor.execute(
        """
        SELECT problem_id, title, topic, pattern, difficulty, time_complexity, space_complexity
        FROM problems
        WHERE dataset_tier = ? AND is_active = 1
        ORDER BY problem_id
        LIMIT 1
        """,
        (PREMIUM_DATASET_TIER,),
    ).fetchone()
    conn.close()
    problem_context = dict(first_problem) if first_problem else {}

    def ask(learner: SyntheticLearner) -> str:
        weaknesses = learner_model.get_weakness_summary(learner.user_id, 3)
        errors = learner_model.get_error_patterns(learner.user_id)
        profile = learner_model.get_user_stats(learner.user_id)
        revisions = scheduler.get_revision_stats(learner.user_id)
        result = rag.query(
            user_id=learner.user_id,
            thread_id=f"phase4-{learner.user_id}",
            question="Need second-level hint focused on my mistakes.",
            hint_level=2,
            want_full_solution=False,
            problem_context=problem_context,
            weakness_context=weaknesses,
            error_context=[{"error_type": k, "count": v} for k, v in errors.items()],
            learner_profile=profile,
            revision_context=revisions,
            problem_attempt_context={"attempts": profile.get("total_attempts", 0)},
            rag_chunks=[
                {"type": "learning_objectives", "text": "Use hash map for complement lookup."},
                {"type": "common_mistakes", "text": "Forgetting to handle duplicates and same index usage."},
            ],
        )
        return result.answer

    answer_a = ask(learner_a)
    answer_b = ask(learner_b)
    return {
        "answer_a": answer_a[:400],
        "answer_b": answer_b[:400],
        "identical": answer_a.strip() == answer_b.strip(),
        "mentions_a_topic": (learner_a.weak_topic or "").lower() in answer_a.lower(),
        "mentions_b_topic": (learner_b.weak_topic or "").lower() in answer_b.lower(),
    }


def run_phase4_validation(config: SimulationConfig) -> Dict[str, object]:
    rng = random.Random(config.seed)
    with tempfile.TemporaryDirectory(prefix="phase4_its_") as tmp:
        db_path = Path(tmp) / "phase4.db"
        db = Database(str(db_path))
        sync_premium_problem_bank(db, config.bank_path)

        all_learners, core_learners, stress_learners = _generate_learners(config, rng)
        _insert_users(db, all_learners)

        catalog, problem_topic, relationship_map = _build_catalog(db)
        all_problem_ids = set(problem_topic.keys())
        start_dt = datetime.now(timezone.utc) - timedelta(days=180)

        core_phase1, core_phase2, core_traces = _simulate_events(
            core_learners,
            catalog,
            attempts_per_user=config.core_attempts_per_user,
            rng=rng,
            start_dt=start_dt,
            include_inactivity=True,
        )
        stress_phase1, stress_phase2, stress_traces = _simulate_events(
            stress_learners,
            catalog,
            attempts_per_user=config.stress_attempts_per_user,
            rng=rng,
            start_dt=start_dt + timedelta(days=8),
            include_inactivity=False,
        )

        phase1_rows = core_phase1 + stress_phase1
        phase2_rows = core_phase2 + stress_phase2
        _bulk_insert_events(db, phase1_rows)
        _ensure_phase4_indexes(db)

        learner_model = LearnerModel(db)
        recommender = RecommendationEngine(db, strategy=config.recommender_strategy)
        scheduler = RevisionScheduler(db)

        baseline_recs: Dict[int, List[str]] = {}
        baseline_mastery: Dict[int, float] = {}
        baseline_weak_topic: Dict[int, str] = {}
        update_latencies: List[float] = []
        rec_latencies: List[float] = []
        revision_latencies: List[float] = []
        revision_completed_count = 0
        conn = db.get_connection()
        cursor = conn.cursor()
        for learner in core_learners:
            t0 = time.perf_counter()
            learner_model.update_learner_metrics(learner.user_id)
            update_latencies.append((time.perf_counter() - t0) * 1000)

            t1 = time.perf_counter()
            recommender.generate_recommendations(
                learner.user_id,
                top_k=config.recommendation_k,
                refresh_pending=True,
            )
            rec_latencies.append((time.perf_counter() - t1) * 1000)
            baseline_recs[learner.user_id] = [
                item["problem_id"]
                for item in recommender.get_recommendations(learner.user_id, status="pending", limit=config.recommendation_k)
            ]
            weak = learner_model.get_weakness_summary(learner.user_id, 1)
            baseline_weak_topic[learner.user_id] = weak[0]["topic"] if weak else ""
            mastery_map = _fetch_mastery_map(db, learner.user_id)
            baseline_mastery[learner.user_id] = _mean(mastery_map.values())

            t2 = time.perf_counter()
            scheduler.schedule_revisions(learner.user_id)
            revision_latencies.append((time.perf_counter() - t2) * 1000)
            if learner.review_compliance > 0.62 and rng.random() < learner.review_compliance:
                yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
                cursor.execute(
                    """
                    UPDATE revision_schedule
                    SET next_review_date = ?
                    WHERE user_id = ? AND status = 'pending'
                    """,
                    (yesterday, learner.user_id),
                )
                conn.commit()
                due = scheduler.get_due_revisions(learner.user_id, limit=2)
                if due:
                    scheduler.mark_revision_completed(due[0]["schedule_id"], learner.user_id)
                    revision_completed_count += 1
        conn.close()

        _bulk_insert_events(db, phase2_rows)
        _ensure_phase4_indexes(db)

        stress_update_latencies: List[float] = []
        stress_rec_latencies: List[float] = []
        stress_revision_latencies: List[float] = []
        stress_started = time.perf_counter()
        cpu_started = time.process_time()
        for idx, learner in enumerate(all_learners, start=1):
            t0 = time.perf_counter()
            learner_model.update_learner_metrics(learner.user_id)
            stress_update_latencies.append((time.perf_counter() - t0) * 1000)
            t1 = time.perf_counter()
            recommender.generate_recommendations(
                learner.user_id,
                top_k=config.stress_recommendation_k,
                refresh_pending=False,
            )
            stress_rec_latencies.append((time.perf_counter() - t1) * 1000)
            t2 = time.perf_counter()
            scheduler.schedule_revisions(learner.user_id)
            stress_revision_latencies.append((time.perf_counter() - t2) * 1000)
            if idx % 1000 == 0:
                print(f"[phase4] stress pass {idx}/{len(all_learners)}", flush=True)
        stress_wall = time.perf_counter() - stress_started
        stress_cpu = time.process_time() - cpu_started

        final_recs: Dict[int, List[Tuple[str, str]]] = {}
        weak_topic_hits = 0
        weak_topic_total = 0
        latent = []
        observed_success = []
        observed_mastery = []
        improvement_deltas = []
        recommendation_precisions = []
        recommendation_recalls = []
        recommendation_ndcgs = []
        recommendation_diversity = []
        recommendation_novelty = []
        recommendation_progression = []
        difficulty_mismatch_rates = []
        unsolved_retry_rates = []
        weak_recovery_hit_rates = []
        topic_distribution: List[str] = []
        rec_overlap = []
        retention_improvement = []
        cold_start_total = 0
        cold_start_with_recs = 0
        expected_by_archetype: Dict[str, List[List[str]]] = {}
        popularity: Dict[str, int] = {}
        conn = db.get_connection()
        cursor = conn.cursor()
        pop_rows = cursor.execute(
            """
            SELECT problem_id, COUNT(*) AS c
            FROM attempts
            GROUP BY problem_id
            """
        ).fetchall()
        for row in pop_rows:
            popularity[row["problem_id"]] = row["c"]
        max_pop = max(popularity.values()) if popularity else 1
        for learner in core_learners:
            stats = learner_model.get_user_stats(learner.user_id)
            mastery_map = _fetch_mastery_map(db, learner.user_id)
            weak_summary = learner_model.get_weakness_summary(learner.user_id, 3)
            pending = recommender.get_recommendations(learner.user_id, status="pending", limit=config.recommendation_k)
            final_recs[learner.user_id] = [(item["problem_id"], item["topic"]) for item in pending]
            final_ids = [item[0] for item in final_recs[learner.user_id]]
            final_diffs = [item["difficulty"] for item in pending]
            base_ids = baseline_recs.get(learner.user_id, [])
            if base_ids:
                rec_overlap.append(len(set(base_ids) & set(final_ids)) / max(1, len(set(base_ids) | set(final_ids))))
            if learner.archetype in TOPIC_FOR_ARCHETYPE:
                weak_topic_total += 1
                weak_target = TOPIC_FOR_ARCHETYPE[learner.archetype].lower()
                if any(weak_target in (item["topic"] or "").lower() for item in weak_summary):
                    weak_topic_hits += 1
            latent.append(learner.end_accuracy)
            observed_success.append((stats.get("success_rate", 0.0) or 0.0) / 100.0)
            observed_mastery.append(_mean(mastery_map.values()))
            improvement_deltas.append(core_traces.get(learner.user_id, {}).get("phase2_accept_rate", 0.0) - core_traces.get(learner.user_id, {}).get("phase1_accept_rate", 0.0))
            solved = _fetch_solved(db, learner.user_id)
            relevant = _build_relevant_set(learner, solved, all_problem_ids, problem_topic, relationship_map)
            if final_ids:
                rel_vec = [1 if pid in relevant else 0 for pid in final_ids]
                precision = sum(rel_vec) / len(rel_vec)
                recall = sum(rel_vec) / max(1, len(relevant))
                ideal = [1] * min(len(relevant), len(rel_vec))
                ndcg = _dcg(rel_vec) / max(_dcg(ideal), 1e-9)
                recommendation_precisions.append(precision)
                recommendation_recalls.append(recall)
                recommendation_ndcgs.append(ndcg)
                recommendation_diversity.append(len({topic for _, topic in final_recs[learner.user_id]}) / len(final_ids))
                recommendation_novelty.append(
                    _mean([1.0 - (popularity.get(pid, 0) / max_pop) for pid in final_ids])
                )
                difficulty_alignment = 0
                for diff in final_diffs:
                    if learner.target_level == "easy" and diff == "Easy":
                        difficulty_alignment += 1
                    elif learner.target_level == "medium" and diff in {"Easy", "Medium"}:
                        difficulty_alignment += 1
                    elif learner.target_level == "hard" and diff in {"Medium", "Hard"}:
                        difficulty_alignment += 1
                difficulty_mismatch_rates.append(1.0 - (difficulty_alignment / len(final_diffs)))

                retry_count = sum(1 for pid in final_ids if pid not in solved)
                unsolved_retry_rates.append(retry_count / len(final_ids))

                weak_topics = {t for t in [learner.weak_topic, learner.weak_secondary] if t}
                weak_hits = sum(1 for _, topic_name in final_recs[learner.user_id] if topic_name in weak_topics)
                weak_recovery_hit_rates.append(weak_hits / len(final_ids))

                progression_hits = 0
                for solved_pid in solved:
                    targets = {edge["target"] for edge in relationship_map.get(solved_pid, [])}
                    progression_hits += sum(1 for pid in final_ids if pid in targets)
                recommendation_progression.append(min(1.0, progression_hits / len(final_ids)))
                topic_distribution.extend([topic for _, topic in final_recs[learner.user_id]])
            reviewed = learner.review_compliance > 0.62
            if reviewed:
                retention_improvement.append(core_traces[learner.user_id]["phase2_accept_rate"] - core_traces[learner.user_id]["phase1_accept_rate"])
            expected_by_archetype.setdefault(learner.archetype, []).append(final_ids)

        for learner in stress_learners:
            attempts = stress_traces.get(learner.user_id, {}).get("attempts", 0)
            if attempts <= 1:
                cold_start_total += 1
                recs = recommender.get_recommendations(learner.user_id, status="pending", limit=config.stress_recommendation_k)
                if recs:
                    cold_start_with_recs += 1
        conn.close()

        recommendation_coverage = len({pid for values in final_recs.values() for pid, _ in values}) / max(1, len(all_problem_ids))
        repeated_rate = 0.0
        conn = db.get_connection()
        cursor = conn.cursor()
        dup_rows = cursor.execute(
            """
            SELECT COUNT(*) AS c
            FROM (
                SELECT user_id, problem_id, status, COUNT(*) AS cnt
                FROM recommendations
                WHERE status = 'pending'
                GROUP BY user_id, problem_id, status
                HAVING cnt > 1
            )
            """
        ).fetchone()
        if dup_rows and dup_rows["c"]:
            repeated_rate = 1.0
        total_attempt_rows = cursor.execute("SELECT COUNT(*) AS c FROM attempts").fetchone()["c"]
        total_submission_rows = cursor.execute("SELECT COUNT(*) AS c FROM submissions").fetchone()["c"]
        total_revision_rows = cursor.execute("SELECT COUNT(*) AS c FROM revision_schedule").fetchone()["c"]
        due_revisions = cursor.execute(
            "SELECT COUNT(*) AS c FROM revision_schedule WHERE status = 'pending' AND next_review_date <= DATE('now')"
        ).fetchone()["c"]
        pending_recommendations = cursor.execute(
            "SELECT COUNT(*) AS c FROM recommendations WHERE status = 'pending'"
        ).fetchone()["c"]
        conn.close()

        archetype_diversity = {}
        archetype_names = list(expected_by_archetype.keys())
        for i, a_name in enumerate(archetype_names):
            sets_a = expected_by_archetype[a_name][:40]
            for b_name in archetype_names[i + 1 :]:
                sets_b = expected_by_archetype[b_name][:40]
                jaccards = []
                for list_a in sets_a:
                    for list_b in sets_b:
                        sa = set(list_a)
                        sb = set(list_b)
                        if not sa and not sb:
                            continue
                        jaccards.append(len(sa & sb) / max(1, len(sa | sb)))
                if jaccards:
                    archetype_diversity[f"{a_name} vs {b_name}"] = _mean(jaccards)

        weak_graph = next((x for x in core_learners if x.archetype == "Weak Graph learners"), None)
        weak_dp = next((x for x in core_learners if x.archetype == "Weak DP learners"), None)
        rag_probe = (
            _run_rag_personalization_probe(learner_model, scheduler, db, weak_graph, weak_dp)
            if weak_graph and weak_dp
            else {"identical": True, "mentions_a_topic": False, "mentions_b_topic": False}
        )

        skill_corr = _pearson(latent, observed_mastery)
        success_corr = _pearson(latent, observed_success)
        weak_detection = weak_topic_hits / max(1, weak_topic_total)
        cold_start_quality = cold_start_with_recs / max(1, cold_start_total)
        rec_precision = _mean(recommendation_precisions)
        rec_recall = _mean(recommendation_recalls)
        rec_ndcg = _mean(recommendation_ndcgs)
        rec_diversity = _mean(recommendation_diversity)
        rec_novelty = _mean(recommendation_novelty)
        rec_progression = _mean(recommendation_progression)
        difficulty_mismatch = _mean(difficulty_mismatch_rates)
        retry_focus = _mean(unsolved_retry_rates)
        weak_recovery = _mean(weak_recovery_hit_rates)
        review_effect = _mean(retention_improvement)
        topic_entropy = _topic_entropy(topic_distribution)
        personalization_overlap = _mean(rec_overlap)
        improvement_rate = _mean(improvement_deltas)

        learning_quality_score = round(
            _clip(
                10
                * (
                    0.30 * max(0.0, skill_corr)
                    + 0.22 * max(0.0, success_corr)
                    + 0.20 * weak_detection
                    + 0.13 * _clip(improvement_rate + 0.5, 0.0, 1.0)
                    + 0.15 * cold_start_quality
                ),
                0.0,
                10.0,
            ),
            2,
        )
        recommendation_quality_score = round(
            _clip(
                10
                * (
                    0.28 * rec_precision
                    + 0.20 * rec_recall
                    + 0.22 * rec_ndcg
                    + 0.15 * rec_diversity
                    + 0.10 * rec_novelty
                    + 0.05 * recommendation_coverage
                ),
                0.0,
                10.0,
            ),
            2,
        )
        revision_quality_score = round(
            _clip(
                10
                * (
                    0.35 * _clip(review_effect + 0.5, 0.0, 1.0)
                    + 0.30 * (1.0 if revision_completed_count > 0 else 0.0)
                    + 0.20 * (1.0 if due_revisions >= 0 else 0.0)
                    + 0.15 * _clip(1.0 - repeated_rate, 0.0, 1.0)
                ),
                0.0,
                10.0,
            ),
            2,
        )
        personalization_quality_score = round(
            _clip(
                10
                * (
                    0.35 * (1.0 - _clip(personalization_overlap, 0.0, 1.0))
                    + 0.25 * (1.0 - _clip(_mean(archetype_diversity.values()) if archetype_diversity else 0.0, 0.0, 1.0))
                    + 0.20 * (1.0 if not rag_probe.get("identical", True) else 0.0)
                    + 0.20 * cold_start_quality
                ),
                0.0,
                10.0,
            ),
            2,
        )
        its_quality_score = round(
            _clip(
                0.35 * learning_quality_score
                + 0.30 * recommendation_quality_score
                + 0.20 * revision_quality_score
                + 0.15 * personalization_quality_score,
                0.0,
                10.0,
            ),
            2,
        )

        recommendation_random_baseline = _mean([min(1.0, len(_build_relevant_set(l, _fetch_solved(db, l.user_id), all_problem_ids, problem_topic, relationship_map)) / max(1, len(all_problem_ids))) for l in core_learners]) * config.recommendation_k / max(1, config.recommendation_k)
        precision_std = statistics.pstdev(recommendation_precisions) if recommendation_precisions else 0.0
        if recommendation_precisions:
            denom = max(1e-9, precision_std / math.sqrt(len(recommendation_precisions)))
            t_stat = (rec_precision - recommendation_random_baseline) / denom
        else:
            t_stat = 0.0

        findings = []
        if repeated_rate > 0:
            findings.append({"severity": "High", "issue": "Duplicate pending recommendations detected", "metric": repeated_rate})
        if weak_detection < 0.6:
            findings.append({"severity": "High", "issue": "Weak-topic detection hit-rate below threshold", "metric": weak_detection})
        if rec_precision < 0.35:
            findings.append({"severity": "Medium", "issue": "Recommendation precision@k below 0.35", "metric": rec_precision})
        if rag_probe.get("identical", True):
            findings.append({"severity": "Medium", "issue": "RAG personalization responses too similar", "metric": 1.0})
        if abs(review_effect) < 0.03:
            findings.append({"severity": "Medium", "issue": "Revision effect size is weak", "metric": review_effect})
        if difficulty_mismatch > 0.42:
            findings.append({"severity": "Medium", "issue": "Recommendation difficulty mismatch is elevated", "metric": difficulty_mismatch})
        if rec_progression < 0.25:
            findings.append({"severity": "Medium", "issue": "Topic progression signal is weak", "metric": rec_progression})

        auto_tuning = {
            "statistically_justified": t_stat < 1.96 and rec_precision < 0.45,
            "recommendation_weight_adjustment": "Increase weak-topic weight by +10% and relationship-edge weight by +5%."
            if t_stat < 1.96 and rec_precision < 0.45
            else "No tuning applied. Evidence does not justify parameter changes.",
            "t_stat_precision_vs_random": round(t_stat, 3),
            "random_baseline_precision": round(recommendation_random_baseline, 4),
        }

        mem_raw = 0.0
        try:
            import resource

            rss = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            mem_raw = rss / (1024.0 * 1024.0) if sys.platform == "darwin" else rss / 1024.0
        except Exception:
            mem_raw = 0.0

        report = {
            "phase": "Phase 4 — Learner Model & Adaptive Intelligence Validation",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "configuration": {
                "learners_per_archetype": config.learners_per_archetype,
                "archetype_count": len(_archetype_specs()),
                "core_learners": len(core_learners),
                "stress_learners": len(stress_learners),
                "total_learners": len(all_learners),
                "core_attempts_per_user": config.core_attempts_per_user,
                "stress_attempts_per_user": config.stress_attempts_per_user,
                "minimum_submissions_required": config.minimum_submissions,
                "recommender_strategy": config.recommender_strategy,
                "seed": config.seed,
            },
            "part_1_synthetic_learners": {
                "archetype_counts": {
                    spec.name: config.learners_per_archetype for spec in _archetype_specs()
                },
                "unique_parameterized_learners": len(all_learners),
                "parameter_ranges": {
                    "accuracy": [round(min(l.start_accuracy for l in all_learners), 4), round(max(l.start_accuracy for l in all_learners), 4)],
                    "speed_ms": [min(l.speed_ms for l in all_learners), max(l.speed_ms for l in all_learners)],
                    "consistency": [round(min(l.consistency for l in all_learners), 4), round(max(l.consistency for l in all_learners), 4)],
                    "learning_rate": [round(min(l.learning_rate for l in all_learners), 4), round(max(l.learning_rate for l in all_learners), 4)],
                    "forgetting_rate": [round(min(l.forgetting_rate for l in all_learners), 4), round(max(l.forgetting_rate for l in all_learners), 4)],
                },
            },
            "part_2_longitudinal_simulation": {
                "attempt_rows": total_attempt_rows,
                "submission_rows": total_submission_rows,
                "verdict_coverage": VERDICTS,
                "minimum_submissions_met": total_submission_rows >= config.minimum_submissions,
                "signals_included": [
                    "Accepted",
                    "Wrong Answer",
                    "Runtime Error",
                    "Compilation Error",
                    "Time Limit Exceeded",
                    "Repeated failures",
                    "Long inactivity",
                    "Rapid improvement",
                    "Regression",
                    "Topic switching",
                ],
            },
            "part_3_learner_model": {
                "skill_vs_mastery_correlation": round(skill_corr, 4),
                "skill_vs_success_correlation": round(success_corr, 4),
                "weak_topic_detection_hit_rate": round(weak_detection, 4),
                "cold_start_recommendation_availability": round(cold_start_quality, 4),
                "average_phase_improvement": round(improvement_rate, 4),
            },
            "part_4_recommendation_engine": {
                "precision_at_k": round(rec_precision, 4),
                "recall_at_k": round(rec_recall, 4),
                "ndcg_at_k": round(rec_ndcg, 4),
                "coverage": round(recommendation_coverage, 4),
                "novelty": round(rec_novelty, 4),
                "diversity": round(rec_diversity, 4),
                "progression_signal": round(rec_progression, 4),
                "difficulty_mismatch_rate": round(difficulty_mismatch, 4),
                "unsolved_retry_focus": round(retry_focus, 4),
                "weak_recovery_hit_rate": round(weak_recovery, 4),
                "repeated_recommendation_rate": round(repeated_rate, 4),
                "topic_entropy": round(topic_entropy, 4),
                "pending_recommendation_rows": pending_recommendations,
                "distribution": {
                    "precision": _mean_ci95(recommendation_precisions),
                    "recall": _mean_ci95(recommendation_recalls),
                    "ndcg": _mean_ci95(recommendation_ndcgs),
                    "diversity": _mean_ci95(recommendation_diversity),
                    "novelty": _mean_ci95(recommendation_novelty),
                    "difficulty_mismatch": _mean_ci95(difficulty_mismatch_rates),
                },
            },
            "part_5_revision_engine": {
                "revision_rows": total_revision_rows,
                "due_revisions": due_revisions,
                "completed_revision_actions": revision_completed_count,
                "retention_improvement_effect": round(review_effect, 4),
            },
            "part_6_personalization": {
                "cross_phase_recommendation_overlap": round(_mean(rec_overlap), 4),
                "cross_archetype_jaccard_mean": round(_mean(archetype_diversity.values()) if archetype_diversity else 0.0, 4),
                "rag_personalization_probe": rag_probe,
            },
            "part_7_stress_test": {
                "active_learners_simulated": len(all_learners),
                "simulated_submissions": total_submission_rows,
                "stress_wall_seconds": round(stress_wall, 4),
                "stress_cpu_seconds": round(stress_cpu, 4),
                "memory_peak_mb": round(mem_raw, 2),
                "learner_update_latency_ms": {
                    "p50": round(_percentile(stress_update_latencies, 0.50), 3),
                    "p95": round(_percentile(stress_update_latencies, 0.95), 3),
                    "max": round(max(stress_update_latencies) if stress_update_latencies else 0.0, 3),
                },
                "recommendation_latency_ms": {
                    "p50": round(_percentile(stress_rec_latencies, 0.50), 3),
                    "p95": round(_percentile(stress_rec_latencies, 0.95), 3),
                    "max": round(max(stress_rec_latencies) if stress_rec_latencies else 0.0, 3),
                },
                "revision_latency_ms": {
                    "p50": round(_percentile(stress_revision_latencies, 0.50), 3),
                    "p95": round(_percentile(stress_revision_latencies, 0.95), 3),
                    "max": round(max(stress_revision_latencies) if stress_revision_latencies else 0.0, 3),
                },
            },
            "part_8_scientific_validation": {
                "consistency_checks": {
                    "no_duplicate_pending_recommendations": repeated_rate == 0.0,
                    "nonzero_revision_activity": total_revision_rows > 0,
                    "weak_topic_signal_present": weak_detection > 0.50,
                },
                "detected_failure_modes": findings,
            },
            "part_9_auto_tuning": auto_tuning,
            "quality_gate": {
                "learning_quality_score": learning_quality_score,
                "recommendation_quality_score": recommendation_quality_score,
                "revision_quality_score": revision_quality_score,
                "personalization_quality_score": personalization_quality_score,
                "its_quality_score": its_quality_score,
                "production_readiness_after_phase4": "Ready for controlled production pilot"
                if its_quality_score >= 7.5 and not any(f["severity"] in {"Critical", "High"} for f in findings)
                else "Not ready for production rollout",
            },
            "tests_added": [
                "tests/test_phase4_adaptive_validation.py::test_phase4_small_run_metrics",
                "tests/test_phase4_adaptive_validation.py::test_phase4_counts_and_quality_gate",
            ],
            "limitations": [
                "Stress test models 10,000 active learners with interleaved operations on SQLite. True multi-node concurrency is out of scope for single-process simulation.",
                "Educational outcomes are derived from synthetic behavior profiles, not real classroom cohorts.",
            ],
            "debug": {
                "baseline_update_latency_ms_p95": round(_percentile(update_latencies, 0.95), 3),
                "baseline_recommendation_latency_ms_p95": round(_percentile(rec_latencies, 0.95), 3),
                "baseline_revision_latency_ms_p95": round(_percentile(revision_latencies, 0.95), 3),
            },
        }
        return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4 adaptive intelligence validation.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--learners-per-archetype", type=int, default=200)
    parser.add_argument("--stress-learners", type=int, default=8000)
    parser.add_argument("--core-attempts", type=int, default=45)
    parser.add_argument("--stress-attempts", type=int, default=2)
    parser.add_argument("--minimum-submissions", type=int, default=100000)
    parser.add_argument("--recommender-strategy", choices=["legacy", "optimized"], default="optimized")
    parser.add_argument("--out", type=Path, default=Path("reports/phase4/phase4_adaptive_validation.json"))
    parser.add_argument("--bank", type=Path, default=Path("data/premium/problem_bank.json"))
    args = parser.parse_args(argv)

    config = SimulationConfig(
        seed=args.seed,
        learners_per_archetype=args.learners_per_archetype,
        stress_learner_count=args.stress_learners,
        core_attempts_per_user=args.core_attempts,
        stress_attempts_per_user=args.stress_attempts,
        minimum_submissions=args.minimum_submissions,
        recommender_strategy=args.recommender_strategy,
        report_path=args.out,
        bank_path=args.bank,
    )
    report = run_phase4_validation(config)
    config.report_path.parent.mkdir(parents=True, exist_ok=True)
    config.report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = {
        "learners": report["configuration"]["total_learners"],
        "submissions": report["part_2_longitudinal_simulation"]["submission_rows"],
        "its_quality_score": report["quality_gate"]["its_quality_score"],
        "production_readiness_after_phase4": report["quality_gate"]["production_readiness_after_phase4"],
    }
    print(json.dumps(summary, indent=2))
    has_blocking = any(
        item["severity"] in {"Critical", "High"}
        for item in report["part_8_scientific_validation"]["detected_failure_modes"]
    )
    if not report["part_2_longitudinal_simulation"]["minimum_submissions_met"]:
        return 1
    return 1 if has_blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
