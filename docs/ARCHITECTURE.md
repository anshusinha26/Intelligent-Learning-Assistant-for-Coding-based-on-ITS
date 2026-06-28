# Architecture

## System Context

The platform is a full-stack ITS coding assistant:

- Frontend: React + Vite
- Backend: FastAPI
- Database: SQLite
- Dataset: premium 75-problem bank
- Intelligence layer: learner model + recommender + revision scheduler + AI tutor (RAG)

## Backend Modules

- `src/main.py`: API routes and workflow orchestration
- `src/auth.py`: authentication, password/OTP flows, token lifecycle
- `src/learner_model.py`: mastery/weakness computations
- `src/recommender.py`: recommendation scoring and filtering
- `src/revision_scheduler.py`: spaced review schedule logic
- `src/rag_service.py` + `src/rag/minimal_engine.py`: tutor query handling
- `src/judge.py`: Python code execution and verdicting
- `src/security.py`: rate limiting, headers, payload constraints
- `src/observability.py`: request IDs, metrics, structured logs
- `src/database.py` + `src/migrations.py`: schema and migration management

## Data Model (High Level)

- User/account/auth state
- Problems and premium educational assets
- Attempts/submissions and learner metrics
- Recommendations and revision schedules
- Notes/bookmarks/settings
- RAG chunks and relationship graph edges

## Learning Loop

1. Learner submits/records attempt.
2. Judge returns verdict (submission flow).
3. Learner model updates mastery/error profile.
4. Recommendation engine re-scores unseen problems.
5. Revision scheduler updates due reviews.
6. Dashboard/AI tutor expose updated learner state.

## API Boundaries

All application endpoints are under `/api/*`.

Critical groups:

- auth and session lifecycle
- problems and submissions
- recommendations and revisions
- analytics
- notes/bookmarks/settings
- AI tutor and health/metrics

## Dataset Boundary

Active runtime surface uses only:

- `dataset_tier='premium'`
- `is_active=1`

Legacy dataset remains archived/inactive.
