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
    
    def generate_recommendations(self, user_id: int, top_k: int = 5) -> List[Dict]:
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
        
        # Get user's target level and metrics
        cursor.execute("SELECT target_level FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        target_level = user_row['target_level'] if user_row else 'medium'
        
        # Get weak topics and patterns
        cursor.execute("""
            SELECT 
                COALESCE(topic, pattern) as area,
                mastery_score,
                error_frequency
            FROM learner_metrics
            WHERE user_id = ?
            ORDER BY mastery_score ASC
            LIMIT 10
        """, (user_id,))
        
        weak_areas = {row['area']: (row['mastery_score'], row['error_frequency']) 
                     for row in cursor.fetchall()}
        
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
        top_recommendations = scored_problems[:top_k]
        
        # Save recommendations to database
        timestamp = datetime.now()
        for rec in top_recommendations:
            cursor.execute("""
                INSERT INTO recommendations 
                (user_id, problem_id, score, reason, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, rec['problem_id'], rec['score'], rec['reason'], timestamp))
        
        conn.commit()
        conn.close()
        
        return top_recommendations
    
    def _score_problem(self, problem: dict, weak_areas: Dict[str, Tuple[float, float]], 
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
            mastery, error_freq = weak_areas[topic]
            weakness_score = (1 - mastery) * 30 + error_freq * 20
            score += weakness_score
            reasons.append(f"Weak in {topic} (mastery: {mastery:.1%})")
        
        # Factor 2: Pattern weakness targeting (0-30 points)
        if pattern and pattern in weak_areas:
            mastery, error_freq = weak_areas[pattern]
            pattern_score = (1 - mastery) * 20 + error_freq * 10
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
        
        conn.commit()
        conn.close()