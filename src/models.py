"""
Data models using Pydantic
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
import re


ALLOWED_ATTEMPT_VERDICTS = {
    "Accepted",
    "Wrong Answer",
    "Time Limit Exceeded",
    "Runtime Error",
    "Manual Review",
    "Compilation Error",
}

SCRIPT_TAG_RE = re.compile(r"<\s*script\b", re.IGNORECASE)


# User Models
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    target_level: Optional[str] = "medium"


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class User(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    target_level: Optional[str]
    email_verified: bool = False
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    otp_sent: bool
    dev_otp: Optional[str] = None


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=10)
    purpose: str = "password_reset"

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        allowed = {"password_reset", "email_verification"}
        purpose = value.strip().lower()
        if purpose not in allowed:
            raise ValueError("Invalid purpose")
        return purpose


class VerifyOtpResponse(BaseModel):
    message: str
    purpose: str
    verified: bool
    reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(min_length=24, max_length=2048)
    new_password: str = Field(min_length=6, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class EmailVerificationVerifyRequest(BaseModel):
    otp: str = Field(min_length=4, max_length=10)


class BasicMessageResponse(BaseModel):
    message: str


# Problem Models
class ProblemCreate(BaseModel):
    problem_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=300)
    topic: str = Field(min_length=1, max_length=120)
    pattern: Optional[str] = None
    difficulty: str = Field(min_length=1, max_length=32)
    tags: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[str] = None
    examples: Optional[str] = None
    source_url: Optional[str] = None
    function_name: Optional[str] = "solve"
    starter_code: Optional[str] = None
    test_cases: Optional[str] = None


class Problem(BaseModel):
    problem_id: str
    title: str
    topic: str
    pattern: Optional[str]
    difficulty: str
    tags: Optional[str]
    description: Optional[str]
    constraints: Optional[str] = None
    examples: Optional[str] = None
    source_url: Optional[str] = None
    function_name: Optional[str] = "solve"
    starter_code: Optional[str] = None
    test_cases: Optional[str] = None


# Attempt Models
class AttemptCreate(BaseModel):
    problem_id: str = Field(min_length=1, max_length=120)
    verdict: str  # Accepted, Wrong Answer, Time Limit Exceeded, etc.
    time_taken: Optional[int] = None  # in seconds
    error_type: Optional[str] = None  # off-by-one, edge-case, logic-error, etc.

    @field_validator("verdict")
    @classmethod
    def validate_verdict(cls, value: str) -> str:
        verdict = value.strip()
        if verdict not in ALLOWED_ATTEMPT_VERDICTS:
            allowed = ", ".join(sorted(ALLOWED_ATTEMPT_VERDICTS))
            raise ValueError(f"Invalid verdict. Allowed values: {allowed}")
        return verdict


class Attempt(BaseModel):
    attempt_id: int
    user_id: int
    problem_id: str
    verdict: str
    time_taken: Optional[int]
    error_type: Optional[str]
    attempted_at: datetime


# Submission Models
class CodeSubmissionCreate(BaseModel):
    problem_id: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=50000)
    language: str = "python"

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        language = value.strip().lower()
        allowed = {"python", "py"}
        if language not in allowed:
            raise ValueError("Only Python is supported")
        return language


class CodeSubmission(BaseModel):
    submission_id: int
    user_id: int
    problem_id: str
    language: str
    code: str
    verdict: str
    runtime_ms: Optional[int]
    output: Optional[str]
    submitted_at: datetime


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


# RAG Models
class RAGQueryCreate(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    problem_id: Optional[str] = None
    thread_id: Optional[str] = None
    hint_level: Optional[int] = Field(default=None, ge=1, le=3)
    want_full_solution: bool = False

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        question = value.strip()
        if SCRIPT_TAG_RE.search(question):
            raise ValueError("Script tags are not allowed")
        return question


class RAGQueryResponse(BaseModel):
    answer: str
    source: str
    rag_available: bool
    thread_id: str
    hint_level: Optional[int] = None
    pedagogical_mode: Optional[str] = None
    code_included: bool = False
    error: Optional[str] = None


# Token Model
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user_id: int
    name: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    problem_id: Optional[str] = None
    pinned: bool = False

    @field_validator("title", "content")
    @classmethod
    def validate_note_text(cls, value: str) -> str:
        text = value.strip()
        if SCRIPT_TAG_RE.search(text):
            raise ValueError("Script tags are not allowed")
        return text


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    pinned: Optional[bool] = None
    problem_id: Optional[str] = None

    @field_validator("title", "content")
    @classmethod
    def validate_note_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        text = value.strip()
        if SCRIPT_TAG_RE.search(text):
            raise ValueError("Script tags are not allowed")
        return text


class Note(BaseModel):
    note_id: int
    user_id: int
    problem_id: Optional[str]
    title: str
    content: str
    pinned: bool
    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    notes: List[Note]
    count: int


class BookmarkCreate(BaseModel):
    problem_id: str = Field(min_length=1, max_length=100)


class Bookmark(BaseModel):
    bookmark_id: int
    user_id: int
    problem_id: str
    created_at: datetime
    title: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None


class BookmarkListResponse(BaseModel):
    bookmarks: List[Bookmark]
    count: int


class UserSettings(BaseModel):
    user_id: int
    theme: str = "light"
    editor_language: str = "python"
    email_notifications: bool = True
    ai_assistant_enabled: bool = True
    daily_goal: int = 2
    updated_at: datetime


class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    editor_language: Optional[str] = None
    email_notifications: Optional[bool] = None
    ai_assistant_enabled: Optional[bool] = None
    daily_goal: Optional[int] = Field(default=None, ge=1, le=50)
