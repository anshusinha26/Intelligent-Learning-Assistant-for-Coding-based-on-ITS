# Configuration Reference

This project is environment-driven through `src/config.py`.

## Environment Templates

- `.env.example`: complete variable list
- `.env.development.example`: local defaults
- `.env.production.example`: production baseline

## Core Variables

| Variable | Purpose | Default | Notes |
|---|---|---|---|
| `APP_ENV` | Runtime mode | `development` | `production` enables strict checks |
| `HOST` | Bind host | `0.0.0.0` | Public bind in prod requires `ALLOW_PUBLIC_BIND=true` |
| `PORT` | API port | `8000` | Override per environment |
| `DB_PATH` | SQLite DB path | `data/coding_assistant.db` | Use persistent volume in production |
| `SECRET_KEY` | JWT signing secret | generated in dev/test | Required and validated in production |
| `CORS_ALLOW_ORIGINS` | Allowed frontend origins | localhost set | Must be explicit in production |
| `HSTS_ENABLED` | HSTS toggle | `false` | Must be `true` in production |
| `PREMIUM_PROBLEM_BANK_PATH` | Premium dataset JSON | `data/premium/problem_bank.json` | Required for loader |
| `LOAD_LEGACY_PROBLEM_BANK` | Load archived legacy rows | `false` | Keep `false` for active runtime |
| `RAG_ENABLED` | AI tutor availability | `true` | Disable only if needed |
| `RAG_MODE` | RAG mode (`local`/`external`) | `local` | `external` needs token/base URL |
| `RAG_SERVICE_TOKEN` | External RAG auth token | empty | Required only for `RAG_MODE=external` |
| `VITE_API_URL` (frontend) | Frontend API base | fallback to `http://localhost:8001/api` | Must include `/api` |

## Security/Policy Variables

- Password policy:
  - `PASSWORD_MIN_LENGTH`
  - `PASSWORD_REQUIRE_UPPER`
  - `PASSWORD_REQUIRE_LOWER`
  - `PASSWORD_REQUIRE_DIGIT`
  - `PASSWORD_REQUIRE_SYMBOL`
- Rate limits:
  - `RATE_LIMIT_LOGIN_PER_MIN`
  - `RATE_LIMIT_REGISTER_PER_MIN`
  - `RATE_LIMIT_FORGOT_PASSWORD_PER_MIN`
  - `RATE_LIMIT_OTP_VERIFY_PER_MIN`
  - `RATE_LIMIT_RESET_PASSWORD_PER_MIN`
  - `RATE_LIMIT_RAG_PER_MIN`
  - `RATE_LIMIT_JUDGE_PER_MIN`
- Judge safety:
  - `JUDGE_TIMEOUT_SECONDS`
  - `JUDGE_MAX_TEST_CASES`
  - `JUDGE_MAX_OUTPUT_CHARS`
  - `JUDGE_MEMORY_LIMIT_MB`
  - `JUDGE_RECURSION_LIMIT`
- Payload limits:
  - `MAX_REQUEST_BODY_BYTES`
  - `MAX_CODE_SIZE_BYTES`
  - `MAX_RAG_QUESTION_CHARS`

## Production Validation Rules

`src/config.py` fails fast in production for:

- missing/weak `SECRET_KEY`
- weak password policy
- `DEV_EXPOSE_OTP=true`
- wildcard or empty CORS
- `HSTS_ENABLED=false`
- public bind without `ALLOW_PUBLIC_BIND=true`

## Compose Profiles

- Development:
  - `docker compose --profile dev up --build`
- Production:
  - `docker compose --profile prod up --build`
