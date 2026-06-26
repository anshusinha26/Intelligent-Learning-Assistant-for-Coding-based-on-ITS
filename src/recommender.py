"""
Recommendation Module
Generates personalized problem recommendations based on learner profile
Uses hybrid approach: content-based + weakness-targeting
"""

from typing import List, Dict, Tuple
from datetime import datetime
from src.database import Database

class RecommendationEngine:
    def __init__(self, db: Database):
        self.db = db
    
    def sync_recommendation_state(self, user_id: int) -> None:
        """Keep pending recommendation state aligned with solved problems."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE recommendations
            SET status = 'completed'
            WHERE user_id = ?
              AND status = 'pending'
              AND problem_id IN (
                    SELECT DISTINCT problem_id
                    FROM attempts
                    WHERE user_id = ? AND verdict = 'Accepted'
              )
        """,
            (user_id, user_id),
        )
        conn.commit()
        conn.close()

    def generate_recommendations(
        self,
        user_id: int,
        top_k: int = 5,
        refresh_pending: bool = True,
    ) -> List[Dict]:
        """
        Generate top-K personalized problem recommendations
        
        Scoring strategy:
        1. Identify weak topics/patterns (low mastery)
        2. Find problems in those areas
        3. Filter out already attempted problems
        4. Rank by difficulty progression and weakness targeting
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        self.sync_recommendation_state(user_id)

        # Get user's target level and metrics
        cursor.execute("SELECT target_level FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        target_level = user_row['target_level'] if user_row else 'medium'
        
        # Get weak topics and patterns
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
        
        # Get attempted problems
        cursor.execute("""
            SELECT DISTINCT problem_id FROM attempts WHERE user_id = ?
        """, (user_id,))
        
        attempted_problems = {row['problem_id'] for row in cursor.fetchall()}
        
        # Get candidate problems (not yet attempted)
        cursor.execute("""
            SELECT problem_id, title, topic, pattern, difficulty, tags
            FROM problems
        """)
        
        all_problems = cursor.fetchall()
        
        # Score each problem
        scored_problems = []
        
        for problem in all_problems:
            pid = problem['problem_id']
            
            # Skip if already attempted
            if pid in attempted_problems:
                continue
            
            score, reason = self._score_problem(
                problem, weak_areas, target_level
            )
            
            scored_problems.append({
                'problem_id': pid,
                'title': problem['title'],
                'topic': problem['topic'],
                'pattern': problem['pattern'],
                'difficulty': problem['difficulty'],
                'score': score,
                'reason': reason
            })
        
        # Sort by score and get top-K
        scored_problems.sort(key=lambda x: x['score'], reverse=True)
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

        # Save recommendations to database (upsert by state)
        timestamp = datetime.now()
        for rec in top_recommendations:
            cursor.execute("""
                INSERT INTO recommendations
                (user_id, problem_id, score, reason, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                ON CONFLICT(user_id, problem_id, status)
                DO UPDATE SET
                    score = excluded.score,
                    reason = excluded.reason,
                    created_at = excluded.created_at
            """, (user_id, rec['problem_id'], rec['score'], rec['reason'], timestamp))
        
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
    
    def _score_problem(self, problem: dict, weak_areas: Dict[str, Tuple[float, float, int]], 
                      target_level: str) -> Tuple[float, str]:
        """
        Score a single problem for recommendation
        
        Scoring factors:
        - Weakness targeting: higher score if problem targets weak topics/patterns
        - Difficulty match: prefer problems matching target difficulty
        - Error pattern relevance: prefer problems that can help fix recurring errors
        """
        score = 0.0
        reasons = []
        
        topic = problem['topic']
        pattern = problem['pattern']
        difficulty = problem['difficulty']
        
        # Factor 1: Topic weakness targeting (0-50 points)
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
        
        # Factor 2: Pattern weakness targeting (0-30 points)
        if pattern and pattern in weak_areas:
            mastery, error_freq, attempts_count = weak_areas[pattern]
            pattern_score = (1 - mastery) * 20 + error_freq * 10
            if mastery >= 0.6 and error_freq <= 0.4:
                pattern_score *= 0.25
            if attempts_count >= 10:
                pattern_score *= 0.85
            score += pattern_score
            reasons.append(f"Practice {pattern} pattern")
        
        # Factor 3: Difficulty progression (0-20 points)
        difficulty_map = {
            'Easy': {'easy': 20, 'medium': 10, 'hard': 5},
            'Medium': {'easy': 5, 'medium': 20, 'hard': 10},
            'Hard': {'easy': 0, 'medium': 10, 'hard': 20}
        }
        
        if difficulty in difficulty_map.get(target_level.capitalize(), {}):
            diff_score = difficulty_map[target_level.capitalize()][difficulty.lower()]
            score += diff_score
            if diff_score >= 15:
                reasons.append(f"Matches your target level")
        
        # Generate explanation
        if not reasons:
            reasons.append("New topic to explore")
        
        reason = " • ".join(reasons)
        
        return score, reason
    
    def get_recommendations(self, user_id: int, status: str = 'pending', limit: int = 10) -> List[Dict]:
        """Fetch existing recommendations from database"""
        self.sync_recommendation_state(user_id)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
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
            WHERE r.user_id = ? AND r.status = ?
            ORDER BY r.score DESC, r.created_at DESC
            LIMIT ?
        """, (user_id, status, limit))
        
        recommendations = []
        for row in cursor.fetchall():
            recommendations.append({
                'rec_id': row['rec_id'],
                'problem_id': row['problem_id'],
                'title': row['title'],
                'difficulty': row['difficulty'],
                'topic': row['topic'],
                'pattern': row['pattern'],
                'score': row['score'],
                'reason': row['reason'],
                'status': row['status'],
                'created_at': row['created_at']
            })
        
        conn.close()
        return recommendations
    
    def mark_recommendation_completed(self, rec_id: int, user_id: int):
        """Mark a recommendation as completed"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE recommendations 
            SET status = 'completed'
            WHERE rec_id = ? AND user_id = ?
        """, (rec_id, user_id))
        if cursor.rowcount == 0:
            conn.close()
            raise ValueError("Recommendation not found")
        conn.commit()
        conn.close()
