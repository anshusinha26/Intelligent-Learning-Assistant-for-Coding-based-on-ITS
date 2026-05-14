"""
Main FastAPI Application
Implements API endpoints with Phase 3 security and reporting upgrades.
"""

from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import Optional, List
import csv
import io
import json
import os
import sys

# Allow running as `python src/main.py` and `python main.py` from inside `src/`.
if __package__ in (None, ""):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from src.database import Database
from src.models import *
from src.auth import AuthService
from src.learner_model import LearnerModel
from src.recommender import RecommendationEngine
from src.revision_scheduler import RevisionScheduler
from src.judge import JudgeService
from src.config import settings

# Initialize app
app = FastAPI(title="Intelligent Coding Assistant", version="1.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = Database()
auth_service = AuthService(db)
learner_model = LearnerModel(db)
recommender = RecommendationEngine(db)
scheduler = RevisionScheduler(db)
judge = JudgeService()


# Dependency for authentication
async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and verify user from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user


def require_admin(current_user: dict) -> None:
    """Restrict admin-only endpoints."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


# ============ Authentication Endpoints ============

@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user (FR1)."""
    try:
        result = auth_service.register_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            target_level=user_data.target_level,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user and get token (FR1)."""
    try:
        result = auth_service.login_user(
            email=credentials.email,
            password=credentials.password,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/auth/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile (FR2)."""
    return {
        "user_id": current_user["user_id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "target_level": current_user["target_level"],
        "created_at": current_user.get("created_at", datetime.now()),
    }


# ============ Problem Management Endpoints ============

@app.post("/api/problems", response_model=Problem)
async def create_problem(problem: ProblemCreate, current_user: dict = Depends(get_current_user)):
    """Create a new problem (FR3, FR13 - admin only)."""
    require_admin(current_user)

    conn = db.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO problems (
                problem_id, title, topic, pattern, difficulty, tags, description,
                constraints, examples, source_url, function_name, starter_code, test_cases
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                problem.problem_id,
                problem.title,
                problem.topic,
                problem.pattern,
                problem.difficulty,
                problem.tags,
                problem.description,
                problem.constraints,
                problem.examples,
                problem.source_url,
                problem.function_name,
                problem.starter_code,
                problem.test_cases,
            ),
        )

        conn.commit()
        return problem
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.get("/api/problems", response_model=List[Problem])
async def get_problems(
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """Get problems with optional filters (FR3)."""
    conn = db.get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM problems WHERE 1=1"
    params = []

    if topic:
        query += " AND topic = ?"
        params.append(topic)
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)
    if q:
        query += " AND (LOWER(title) LIKE ? OR LOWER(tags) LIKE ? OR LOWER(topic) LIKE ?)"
        term = f"%{q.lower()}%"
        params.extend([term, term, term])

    query += " LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    problems = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return problems


@app.get("/api/problems/{problem_id}", response_model=Problem)
async def get_problem(problem_id: str, current_user: dict = Depends(get_current_user)):
    """Get one problem with starter code and judge metadata."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM problems WHERE problem_id = ?", (problem_id,))
    problem = cursor.fetchone()
    conn.close()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    return dict(problem)


# ============ Attempt Recording Endpoints ============

@app.post("/api/attempts")
async def record_attempt(attempt: AttemptCreate, current_user: dict = Depends(get_current_user)):
    """Record a practice attempt (FR4, FR12)."""
    user_id = current_user["user_id"]

    try:
        attempt_id = learner_model.record_attempt(
            user_id=user_id,
            problem_id=attempt.problem_id,
            verdict=attempt.verdict,
            time_taken=attempt.time_taken,
            error_type=attempt.error_type,
        )

        # Update revision schedule if accepted
        if attempt.verdict == "Accepted":
            scheduler.schedule_revisions(user_id)

        return {"attempt_id": attempt_id, "message": "Attempt recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/attempts", response_model=List[Attempt])
async def get_attempts(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """Get user's attempt history."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM attempts
        WHERE user_id = ?
        ORDER BY attempted_at DESC
        LIMIT ?
    """,
        (user_id, limit),
    )

    attempts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return attempts


# ============ Code Submission Endpoints ============

@app.post("/api/submissions")
async def submit_code(
    submission: CodeSubmissionCreate,
    current_user: dict = Depends(get_current_user),
):
    """Run Python code against configured tests and record the result."""
    user_id = current_user["user_id"]
    language = submission.language.lower()
    if language not in ("python", "py"):
        raise HTTPException(status_code=400, detail="Only Python submissions are supported")

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM problems WHERE problem_id = ?", (submission.problem_id,))
    problem = cursor.fetchone()
    conn.close()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    result = judge.run_python(
        code=submission.code,
        function_name=problem["function_name"] or "solve",
        test_cases_json=problem["test_cases"],
    )
    verdict = result["verdict"]
    runtime_ms = result["runtime_ms"]
    output_json = json.dumps(result["output"])

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO submissions (user_id, problem_id, language, code, verdict, runtime_ms, output)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (user_id, submission.problem_id, "python", submission.code, verdict, runtime_ms, output_json),
    )
    submission_id = cursor.lastrowid
    conn.commit()
    conn.close()

    attempt_id = None
    if verdict != "Manual Review":
        attempt_id = learner_model.record_attempt(
            user_id=user_id,
            problem_id=submission.problem_id,
            verdict=verdict,
            time_taken=runtime_ms,
            error_type=judge.summarize_error_type(verdict),
        )
        if verdict == "Accepted":
            scheduler.schedule_revisions(user_id)

    return {
        "submission_id": submission_id,
        "attempt_id": attempt_id,
        "verdict": verdict,
        "runtime_ms": runtime_ms,
        "output": result["output"],
    }


@app.get("/api/submissions")
async def get_submissions(
    problem_id: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """Get recent code submissions for the current user."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()

    query = """
        SELECT s.submission_id, s.problem_id, p.title, s.language, s.verdict,
               s.runtime_ms, s.output, s.submitted_at
        FROM submissions s
        JOIN problems p ON s.problem_id = p.problem_id
        WHERE s.user_id = ?
    """
    params = [user_id]
    if problem_id:
        query += " AND s.problem_id = ?"
        params.append(problem_id)

    query += " ORDER BY s.submitted_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    submissions = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"submissions": submissions, "count": len(submissions)}


# ============ Recommendations Endpoints ============

@app.post("/api/recommendations/generate")
async def generate_recommendations(
    top_k: int = 5,
    current_user: dict = Depends(get_current_user),
):
    """Generate new personalized recommendations (FR7, FR8)."""
    user_id = current_user["user_id"]

    try:
        recommendations = recommender.generate_recommendations(user_id, top_k)
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "message": "Recommendations generated successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations")
async def get_recommendations(
    status: str = "pending",
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """Get existing recommendations (FR7)."""
    user_id = current_user["user_id"]
    recommendations = recommender.get_recommendations(user_id, status, limit)

    return {
        "recommendations": recommendations,
        "count": len(recommendations),
    }


@app.post("/api/recommendations/{rec_id}/complete")
async def complete_recommendation(rec_id: int, current_user: dict = Depends(get_current_user)):
    """Mark recommendation as completed (FR11)."""
    user_id = current_user["user_id"]
    recommender.mark_recommendation_completed(rec_id, user_id)
    return {"message": "Recommendation marked as completed"}


# ============ Learner Analytics Endpoints ============

@app.get("/api/analytics/weaknesses")
async def get_weaknesses(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
):
    """Get user's top weaknesses (FR5, FR6)."""
    user_id = current_user["user_id"]
    weaknesses = learner_model.get_weakness_summary(user_id, limit)
    return {"weaknesses": weaknesses}


@app.get("/api/analytics/errors")
async def get_error_patterns(current_user: dict = Depends(get_current_user)):
    """Get recurring error patterns (FR6)."""
    user_id = current_user["user_id"]
    errors = learner_model.get_error_patterns(user_id)
    return {"error_patterns": errors}


@app.get("/api/analytics/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get complete dashboard statistics (FR10)."""
    user_id = current_user["user_id"]

    # Get overall stats
    stats = learner_model.get_user_stats(user_id)

    # Get weaknesses
    weaknesses = learner_model.get_weakness_summary(user_id, 5)

    # Get recent attempts
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM attempts
        WHERE user_id = ?
        ORDER BY attempted_at DESC
        LIMIT 10
    """,
        (user_id,),
    )
    recent_attempts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "total_problems_attempted": stats["total_problems_attempted"],
        "total_problems_solved": stats["total_problems_solved"],
        "current_streak": stats["current_streak"],
        "success_rate": stats["success_rate"],
        "top_weaknesses": weaknesses,
        "recent_attempts": recent_attempts,
    }


@app.get("/api/analytics/export")
async def export_attempts_csv(current_user: dict = Depends(get_current_user)):
    """Export user attempts as CSV (FR14)."""
    user_id = current_user["user_id"]

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            a.attempt_id,
            a.problem_id,
            p.title,
            p.topic,
            p.pattern,
            p.difficulty,
            a.verdict,
            a.time_taken,
            a.error_type,
            a.attempted_at
        FROM attempts a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.user_id = ?
        ORDER BY a.attempted_at DESC
    """,
        (user_id,),
    )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    fieldnames = [
        "attempt_id",
        "problem_id",
        "title",
        "topic",
        "pattern",
        "difficulty",
        "verdict",
        "time_taken",
        "error_type",
        "attempted_at",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    filename = f"attempts_user_{user_id}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ============ Revision Endpoints ============

@app.get("/api/revisions/due")
async def get_due_revisions(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
):
    """Get problems due for revision (FR9)."""
    user_id = current_user["user_id"]
    revisions = scheduler.get_due_revisions(user_id, limit)
    stats = scheduler.get_revision_stats(user_id)

    return {
        "revisions": revisions,
        "stats": stats,
    }


@app.post("/api/revisions/{schedule_id}/complete")
async def complete_revision(schedule_id: int, current_user: dict = Depends(get_current_user)):
    """Mark revision as completed (FR9)."""
    user_id = current_user["user_id"]
    scheduler.mark_revision_completed(schedule_id, user_id)
    return {"message": "Revision completed, next review scheduled"}


# ============ Health Check ============

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Intelligent Coding Assistant API"}


@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon response to avoid 404 noise in logs."""
    return Response(status_code=204)


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": "1.1.0",
        "database": "connected",
        "cors_origins": settings.cors_origins,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
