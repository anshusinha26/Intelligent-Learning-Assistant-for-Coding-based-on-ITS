# Infrastructure

## Container Images

- Backend image: `Dockerfile` (multi-stage)
- Frontend image: `frontend/Dockerfile` (multi-stage)

## Compose Profiles

`docker-compose.yml` defines:

- `backend-dev`, `frontend-dev` for local development
- `backend`, `frontend`, `prometheus`, `grafana` for production profile

Persistent volumes:

- `db_data`
- `backups`
- `grafana_data`

## CI/CD

GitHub Actions workflow: `.github/workflows/ci.yml`

Pipeline stages:

1. Backend quality
   - compile/lint checks
   - formatting checks
   - unittest suite + coverage
   - phase validators
   - security scans (`bandit`, `pip-audit`)
2. Frontend quality
   - install/build
   - dependency audit
3. Docker/compose validation
   - image builds
   - compose config checks

## Observability

Backend emits:

- structured logs
- request IDs
- health/readiness/liveness endpoints
- Prometheus metrics

Observability assets:

- `observability/prometheus/prometheus.yml`
- `observability/grafana/dashboards/ila-overview.json`

Default ports:

- API: backend mapped to `8001` in compose prod
- Frontend: `3000`
- Prometheus: `9090`
- Grafana: `3001`

## Database Operations

Migration management:

- `python3 scripts/manage_migrations.py status --db-path data/coding_assistant.db`
- `python3 scripts/manage_migrations.py upgrade --db-path data/coding_assistant.db`
- `python3 scripts/manage_migrations.py downgrade --db-path data/coding_assistant.db`

Backup/restore/integrity:

- `python3 scripts/db_backup.py --db-path data/coding_assistant.db --output-dir backups`
- `python3 scripts/db_restore.py --backup-path backups/<file>.db --target-db-path data/coding_assistant.db`
- `python3 scripts/db_integrity_check.py --db-path data/coding_assistant.db`
