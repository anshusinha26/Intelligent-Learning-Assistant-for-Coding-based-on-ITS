"""
Authentication Module
Handles user registration, login, JWT lifecycle, refresh, and revocation
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import bcrypt
import jwt

from src.config import settings
from src.database import Database


class AuthService:
    def __init__(self, db: Database):
        self.db = db

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _to_sql_datetime(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _exp_from_payload(payload: dict) -> Optional[datetime]:
        exp = payload.get("exp")
        if exp is None:
            return None
        if isinstance(exp, (int, float)):
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        if isinstance(exp, str):
            try:
                return datetime.fromisoformat(exp.replace("Z", "+00:00"))
            except ValueError:
                return None
        if isinstance(exp, datetime):
            return exp.astimezone(timezone.utc)
        return None

    def _encode_token(
        self,
        user_id: int,
        email: str,
        name: str,
        token_type: str,
        expires_delta: timedelta,
    ) -> Tuple[str, str, datetime]:
        token_id = uuid.uuid4().hex
        expire = self._now_utc() + expires_delta
        payload = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "type": token_type,
            "jti": token_id,
            "exp": expire,
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        return token, token_id, expire

    def create_access_token(self, user_id: int, email: str, name: str) -> str:
        token, _, _ = self._encode_token(
            user_id=user_id,
            email=email,
            name=name,
            token_type="access",
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        return token

    def _create_refresh_token(self, user_id: int, email: str, name: str) -> Tuple[str, str, datetime]:
        return self._encode_token(
            user_id=user_id,
            email=email,
            name=name,
            token_type="refresh",
            expires_delta=timedelta(days=settings.refresh_token_expire_days),
        )

    def _save_refresh_token(self, token_id: str, user_id: int, expires_at: datetime) -> None:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO refresh_tokens (token_id, user_id, expires_at, revoked)
            VALUES (?, ?, ?, 0)
        """,
            (token_id, user_id, self._to_sql_datetime(expires_at)),
        )
        conn.commit()
        conn.close()

    def _revoke_refresh_token(self, token_id: str, replaced_by: Optional[str] = None) -> None:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE refresh_tokens
            SET revoked = 1, replaced_by = COALESCE(?, replaced_by)
            WHERE token_id = ?
        """,
            (replaced_by, token_id),
        )
        conn.commit()
        conn.close()

    def _revoke_all_refresh_tokens(self, user_id: int) -> None:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE refresh_tokens
            SET revoked = 1
            WHERE user_id = ? AND revoked = 0
        """,
            (user_id,),
        )
        conn.commit()
        conn.close()

    def _is_refresh_token_active(self, token_id: str, user_id: int) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT token_id
            FROM refresh_tokens
            WHERE token_id = ?
              AND user_id = ?
              AND revoked = 0
              AND expires_at > ?
        """,
            (token_id, user_id, self._to_sql_datetime(self._now_utc())),
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def _revoke_access_token_id(self, token_id: str, expires_at: Optional[datetime]) -> None:
        if not token_id:
            return
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO revoked_tokens (token_id, expires_at)
            VALUES (?, ?)
        """,
            (
                token_id,
                self._to_sql_datetime(expires_at or (self._now_utc() + timedelta(days=1))),
            ),
        )
        conn.commit()
        conn.close()

    def is_token_revoked(self, token_id: Optional[str]) -> bool:
        if not token_id:
            return True
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT token_id
            FROM revoked_tokens
            WHERE token_id = ?
              AND expires_at > ?
        """,
            (token_id, self._to_sql_datetime(self._now_utc())),
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def verify_token(
        self,
        token: str,
        expected_type: str = "access",
        verify_exp: bool = True,
    ) -> Optional[dict]:
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
                options={"verify_exp": verify_exp},
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

        token_type = payload.get("type", "access")
        if token_type != expected_type:
            return None

        if expected_type == "access" and self.is_token_revoked(payload.get("jti")):
            return None

        return payload

    def _issue_session_tokens(self, user_id: int, email: str, name: str) -> Tuple[str, str]:
        access_token = self.create_access_token(user_id, email, name)
        refresh_token, refresh_id, refresh_expire = self._create_refresh_token(user_id, email, name)
        self._save_refresh_token(refresh_id, user_id, refresh_expire)
        return access_token, refresh_token

    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        target_level: str = "medium",
    ) -> dict:
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Email already registered")

        password_hash = self.hash_password(password)
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, target_level)
            VALUES (?, ?, ?, ?)
        """,
            (name, email, password_hash, target_level),
        )

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        access_token, refresh_token = self._issue_session_tokens(user_id, email, name)

        return {
            "user_id": user_id,
            "name": name,
            "email": email,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def login_user(self, email: str, password: str) -> dict:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, email, password_hash
            FROM users WHERE email = ?
        """,
            (email,),
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise ValueError("Invalid email or password")

        if not self.verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password")

        access_token, refresh_token = self._issue_session_tokens(
            user["user_id"], user["email"], user["name"]
        )

        return {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        payload = self.verify_token(refresh_token, expected_type="refresh")
        if not payload:
            raise ValueError("Invalid or expired refresh token")

        token_id = payload.get("jti")
        user_id = payload.get("user_id")
        if not token_id or not user_id:
            raise ValueError("Invalid refresh token payload")

        if not self._is_refresh_token_active(token_id, user_id):
            raise ValueError("Refresh token has been revoked")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, email
            FROM users
            WHERE user_id = ?
        """,
            (user_id,),
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise ValueError("User not found")

        new_access_token = self.create_access_token(user["user_id"], user["email"], user["name"])
        new_refresh_token, new_refresh_id, new_refresh_expire = self._create_refresh_token(
            user["user_id"], user["email"], user["name"]
        )
        self._save_refresh_token(new_refresh_id, user["user_id"], new_refresh_expire)
        self._revoke_refresh_token(token_id, replaced_by=new_refresh_id)

        return {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    def logout_user(self, access_token: str, user_id: int, refresh_token: Optional[str] = None) -> None:
        access_payload = self.verify_token(access_token, expected_type="access", verify_exp=False)
        if access_payload and access_payload.get("user_id") == user_id:
            self._revoke_access_token_id(
                access_payload.get("jti"),
                self._exp_from_payload(access_payload),
            )

        if refresh_token:
            refresh_payload = self.verify_token(
                refresh_token,
                expected_type="refresh",
                verify_exp=False,
            )
            if refresh_payload and refresh_payload.get("user_id") == user_id:
                token_id = refresh_payload.get("jti")
                if token_id:
                    self._revoke_refresh_token(token_id)

        self._revoke_all_refresh_tokens(user_id)

    def get_current_user(self, token: str) -> Optional[dict]:
        payload = self.verify_token(token, expected_type="access")
        if not payload:
            return None

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, email, role, target_level, created_at
            FROM users WHERE user_id = ?
        """,
            (payload["user_id"],),
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            user_data = dict(user)
            user_data["token_id"] = payload.get("jti")
            return user_data
        return None
