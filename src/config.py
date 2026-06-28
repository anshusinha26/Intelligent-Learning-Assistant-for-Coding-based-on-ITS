"""Application configuration and environment helpers."""

import os
import secrets
from typing import List


class Settings:
    """Loads runtime settings from environment variables."""

    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development").strip().lower()
        self.app_name = os.getenv("APP_NAME", "ila-coding")
        self.log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        self.request_id_header = os.getenv("REQUEST_ID_HEADER", "X-Request-ID")
        self.metrics_enabled = self._parse_bool(os.getenv("METRICS_ENABLED", "true"), True)
        self.slow_request_threshold_ms = self._parse_int(
            os.getenv("SLOW_REQUEST_THRESHOLD_MS", "1200"),
            default=1200,
        )
        self.db_slow_query_threshold_ms = self._parse_int(
            os.getenv("DB_SLOW_QUERY_THRESHOLD_MS", "120"),
            default=120,
        )

        configured_secret = os.getenv("SECRET_KEY", "").strip()
        if configured_secret:
            self.secret_key = configured_secret
        elif self.app_env in {"development", "dev", "test"}:
            self.secret_key = secrets.token_hex(32)
        else:
            raise ValueError("SECRET_KEY must be set")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_issuer = os.getenv("JWT_ISSUER", "ila-coding-api")
        self.jwt_audience = os.getenv("JWT_AUDIENCE", "ila-coding-clients")
        self.access_token_expire_minutes = self._parse_int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"),
            default=1440,
        )
        self.refresh_token_expire_days = self._parse_int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"),
            default=30,
        )
        self.password_reset_token_expire_minutes = self._parse_int(
            os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "20"),
            default=20,
        )
        self.otp_expire_minutes = self._parse_int(
            os.getenv("OTP_EXPIRE_MINUTES", "10"),
            default=10,
        )
        self.otp_max_attempts = self._parse_int(
            os.getenv("OTP_MAX_ATTEMPTS", "5"),
            default=5,
        )
        self.otp_cooldown_seconds = self._parse_int(
            os.getenv("OTP_COOLDOWN_SECONDS", "30"),
            default=30,
        )
        self.dev_expose_otp = self._parse_bool(
            os.getenv("DEV_EXPOSE_OTP", "true"),
            True,
        )

        self.password_min_length = self._parse_int(
            os.getenv("PASSWORD_MIN_LENGTH", "6"),
            default=6,
        )
        self.password_require_upper = self._parse_bool(
            os.getenv("PASSWORD_REQUIRE_UPPER", "false"),
            False,
        )
        self.password_require_lower = self._parse_bool(
            os.getenv("PASSWORD_REQUIRE_LOWER", "true"),
            True,
        )
        self.password_require_digit = self._parse_bool(
            os.getenv("PASSWORD_REQUIRE_DIGIT", "true"),
            True,
        )
        self.password_require_symbol = self._parse_bool(
            os.getenv("PASSWORD_REQUIRE_SYMBOL", "false"),
            False,
        )

        self.max_request_body_bytes = self._parse_int(
            os.getenv("MAX_REQUEST_BODY_BYTES", "262144"),
            default=262144,
        )
        self.max_code_size_bytes = self._parse_int(
            os.getenv("MAX_CODE_SIZE_BYTES", "50000"),
            default=50000,
        )
        self.max_rag_question_chars = self._parse_int(
            os.getenv("MAX_RAG_QUESTION_CHARS", "2000"),
            default=2000,
        )

        self.rate_limit_login_per_min = self._parse_int(
            os.getenv("RATE_LIMIT_LOGIN_PER_MIN", "12"),
            default=12,
        )
        self.rate_limit_register_per_min = self._parse_int(
            os.getenv("RATE_LIMIT_REGISTER_PER_MIN", "6"),
            default=6,
        )
        self.rate_limit_forgot_password_per_min = self._parse_int(
            os.getenv("RATE_LIMIT_FORGOT_PASSWORD_PER_MIN", "6"),
            default=6,
        )
        self.rate_limit_otp_verify_per_min = self._parse_int(
            os.getenv("RATE_LIMIT_OTP_VERIFY_PER_MIN", "20"),
            default=20,
        )
        self.rate_limit_reset_password_per_min = self._parse_int(
            os.getenv("RATE_LIMIT_RESET_PASSWORD_PER_MIN", "8"),
            default=8,
        )
        self.rate_limit_rag_per_min = self._parse_int(
            os.getenv("RATE_LIMIT_RAG_PER_MIN", "30"),
            default=30,
        )
        self.rate_limit_judge_per_min = self._parse_int(
            os.getenv("RATE_LIMIT_JUDGE_PER_MIN", "45"),
            default=45,
        )

        self.judge_timeout_seconds = self._parse_int(
            os.getenv("JUDGE_TIMEOUT_SECONDS", "3"),
            default=3,
        )
        self.judge_max_test_cases = self._parse_int(
            os.getenv("JUDGE_MAX_TEST_CASES", "30"),
            default=30,
        )
        self.judge_max_output_chars = self._parse_int(
            os.getenv("JUDGE_MAX_OUTPUT_CHARS", "12000"),
            default=12000,
        )
        self.judge_memory_limit_mb = self._parse_int(
            os.getenv("JUDGE_MEMORY_LIMIT_MB", "128"),
            default=128,
        )
        self.judge_recursion_limit = self._parse_int(
            os.getenv("JUDGE_RECURSION_LIMIT", "2000"),
            default=2000,
        )

        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = self._parse_int(os.getenv("PORT", "8000"), default=8000)
        self.db_path = os.getenv("DB_PATH", "data/coding_assistant.db")
        self.premium_problem_bank_path = os.getenv(
            "PREMIUM_PROBLEM_BANK_PATH",
            "data/premium/problem_bank.json",
        )
        self.legacy_problem_bank_path = os.getenv(
            "LEGACY_PROBLEM_BANK_PATH",
            "data/archive/legacy_problem_bank/dsa_problems.md",
        )
        self.load_legacy_problem_bank = self._parse_bool(
            os.getenv("LOAD_LEGACY_PROBLEM_BANK", "false"),
            False,
        )

        default_origins = (
            "http://localhost:8080,"
            "http://127.0.0.1:8080,"
            "http://localhost:5173,"
            "http://127.0.0.1:5173,"
            "http://localhost:5500,"
            "http://127.0.0.1:5500"
        )
        self.cors_origins = self._parse_origins(
            os.getenv("CORS_ALLOW_ORIGINS", default_origins)
        )

        self.csp_policy = os.getenv(
            "CSP_POLICY",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        self.hsts_enabled = self._parse_bool(os.getenv("HSTS_ENABLED", "false"), False)
        self.hsts_max_age = self._parse_int(os.getenv("HSTS_MAX_AGE", "31536000"), default=31536000)
        self.x_frame_options = os.getenv("X_FRAME_OPTIONS", "DENY")
        self.referrer_policy = os.getenv("REFERRER_POLICY", "strict-origin-when-cross-origin")

        # RAG configuration: local mode runs fully in this repo.
        self.rag_enabled = self._parse_bool(os.getenv("RAG_ENABLED", "true"), True)
        self.rag_mode = os.getenv("RAG_MODE", "local").strip().lower()
        self.rag_base_url = os.getenv("RAG_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
        self.rag_org_id = os.getenv("RAG_ORG_ID", "test_org")
        self.rag_agent_id = os.getenv("RAG_AGENT_ID", "default_bot")
        self.rag_service_token = os.getenv("RAG_SERVICE_TOKEN", "")
        self.rag_timeout_seconds = self._parse_float(
            os.getenv("RAG_TIMEOUT_SECONDS", "20"),
            default=20.0,
        )
        self.rag_allow_full_solutions = self._parse_bool(
            os.getenv("RAG_ALLOW_FULL_SOLUTIONS", "false"),
            False,
        )
        self.rag_enforce_hint_progression = self._parse_bool(
            os.getenv("RAG_ENFORCE_HINT_PROGRESSION", "true"),
            True,
        )
        self.rag_thread_state_max = self._parse_int(
            os.getenv("RAG_THREAD_STATE_MAX", "5000"),
            default=5000,
        )
        self.validate()

    @staticmethod
    def _parse_int(value: str, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_float(value: str, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_bool(value: str, default: bool) -> bool:
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _parse_origins(value: str) -> List[str]:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        return origins or ["http://localhost:8080"]

    def validate(self) -> None:
        is_production = self.app_env in {"production", "prod"}
        if self.password_min_length < 6:
            raise ValueError("PASSWORD_MIN_LENGTH must be >= 6")
        if self.max_request_body_bytes < 1024:
            raise ValueError("MAX_REQUEST_BODY_BYTES too small")
        if self.max_code_size_bytes < 512:
            raise ValueError("MAX_CODE_SIZE_BYTES too small")
        if self.judge_timeout_seconds < 1:
            raise ValueError("JUDGE_TIMEOUT_SECONDS must be >= 1")
        if self.otp_max_attempts < 1:
            raise ValueError("OTP_MAX_ATTEMPTS must be >= 1")
        if self.slow_request_threshold_ms < 1:
            raise ValueError("SLOW_REQUEST_THRESHOLD_MS must be >= 1")
        if self.db_slow_query_threshold_ms < 1:
            raise ValueError("DB_SLOW_QUERY_THRESHOLD_MS must be >= 1")
        if not self.premium_problem_bank_path:
            raise ValueError("PREMIUM_PROBLEM_BANK_PATH must be configured")
        if self.rag_thread_state_max < 100:
            raise ValueError("RAG_THREAD_STATE_MAX must be >= 100")

        if is_production:
            if self.password_min_length < 8:
                raise ValueError("PASSWORD_MIN_LENGTH must be >= 8 in production")
            if not self.password_require_upper or not self.password_require_symbol:
                raise ValueError("PASSWORD policy must require upper and symbol in production")
            if len(self.secret_key) < 32:
                raise ValueError("Unsafe SECRET_KEY for production")
            if self.dev_expose_otp:
                raise ValueError("DEV_EXPOSE_OTP must be false in production")
            if not self.cors_origins or "*" in self.cors_origins:
                raise ValueError("CORS_ALLOW_ORIGINS must be explicit in production")
            if self.hsts_enabled is False:
                raise ValueError("HSTS_ENABLED must be true in production")
            if self.host in {"0.0.0.0", "::"} and os.getenv("ALLOW_PUBLIC_BIND", "false").lower() != "true":
                raise ValueError("Public bind requires ALLOW_PUBLIC_BIND=true in production")


settings = Settings()
