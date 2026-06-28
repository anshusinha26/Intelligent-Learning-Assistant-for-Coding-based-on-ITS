"""
Recommendation Module
Generates personalized problem recommendations based on learner profile
Uses hybrid approach: weakness-targeting + progression + exploration
"""

from typing import List, Dict, Tuple, Set, Optional
from datetime import datetime
import os

from src.database import Database
from src.problem_bank import PREMIUM_DATASET_TIER, active_problem_clause


class RecommendationEngine:
    def __init__(self, db: Database, strategy: Optional[str] = None):
        self.db = db
        selected = (strategy or os.getenv("RECOMMENDER_STRATEGY", "optimized") or "optimized").strip().lower()
        self.strategy = selected if selected in {"legacy", "optimized"} else "optimized"

    def sync_recommendation_state(self, user_id: int, cursor=None) -> None:
        """Keep pending recommendation state aligned with solved problems."""
        own_connection = cursor is None
        conn = self.db.get_connection() if own_connection else None
        if own_connection:
            cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE recommendations
            SET status = 'completed'
            WHERE user_id = ?
              AND status = 'pending'
              AND problem_id IN (
                    SELECT DISTINCT a.problem_id
                    FROM attempts a
                    JOIN problems p ON p.problem_id = a.problem_id
                    WHERE a.user_id = ?
                      AND a.verdict = 'Accepted'
                      AND p.dataset_tier = ?
                      AND p.is_active = 1
              )
        """,
            (user_id, user_id, PREMIUM_DATASET_TIER),
        )
        cursor.execute(
            """
            DELETE FROM recommendations
            WHERE user_id = ?
              AND status = 'pending'
              AND problem_id IN (
                    SELECT problem_id
                    FROM problems
                    WHERE dataset_tier != ? OR is_active != 1
              )
        """,
            (user_id, PREMIUM_DATASET_TIER),
        )
        if own_connection:
            conn.commit()
            conn.close()

    def generate_recommendations(
        self,
        user_id: int,
        top_k: int = 5,
        refresh_pending: bool = True,
    ) -> List[Dict]:
        """
        Generate top-K personalized problem recommendations.

        Legacy strategy:
        - excludes any attempted problem

        Optimized strategy:
        - excludes solved problems only
        - boosts unsolved retry/recovery candidates
        - adds novelty and stronger progression scoring
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        self.sync_recommendation_state(user_id, cursor=cursor)

        cursor.execute("SELECT target_level FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        target_level = user_row["target_level"] if user_row else "medium"

        cursor.execute(
            """
            SELECT
                COALESCE(topic, pattern) as area,
                mastery_score,
                error_frequency,
                attempts_count
            FROM learner_metrics
            WHERE user_id = ?
            ORDER BY mastery_score ASC
            LIMIT 10
        """,
            (user_id,),
        )
        weak_areas = {
            row["area"]: (
                row["mastery_score"],
                row["error_frequency"],
                row["attempts_count"],
            )
            for row in cursor.fetchall()
        }

        cursor.execute(
            """
            SELECT
                a.problem_id,
                COUNT(*) AS attempts,
                SUM(CASE WHEN a.verdict = 'Accepted' THEN 1 ELSE 0 END) AS accepts,
                SUM(CASE WHEN a.verdict != 'Accepted' THEN 1 ELSE 0 END) AS fails,
                MAX(a.attempted_at) AS last_attempt
            FROM attempts a
            JOIN problems p ON p.problem_id = a.problem_id
            WHERE a.user_id = ?
              AND p.dataset_tier = ?
              AND p.is_active = 1
            GROUP BY a.problem_id
        """,
            (user_id, PREMIUM_DATASET_TIER),
        )
        attempt_rows = cursor.fetchall()
        attempt_stats = {
            row["problem_id"]: {
                "attempts": int(row["attempts"] or 0),
                "accepts": int(row["accepts"] or 0),
                "fails": int(row["fails"] or 0),
                "last_attempt": row["last_attempt"],
            }
            for row in attempt_rows
        }
        attempted_problems = set(attempt_stats.keys())
        solved_problems = {pid for pid, stats in attempt_stats.items() if int(stats.get("accepts", 0)) > 0}

        relationship_signals = self._build_relationship_signals(cursor, solved_problems)

        popularity_map: Dict[str, int] = {}
        max_popularity = 1
        if self.strategy == "optimized":
            cursor.execute(
                """
                SELECT problem_id, COUNT(*) AS popularity
                FROM attempts
                GROUP BY problem_id
            """
            )
            popularity_map = {row["problem_id"]: int(row["popularity"] or 0) for row in cursor.fetchall()}
            if popularity_map:
                max_popularity = max(popularity_map.values()) or 1

        cursor.execute(
            f"""
            SELECT problem_id, title, topic, pattern, difficulty, tags
            FROM problems
            WHERE {active_problem_clause()}
        """
        )
        all_problems = cursor.fetchall()

        scored_problems = []
        for problem in all_problems:
            pid = problem["problem_id"]
            if pid in solved_problems:
                continue
            if pid in attempted_problems:
                continue

            score, reason = self._score_problem(
                problem,
                weak_areas,
                target_level,
                relationship_signals.get(pid, []),
                attempt_stats=attempt_stats.get(pid),
                popularity=popularity_map.get(pid, 0),
                max_popularity=max_popularity,
            )

            scored_problems.append(
                {
                    "problem_id": pid,
                    "title": problem["title"],
                    "topic": problem["topic"],
                    "pattern": problem["pattern"],
                    "difficulty": problem["difficulty"],
                    "score": score,
                    "reason": reason,
                }
            )

        scored_problems.sort(key=lambda x: x["score"], reverse=True)
        top_recommendations: List[Dict] = []
        topic_counts: Dict[str, int] = {}
        selected_ids = set()

        for candidate in scored_problems:
            topic = candidate["topic"]
            cap = self._topic_recommendation_cap(topic, weak_areas, top_k)
            if topic_counts.get(topic, 0) >= cap:
                continue
            top_recommendations.append(candidate)
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            selected_ids.add(candidate["problem_id"])
            if len(top_recommendations) >= top_k:
                break

        if len(top_recommendations) < top_k:
            for candidate in scored_problems:
                if candidate["problem_id"] in selected_ids:
                    continue
                top_recommendations.append(candidate)
                if len(top_recommendations) >= top_k:
                    break

        if refresh_pending:
            top_ids = {rec["problem_id"] for rec in top_recommendations}
            if top_ids:
                placeholders = ",".join(["?"] * len(top_ids))
                params = [user_id, *top_ids]
                cursor.execute(
                    f"""
                    DELETE FROM recommendations
                    WHERE user_id = ?
                      AND status = 'pending'
                      AND problem_id NOT IN ({placeholders})
                """,
                    params,
                )
            else:
                cursor.execute(
                    """
                    DELETE FROM recommendations
                    WHERE user_id = ? AND status = 'pending'
                """,
                    (user_id,),
                )

        timestamp = datetime.now()
        for rec in top_recommendations:
            cursor.execute(
                """
                INSERT INTO recommendations
                (user_id, problem_id, score, reason, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                ON CONFLICT(user_id, problem_id, status)
                DO UPDATE SET
                    score = excluded.score,
                    reason = excluded.reason,
                    created_at = excluded.created_at
            """,
                (user_id, rec["problem_id"], rec["score"], rec["reason"], timestamp),
            )

        conn.commit()
        conn.close()
        return top_recommendations

    @staticmethod
    def _topic_recommendation_cap(
        topic: str,
        weak_areas: Dict[str, Tuple[float, float, int]],
        top_k: int,
    ) -> int:
        area = weak_areas.get(topic)
        if not area:
            return max(2, top_k // 2)
        mastery, error_freq, _ = area
        if mastery < 0.5 or error_freq >= 0.5:
            return top_k
        if mastery < 0.65:
            return max(2, top_k // 3)
        return max(1, top_k // 4)

    def _score_problem(
        self,
        problem: dict,
        weak_areas: Dict[str, Tuple[float, float, int]],
        target_level: str,
        relationship_edges: Optional[List[Dict[str, object]]] = None,
        attempt_stats: Optional[Dict[str, object]] = None,
        popularity: int = 0,
        max_popularity: int = 1,
    ) -> Tuple[float, str]:
        score = 0.0
        reasons = []

        topic = problem["topic"]
        pattern = problem["pattern"]
        difficulty = problem["difficulty"]

        if topic in weak_areas:
            mastery, error_freq, attempts_count = weak_areas[topic]
            weakness_score = (1 - mastery) * 30 + error_freq * 20
            if mastery >= 0.6 and error_freq <= 0.4:
                weakness_score *= 0.2
            elif mastery >= 0.5:
                weakness_score *= 0.5
            if attempts_count >= 10:
                weakness_score *= 0.8
            score += weakness_score
            reasons.append(f"Weak in {topic} (mastery: {mastery:.1%})")
        else:
            score += 8
            reasons.append(f"Explore {topic}")

        if pattern and pattern in weak_areas:
            mastery, error_freq, attempts_count = weak_areas[pattern]
            pattern_score = (1 - mastery) * 20 + error_freq * 10
            if mastery >= 0.6 and error_freq <= 0.4:
                pattern_score *= 0.25
            if attempts_count >= 10:
                pattern_score *= 0.85
            score += pattern_score
            reasons.append(f"Practice {pattern} pattern")

        if self.strategy == "optimized":
            difficulty_map = {
                "Easy": {"easy": 24, "medium": 6, "hard": -6},
                "Medium": {"easy": 10, "medium": 22, "hard": 8},
                "Hard": {"easy": -8, "medium": 12, "hard": 24},
            }
        else:
            difficulty_map = {
                "Easy": {"easy": 20, "medium": 10, "hard": 5},
                "Medium": {"easy": 5, "medium": 20, "hard": 10},
                "Hard": {"easy": 0, "medium": 10, "hard": 20},
            }

        if difficulty in difficulty_map.get(target_level.capitalize(), {}):
            diff_score = difficulty_map[target_level.capitalize()][difficulty.lower()]
            score += diff_score
            if diff_score >= 15:
                reasons.append("Matches your target level")

        if attempt_stats:
            attempts = int(attempt_stats.get("attempts", 0) or 0)
            accepts = int(attempt_stats.get("accepts", 0) or 0)
            fails = int(attempt_stats.get("fails", 0) or 0)
            last_attempt = str(attempt_stats.get("last_attempt") or "")
            if attempts > 0 and accepts == 0:
                recovery_score = 18.0 + min(12.0, fails * 2.2)
                score += recovery_score
                reasons.append("Recovery on previously unsolved problem")
                if self.strategy == "optimized":
                    score += self._recent_retry_penalty(last_attempt)
            elif attempts > 0 and self.strategy == "optimized":
                score -= min(15.0, attempts * 1.2)

        if self.strategy == "optimized":
            targeted = topic in weak_areas or (bool(pattern) and pattern in weak_areas) or bool(relationship_edges)
            novelty = 1.0 - min(1.0, float(popularity) / float(max(1, max_popularity)))
            score += novelty * (6.0 if targeted else 12.0)
            if novelty >= 0.6:
                reasons.append("Exploration candidate")

        for edge in relationship_edges or []:
            edge_type = str(edge.get("edge_type") or "")
            weight = float(edge.get("weight") or 1.0)
            if edge_type == "prerequisite":
                score += (18.0 if self.strategy == "optimized" else 14.0) * weight
                reasons.append("Prerequisite progression")
            elif edge_type == "follow_up":
                score += (16.0 if self.strategy == "optimized" else 12.0) * weight
                reasons.append("Follow-up progression")
            elif edge_type == "review":
                score += (13.0 if self.strategy == "optimized" else 10.0) * weight
                reasons.append("Revision reinforcement")
            elif edge_type == "recovery":
                score += (15.0 if self.strategy == "optimized" else 11.0) * weight
                reasons.append("Recovery track")
            elif edge_type == "alternative":
                score += 7.0 * weight
                reasons.append("Alternative path")

        if not reasons:
            reasons.append("New topic to explore")
        return score, " • ".join(reasons)

    @staticmethod
    def _recent_retry_penalty(last_attempt: str) -> float:
        if not last_attempt:
            return 0.0
        normalized = last_attempt.strip().replace(" ", "T")
        try:
            when = datetime.fromisoformat(normalized)
        except ValueError:
            return 0.0
        now = datetime.now(when.tzinfo) if when.tzinfo else datetime.now()
        days = (now - when).total_seconds() / 86400.0
        if days < 0.25:
            return -8.0
        if days < 1.0:
            return -5.0
        if days < 3.0:
            return -2.5
        if days > 14.0:
            return 2.5
        return 0.0

    def get_recommendations(self, user_id: int, status: str = "pending", limit: int = 10) -> List[Dict]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        self.sync_recommendation_state(user_id, cursor=cursor)
        cursor.execute(
            """
            SELECT
                r.rec_id,
                r.problem_id,
                r.score,
                r.reason,
                r.status,
                r.created_at,
                p.title,
                p.difficulty,
                p.topic,
                p.pattern
            FROM recommendations r
            JOIN problems p ON r.problem_id = p.problem_id
            WHERE r.user_id = ? AND r.status = ? AND p.dataset_tier = ? AND p.is_active = 1
            ORDER BY r.score DESC, r.created_at DESC
            LIMIT ?
        """,
            (user_id, status, PREMIUM_DATASET_TIER, limit),
        )
        recommendations = [
            {
                "rec_id": row["rec_id"],
                "problem_id": row["problem_id"],
                "title": row["title"],
                "difficulty": row["difficulty"],
                "topic": row["topic"],
                "pattern": row["pattern"],
                "score": row["score"],
                "reason": row["reason"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return recommendations

    def mark_recommendation_completed(self, rec_id: int, user_id: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE recommendations
            SET status = 'completed'
            WHERE rec_id = ? AND user_id = ?
        """,
            (rec_id, user_id),
        )
        if cursor.rowcount == 0:
            conn.close()
            raise ValueError("Recommendation not found")
        conn.commit()
        conn.close()

    @staticmethod
    def _build_relationship_signals(cursor, solved_problems: Set[str]) -> Dict[str, List[Dict[str, object]]]:
        if not solved_problems:
            return {}
        placeholders = ",".join(["?"] * len(solved_problems))
        cursor.execute(
            f"""
            SELECT problem_id, related_problem_id, edge_type, weight
            FROM premium_problem_relationships
            WHERE problem_id IN ({placeholders})
        """,
            list(solved_problems),
        )
        signal_map: Dict[str, List[Dict[str, object]]] = {}
        for row in cursor.fetchall():
            target = row["related_problem_id"]
            signal_map.setdefault(target, []).append(
                {
                    "from_problem_id": row["problem_id"],
                    "edge_type": row["edge_type"],
                    "weight": row["weight"] or 1.0,
                }
            )
        return signal_map
