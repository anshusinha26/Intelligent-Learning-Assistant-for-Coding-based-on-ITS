"""
Main FastAPI Application
Implements API endpoints with Phase 3 security and reporting upgrades.
"""

from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional, List, Dict
import csv
import io
import json
import logging
import os
import sys
import time
import uuid

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
from src.rag_service import RAGService
from src.config import settings
from src.observability import (
    mark_shutdown,
    mark_startup,
    record_http_request,
    record_judge_execution,
    record_rag_query,
    record_recommendation_completion,
    record_recommendation_generation,
    record_slow_request,
    render_metrics,
)
from src.security import (
    ApiError,
    RateLimiter,
    error_response,
    get_client_ip,
    get_request_id,
    structured_log,
)
from src.problem_bank import PREMIUM_DATASET_TIER, active_problem_clause

logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO), format="%(message)s")
logger = logging.getLogger("ila-api")

APP_VERSION = "1.4.0"
app = FastAPI(title="Intelligent Coding Assistant", version=APP_VERSION)
ACTIVE_PROBLEM_FILTER = active_problem_clause()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = Database(settings.db_path)
auth_service = AuthService(db)
learner_model = LearnerModel(db)
recommender = RecommendationEngine(db)
scheduler = RevisionScheduler(db)
judge = JudgeService()
rate_limiter = RateLimiter()
rag_service = RAGService(
    enabled=settings.rag_enabled,
    mode=settings.rag_mode,
    base_url=settings.rag_base_url,
    org_id=settings.rag_org_id,
    agent_id=settings.rag_agent_id,
    service_token=settings.rag_service_token,
    allow_full_solutions=settings.rag_allow_full_solutions,
    enforce_hint_progression=settings.rag_enforce_hint_progression,
    max_question_chars=settings.max_rag_question_chars,
    max_thread_state=settings.rag_thread_state_max,
    timeout_seconds=settings.rag_timeout_seconds,
)


RATE_LIMIT_RULES = {
    ("POST", "/api/auth/login"): ("auth_login", settings.rate_limit_login_per_min),
    ("POST", "/api/auth/register"): ("auth_register", settings.rate_limit_register_per_min),
    ("POST", "/api/auth/forgot-password"): ("auth_forgot_password", settings.rate_limit_forgot_password_per_min),
    ("POST", "/api/auth/verify-otp"): ("auth_verify_otp", settings.rate_limit_otp_verify_per_min),
    ("POST", "/api/auth/email-verification/verify"): ("auth_verify_otp", settings.rate_limit_otp_verify_per_min),
    ("POST", "/api/auth/reset-password"): ("auth_reset_password", settings.rate_limit_reset_password_per_min),
    ("GET", "/api/rag/health"): ("rag_health", settings.rate_limit_rag_per_min),
    ("POST", "/api/rag/query"): ("rag_query", settings.rate_limit_rag_per_min),
    ("POST", "/api/submissions"): ("judge_submit", settings.rate_limit_judge_per_min),
}


def attach_security_headers(response: Response) -> Response:
    if not response.headers.get(settings.request_id_header):
        response.headers[settings.request_id_header] = uuid.uuid4().hex
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = settings.x_frame_options
    response.headers["Referrer-Policy"] = settings.referrer_policy
    response.headers["Content-Security-Policy"] = settings.csp_policy
    if settings.hsts_enabled:
        response.headers["Strict-Transport-Security"] = f"max-age={settings.hsts_max_age}; includeSubDomains"
    return response


def capture_request_metrics(method: str, path: str, status_code: int, elapsed_ms: int, request_id: str, client_ip: str) -> None:
    if settings.metrics_enabled:
        record_http_request(method=method, path=path, status_code=status_code, elapsed_ms=elapsed_ms)
    if elapsed_ms >= settings.slow_request_threshold_ms:
        if settings.metrics_enabled:
            record_slow_request(method=method, path=path)
        logger.warning(
            structured_log(
                "slow_request",
                request_id=request_id,
                method=method,
                path=path,
                status_code=status_code,
                elapsed_ms=elapsed_ms,
                threshold_ms=settings.slow_request_threshold_ms,
                client_ip=client_ip,
            )
        )


def _json_safe(value):
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


