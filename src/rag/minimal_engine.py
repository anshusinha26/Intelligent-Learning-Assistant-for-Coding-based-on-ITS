"""Pedagogical local RAG engine for ITS coding guidance."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Sequence, Tuple, Union


_TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_DEF_LINE_RE = re.compile(r"^\s*def\s+[a-zA-Z_]\w*\s*\(.*$", re.MULTILINE)


_PATTERN_NUDGES: Dict[str, str] = {
    "complement lookup": "Look for what missing value each element needs to complete the target.",
    "membership test": "Track seen values and ask whether current value violates uniqueness.",
    "character histogram": "Compare frequency behavior instead of positional behavior.",
    "canonical representation": "Normalize each item into one canonical key before grouping.",
    "two pass prefix-suffix": "Think about contribution from left side and right side independently.",
    "sort + two pointers": "Use ordering to shrink search space from both ends.",
    "monotonic stack": "Maintain an order invariant so each index is processed once in/out.",
    "binary search on answer": "Check feasibility for a candidate answer and move bounds.",
    "topological ordering": "Model dependencies and process nodes with no remaining prerequisites.",
    "2d tabulation": "Define state dimensions first, then transition in a valid dependency order.",
    "fibonacci dp": "Memoize repeated subproblems or tabulate from smallest base states.",
}


_ERROR_HINTS: Dict[str, str] = {
    "off-by-one": "Re-check inclusive/exclusive bounds for loop or pointer updates.",
    "edge-case": "Run empty, single-item, duplicates, and max-boundary cases explicitly.",
    "logic-error": "State your invariant in one line and verify it after each update.",
    "time-limit": "Reduce quadratic scans by precomputation, hashing, or monotonic structure.",
    "timeout": "Reduce quadratic scans by precomputation, hashing, or monotonic structure.",
    "runtime-error": "Audit null/empty accesses and integer-boundary assumptions first.",
    "compilation-error": "Validate function signature and return type before deeper debugging.",
}


_SOLUTION_TRIGGERS = (
    "full solution",
    "complete solution",
    "full code",
    "complete code",
    "give code",
    "show code",
    "reference solution",
    "final code",
    "write the code",
)


_HINT_LEVEL_1_TRIGGERS = ("hint 1", "level 1", "first hint", "gentle hint", "nudge")
_HINT_LEVEL_2_TRIGGERS = ("hint 2", "level 2", "second hint", "intuition", "which algorithm")
_HINT_LEVEL_3_TRIGGERS = ("hint 3", "level 3", "third hint", "full approach", "walkthrough")


_GENERIC_SNIPPETS = (
    "start with brute force",
    "list invariants before coding",
)


ErrorContext = Optional[Union[List[Dict[str, object]], Dict[str, int]]]


@dataclass
class RetrievedChunk:
    text: str
    score: int
    chunk_type: str


@dataclass
class TutorResponse:
    answer: str
    mode: str
    hint_level: int
    code_included: bool
    progression_blocked: bool


class MinimalRAGEngine:
    def answer(
        self,
        question: str,
        problem_context: Optional[Dict[str, object]] = None,
        weakness_context: Optional[List[Dict[str, object]]] = None,
        error_context: ErrorContext = None,
        rag_chunks: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        response = self.tutor_response(
            question=question,
            problem_context=problem_context,
            weakness_context=weakness_context,
            error_context=error_context,
            rag_chunks=rag_chunks,
            hint_level_requested=None,
            want_full_solution=False,
            allow_full_solution=False,
            enforce_hint_progression=True,
            thread_progress_level=0,
            learner_profile=None,
            recent_attempts=None,
            revision_context=None,
            problem_attempt_context=None,
        )
        return response.answer

    def tutor_response(
        self,
        question: str,
        problem_context: Optional[Dict[str, object]],
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: ErrorContext,
        rag_chunks: Optional[List[Dict[str, str]]],
        hint_level_requested: Optional[int],
        want_full_solution: bool,
        allow_full_solution: bool,
        enforce_hint_progression: bool,
        thread_progress_level: int,
        learner_profile: Optional[Dict[str, object]],
        recent_attempts: Optional[List[Dict[str, object]]],
        revision_context: Optional[Dict[str, object]],
        problem_attempt_context: Optional[Dict[str, object]],
    ) -> TutorResponse:
        normalized_question = (question or "").strip()
        inferred_level = self._infer_hint_level(normalized_question)
        requested_level = hint_level_requested or inferred_level or 1
        requested_level = max(1, min(3, requested_level))
        explicit_solution = want_full_solution or self._wants_solution(normalized_question)

        if explicit_solution or (allow_full_solution and requested_level >= 3):
            answer = self._full_solution_response(problem_context)
            return TutorResponse(
                answer=answer,
                mode="full_solution",
                hint_level=3,
                code_included=self._contains_code(answer),
                progression_blocked=False,
            )

        progression_blocked = False
        effective_level = requested_level
        if not explicit_solution and enforce_hint_progression:
            if requested_level == 3 and thread_progress_level < 2:
                effective_level = max(1, thread_progress_level + 1)
                progression_blocked = True

        chunks = self.retrieve(
            question=normalized_question,
            problem_context=problem_context,
            weakness_context=weakness_context,
            error_context=error_context,
            rag_chunks=rag_chunks,
            hint_level=effective_level,
        )
        answer = self._compose_hint_response(
            question=normalized_question,
            hint_level=effective_level,
            progression_blocked=progression_blocked,
            chunks=chunks,
            problem_context=problem_context,
            weakness_context=weakness_context,
            error_context=error_context,
            learner_profile=learner_profile,
            recent_attempts=recent_attempts,
            revision_context=revision_context,
            problem_attempt_context=problem_attempt_context,
        )
        answer = self._strip_code(answer)
        return TutorResponse(
            answer=answer,
            mode=f"hint_level_{effective_level}",
            hint_level=effective_level,
            code_included=False,
            progression_blocked=progression_blocked,
        )

    def retrieve(
        self,
        question: str,
        problem_context: Optional[Dict[str, object]],
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: ErrorContext,
        rag_chunks: Optional[List[Dict[str, str]]],
        hint_level: int,
    ) -> List[RetrievedChunk]:
        query_tokens = set(self._tokenize(question))
        docs = self._build_docs(problem_context, weakness_context, error_context, rag_chunks)

        scored: List[RetrievedChunk] = []
        for text, tags, chunk_type, base_priority in docs:
            text_tokens = set(self._tokenize(text))
            overlap = len(query_tokens & text_tokens)
            if not overlap and base_priority <= 2:
                continue
            tag_bonus = 2 if any(tag in query_tokens for tag in tags if tag) else 0
            type_bonus = self._type_bonus(chunk_type, hint_level, query_tokens)
            score = overlap * 4 + tag_bonus + base_priority + type_bonus
            if score > 0:
                scored.append(
                    RetrievedChunk(
                        text=text,
                        score=score,
                        chunk_type=chunk_type,
                    )
                )

        if not scored:
            return [
                RetrievedChunk(
                    text="Restate the input-output contract in your own words before choosing a strategy.",
                    score=1,
                    chunk_type="learning_objectives",
                ),
                RetrievedChunk(
                    text="Identify one invariant that must remain true after each iteration.",
                    score=1,
                    chunk_type="learning_objectives",
                ),
            ]

        scored.sort(key=lambda item: item.score, reverse=True)
        unique: List[RetrievedChunk] = []
        seen = set()
        for item in scored:
            key = item.text.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
            if len(unique) >= 8:
                break
        return unique

    def _build_docs(
        self,
        problem_context: Optional[Dict[str, object]],
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: ErrorContext,
        rag_chunks: Optional[List[Dict[str, str]]],
    ) -> List[Tuple[str, Sequence[str], str, int]]:
        docs: List[Tuple[str, Sequence[str], str, int]] = []

        if problem_context:
            topic = str(problem_context.get("topic") or "")
            pattern = str(problem_context.get("pattern") or "").strip().lower()
            title = str(problem_context.get("title") or "current problem")
            docs.append(
                (
                    f"Learning objective for {title}: map constraints to a valid strategy before coding.",
                    [topic.lower(), pattern],
                    "learning_objectives",
                    8,
                )
            )
            if pattern:
                nudge = _PATTERN_NUDGES.get(pattern)
                if nudge:
                    docs.append((nudge, [pattern], "hints", 7))

            related = problem_context.get("related_problems") or []
            if isinstance(related, list) and related:
                docs.append(
                    (
                        "Related problems to reinforce transfer: " + ", ".join(str(item) for item in related[:4]),
                        [topic.lower()],
                        "related",
                        5,
                    )
                )

        if weakness_context:
            for item in weakness_context[:3]:
                topic = str(item.get("topic") or "")
                if not topic:
                    continue
                mastery = item.get("mastery_score")
                rate = item.get("success_rate")
                docs.append(
                    (
                        f"Weak area: {topic}. Reinforce this topic with one easier warm-up before this problem. "
                        f"Current mastery={mastery}, success_rate={rate}%.",
                        [topic.lower()],
                        "learning_objectives",
                        9,
                    )
                )

        for item in self._normalize_errors(error_context):
            err = item["error_type"]
            docs.append(
                (
                    _ERROR_HINTS.get(err, f"Recent recurring error: {err}. Add a targeted check before final submit."),
                    [err],
                    "common_mistakes",
                    8,
                )
            )

        if rag_chunks:
            for chunk in rag_chunks:
                chunk_type = str(chunk.get("chunk_type") or "").strip().lower()
                chunk_text = str(chunk.get("chunk_text") or "").strip()
                if not chunk_text:
                    continue
                if any(snippet in chunk_text.lower() for snippet in _GENERIC_SNIPPETS):
                    continue
                base_priority = {
                    "learning_objectives": 10,
                    "common_mistakes": 9,
                    "editorial": 8,
                    "hints": 7,
                    "related": 6,
                    "statement": 3,
                }.get(chunk_type, 4)
                docs.append((chunk_text, [chunk_type], chunk_type or "rag", base_priority))

        return docs

    @staticmethod
    def _type_bonus(chunk_type: str, hint_level: int, query_tokens: Sequence[str]) -> int:
        if hint_level <= 1:
            level_priority = {
                "learning_objectives": 8,
                "common_mistakes": 7,
                "hints": 6,
                "editorial": 3,
                "related": 3,
                "statement": 1,
            }
        elif hint_level == 2:
            level_priority = {
                "common_mistakes": 7,
                "editorial": 8,
                "hints": 7,
                "learning_objectives": 6,
                "related": 4,
                "statement": 1,
            }
        else:
            level_priority = {
                "editorial": 10,
                "common_mistakes": 8,
                "hints": 7,
                "learning_objectives": 6,
                "related": 5,
                "statement": 2,
            }

        bonus = level_priority.get(chunk_type, 2)
        tokens = set(query_tokens)
        if "complexity" in tokens and chunk_type == "editorial":
            bonus += 2
        if "edge" in tokens and chunk_type == "common_mistakes":
            bonus += 2
        return bonus

    def _compose_hint_response(
        self,
        question: str,
        hint_level: int,
        progression_blocked: bool,
        chunks: List[RetrievedChunk],
        problem_context: Optional[Dict[str, object]],
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: ErrorContext,
        learner_profile: Optional[Dict[str, object]],
        recent_attempts: Optional[List[Dict[str, object]]],
        revision_context: Optional[Dict[str, object]],
        problem_attempt_context: Optional[Dict[str, object]],
    ) -> str:
        title = str((problem_context or {}).get("title") or "this problem")
        topic = str((problem_context or {}).get("topic") or "this topic")
        pattern = str((problem_context or {}).get("pattern") or "")
        lines: List[str] = []

        if hint_level == 1:
            lines.append(f"Hint Level 1 - Gentle Nudge for {title}")
            lines.append("- Goal: clarify the task and identify one key observation.")
        elif hint_level == 2:
            lines.append(f"Hint Level 2 - Algorithm Direction for {title}")
            lines.append("- Goal: choose the right approach and data structure.")
        else:
            lines.append(f"Hint Level 3 - Full Approach (No Code) for {title}")
            lines.append("- Goal: walk through the complete algorithm before implementation.")

        if progression_blocked:
            lines.append("- Progression guard: let's unlock hints step by step to preserve learning.")

        personalization = self._personalization_lines(
            weakness_context=weakness_context,
            error_context=error_context,
            learner_profile=learner_profile,
            recent_attempts=recent_attempts,
            revision_context=revision_context,
            problem_attempt_context=problem_attempt_context,
        )
        if personalization:
            lines.append("- Personalized for you:")
            for item in personalization:
                lines.append(f"  - {item}")

        support_points = self._pick_support_points(chunks, hint_level)

        if hint_level == 1:
            key_observation = (
                _PATTERN_NUDGES.get(pattern.lower(), "")
                if pattern
                else ""
            ) or "Focus on the relation between current state and target condition before writing loops."
            lines.append(f"- Key observation: {self._truncate_sentence(key_observation, 170)}")
            if support_points:
                lines.append(f"- Clarify first: {self._truncate_sentence(support_points[0], 180)}")
            lines.append("- Next step: write 2-3 tiny examples and state what must stay true at each step.")

        elif hint_level == 2:
            strategy = self._derive_strategy(topic, pattern, support_points)
            lines.append(f"- Suggested strategy family: {strategy}.")
            if support_points:
                lines.append(f"- Useful data-structure intuition: {self._truncate_sentence(support_points[0], 190)}")
            if len(support_points) > 1:
                lines.append(f"- Common pitfall to avoid: {self._truncate_sentence(support_points[1], 190)}")
            lines.append("- Stop before coding: confirm complexity target and invariant in one line.")

        else:
            steps = self._derive_steps(topic, pattern, support_points)
            lines.append("- Algorithm walkthrough:")
            for index, step in enumerate(steps[:4], start=1):
                lines.append(f"  {index}) {self._truncate_sentence(step, 210)}")
            complexity_line = self._complexity_line(problem_context, chunks)
            if complexity_line:
                lines.append(f"- Complexity target: {complexity_line}")
            lines.append("- Implementation plan: convert each step into one clean block in solve(...).")

        lines.append("- Validation: dry-run sample, then edge cases, then constraint boundary.")
        return "\n".join(lines)

    @staticmethod
    def _derive_strategy(topic: str, pattern: str, support_points: List[str]) -> str:
        if pattern:
            return pattern
        if support_points:
            return "constraint-driven approach based on retrieved guidance"
        return f"{topic} core pattern"

    @staticmethod
    def _derive_steps(topic: str, pattern: str, support_points: List[str]) -> List[str]:
        steps: List[str] = []
        if pattern:
            steps.append(f"Model the problem using pattern: {pattern}.")
        steps.append("Define state/invariant and data structure before loops or recursion.")
        if support_points:
            steps.append(support_points[0])
        steps.append("Execute transitions consistently and handle boundary cases explicitly.")
        if len(support_points) > 1:
            steps.append(support_points[1])
        else:
            steps.append(f"Finalize with complexity check appropriate for {topic}.")
        return steps

    @staticmethod
    def _complexity_line(problem_context: Optional[Dict[str, object]], chunks: List[RetrievedChunk]) -> str:
        tc = str((problem_context or {}).get("time_complexity") or "").strip()
        sc = str((problem_context or {}).get("space_complexity") or "").strip()
        if tc and sc:
            return f"time {tc}, space {sc}"
        for item in chunks:
            text = item.text.lower()
            if "o(" in text and "time" in text:
                return item.text
        return ""

    @staticmethod
    def _pick_support_points(chunks: List[RetrievedChunk], hint_level: int) -> List[str]:
        points: List[str] = []
        for item in chunks:
            text = item.text.strip()
            if not text:
                continue
            lowered = text.lower()
            if "def solve" in lowered or "```" in lowered:
                continue
            if hint_level == 1 and item.chunk_type == "statement":
                continue
            points.append(text)
            if len(points) >= 3:
                break
        return points

    def _full_solution_response(self, problem_context: Optional[Dict[str, object]]) -> str:
        title = str((problem_context or {}).get("title") or "Current Problem")
        solution_code = str((problem_context or {}).get("reference_solution_code") or "").strip()
        time_complexity = str((problem_context or {}).get("time_complexity") or "").strip()
        space_complexity = str((problem_context or {}).get("space_complexity") or "").strip()
        if solution_code:
            lines = [f"Full reference solution for {title}:"]
            lines.append("```python")
            lines.append(solution_code)
            lines.append("```")
            if time_complexity or space_complexity:
                lines.append(f"Complexity: time {time_complexity or 'N/A'}, space {space_complexity or 'N/A'}.")
            return "\n".join(lines)

        return (
            f"Full solution requested for {title}, but a stored reference solution is unavailable.\n"
            "```python\n"
            "def solve(*args):\n"
            "    raise NotImplementedError('Reference solution unavailable in local context')\n"
            "```"
        )

    @staticmethod
    def _personalization_lines(
        weakness_context: Optional[List[Dict[str, object]]],
        error_context: ErrorContext,
        learner_profile: Optional[Dict[str, object]],
        recent_attempts: Optional[List[Dict[str, object]]],
        revision_context: Optional[Dict[str, object]],
        problem_attempt_context: Optional[Dict[str, object]],
    ) -> List[str]:
        lines: List[str] = []
        if learner_profile:
            target_level = learner_profile.get("target_level")
            if target_level:
                lines.append(f"Target level: {target_level}.")

        if weakness_context:
            top = weakness_context[0]
            topic = top.get("topic")
            mastery = top.get("mastery_score")
            if topic is not None and mastery is not None:
                lines.append(f"Weak area focus: {topic} (mastery {float(mastery):.0%}).")

        normalized_errors = MinimalRAGEngine._normalize_errors(error_context)
        if normalized_errors:
            top_error = normalized_errors[0]
            lines.append(
                f"Recent recurring mistake: {top_error['error_type']} ({top_error.get('count', 0)} times)."
            )

        if problem_attempt_context:
            attempts = int(problem_attempt_context.get("attempts", 0))
            last_verdict = problem_attempt_context.get("last_verdict")
            if attempts > 0:
                lines.append(f"You have attempted this problem {attempts} time(s), last verdict: {last_verdict}.")

        if revision_context:
            due = int(revision_context.get("due_revisions", 0))
            if due > 0:
                lines.append(f"You have {due} due revision task(s); keep this hint concise and actionable.")

        if recent_attempts:
            last = recent_attempts[0]
            problem = last.get("problem_id")
            verdict = last.get("verdict")
            if problem and verdict:
                lines.append(f"Most recent attempt: {problem} -> {verdict}.")
        return lines[:4]

    @staticmethod
    def _infer_hint_level(question: str) -> Optional[int]:
        q = question.lower()
        if any(token in q for token in _HINT_LEVEL_3_TRIGGERS):
            return 3
        if any(token in q for token in _HINT_LEVEL_2_TRIGGERS):
            return 2
        if any(token in q for token in _HINT_LEVEL_1_TRIGGERS):
            return 1
        return None

    @staticmethod
    def _wants_solution(question: str) -> bool:
        q = question.lower()
        return any(token in q for token in _SOLUTION_TRIGGERS)

    @staticmethod
    def _contains_code(text: str) -> bool:
        if "```" in text:
            return True
        return bool(_DEF_LINE_RE.search(text))

    @staticmethod
    def _strip_code(text: str) -> str:
        no_blocks = _CODE_BLOCK_RE.sub("", text)
        no_defs = _DEF_LINE_RE.sub("", no_blocks)
        return re.sub(r"\n{3,}", "\n\n", no_defs).strip()

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
    def _tokenize(text: object) -> List[str]:
        if text is None:
            return []
        return [tok.lower() for tok in _TOKEN_RE.findall(str(text))]

    @staticmethod
    def _truncate_sentence(text: str, limit: int) -> str:
        clean = " ".join(str(text).split())
        if len(clean) <= limit:
            return clean
        return clean[: limit - 3].rstrip() + "..."
