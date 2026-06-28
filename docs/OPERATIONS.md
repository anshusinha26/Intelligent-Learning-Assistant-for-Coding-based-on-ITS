# Operations Runbook

## Startup Sequence (Local)

1. Apply migrations:
   - `python3 scripts/manage_migrations.py upgrade --db-path data/coding_assistant.db`
2. Load premium dataset + demo user:
   - `python3 load_sample_data.py`
3. Start backend:
   - `PORT=8020 python3 -m src.main`
4. Start frontend:
   - `cd frontend && VITE_API_URL=http://localhost:8020/api npm run dev -- --host 0.0.0.0 --port 5173`

## Health Endpoints

- `GET /api/health` — overall service/DB state
- `GET /api/liveness` — process liveness
- `GET /api/readiness` — schema readiness checks
- `GET /api/metrics` — Prometheus metrics

## Migration Operations

- Status:
  - `python3 scripts/manage_migrations.py status --db-path data/coding_assistant.db`
- Upgrade:
  - `python3 scripts/manage_migrations.py upgrade --db-path data/coding_assistant.db`
- Rollback last migration:
  - `python3 scripts/manage_migrations.py downgrade --db-path data/coding_assistant.db`

## Database Operations

- Backup:
  - `python3 scripts/db_backup.py --db-path data/coding_assistant.db --output-dir backups`
- Restore:
  - `python3 scripts/db_restore.py --backup-path backups/<file>.db --target-db-path data/coding_assistant.db`
- Integrity:
  - `python3 scripts/db_integrity_check.py --db-path data/coding_assistant.db`

## Premium Dataset Verification

Expected active premium problems: **75**

```bash
python3 - <<'PY'
import sqlite3
conn = sqlite3.connect("data/coding_assistant.db")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM problems WHERE dataset_tier='premium' AND is_active=1")
print(cur.fetchone()[0])
conn.close()
PY
```

## Observability

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Provisioned dashboard: `ILA Coding - Production Overview`

## Common Operational Failures

- `SECRET_KEY must be set` in production: define in `.env`.
- Frontend API 404: ensure API base includes `/api` and backend instance is current.
- Migration mismatch: run migration status and upgrade.
- Wrong dataset: reload via `load_sample_data.py` with legacy loading disabled.
- Port collision: change `PORT` or frontend dev port.
