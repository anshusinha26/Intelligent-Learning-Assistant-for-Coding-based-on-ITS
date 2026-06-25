"""Thin adapter for external RAG runtime integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from urllib import request, error


@dataclass
class RAGResult:
    answer: str
    source: str
    rag_available: bool
    error: Optional[str] = None


class RAGService:
    """Calls external RAG API and returns normalized responses."""

    def __init__(
        self,
        enabled: bool,
        base_url: str,
        org_id: str,
        agent_id: str,
        service_token: str,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.enabled = enabled
        self.base_url = base_url.rstrip("/")
        self.org_id = org_id
        self.agent_id = agent_id
        self.service_token = service_token
        self.timeout_seconds = timeout_seconds

    def health(self) -> Dict[str, object]:
        if not self.enabled:
            return {
                "rag_enabled": False,
                "reachable": False,
                "message": "RAG integration disabled",
            }

        for path in ("/health", "/ready"):
            try:
                url = f"{self.base_url}{path}"
                req = request.Request(url, method="GET")
                with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    body = resp.read().decode("utf-8")
                return {
                    "rag_enabled": True,
                    "reachable": True,
                    "status_code": 200,
                    "path": path,
                    "raw": body[:300],
                }
            except Exception:
                continue

        return {
            "rag_enabled": True,
            "reachable": False,
            "message": "RAG runtime unreachable",
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
            return self._local_fallback(question, weakness_context, error_context)

        if not self.service_token:
            return RAGResult(
                answer=(
                    "RAG service token missing. Set RAG_SERVICE_TOKEN in backend environment."
                ),
                source="local-fallback",
                rag_available=False,
                error="missing_service_token",
            )

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

        url = f"{self.base_url}/rag"
        req = request.Request(
            url,
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
            return RAGResult(
                answer=answer,
                source="rag-service",
                rag_available=True,
            )
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            return RAGResult(
                answer=f"RAG HTTP error {exc.code}: {detail[:300]}",
                source="local-fallback",
                rag_available=False,
                error=f"http_{exc.code}",
            )
        except Exception as exc:
            fallback = self._local_fallback(question, weakness_context, error_context)
            fallback.error = str(exc)
            return fallback

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
                f"title={problem_context.get('title')}, "
                f"topic={problem_context.get('topic')}, "
                f"pattern={problem_context.get('pattern')}, "
                f"difficulty={problem_context.get('difficulty')}"
            )

        if weakness_context:
            weakness_bits = []
            for item in weakness_context[:3]:
                weakness_bits.append(
                    f"{item.get('topic')} (mastery={item.get('mastery_score')}, success={item.get('success_rate')}%)"
                )
            lines.append("Weak areas: " + "; ".join(weakness_bits))

        if error_context:
            error_bits = []
            for item in error_context[:3]:
                error_bits.append(f"{item.get('error_type')} x{item.get('count')}")
            lines.append("Frequent errors: " + "; ".join(error_bits))

        lines.append(
            "Instruction: provide concise tutoring guidance, step-by-step hints, and avoid giving full final code unless user asks explicitly."
        )
        return "\n".join(lines)

    @staticmethod
    def _local_fallback(
        question: str,
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: Optional[List[Dict[str, object]]],
    ) -> RAGResult:
        weak_topic = None
        if weakness_context:
            weak_topic = weakness_context[0].get("topic")

        common_error = None
        if error_context:
            common_error = error_context[0].get("error_type")

        guidance_lines = [
            "External RAG unavailable. Local ITS fallback guidance:",
            f"- Your question: {question}",
        ]
        if weak_topic:
            guidance_lines.append(f"- Prioritize concept revision for: {weak_topic}")
        if common_error:
            guidance_lines.append(f"- Common recurring error to watch: {common_error}")
        guidance_lines.append("- Use dry-run on sample testcase, then verify edge cases and complexity.")

        return RAGResult(
            answer="\n".join(guidance_lines),
            source="local-fallback",
            rag_available=False,
            error="rag_unavailable",
        )
