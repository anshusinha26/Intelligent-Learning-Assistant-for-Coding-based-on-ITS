"""
Main FastAPI Application
Implements all API endpoints per Phase 2 requirements
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Optional, List
import os

from src.database import Database
from src.models import *
from src.auth import AuthService
from src.learner_model import LearnerModel
from src.recommender import RecommendationEngine
from src.revision_scheduler import RevisionScheduler

# Initialize app
app = FastAPI(title="Intelligent Coding Assistant", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Dependency for authentication
async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and verify user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user

# ============ Authentication Endpoints ============

@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user (FR1)"""
    try:
        result = auth_service.register_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            target_level=user_data.target_level
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user and get token (FR1)"""
    try:
        result = auth_service.login_user(
            email=credentials.email,
            password=credentials.password
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/api/auth/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile (FR2)"""
    return {
        "user_id": current_user['user_id'],
        "name": current_user['name'],
        "email": current_user['email'],
        "role": current_user['role'],
        "target_level": current_user['target_level'],
        "created_at": datetime.now()
    }

# ============ Problem Management Endpoints ============

@app.post("/api/problems", response_model=Problem)
async def create_problem(problem: ProblemCreate, current_user: dict = Depends(get_current_user)):
    """Create a new problem (FR3, FR13 - admin only)"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO problems (problem_id, title, topic, pattern, difficulty, tags, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (problem.problem_id, problem.title, problem.topic, problem.pattern, 
              problem.difficulty, problem.tags, problem.description))
        
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
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get problems with optional filters (FR3)"""
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
    
    query += " LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    problems = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return problems

# ============ Attempt Recording Endpoints ============

@app.post("/api/attempts")
async def record_attempt(attempt: AttemptCreate, current_user: dict = Depends(get_current_user)):
    """Record a practice attempt (FR4, FR12)"""
    user_id = current_user['user_id']
    
    try:
        attempt_id = learner_model.record_attempt(
            user_id=user_id,
            problem_id=attempt.problem_id,
            verdict=attempt.verdict,
            time_taken=attempt.time_taken,
            error_type=attempt.error_type
        )
        
        # Update revision schedule if accepted
        if attempt.verdict == 'Accepted':
            scheduler.schedule_revisions(user_id)
        
        return {"attempt_id": attempt_id, "message": "Attempt recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/attempts", response_model=List[Attempt])
async def get_attempts(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get user's attempt history"""
    user_id = current_user['user_id']
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM attempts
        WHERE user_id = ?
        ORDER BY attempted_at DESC
        LIMIT ?
    """, (user_id, limit))
    
    attempts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return attempts

# ============ Recommendations Endpoints ============

@app.post("/api/recommendations/generate")
async def generate_recommendations(
    top_k: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """Generate new personalized recommendations (FR7, FR8)"""
    user_id = current_user['user_id']
    
    try:
        recommendations = recommender.generate_recommendations(user_id, top_k)
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "message": "Recommendations generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations")
async def get_recommendations(
    status: str = 'pending',
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get existing recommendations (FR7)"""
    user_id = current_user['user_id']
    recommendations = recommender.get_recommendations(user_id, status, limit)
    
    return {
        "recommendations": recommendations,
        "count": len(recommendations)
    }

@app.post("/api/recommendations/{rec_id}/complete")
async def complete_recommendation(rec_id: int, current_user: dict = Depends(get_current_user)):
    """Mark recommendation as completed (FR11)"""
    user_id = current_user['user_id']
    recommender.mark_recommendation_completed(rec_id, user_id)
    return {"message": "Recommendation marked as completed"}

# ============ Learner Analytics Endpoints ============

@app.get("/api/analytics/weaknesses")
async def get_weaknesses(
    limit: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """Get user's top weaknesses (FR5, FR6)"""
    user_id = current_user['user_id']
    weaknesses = learner_model.get_weakness_summary(user_id, limit)
    return {"weaknesses": weaknesses}

@app.get("/api/analytics/errors")
async def get_error_patterns(current_user: dict = Depends(get_current_user)):
    """Get recurring error patterns (FR6)"""
    user_id = current_user['user_id']
    errors = learner_model.get_error_patterns(user_id)
    return {"error_patterns": errors}

@app.get("/api/analytics/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get complete dashboard statistics (FR10)"""
    user_id = current_user['user_id']
    
    # Get overall stats
    stats = learner_model.get_user_stats(user_id)
    
    # Get weaknesses
    weaknesses = learner_model.get_weakness_summary(user_id, 5)
    
    # Get recent attempts
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM attempts
        WHERE user_id = ?
        ORDER BY attempted_at DESC
        LIMIT 10
    """, (user_id,))
    recent_attempts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "total_problems_attempted": stats['total_problems_attempted'],
        "total_problems_solved": stats['total_problems_solved'],
        "current_streak": stats['current_streak'],
        "success_rate": stats['success_rate'],
        "top_weaknesses": weaknesses,
        "recent_attempts": recent_attempts
    }

# ============ Revision Endpoints ============

@app.get("/api/revisions/due")
async def get_due_revisions(
    limit: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """Get problems due for revision (FR9)"""
    user_id = current_user['user_id']
    revisions = scheduler.get_due_revisions(user_id, limit)
    stats = scheduler.get_revision_stats(user_id)
    
    return {
        "revisions": revisions,
        "stats": stats
    }

@app.post("/api/revisions/{schedule_id}/complete")
async def complete_revision(schedule_id: int, current_user: dict = Depends(get_current_user)):
    """Mark revision as completed (FR9)"""
    user_id = current_user['user_id']
    scheduler.mark_revision_completed(schedule_id, user_id)
    return {"message": "Revision completed, next review scheduled"}

# ============ Health Check ============

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Intelligent Coding Assistant API"}

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)