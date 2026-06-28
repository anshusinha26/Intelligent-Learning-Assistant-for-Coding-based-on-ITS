# Deployment

## Local Deployment (Recommended for Development)

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/manage_migrations.py upgrade --db-path data/coding_assistant.db
python3 load_sample_data.py
PORT=8020 python3 -m src.main
```

### Frontend

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8020/api npm run dev -- --host 0.0.0.0 --port 5173
```

## Container Deployment

### Development profile

```bash
docker compose --profile dev up --build
```

### Production profile

```bash
docker compose --profile prod up --build
```

Production profile includes:

- backend service
- frontend service
- prometheus
- grafana
- health checks and startup ordering

## Environment Setup

1. Copy a template:
   - `cp .env.example .env`
2. Set production secrets and policies:
   - `SECRET_KEY`
   - strict password policy variables
   - explicit `CORS_ALLOW_ORIGINS`
   - `HSTS_ENABLED=true`
3. Set frontend API URL:
   - `VITE_API_URL=https://<backend-domain>/api`

## Post-Deployment Verification

- API health: `GET /api/health`
- Readiness: `GET /api/readiness`
- Metrics: `GET /api/metrics`
- Auth login flow
- Problems endpoint returns premium-only records
- Dashboard and recommendations load for authenticated user
