# Quick Start (Current)

This file tracks the current Phase 1–6 runtime flow.

For full documentation, use `README.md`.

## 1) Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/manage_migrations.py upgrade --db-path data/coding_assistant.db
python3 load_sample_data.py
PORT=8020 python3 -m src.main
```

Backend:

- `http://localhost:8020/api/health`
- `http://localhost:8020/docs`

## 2) Frontend

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8020/api npm run dev -- --host 0.0.0.0 --port 5173
```

Frontend:

- `http://localhost:5173`

## 3) Demo Login

- Email: `demo@example.com`
- Password: `demo123`

## 4) Quick Verification

Premium active count should be 75:

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
