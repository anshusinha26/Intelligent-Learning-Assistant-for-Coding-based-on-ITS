"""
Authentication Module
Handles user registration, login, JWT lifecycle, refresh, and revocation
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import bcrypt
import jwt

from src.config import settings
from src.database import Database
from src.security import validate_password_strength


class AuthService:
    def __init__(self, db: Database):
        self.db = db

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def _validate_new_password(password: str) -> None:
        ok, message = validate_password_strength(
            password or "",
            min_length=settings.password_min_length,
            require_upper=settings.password_require_upper,
            require_lower=settings.password_require_lower,
            require_digit=settings.password_require_digit,
            require_symbol=settings.password_require_symbol,
        )
        if not ok:
            raise ValueError(message)

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
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": self._now_utc(),
            "nbf": self._now_utc(),
            "exp": expire,
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        return token, token_id, expire

    def _create_password_reset_token(self, user_id: int, email: str, name: str) -> str:
        token, _, _ = self._encode_token(
            user_id=user_id,
            email=email,
            name=name,
            token_type="password_reset",
            expires_delta=timedelta(minutes=settings.password_reset_token_expire_minutes),
        )
        return token

    @staticmethod
    def _normalize_email(email: str) -> str:
        return (email or "").strip().lower()

    def _hash_otp(self, email: str, purpose: str, otp: str) -> str:
        msg = f"{self._normalize_email(email)}:{purpose}:{otp}".encode("utf-8")
        return hmac.new(settings.secret_key.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    @staticmethod
    def _generate_otp() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

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

    def _get_refresh_token_record(self, token_id: str) -> Optional[dict]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT token_id, user_id, revoked, expires_at, replaced_by
            FROM refresh_tokens
            WHERE token_id = ?
        """,
            (token_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def _handle_refresh_reuse(self, user_id: int, token_id: str) -> None:
        self._revoke_all_refresh_tokens(user_id)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO revoked_tokens (token_id, expires_at)
            VALUES (?, ?)
        """,
            (f"reuse_{token_id}", self._to_sql_datetime(self._now_utc() + timedelta(days=7))),
        )
        conn.commit()
        conn.close()

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
                issuer=settings.jwt_issuer,
                audience=settings.jwt_audience,
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

    @staticmethod
    def _parse_sql_datetime(value: str) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

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
        normalized_email = self._normalize_email(email)
        self._validate_new_password(password)
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT email FROM users WHERE email = ?", (normalized_email,))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Email already registered")

        password_hash = self.hash_password(password)
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, target_level)
            VALUES (?, ?, ?, ?)
        """,
            (name, normalized_email, password_hash, target_level),
        )

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        access_token, refresh_token = self._issue_session_tokens(user_id, normalized_email, name)

        return {
            "user_id": user_id,
            "name": name,
            "email": normalized_email,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def login_user(self, email: str, password: str) -> dict:
        normalized_email = self._normalize_email(email)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, email, password_hash
            FROM users WHERE email = ?
        """,
            (normalized_email,),
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

        refresh_record = self._get_refresh_token_record(token_id)
        if not refresh_record:
            raise ValueError("Refresh token is unknown")

        if int(refresh_record.get("revoked", 0)) == 1:
            self._handle_refresh_reuse(user_id, token_id)
            raise ValueError("Refresh token reuse detected; all sessions revoked")

        if not self._is_refresh_token_active(token_id, user_id):
            raise ValueError("Refresh token has expired")

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
            SELECT user_id, name, email, role, target_level, email_verified, created_at
            FROM users WHERE user_id = ?
        """,
            (payload["user_id"],),
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            user_data = dict(user)
            user_data["email_verified"] = bool(user_data.get("email_verified", 0))
            user_data["token_id"] = payload.get("jti")
            return user_data
        return None

    def _create_otp_code(
        self,
        email: str,
        purpose: str,
        user_id: Optional[int] = None,
    ) -> str:
        normalized_email = self._normalize_email(email)
        normalized_purpose = (purpose or "").strip().lower()
        otp = self._generate_otp()
        otp_hash = self._hash_otp(normalized_email, normalized_purpose, otp)
        expires_at = self._now_utc() + timedelta(minutes=settings.otp_expire_minutes)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT created_at
            FROM otp_codes
            WHERE email = ? AND purpose = ?
            ORDER BY otp_id DESC
            LIMIT 1
        """,
            (normalized_email, normalized_purpose),
        )
        latest = cursor.fetchone()
        if latest:
            created_at = self._parse_sql_datetime(latest["created_at"])
            if created_at:
                since = (self._now_utc() - created_at).total_seconds()
                if since < settings.otp_cooldown_seconds:
                    conn.close()
                    raise ValueError(
                        f"OTP recently generated. Retry after {int(settings.otp_cooldown_seconds - since) + 1}s"
                    )

        cursor.execute(
            """
            UPDATE otp_codes
            SET consumed = 1
            WHERE email = ? AND purpose = ? AND consumed = 0
        """,
            (normalized_email, normalized_purpose),
        )
        cursor.execute(
            """
            INSERT INTO otp_codes (user_id, email, purpose, otp_hash, expires_at, consumed, attempts)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """,
            (
                user_id,
                normalized_email,
                normalized_purpose,
                otp_hash,
                self._to_sql_datetime(expires_at),
            ),
        )
        conn.commit()
        conn.close()
        return otp

    def request_password_reset(self, email: str) -> dict:
        normalized_email = self._normalize_email(email)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, email
            FROM users
            WHERE email = ?
        """,
            (normalized_email,),
        )
        user = cursor.fetchone()
        conn.close()

        dev_otp = None
        if user:
            try:
                otp = self._create_otp_code(
                    email=normalized_email,
                    purpose="password_reset",
                    user_id=user["user_id"],
                )
                if settings.dev_expose_otp:
                    dev_otp = otp
            except ValueError:
                dev_otp = None

        return {
            "message": "If the account exists, an OTP has been generated.",
            "otp_sent": True,
            "dev_otp": dev_otp,
        }

    def request_email_verification(self, user_id: int) -> dict:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, email, email_verified
            FROM users
            WHERE user_id = ?
        """,
            (user_id,),
        )
        user = cursor.fetchone()
        conn.close()
        if not user:
            raise ValueError("User not found")
        if int(user["email_verified"] or 0) == 1:
            return {
                "message": "Email is already verified.",
                "otp_sent": False,
                "dev_otp": None,
            }

        otp = self._create_otp_code(
            email=user["email"],
            purpose="email_verification",
            user_id=user_id,
        )
        return {
            "message": "Verification OTP generated.",
            "otp_sent": True,
            "dev_otp": otp if settings.dev_expose_otp else None,
        }

    def verify_otp(self, email: str, otp: str, purpose: str) -> dict:
        normalized_email = self._normalize_email(email)
        normalized_purpose = (purpose or "").strip().lower()
        expected_hash = self._hash_otp(normalized_email, normalized_purpose, otp.strip())
        now_sql = self._to_sql_datetime(self._now_utc())

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT otp_id, user_id, email, purpose, otp_hash, attempts
            FROM otp_codes
            WHERE email = ? AND purpose = ? AND consumed = 0 AND expires_at > ?
            ORDER BY created_at DESC, otp_id DESC
            LIMIT 1
        """,
            (normalized_email, normalized_purpose, now_sql),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError("OTP is invalid or expired")

        if not hmac.compare_digest(row["otp_hash"], expected_hash):
            attempts = int(row["attempts"] or 0) + 1
            consumed = 1 if attempts >= settings.otp_max_attempts else 0
            cursor.execute(
                """
                UPDATE otp_codes
                SET attempts = ?, consumed = ?
                WHERE otp_id = ?
            """,
                (attempts, consumed, row["otp_id"]),
            )
            conn.commit()
            conn.close()
            raise ValueError("OTP is invalid")

        cursor.execute(
            """
            UPDATE otp_codes
            SET consumed = 1
            WHERE otp_id = ?
        """,
            (row["otp_id"],),
        )

        reset_token = None
        if normalized_purpose == "password_reset":
            cursor.execute(
                """
                SELECT user_id, name, email
                FROM users
                WHERE email = ?
            """,
                (normalized_email,),
            )
            user = cursor.fetchone()
            if not user:
                conn.commit()
                conn.close()
                raise ValueError("User not found")
            reset_token = self._create_password_reset_token(
                user["user_id"],
                user["email"],
                user["name"],
            )
        elif normalized_purpose == "email_verification":
            cursor.execute(
                """
                UPDATE users
                SET email_verified = 1, email_verified_at = ?
                WHERE email = ?
            """,
                (self._to_sql_datetime(self._now_utc()), normalized_email),
            )

        conn.commit()
        conn.close()
        return {
            "message": "OTP verified successfully",
            "purpose": normalized_purpose,
            "verified": True,
            "reset_token": reset_token,
        }

    def verify_email_otp(self, user_id: int, otp: str) -> dict:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise ValueError("User not found")
        return self.verify_otp(row["email"], otp, "email_verification")

    def reset_password(self, reset_token: str, new_password: str) -> None:
        self._validate_new_password(new_password)
        payload = self.verify_token(reset_token, expected_type="password_reset")
        if not payload:
            raise ValueError("Invalid or expired reset token")

        user_id = payload.get("user_id")
        email = self._normalize_email(payload.get("email", ""))
        if not user_id or not email:
            raise ValueError("Invalid reset token payload")

        password_hash = self.hash_password(new_password)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE user_id = ? AND email = ?
        """,
            (password_hash, user_id, email),
        )
        if cursor.rowcount == 0:
            conn.close()
            raise ValueError("User not found")
        conn.commit()
        conn.close()
        self._revoke_all_refresh_tokens(user_id)

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        self._validate_new_password(new_password)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT password_hash
            FROM users
            WHERE user_id = ?
        """,
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            conn.close()
            raise ValueError("User not found")

        if not self.verify_password(current_password, user["password_hash"]):
            conn.close()
            raise ValueError("Current password is incorrect")

        new_hash = self.hash_password(new_password)
        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE user_id = ?
        """,
            (new_hash, user_id),
        )
        conn.commit()
        conn.close()
        self._revoke_all_refresh_tokens(user_id)
