"""Application configuration and environment helpers."""

import os
from typing import List


class Settings:
    """Loads runtime settings from environment variables."""

    def __init__(self) -> None:
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = self._parse_int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"),
            default=1440,
        )
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = self._parse_int(os.getenv("PORT", "8000"), default=8000)

        default_origins = (
            "http://localhost:8080,"
            "http://127.0.0.1:8080,"
            "http://localhost:5500,"
            "http://127.0.0.1:5500"
        )
        self.cors_origins = self._parse_origins(
            os.getenv("CORS_ALLOW_ORIGINS", default_origins)
        )

    @staticmethod
    def _parse_int(value: str, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_origins(value: str) -> List[str]:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        return origins or ["http://localhost:8080"]


settings = Settings()
