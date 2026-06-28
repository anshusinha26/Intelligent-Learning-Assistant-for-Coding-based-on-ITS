"""Security and reliability helpers (rate limiting, validation, errors)."""

from __future__ import annotations

import json
import re
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse


COMMON_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "123456789",
    "qwerty",
    "qwerty123",
    "letmein",
    "welcome",
    "admin123",
    "iloveyou",
    "123123123",
    "00000000",
    "abc12345",
}


PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all|any|previous)\s+instructions?", re.IGNORECASE),
    re.compile(r"reveal\s+(system|hidden)\s+prompt", re.IGNORECASE),
    re.compile(r"bypass\s+(safety|guardrails?|filters?)", re.IGNORECASE),
    re.compile(r"developer\s+message", re.IGNORECASE),
    re.compile(r"role\s*:\s*system", re.IGNORECASE),
    re.compile(r"(reveal|show|leak)\s+hidden\s+tests?", re.IGNORECASE),
    re.compile(r"hidden\s+test\s*cases?", re.IGNORECASE),
    re.compile(r"give\s+me\s+all\s+test\s*cases?", re.IGNORECASE),
]


@dataclass
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: int


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: Optional[dict] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        self.headers = headers or {}


class RateLimiter:
    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, *, limit: int, window_seconds: int = 60) -> RateLimitDecision:
        now = time.time()
        start = now - window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < start:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = int(max(1, window_seconds - (now - bucket[0])))
                return RateLimitDecision(
                    allowed=False,
                    remaining=0,
                    retry_after_seconds=retry_after,
                )

            bucket.append(now)
            remaining = max(0, limit - len(bucket))
            return RateLimitDecision(
                allowed=True,
                remaining=remaining,
                retry_after_seconds=0,
            )


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return request_id
    return uuid.uuid4().hex


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Optional[dict] = None,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    payload = {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": get_request_id(request),
        }
    }
    response_headers = headers or {}
    return JSONResponse(status_code=status_code, content=payload, headers=response_headers)


def validate_password_strength(
    password: str,
    *,
    min_length: int,
    require_upper: bool,
    require_lower: bool,
    require_digit: bool,
    require_symbol: bool,
) -> Tuple[bool, str]:
    if len(password or "") < min_length:
        return False, f"Password must be at least {min_length} characters"
    lowered = (password or "").lower()
    if lowered in COMMON_PASSWORDS:
        return False, "Password is too common; choose a stronger password"
    if require_upper and not re.search(r"[A-Z]", password or ""):
        return False, "Password must include an uppercase letter"
    if require_lower and not re.search(r"[a-z]", password or ""):
        return False, "Password must include a lowercase letter"
    if require_digit and not re.search(r"\d", password or ""):
        return False, "Password must include a digit"
    if require_symbol and not re.search(r"[^A-Za-z0-9]", password or ""):
        return False, "Password must include a symbol"
    return True, ""


def rag_question_guardrail(question: str, max_chars: int) -> Tuple[bool, str]:
    normalized = (question or "").strip()
    if not normalized:
        return False, "Question cannot be empty"
    if len(normalized) > max_chars:
        return False, f"Question exceeds maximum length of {max_chars} characters"
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(normalized):
            return (
                False,
                "Prompt rejected due to prompt-injection pattern. Ask a direct coding question.",
            )
    return True, normalized


def structured_log(event: str, **fields: object) -> str:
    payload = {"event": event, **fields}
    return json.dumps(payload, ensure_ascii=True, default=str)
