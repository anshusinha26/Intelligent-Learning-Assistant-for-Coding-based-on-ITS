"""Minimal local RAG engine for ITS coding guidance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union
import re


_TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


_PATTERN_HINTS: Dict[str, str] = {
    "array": "Try index-based traversal and keep clear index invariants.",
    "string": "Use two pointers or frequency maps; handle empty and single-char cases.",
    "hash": "Hash map/set often reduces lookup to O(1) average.",
    "two pointers": "Define pointer movement and stop condition before coding.",
    "sliding window": "Track window validity and only then update best answer.",
    "binary search": "Maintain low/high invariant and move bounds based on condition.",
    "stack": "Push when opening state, pop when resolving dependency/order.",
    "queue": "Use queue for BFS-like level/state traversal.",
    "dp": "Write recurrence and base cases first, then transition order.",
    "graph": "Choose BFS/DFS based on shortest path vs reachability.",
    "tree": "Pick traversal order based on output requirement.",
    "greedy": "Validate local-choice reasoning before implementation.",
}

_ERROR_HINTS: Dict[str, str] = {
    "off-by-one": "Re-check loop bounds and inclusive/exclusive ranges.",
    "edge-case": "Test empty input, single item, duplicates, and max constraints.",
    "logic-error": "Write expected state after each major step and compare with dry run.",
    "time-limit": "Reduce nested loops; use hashing/sorting/pruning where possible.",
}

ErrorContext = Optional[Union[List[Dict[str, object]], Dict[str, int]]]


@dataclass
class RetrievedChunk:
    text: str
    score: int


class MinimalRAGEngine:
    """Small retrieval + template generation engine for coding support."""

    def answer(
        self,
        question: str,
        problem_context: Optional[Dict[str, object]] = None,
        weakness_context: Optional[List[Dict[str, object]]] = None,
        error_context: ErrorContext = None,
    ) -> str:
        chunks = self.retrieve(
            question=question,
            problem_context=problem_context,
            weakness_context=weakness_context,
            error_context=error_context,
        )

        lines: List[str] = ["Focused guidance for your question:"]

        if problem_context:
            title = problem_context.get("title") or "current problem"
            topic = problem_context.get("topic") or "unknown topic"
            pattern = problem_context.get("pattern") or "unknown pattern"
            lines.append(f"- Context: {title} ({topic}, pattern: {pattern})")

        lines.append("- Suggested approach:")
        for idx, chunk in enumerate(chunks[:3], start=1):
            lines.append(f"  {idx}) {chunk.text}")

        common_error = self._top_error(error_context)
        if common_error:
            lines.append(f"- Watch-out: {common_error}")

        weak_topic = self._top_weak_topic(weakness_context)
        if weak_topic:
            lines.append(f"- Revision focus after solving: {weak_topic}")

        lines.append("- Verify with dry-run on sample, then edge cases, then complexity.")
        return "\n".join(lines)

    def retrieve(
        self,
        question: str,
        problem_context: Optional[Dict[str, object]],
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: ErrorContext,
    ) -> List[RetrievedChunk]:
        query_tokens = set(self._tokenize(question))
        docs = self._build_docs(problem_context, weakness_context, error_context)

        scored: List[RetrievedChunk] = []
        for text, tags in docs:
            text_tokens = set(self._tokenize(text))
            overlap = len(query_tokens & text_tokens)
            tag_bonus = 2 if any(tag in query_tokens for tag in tags) else 0
            score = overlap + tag_bonus
            if score > 0:
                scored.append(RetrievedChunk(text=text, score=score))

        if not scored:
            return [
                RetrievedChunk(
                    text="Start with brute force to confirm correctness, then optimize using the right data structure.",
                    score=1,
                ),
                RetrievedChunk(
                    text="List invariants before coding: what each variable means at every step.",
                    score=1,
                ),
            ]

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:5]

    def _build_docs(
        self,
        problem_context: Optional[Dict[str, object]],
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: ErrorContext,
    ) -> List[Tuple[str, Sequence[str]]]:
        docs: List[Tuple[str, Sequence[str]]] = []

        if problem_context:
            topic = str(problem_context.get("topic") or "")
            pattern = str(problem_context.get("pattern") or "")
            docs.append(
                (
                    f"For topic {topic} and pattern {pattern}, define input-output contract and constraints before coding.",
                    [topic.lower(), pattern.lower()],
                )
            )

        for key, hint in _PATTERN_HINTS.items():
            docs.append((hint, self._tokenize(key)))

        if weakness_context:
            for item in weakness_context[:3]:
                topic = str(item.get("topic") or "")
                if topic:
                    docs.append(
                        (
                            f"You are weak in {topic}; solve one easy then one medium problem in this topic today.",
                            [topic.lower()],
                        )
                    )

        for item in self._normalize_errors(error_context):
            err = item["error_type"]
            docs.append(
                (
                    _ERROR_HINTS.get(err, f"For {err}, add explicit checks and validate assumptions during dry run."),
                    [err],
                )
            )

        return docs

    def _top_error(self, error_context: ErrorContext) -> Optional[str]:
        normalized = self._normalize_errors(error_context)
        if not normalized:
            return None
        err = normalized[0]["error_type"]
        return _ERROR_HINTS.get(err, f"Common error: {err}. Add targeted checks.")

    @staticmethod
    def _normalize_errors(error_context: ErrorContext) -> List[Dict[str, object]]:
        if not error_context:
            return []

        if isinstance(error_context, dict):
            items = [
                {"error_type": str(key).lower(), "count": int(value)}
                for key, value in error_context.items()
                if key
            ]
            items.sort(key=lambda item: int(item.get("count", 0)), reverse=True)
            return items[:3]

        normalized: List[Dict[str, object]] = []
        for item in error_context[:3]:
            err = str(item.get("error_type") or "").lower()
            if not err:
                continue
            normalized.append({"error_type": err, "count": int(item.get("count") or 0)})
        return normalized

    @staticmethod
    def _top_weak_topic(weakness_context: Optional[List[Dict[str, object]]]) -> Optional[str]:
        if not weakness_context:
            return None
        topic = weakness_context[0].get("topic")
        return str(topic) if topic else None

    @staticmethod
    def _tokenize(text: object) -> List[str]:
        if text is None:
            return []
        return [tok.lower() for tok in _TOKEN_RE.findall(str(text))]