@app.middleware("http")
async def hardening_middleware(request: Request, call_next):
    request_id = request.headers.get(settings.request_id_header, "").strip() or uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()
    client_ip = get_client_ip(request)

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.max_request_body_bytes:
                response = error_response(
                    request,
                    status_code=413,
                    code="payload_too_large",
                    message=f"Request payload too large (max {settings.max_request_body_bytes} bytes)",
                )
                response.headers[settings.request_id_header] = request_id
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                capture_request_metrics(request.method, request.url.path, response.status_code, elapsed_ms, request_id, client_ip)
                return attach_security_headers(response)
        except ValueError:
            response = error_response(
                request,
                status_code=400,
                code="invalid_content_length",
                message="Invalid Content-Length header",
            )
            response.headers[settings.request_id_header] = request_id
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            capture_request_metrics(request.method, request.url.path, response.status_code, elapsed_ms, request_id, client_ip)
            return attach_security_headers(response)
    elif request.method in {"POST", "PUT", "PATCH"}:
        body = await request.body()
        if len(body) > settings.max_request_body_bytes:
            response = error_response(
                request,
                status_code=413,
                code="payload_too_large",
                message=f"Request payload too large (max {settings.max_request_body_bytes} bytes)",
            )
            response.headers[settings.request_id_header] = request_id
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            capture_request_metrics(request.method, request.url.path, response.status_code, elapsed_ms, request_id, client_ip)
            return attach_security_headers(response)
        request._body = body

    rule = RATE_LIMIT_RULES.get((request.method.upper(), request.url.path))
    if rule:
        scope, limit = rule
        decision = rate_limiter.check(f"{scope}:{client_ip}", limit=limit, window_seconds=60)
        if not decision.allowed:
            response = error_response(
                request,
                status_code=429,
                code="rate_limited",
                message="Too many requests. Retry later.",
                details={"retry_after_seconds": decision.retry_after_seconds, "scope": scope},
                headers={"Retry-After": str(decision.retry_after_seconds)},
            )
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(decision.retry_after_seconds)
            response.headers[settings.request_id_header] = request_id
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            capture_request_metrics(request.method, request.url.path, response.status_code, elapsed_ms, request_id, client_ip)
            return attach_security_headers(response)

    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    capture_request_metrics(request.method, request.url.path, response.status_code, elapsed_ms, request_id, client_ip)
    response.headers[settings.request_id_header] = request_id
    response = attach_security_headers(response)
    if logger.isEnabledFor(logging.INFO):
        logger.info(
            structured_log(
                "http_request",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                client_ip=client_ip,
            )
        )
    return response


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    response = error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )
    response.headers[settings.request_id_header] = get_request_id(request)
    return attach_security_headers(response)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    details = {"errors": _json_safe(exc.errors())}
    response = error_response(
        request,
        status_code=422,
        code="validation_error",
        message="Invalid request payload",
        details=details,
    )
    response.headers[settings.request_id_header] = get_request_id(request)
    return attach_security_headers(response)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = f"http_{exc.status_code}"
    message = str(exc.detail) if exc.detail else "Request failed"
    response = error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
    )
    response.headers[settings.request_id_header] = get_request_id(request)
    return attach_security_headers(response)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = f"http_{exc.status_code}"
    message = str(exc.detail) if exc.detail else "Request failed"
    response = error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
    )
    response.headers[settings.request_id_header] = get_request_id(request)
    return attach_security_headers(response)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        structured_log(
            "unhandled_exception",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )
    )
    response = error_response(
        request,
        status_code=500,
        code="internal_error",
        message="Internal server error",
    )
    response.headers[settings.request_id_header] = get_request_id(request)
    return attach_security_headers(response)


# Dependency for authentication
async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and verify user from JWT token."""
    if not authorization:
        raise ApiError(status_code=401, code="not_authenticated", message="Not authenticated")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ApiError(
                status_code=401,
                code="invalid_auth_scheme",
                message="Invalid authentication scheme",
            )
    except ValueError:
        raise ApiError(
            status_code=401,
            code="invalid_authorization_header",
            message="Invalid authorization header",
        )

    user = auth_service.get_current_user(token)
    if not user:
        raise ApiError(status_code=401, code="invalid_token", message="Invalid or expired token")

    return user


def require_admin(current_user: dict) -> None:
    """Restrict admin-only endpoints."""
    if current_user.get("role") != "admin":
        raise ApiError(status_code=403, code="admin_required", message="Admin access required")


def ensure_user_settings(user_id: int) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO user_settings (user_id)
        VALUES (?)
    """,
        (user_id,),
    )
    conn.commit()
    conn.close()


