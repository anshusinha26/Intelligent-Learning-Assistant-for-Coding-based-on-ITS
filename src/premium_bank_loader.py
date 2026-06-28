"""Premium problem-bank loading and template enforcement."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from src.database import Database
from src.problem_bank import PREMIUM_DATASET_TIER, RAG_CHUNK_TYPES, RECOMMENDATION_EDGE_TYPES


REQUIRED_ROOT_FIELDS = {
    "problem_id",
    "title",
    "topic",
    "subtopic",
    "pattern",
    "difficulty",
    "metadata",
    "educational_assets",
    "hints",
    "reference_solution",
    "starter_code",
    "tests",
    "recommendation_graph",
    "learning_objectives",
    "common_mistakes",
    "prerequisites",
    "related_problems",
    "rag_assets",
    "version",
}

ALLOWED_DIFFICULTIES = {"Easy", "Medium", "Hard"}


@dataclass
class PremiumLoadResult:
    loaded_count: int
    skipped_count: int
    relationship_count: int
    rag_chunk_count: int


def _read_problem_bank(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        problems = payload.get("problems")
        if isinstance(problems, list):
            return problems
    raise ValueError(f"Invalid premium problem bank structure in {path}")


def _as_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _require_string(problem_id: str, obj: Dict[str, object], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{problem_id}: missing required string field '{key}'")
    return value.strip()


def _require_list(problem_id: str, obj: Dict[str, object], key: str) -> List[object]:
    value = obj.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{problem_id}: missing required list field '{key}'")
    return value


def _validate_problem_shape(problem: Dict[str, object]) -> None:
    missing = sorted(REQUIRED_ROOT_FIELDS - set(problem.keys()))
    problem_id = str(problem.get("problem_id") or "unknown")
    if missing:
        raise ValueError(f"{problem_id}: missing required fields: {', '.join(missing)}")

    difficulty = _require_string(problem_id, problem, "difficulty")
    if difficulty not in ALLOWED_DIFFICULTIES:
        raise ValueError(f"{problem_id}: invalid difficulty '{difficulty}'")

    educational = problem.get("educational_assets")
    if not isinstance(educational, dict):
        raise ValueError(f"{problem_id}: educational_assets must be object")
    for key in ("statement_md", "constraints_md", "examples_md", "editorial_md"):
        _require_string(problem_id, educational, key)

    reference_solution = problem.get("reference_solution")
    if not isinstance(reference_solution, dict):
        raise ValueError(f"{problem_id}: reference_solution must be object")
    for key in ("language", "code", "time_complexity", "space_complexity"):
        _require_string(problem_id, reference_solution, key)

    starter_code = problem.get("starter_code")
    if not isinstance(starter_code, dict):
        raise ValueError(f"{problem_id}: starter_code must be object")
    for key in ("language", "function_name", "code"):
        _require_string(problem_id, starter_code, key)

    tests = problem.get("tests")
    if not isinstance(tests, dict):
        raise ValueError(f"{problem_id}: tests must be object")
    for key in ("visible", "hidden"):
        test_cases = tests.get(key)
        if not isinstance(test_cases, list) or not test_cases:
            raise ValueError(f"{problem_id}: tests.{key} must contain at least one case")

    hints = _require_list(problem_id, problem, "hints")
    for index, hint in enumerate(hints, start=1):
        if not isinstance(hint, dict):
            raise ValueError(f"{problem_id}: hint #{index} must be object")
        _require_string(problem_id, hint, "text_md")

    _require_list(problem_id, problem, "learning_objectives")
    _require_list(problem_id, problem, "common_mistakes")

    metadata = problem.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"{problem_id}: metadata must be object")

    recommendation_graph = problem.get("recommendation_graph")
    if not isinstance(recommendation_graph, dict):
        raise ValueError(f"{problem_id}: recommendation_graph must be object")
    for edge_type in ("prerequisite", "alternative", "follow_up", "review", "recovery"):
        values = recommendation_graph.get(edge_type)
        if not isinstance(values, list):
            raise ValueError(f"{problem_id}: recommendation_graph.{edge_type} must be list")

    rag_assets = problem.get("rag_assets")
    if not isinstance(rag_assets, dict):
        raise ValueError(f"{problem_id}: rag_assets must be object")
    for key in (
        "statement_chunks",
        "editorial_chunks",
        "hints_chunks",
        "common_mistakes_chunks",
        "learning_objectives_chunks",
    ):
        values = rag_assets.get(key)
        if not isinstance(values, list):
            raise ValueError(f"{problem_id}: rag_assets.{key} must be list")


def _build_embedding(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).digest()[:16]
    values = []
    for byte in digest:
        values.append(round((byte / 255.0) * 2 - 1, 6))
    return _as_json(values)


def _upsert_problem_core(cursor, problem: Dict[str, object]) -> None:
    problem_id = _require_string(problem["problem_id"], problem, "problem_id")
    title = _require_string(problem_id, problem, "title")
    topic = _require_string(problem_id, problem, "topic")
    pattern = _require_string(problem_id, problem, "pattern")
    difficulty = _require_string(problem_id, problem, "difficulty")
    educational = problem["educational_assets"]
    starter = problem["starter_code"]
    tests = problem["tests"]
    source = str(problem.get("metadata", {}).get("source") or "premium")
    tags = ",".join(problem.get("metadata", {}).get("tags") or [])
    version = int(problem.get("version") or 1)

    cursor.execute(
        """
        INSERT INTO problems (
            problem_id, title, topic, pattern, difficulty, tags, description,
            constraints, examples, source_url, function_name, starter_code, test_cases,
            dataset_tier, is_active, curriculum_version, time_complexity, space_complexity,
            metadata_json, learning_objectives_json, common_mistakes_json, recommendation_graph_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(problem_id)
        DO UPDATE SET
            title = excluded.title,
            topic = excluded.topic,
            pattern = excluded.pattern,
            difficulty = excluded.difficulty,
            tags = excluded.tags,
            description = excluded.description,
            constraints = excluded.constraints,
            examples = excluded.examples,
            source_url = excluded.source_url,
            function_name = excluded.function_name,
            starter_code = excluded.starter_code,
            test_cases = excluded.test_cases,
            dataset_tier = excluded.dataset_tier,
            is_active = excluded.is_active,
            curriculum_version = excluded.curriculum_version,
            time_complexity = excluded.time_complexity,
            space_complexity = excluded.space_complexity,
            metadata_json = excluded.metadata_json,
            learning_objectives_json = excluded.learning_objectives_json,
            common_mistakes_json = excluded.common_mistakes_json,
            recommendation_graph_json = excluded.recommendation_graph_json
    """,
        (
            problem_id,
            title,
            topic,
            pattern,
            difficulty,
            tags,
            educational["statement_md"],
            educational["constraints_md"],
            educational["examples_md"],
            source,
            starter["function_name"],
            starter["code"],
            _as_json(tests["visible"]),
            PREMIUM_DATASET_TIER,
            1,
            version,
            problem["reference_solution"]["time_complexity"],
            problem["reference_solution"]["space_complexity"],
            _as_json(problem["metadata"]),
            _as_json(problem["learning_objectives"]),
            _as_json(problem["common_mistakes"]),
            _as_json(problem["recommendation_graph"]),
        ),
    )

    cursor.execute(
        "UPDATE premium_problem_versions SET is_current = 0 WHERE problem_id = ?",
        (problem_id,),
    )
    cursor.execute(
        """
        INSERT INTO premium_problem_versions (
            problem_id, version, statement_md, constraints_md, examples_md, editorial_md,
            reference_solution, starter_code, time_complexity, space_complexity, metadata_json,
            learning_objectives_json, common_mistakes_json, recommendation_graph_json, is_current
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(problem_id, version)
        DO UPDATE SET
            statement_md = excluded.statement_md,
            constraints_md = excluded.constraints_md,
            examples_md = excluded.examples_md,
            editorial_md = excluded.editorial_md,
            reference_solution = excluded.reference_solution,
            starter_code = excluded.starter_code,
            time_complexity = excluded.time_complexity,
            space_complexity = excluded.space_complexity,
            metadata_json = excluded.metadata_json,
            learning_objectives_json = excluded.learning_objectives_json,
            common_mistakes_json = excluded.common_mistakes_json,
            recommendation_graph_json = excluded.recommendation_graph_json,
            is_current = 1
    """,
        (
            problem_id,
            version,
            educational["statement_md"],
            educational["constraints_md"],
            educational["examples_md"],
            educational["editorial_md"],
            _as_json(problem["reference_solution"]),
            starter["code"],
            problem["reference_solution"]["time_complexity"],
            problem["reference_solution"]["space_complexity"],
            _as_json(problem["metadata"]),
            _as_json(problem["learning_objectives"]),
            _as_json(problem["common_mistakes"]),
            _as_json(problem["recommendation_graph"]),
        ),
    )

    cursor.execute(
        "DELETE FROM premium_problem_hints WHERE problem_id = ? AND version = ?",
        (problem_id, version),
    )
    for index, hint in enumerate(problem["hints"], start=1):
        order = int(hint.get("order") or index)
        cursor.execute(
            """
            INSERT INTO premium_problem_hints (problem_id, version, hint_order, hint_md)
            VALUES (?, ?, ?, ?)
        """,
            (problem_id, version, order, hint["text_md"].strip()),
        )

    cursor.execute(
        "DELETE FROM premium_problem_tests WHERE problem_id = ? AND version = ?",
        (problem_id, version),
    )
    for visibility in ("visible", "hidden"):
        for case in tests[visibility]:
            cursor.execute(
                """
                INSERT INTO premium_problem_tests (
                    problem_id, version, visibility, input_json, expected_json, explanation, weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    problem_id,
                    version,
                    visibility,
                    _as_json(case.get("input")),
                    _as_json(case.get("expected")),
                    str(case.get("explanation") or "").strip() or None,
                    float(case.get("weight") or 1.0),
                ),
            )


def _iter_relationship_edges(problem: Dict[str, object]) -> Iterable[Tuple[str, str, float]]:
    graph = problem["recommendation_graph"]
    for edge_type in RECOMMENDATION_EDGE_TYPES:
        for related_problem_id in graph.get(edge_type, []):
            if isinstance(related_problem_id, str) and related_problem_id.strip():
                yield edge_type, related_problem_id.strip(), 1.0
    for related_problem_id in problem.get("related_problems", []):
        if isinstance(related_problem_id, str) and related_problem_id.strip():
            yield "related", related_problem_id.strip(), 1.0


def _upsert_relationships(cursor, problems: List[Dict[str, object]]) -> int:
    cursor.execute("DELETE FROM premium_problem_relationships")
    existing_ids = {row["problem_id"] for row in cursor.execute("SELECT problem_id FROM problems")}
    inserted = 0
    for problem in problems:
        source_id = problem["problem_id"]
        for edge_type, target_id, weight in _iter_relationship_edges(problem):
            if source_id == target_id:
                continue
            if target_id not in existing_ids:
                continue
            cursor.execute(
                """
                INSERT OR IGNORE INTO premium_problem_relationships (
                    problem_id, related_problem_id, edge_type, weight, metadata_json
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (source_id, target_id, edge_type, weight, _as_json({"source": "premium_problem_bank"})),
            )
            inserted += cursor.rowcount
    return inserted


def _extract_rag_chunks(problem: Dict[str, object]) -> Dict[str, List[str]]:
    rag_assets = problem["rag_assets"]
    educational = problem["educational_assets"]
    hints = problem["hints"]
    objectives = problem["learning_objectives"]
    mistakes = problem["common_mistakes"]
    fallback = {
        "statement": [educational["statement_md"]],
        "editorial": [educational["editorial_md"]],
        "hints": [hint["text_md"] for hint in hints],
        "common_mistakes": [str(item) for item in mistakes],
        "learning_objectives": [str(item) for item in objectives],
    }
    mapped = {
        "statement": rag_assets.get("statement_chunks", []),
        "editorial": rag_assets.get("editorial_chunks", []),
        "hints": rag_assets.get("hints_chunks", []),
        "common_mistakes": rag_assets.get("common_mistakes_chunks", []),
        "learning_objectives": rag_assets.get("learning_objectives_chunks", []),
    }
    out: Dict[str, List[str]] = {}
    for chunk_type in RAG_CHUNK_TYPES:
        values = [str(item).strip() for item in mapped.get(chunk_type, []) if str(item).strip()]
        out[chunk_type] = values or fallback[chunk_type]
    return out


def _upsert_rag_chunks(cursor, problems: List[Dict[str, object]]) -> int:
    count = 0
    cursor.execute("DELETE FROM premium_problem_rag_chunks")
    for problem in problems:
        version = int(problem.get("version") or 1)
        chunks = _extract_rag_chunks(problem)
        for chunk_type, values in chunks.items():
            for chunk in values:
                cursor.execute(
                    """
                    INSERT INTO premium_problem_rag_chunks (
                        problem_id, version, chunk_type, chunk_text, embedding_model, embedding_vector, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        problem["problem_id"],
                        version,
                        chunk_type,
                        chunk,
                        "sha256-lite",
                        _build_embedding(chunk),
                        hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                    ),
                )
                count += 1
    return count


def sync_premium_problem_bank(db: Database, bank_path: Path) -> PremiumLoadResult:
    problems = _read_problem_bank(bank_path)
    for problem in problems:
        if not isinstance(problem, dict):
            raise ValueError("Each premium problem must be an object")
        _validate_problem_shape(problem)

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE problems SET is_active = 0 WHERE dataset_tier = ?",
        (PREMIUM_DATASET_TIER,),
    )

    loaded = 0
    for problem in problems:
        _upsert_problem_core(cursor, problem)
        loaded += 1

    relationship_count = _upsert_relationships(cursor, problems)
    rag_chunk_count = _upsert_rag_chunks(cursor, problems)

    conn.commit()
    conn.close()
    return PremiumLoadResult(
        loaded_count=loaded,
        skipped_count=0,
        relationship_count=relationship_count,
        rag_chunk_count=rag_chunk_count,
    )
