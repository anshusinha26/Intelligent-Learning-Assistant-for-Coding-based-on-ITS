"""
Data models using Pydantic
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

# User Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    target_level: Optional[str] = "medium"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    target_level: Optional[str]
    created_at: datetime

# Problem Models
class ProblemCreate(BaseModel):
    problem_id: str
    title: str
    topic: str
    pattern: Optional[str] = None
    difficulty: str
    tags: Optional[str] = None
    description: Optional[str] = None

class Problem(BaseModel):
    problem_id: str
    title: str
    topic: str
    pattern: Optional[str]
    difficulty: str
    tags: Optional[str]
    description: Optional[str]

# Attempt Models
class AttemptCreate(BaseModel):
    problem_id: str
    verdict: str  # Accepted, Wrong Answer, Time Limit Exceeded, etc.
    time_taken: Optional[int] = None  # in seconds
    error_type: Optional[str] = None  # off-by-one, edge-case, logic-error, etc.

class Attempt(BaseModel):
    attempt_id: int
    user_id: int
    problem_id: str
    verdict: str
    time_taken: Optional[int]
    error_type: Optional[str]
    attempted_at: datetime

# Learner Metrics Models
class LearnerMetric(BaseModel):
    metric_id: int
    user_id: int
    topic: Optional[str]
    pattern: Optional[str]
    mastery_score: float
    error_frequency: float
    attempts_count: int
    success_count: int
    updated_at: datetime

# Recommendation Models
class Recommendation(BaseModel):
    rec_id: int
    user_id: int
    problem_id: str
    score: float
    reason: str
    status: str
    created_at: datetime
    problem_title: Optional[str] = None
    problem_difficulty: Optional[str] = None
    problem_topic: Optional[str] = None

class RecommendationResponse(BaseModel):
    recommendations: List[Recommendation]
    total_count: int

# Revision Schedule Models
class RevisionTask(BaseModel):
    schedule_id: int
    user_id: int
    problem_id: str
    next_review_date: date
    interval_days: int
    status: str
    problem_title: Optional[str] = None

# Dashboard Models
class WeaknessSummary(BaseModel):
    topic: str
    mastery_score: float
    error_frequency: float
    attempts_count: int
    success_rate: float

class DashboardStats(BaseModel):
    total_problems_attempted: int
    total_problems_solved: int
    current_streak: int
    success_rate: float
    top_weaknesses: List[WeaknessSummary]
    recent_attempts: List[Attempt]

# Token Model
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str