def validate_database_state() -> dict:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    existing_tables = {row["name"] for row in cursor.fetchall()}
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
    existing_indexes = {row["name"] for row in cursor.fetchall()}
    required_tables = {
        "schema_migrations",
        "users",
        "problems",
        "attempts",
        "learner_metrics",
        "recommendations",
        "revision_schedule",
        "submissions",
        "refresh_tokens",
        "revoked_tokens",
        "otp_codes",
        "notes",
        "bookmarks",
        "user_settings",
        "premium_problem_versions",
        "premium_problem_hints",
        "premium_problem_tests",
        "premium_problem_relationships",
        "premium_problem_rag_chunks",
    }
    required_indexes = {
        "idx_recommendations_unique_state",
        "idx_recommendations_user_status",
        "idx_revision_unique_pending",
        "idx_refresh_tokens_user_revoked",
        "idx_bookmarks_unique_user_problem",
        "idx_notes_user_problem",
        "idx_otp_lookup",
        "idx_problems_dataset_active",
        "idx_premium_problem_versions_unique",
        "idx_premium_problem_versions_current",
        "idx_premium_problem_hints_unique",
        "idx_premium_problem_tests_visibility",
        "idx_premium_problem_relationships_unique",
        "idx_premium_problem_rag_chunks_lookup",
    }
    missing = sorted(required_tables - existing_tables)
    if missing:
        conn.close()
        raise RuntimeError(f"Missing required tables: {', '.join(missing)}")
    missing_indexes = sorted(required_indexes - existing_indexes)
    if missing_indexes:
        conn.close()
        raise RuntimeError(f"Missing required indexes: {', '.join(missing_indexes)}")

    cursor.execute("PRAGMA foreign_key_check")
    fk_issues = cursor.fetchall()
    conn.close()
    if fk_issues:
        raise RuntimeError("Foreign key violations detected during startup validation")
    return {"tables": len(existing_tables), "required_tables": len(required_tables)}


@app.on_event("startup")
async def on_startup() -> None:
    from src.migrations import apply_pending_migrations, verify_migrations

    migration_report = apply_pending_migrations(settings.db_path)
    verify_migrations(settings.db_path)
    state = validate_database_state()
    mark_startup(settings.app_name, settings.app_env, APP_VERSION)
    logger.info(
        structured_log(
            "startup_complete",
            app_name=settings.app_name,
            env=settings.app_env,
            db_tables=state["tables"],
            migration_total=migration_report["total"],
            migration_applied=migration_report["applied"],
        )
    )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    mark_shutdown()
    logger.info(structured_log("shutdown_complete", app_name=settings.app_name, env=settings.app_env))


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


