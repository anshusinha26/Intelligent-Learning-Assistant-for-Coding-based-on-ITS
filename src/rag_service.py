"""RAG service with local in-repo engine and optional external mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from urllib import request, error

from src.rag import MinimalRAGEngine


@dataclass
class RAGResult:
    answer: str
    source: str
    rag_available: bool
    error: Optional[str] = None


class RAGService:
    """Unified RAG service: local mode (default) or external runtime mode."""

    def __init__(
        self,
        enabled: bool,
        mode: str,
        base_url: str,
        org_id: str,
        agent_id: str,
        service_token: str,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.enabled = enabled
        normalized_mode = (mode or "local").strip().lower()
        self.mode = normalized_mode if normalized_mode in {"local", "external"} else "local"
        self.base_url = base_url.rstrip("/")
        self.org_id = org_id
        self.agent_id = agent_id
        self.service_token = service_token
        self.timeout_seconds = timeout_seconds
        self.local_engine = MinimalRAGEngine()

    def health(self) -> Dict[str, object]:
        if not self.enabled:
            return {
                "rag_enabled": False,
                "mode": self.mode,
                "reachable": False,
                "message": "RAG integration disabled",
            }

        if self.mode == "local":
            return {
                "rag_enabled": True,
                "mode": "local",
                "reachable": True,
                "message": "Local in-repo RAG ready",
            }

        for path in ("/health", "/ready"):
            try:
                url = f"{self.base_url}{path}"
                req = request.Request(url, method="GET")
                with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    body = resp.read().decode("utf-8")
                return {
                    "rag_enabled": True,
                    "mode": "external",
                    "reachable": True,
                    "status_code": 200,
                    "path": path,
                    "raw": body[:300],
                }
            except Exception:
                continue

        return {
            "rag_enabled": True,
            "mode": "external",
            "reachable": False,
            "message": "External RAG runtime unreachable",
        }

    def query(
        self,
        user_id: int,
        thread_id: str,
        question: str,
        problem_context: Optional[Dict[str, object]] = None,
        weakness_context: Optional[List[Dict[str, object]]] = None,
        error_context: Optional[List[Dict[str, object]]] = None,
    ) -> RAGResult:
        if not self.enabled:
            return RAGResult(
                answer="RAG is disabled in backend config. Set RAG_ENABLED=true to use Ask AI.",
                source="rag-disabled",
                rag_available=False,
                error="rag_disabled",
            )

        if self.mode == "local":
            return self._local_result(question, problem_context, weakness_context, error_context)

        return self._external_query(
            user_id=user_id,
            thread_id=thread_id,
            question=question,
            problem_context=problem_context,
            weakness_context=weakness_context,
            error_context=error_context,
        )

    def _local_result(
        self,
        question: str,
        problem_context: Optional[Dict[str, object]],
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: Optional[List[Dict[str, object]]],
    ) -> RAGResult:
        answer = self.local_engine.answer(
            question=question,
            problem_context=problem_context,
            weakness_context=weakness_context,
            error_context=error_context,
        )
        return RAGResult(
            answer=answer,
            source="local-rag",
            rag_available=True,
            error=None,
        )

    def _external_query(
        self,
        user_id: int,
        thread_id: str,
        question: str,
        problem_context: Optional[Dict[str, object]] = None,
        weakness_context: Optional[List[Dict[str, object]]] = None,
        error_context: Optional[List[Dict[str, object]]] = None,
    ) -> RAGResult:
        if not self.service_token:
            local = self._local_result(question, problem_context, weakness_context, error_context)
            local.error = "missing_service_token"
            return local

        contextual_question = self._build_contextual_question(
            question,
            problem_context=problem_context,
            weakness_context=weakness_context,
            error_context=error_context,
        )

        payload = {
            "question": contextual_question,
            "org_id": self.org_id,
            "agent_id": self.agent_id,
            "user_id": f"its_user_{user_id}",
            "thread_id": thread_id,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.service_token}",
        }

        req = request.Request(
            f"{self.base_url}/rag",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            answer = (data.get("answer") or "").strip()
            if not answer:
                raise ValueError("Missing answer in RAG response")
            return RAGResult(answer=answer, source="rag-service", rag_available=True)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            local = self._local_result(question, problem_context, weakness_context, error_context)
            local.error = f"http_{exc.code}:{detail[:120]}"
            return local
        except Exception as exc:
            local = self._local_result(question, problem_context, weakness_context, error_context)
            local.error = str(exc)
            return local

    @staticmethod
    def _build_contextual_question(
        question: str,
        problem_context: Optional[Dict[str, object]],
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: Optional[List[Dict[str, object]]],
    ) -> str:
        lines = [f"User question: {question}"]

        if problem_context:
            lines.append(
                "Current problem context: "
                f"title={problem_context.get(title)}, "
                f"topic={problem_context.get(topic)}, "
                f"pattern={problem_context.get(pattern)}, "
                f"difficulty={problem_context.get(difficulty)}"
            )

        if weakness_context:
            weakness_bits = []
            for item in weakness_context[:3]:
                weakness_bits.append(
                    f"{item.get(topic)} (mastery={item.get(mastery_score)}, success={item.get(success_rate)}%)"
                )
            lines.append("Weak areas: " + "; ".join(weakness_bits))

        if error_context:
            error_bits = []
            for item in error_context[:3]:
                error_bits.append(f"{item.get(error_type)} x{item.get(count)}")
            lines.append("Frequent errors: " + "; ".join(error_bits))

        lines.append(
            "Instruction: provide concise tutoring guidance, step-by-step hints, and avoid giving full final code unless user asks explicitly."
        )
        return "\n".join(lines)