@app.post("/api/auth/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(payload: ForgotPasswordRequest):
    """Request OTP for password reset."""
    return auth_service.request_password_reset(payload.email)


@app.post("/api/auth/verify-otp", response_model=VerifyOtpResponse)
async def verify_otp(payload: VerifyOtpRequest):
    """Verify OTP for password reset/email verification."""
    try:
        return auth_service.verify_otp(
            email=payload.email,
            otp=payload.otp,
            purpose=payload.purpose,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/reset-password", response_model=BasicMessageResponse)
async def reset_password(payload: ResetPasswordRequest):
    """Reset password using OTP-verified reset token."""
    try:
        auth_service.reset_password(payload.reset_token, payload.new_password)
        return {"message": "Password reset successful. Please log in again."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/change-password", response_model=BasicMessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    """Change password for authenticated user."""
    try:
        auth_service.change_password(
            user_id=current_user["user_id"],
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/email-verification/request", response_model=ForgotPasswordResponse)
async def request_email_verification(current_user: dict = Depends(get_current_user)):
    """Generate OTP for email verification."""
    try:
        return auth_service.request_email_verification(current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/email-verification/verify", response_model=VerifyOtpResponse)
async def verify_email_otp(
    payload: EmailVerificationVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Verify authenticated user's email OTP."""
    try:
        return auth_service.verify_email_otp(current_user["user_id"], payload.otp)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(payload: RefreshTokenRequest):
    """Refresh access token using a valid refresh token."""
    try:
        return auth_service.refresh_access_token(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/auth/logout")
async def logout(
    payload: Optional[LogoutRequest] = None,
    authorization: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user),
):
    """Logout current session and revoke active tokens."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        _, token = authorization.split()
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    refresh_token = payload.refresh_token if payload else None
    auth_service.logout_user(token, current_user["user_id"], refresh_token)
    return {"message": "Logged out successfully"}


@app.get("/api/auth/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile (FR2)."""
    return {
        "user_id": current_user["user_id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "target_level": current_user["target_level"],
        "email_verified": bool(current_user.get("email_verified", False)),
        "created_at": current_user.get("created_at", datetime.now()),
    }


# ============ User Preferences Endpoints ============

@app.get("/api/settings", response_model=UserSettings)
async def get_user_settings(current_user: dict = Depends(get_current_user)):
    """Get user preferences/settings."""
    user_id = current_user["user_id"]
    ensure_user_settings(user_id)

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Settings not found")

    data = dict(row)
    data["email_notifications"] = bool(data.get("email_notifications", 1))
    data["ai_assistant_enabled"] = bool(data.get("ai_assistant_enabled", 1))
    return data


@app.put("/api/settings", response_model=UserSettings)
async def update_user_settings(
    payload: UserSettingsUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update user preferences/settings."""
    user_id = current_user["user_id"]
    ensure_user_settings(user_id)

    updates = {}
    if payload.theme is not None:
        updates["theme"] = payload.theme.strip().lower()
    if payload.editor_language is not None:
        updates["editor_language"] = payload.editor_language.strip().lower()
    if payload.email_notifications is not None:
        updates["email_notifications"] = 1 if payload.email_notifications else 0
    if payload.ai_assistant_enabled is not None:
        updates["ai_assistant_enabled"] = 1 if payload.ai_assistant_enabled else 0
    if payload.daily_goal is not None:
        updates["daily_goal"] = payload.daily_goal

    if not updates:
        raise HTTPException(status_code=400, detail="No settings fields provided")

    allowed_themes = {"light", "dark", "system"}
    if "theme" in updates and updates["theme"] not in allowed_themes:
        raise HTTPException(status_code=400, detail="theme must be one of: light, dark, system")

    updates["updated_at"] = datetime.now().isoformat(sep=" ", timespec="seconds")
    set_clause = ", ".join(f"{column} = ?" for column in updates.keys())
    params = list(updates.values()) + [user_id]

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        UPDATE user_settings
        SET {set_clause}
        WHERE user_id = ?
    """,
        params,
    )
    conn.commit()
    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    data = dict(row)
    data["email_notifications"] = bool(data.get("email_notifications", 1))
    data["ai_assistant_enabled"] = bool(data.get("ai_assistant_enabled", 1))
    return data


# ============ Notes Endpoints ============

@app.post("/api/notes", response_model=Note)
async def create_note(
    payload: NoteCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create user note."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()

    if payload.problem_id:
        cursor.execute(
            f"SELECT 1 FROM problems WHERE problem_id = ? AND {ACTIVE_PROBLEM_FILTER}",
            (payload.problem_id,),
        )
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Problem not found")

    now_sql = datetime.now().isoformat(sep=" ", timespec="seconds")
    cursor.execute(
        """
        INSERT INTO notes (user_id, problem_id, title, content, pinned, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            user_id,
            payload.problem_id,
            payload.title.strip(),
            payload.content,
            1 if payload.pinned else 0,
            now_sql,
            now_sql,
        ),
    )
    note_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM notes WHERE note_id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()
    data = dict(row)
    data["pinned"] = bool(data.get("pinned", 0))
    return data


@app.get("/api/notes", response_model=NoteListResponse)
async def list_notes(
    problem_id: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """List user notes with optional search/problem filter."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()

    query = (
        "SELECT * FROM notes WHERE user_id = ? "
        "AND (problem_id IS NULL OR EXISTS ("
        "SELECT 1 FROM problems p WHERE p.problem_id = notes.problem_id "
        "AND p.dataset_tier = 'premium' AND p.is_active = 1))"
    )
    params = [user_id]
    if problem_id:
        query += " AND problem_id = ?"
        params.append(problem_id)
    if q:
        query += " AND (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)"
        term = f"%{q.lower()}%"
        params.extend([term, term])

    query += " ORDER BY pinned DESC, updated_at DESC, note_id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    for row in rows:
        row["pinned"] = bool(row.get("pinned", 0))
    return {"notes": rows, "count": len(rows)}


@app.get("/api/notes/{note_id}", response_model=Note)
async def get_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """Fetch one user note."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM notes
        WHERE note_id = ? AND user_id = ?
          AND (
                problem_id IS NULL OR EXISTS (
                    SELECT 1 FROM problems p
                    WHERE p.problem_id = notes.problem_id
                      AND p.dataset_tier = 'premium'
                      AND p.is_active = 1
                )
          )
    """,
        (note_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Note not found")
    data = dict(row)
    data["pinned"] = bool(data.get("pinned", 0))
    return data


@app.put("/api/notes/{note_id}", response_model=Note)
async def update_note(
    note_id: int,
    payload: NoteUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update one user note."""
    user_id = current_user["user_id"]
    updates = {}
    if payload.title is not None:
        updates["title"] = payload.title.strip()
    if payload.content is not None:
        updates["content"] = payload.content
    if payload.pinned is not None:
        updates["pinned"] = 1 if payload.pinned else 0
    if payload.problem_id is not None:
        updates["problem_id"] = payload.problem_id

    if not updates:
        raise HTTPException(status_code=400, detail="No note fields provided")

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT note_id FROM notes WHERE note_id = ? AND user_id = ?", (note_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    if "problem_id" in updates and updates["problem_id"]:
        cursor.execute(
            f"SELECT 1 FROM problems WHERE problem_id = ? AND {ACTIVE_PROBLEM_FILTER}",
            (updates["problem_id"],),
        )
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Problem not found")

    updates["updated_at"] = datetime.now().isoformat(sep=" ", timespec="seconds")
    set_clause = ", ".join(f"{column} = ?" for column in updates.keys())
    params = list(updates.values()) + [note_id, user_id]
    cursor.execute(
        f"""
        UPDATE notes
        SET {set_clause}
        WHERE note_id = ? AND user_id = ?
    """,
        params,
    )
    conn.commit()
    cursor.execute(
        """
        SELECT *
        FROM notes
        WHERE note_id = ? AND user_id = ?
          AND (
                problem_id IS NULL OR EXISTS (
                    SELECT 1 FROM problems p
                    WHERE p.problem_id = notes.problem_id
                      AND p.dataset_tier = 'premium'
                      AND p.is_active = 1
                )
          )
    """,
        (note_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()
    data = dict(row)
    data["pinned"] = bool(data.get("pinned", 0))
    return data


@app.delete("/api/notes/{note_id}", response_model=BasicMessageResponse)
async def delete_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """Delete one user note."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE note_id = ? AND user_id = ?", (note_id, user_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")
    conn.commit()
    conn.close()
    return {"message": "Note deleted"}


# ============ Bookmarks Endpoints ============

@app.post("/api/bookmarks", response_model=Bookmark)
async def create_bookmark(
    payload: BookmarkCreate,
    current_user: dict = Depends(get_current_user),
):
    """Bookmark a problem for user."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT 1 FROM problems WHERE problem_id = ? AND {ACTIVE_PROBLEM_FILTER}",
        (payload.problem_id,),
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Problem not found")

    cursor.execute(
        """
        INSERT OR IGNORE INTO bookmarks (user_id, problem_id)
        VALUES (?, ?)
    """,
        (user_id, payload.problem_id),
    )
    conn.commit()
    cursor.execute(
        """
        SELECT b.bookmark_id, b.user_id, b.problem_id, b.created_at, p.title, p.topic, p.difficulty
        FROM bookmarks b
        JOIN problems p ON p.problem_id = b.problem_id
        WHERE b.user_id = ? AND b.problem_id = ? AND p.dataset_tier = ? AND p.is_active = 1
    """,
        (user_id, payload.problem_id, PREMIUM_DATASET_TIER),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row)


@app.get("/api/bookmarks", response_model=BookmarkListResponse)
async def list_bookmarks(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """List user bookmarks."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT b.bookmark_id, b.user_id, b.problem_id, b.created_at, p.title, p.topic, p.difficulty
        FROM bookmarks b
        JOIN problems p ON p.problem_id = b.problem_id
        WHERE b.user_id = ? AND p.dataset_tier = ? AND p.is_active = 1
        ORDER BY b.created_at DESC, b.bookmark_id DESC
        LIMIT ? OFFSET ?
    """,
        (user_id, PREMIUM_DATASET_TIER, limit, offset),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"bookmarks": rows, "count": len(rows)}


@app.delete("/api/bookmarks/{problem_id}", response_model=BasicMessageResponse)
async def delete_bookmark(problem_id: str, current_user: dict = Depends(get_current_user)):
    """Remove bookmarked problem."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM bookmarks WHERE user_id = ? AND problem_id = ?",
        (user_id, problem_id),
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Bookmark not found")
    conn.commit()
    conn.close()
    return {"message": "Bookmark removed"}


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
                constraints, examples, source_url, function_name, starter_code, test_cases,
                dataset_tier, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                PREMIUM_DATASET_TIER,
                1,
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
def get_problems(
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    pattern: Optional[str] = None,
    tags: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """Get problems with optional filters (FR3)."""
    conn = db.get_connection()
    cursor = conn.cursor()

    query = f"SELECT * FROM problems WHERE {ACTIVE_PROBLEM_FILTER}"
    params = []

    def parse_values(value: Optional[str]) -> List[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    topic_values = parse_values(topic)
    difficulty_values = parse_values(difficulty)
    pattern_values = parse_values(pattern)

    if topic_values:
        placeholders = ",".join(["?"] * len(topic_values))
        query += f" AND topic IN ({placeholders})"
        params.extend(topic_values)
    if difficulty_values:
        placeholders = ",".join(["?"] * len(difficulty_values))
        query += f" AND difficulty IN ({placeholders})"
        params.extend(difficulty_values)
    if pattern_values:
        placeholders = ",".join(["?"] * len(pattern_values))
        query += f" AND pattern IN ({placeholders})"
        params.extend(pattern_values)
    if tags:
        query += " AND LOWER(tags) LIKE ?"
        params.append(f"%{tags.lower()}%")
    if q:
        query += """
            AND (
                LOWER(title) LIKE ?
                OR LOWER(tags) LIKE ?
                OR LOWER(topic) LIKE ?
                OR LOWER(COALESCE(pattern, '')) LIKE ?
                OR LOWER(COALESCE(description, '')) LIKE ?
            )
        """
        term = f"%{q.lower()}%"
        params.extend([term, term, term, term, term])

    query += " LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    problems = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return problems


@app.get("/api/problems/{problem_id}", response_model=Problem)
def get_problem(problem_id: str, current_user: dict = Depends(get_current_user)):
    """Get one problem with starter code and judge metadata."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM problems WHERE problem_id = ? AND {ACTIVE_PROBLEM_FILTER}",
        (problem_id,),
    )
    problem = cursor.fetchone()
    conn.close()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    return dict(problem)


# ============ Attempt Recording Endpoints ============

@app.post("/api/attempts")
def record_attempt(attempt: AttemptCreate, current_user: dict = Depends(get_current_user)):
    """Record a practice attempt (FR4, FR12)."""
    user_id = current_user["user_id"]
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT 1 FROM problems WHERE problem_id = ? AND {ACTIVE_PROBLEM_FILTER}",
        (attempt.problem_id,),
    )
    exists = cursor.fetchone()
    conn.close()
    if not exists:
        raise HTTPException(status_code=404, detail="Problem not found")

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
        SELECT a.*
        FROM attempts a
        JOIN problems p ON p.problem_id = a.problem_id
        WHERE a.user_id = ?
          AND p.dataset_tier = ?
          AND p.is_active = 1
        ORDER BY attempted_at DESC, attempt_id DESC
        LIMIT ?
    """,
        (user_id, PREMIUM_DATASET_TIER, limit),
    )

    attempts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return attempts


# ============ Code Submission Endpoints ============

@app.post("/api/submissions")
def submit_code(
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
    cursor.execute(
        f"SELECT * FROM problems WHERE problem_id = ? AND {ACTIVE_PROBLEM_FILTER}",
        (submission.problem_id,),
    )
    problem = cursor.fetchone()
    conn.close()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    judge_started_at = time.perf_counter()
    result = judge.run_python(
        code=submission.code,
        function_name=problem["function_name"] or "solve",
        test_cases_json=problem["test_cases"],
    )
    judge_elapsed_ms = int((time.perf_counter() - judge_started_at) * 1000)
    verdict = result["verdict"]
    runtime_ms = result["runtime_ms"]
    if settings.metrics_enabled:
        record_judge_execution(verdict=verdict, runtime_ms=runtime_ms or judge_elapsed_ms)
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
        WHERE s.user_id = ? AND p.dataset_tier = ? AND p.is_active = 1
    """
    params = [user_id, PREMIUM_DATASET_TIER]
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
def generate_recommendations(
    top_k: int = 5,
    refresh: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """Generate new personalized recommendations (FR7, FR8)."""
    user_id = current_user["user_id"]

    try:
        started_at = time.perf_counter()
        recommendations = recommender.generate_recommendations(
            user_id=user_id,
            top_k=top_k,
            refresh_pending=refresh,
        )
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        if settings.metrics_enabled:
            record_recommendation_generation(count=len(recommendations), refresh=refresh)
        if logger.isEnabledFor(logging.INFO):
            logger.info(
                structured_log(
                    "recommendations_generated",
                    user_id=user_id,
                    count=len(recommendations),
                    refresh=refresh,
                    elapsed_ms=elapsed_ms,
                )
            )
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "message": "Recommendations generated successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations")
def get_recommendations(
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
    try:
        recommender.mark_recommendation_completed(rec_id, user_id)
        if settings.metrics_enabled:
            record_recommendation_completion()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Recommendation marked as completed"}


# ============ Learner Analytics Endpoints ============

@app.get("/api/analytics/weaknesses")
def get_weaknesses(
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
def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
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
        SELECT a.*
        FROM attempts a
        JOIN problems p ON p.problem_id = a.problem_id
        WHERE a.user_id = ?
          AND p.dataset_tier = ?
          AND p.is_active = 1
        ORDER BY attempted_at DESC, attempt_id DESC
        LIMIT 10
    """,
        (user_id, PREMIUM_DATASET_TIER),
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
        WHERE a.user_id = ? AND p.dataset_tier = ? AND p.is_active = 1
        ORDER BY a.attempted_at DESC
    """,
        (user_id, PREMIUM_DATASET_TIER),
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
def get_due_revisions(
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
    try:
        scheduler.mark_revision_completed(schedule_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Revision completed, next review scheduled"}


# ============ RAG Assistant Endpoints ============

@app.get("/api/rag/health")
def rag_health(current_user: dict = Depends(get_current_user)):
    """Check configured RAG availability (local or external)."""
    return rag_service.health()


@app.post("/api/rag/query", response_model=RAGQueryResponse)
def rag_query(payload: RAGQueryCreate, current_user: dict = Depends(get_current_user)):
    """Ask ITS-aware RAG assistant with user-scoped learning context."""
    user_id = current_user["user_id"]
    thread_id = payload.thread_id or f"its_{user_id}_{payload.problem_id or 'general'}"

    weaknesses = learner_model.get_weakness_summary(user_id, 3)
    error_patterns = learner_model.get_error_patterns(user_id)
    learner_stats = learner_model.get_user_stats(user_id)
    revision_stats = scheduler.get_revision_stats(user_id)

    recent_attempts: List[Dict[str, object]] = []
    problem_attempt_context: Dict[str, object] = {"attempts": 0, "accepted": 0, "last_verdict": None}

    problem_context = None
    rag_chunks: List[Dict[str, str]] = []
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.problem_id, a.verdict, a.error_type, a.attempted_at
        FROM attempts a
        JOIN problems p ON p.problem_id = a.problem_id
        WHERE a.user_id = ?
          AND p.dataset_tier = ?
          AND p.is_active = 1
        ORDER BY a.attempted_at DESC, a.attempt_id DESC
        LIMIT 5
    """,
        (user_id, PREMIUM_DATASET_TIER),
    )
    recent_attempts = [dict(row) for row in cursor.fetchall()]

    if payload.problem_id:
        cursor.execute(
            """
            SELECT
                p.problem_id,
                p.title,
                p.topic,
                p.pattern,
                p.difficulty,
                p.time_complexity,
                p.space_complexity,
                v.reference_solution,
                (
                    SELECT GROUP_CONCAT(related_problem_id, ',')
                    FROM premium_problem_relationships r
                    WHERE r.problem_id = p.problem_id
                    ORDER BY r.weight DESC, r.related_problem_id ASC
                    LIMIT 5
                ) AS related_ids
            FROM problems p
            LEFT JOIN premium_problem_versions v
              ON v.problem_id = p.problem_id AND v.is_current = 1
            WHERE p.problem_id = ?
              AND p.dataset_tier = ?
              AND p.is_active = 1
            LIMIT 1
        """,
            (payload.problem_id, PREMIUM_DATASET_TIER),
        )
        row = cursor.fetchone()
        cursor.execute(
            """
            SELECT
                COUNT(*) AS attempts,
                SUM(CASE WHEN verdict = 'Accepted' THEN 1 ELSE 0 END) AS accepted,
                (
                    SELECT a2.verdict
                    FROM attempts a2
                    WHERE a2.user_id = ? AND a2.problem_id = ?
                    ORDER BY a2.attempted_at DESC, a2.attempt_id DESC
                    LIMIT 1
                ) AS last_verdict
            FROM attempts a
            WHERE a.user_id = ? AND a.problem_id = ?
        """,
            (user_id, payload.problem_id, user_id, payload.problem_id),
        )
        attempt_row = cursor.fetchone()
        if attempt_row:
            problem_attempt_context = {
                "attempts": int(attempt_row["attempts"] or 0),
                "accepted": int(attempt_row["accepted"] or 0),
                "last_verdict": attempt_row["last_verdict"],
            }
        cursor.execute(
            """
            SELECT c.chunk_type, c.chunk_text
            FROM premium_problem_rag_chunks c
            JOIN problems p ON p.problem_id = c.problem_id
            WHERE c.problem_id = ?
              AND p.dataset_tier = ?
              AND p.is_active = 1
            ORDER BY chunk_type, chunk_id
            LIMIT 20
        """,
            (payload.problem_id, PREMIUM_DATASET_TIER),
        )
        rag_chunks = [dict(chunk) for chunk in cursor.fetchall()]
        if row:
            context = dict(row)
            ref_payload = {}
            try:
                ref_payload = json.loads(context.get("reference_solution") or "{}")
            except (TypeError, json.JSONDecodeError):
                ref_payload = {}
            related_ids_raw = str(context.get("related_ids") or "").strip()
            related = [item.strip() for item in related_ids_raw.split(",") if item.strip()]
            context["related_problems"] = related
            context["reference_solution_code"] = str(ref_payload.get("code") or "").strip()
            context.pop("reference_solution", None)
            context.pop("related_ids", None)
            problem_context = context
    conn.close()

    started_at = time.perf_counter()
    result = rag_service.query(
        user_id=user_id,
        thread_id=thread_id,
        question=payload.question,
        hint_level=payload.hint_level,
        want_full_solution=payload.want_full_solution,
        problem_context=problem_context,
        weakness_context=weaknesses,
        error_context=error_patterns,
        learner_profile={
            "target_level": current_user.get("target_level"),
            "total_attempts": learner_stats.get("total_attempts"),
            "current_streak": learner_stats.get("current_streak"),
            "success_rate": learner_stats.get("success_rate"),
        },
        recent_attempts=recent_attempts,
        revision_context=revision_stats,
        problem_attempt_context=problem_attempt_context,
        rag_chunks=rag_chunks,
    )
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    if settings.metrics_enabled:
        record_rag_query(source=result.source, error=result.error or "", elapsed_ms=elapsed_ms)

    return {
        "answer": result.answer,
        "source": result.source,
        "rag_available": result.rag_available,
        "thread_id": thread_id,
        "hint_level": result.hint_level,
        "pedagogical_mode": result.pedagogical_mode,
        "code_included": result.code_included,
        "error": result.error,
    }


# ============ Health Check ============

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name, "message": "Intelligent Coding Assistant API"}


@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon response to avoid 404 noise in logs."""
    return Response(status_code=204)


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    db_state = validate_database_state()
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "database": "connected" if db_state else "unknown",
        "db_required_tables": db_state["required_tables"],
        "cors_origins": settings.cors_origins,
    }


@app.get("/api/liveness")
async def liveness_check():
    return {"status": "alive", "service": settings.app_name}


@app.get("/api/readiness")
async def readiness_check():
    try:
        db_state = validate_database_state()
        return {
            "status": "ready",
            "database": "ready",
            "db_required_tables": db_state["required_tables"],
        }
    except Exception as exc:
        raise ApiError(
            status_code=503,
            code="service_not_ready",
            message="Service not ready",
            details={"reason": str(exc)},
        )


@app.get("/api/metrics")
async def metrics_endpoint():
    if not settings.metrics_enabled:
        raise ApiError(status_code=404, code="metrics_disabled", message="Metrics endpoint is disabled")
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
