import csv
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.problem_bank import PREMIUM_DATASET_TIER


ALLOWED_DIFFICULTIES = {"Easy", "Medium", "Hard"}
KNOWN_COMPANY_TAGS = {
    "google",
    "amazon",
    "microsoft",
    "meta",
    "apple",
    "adobe",
    "uber",
    "netflix",
    "atlassian",
    "oracle",
    "salesforce",
    "paypal",
    "linkedin",
    "tcs",
    "walmart",
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    normalized = normalized.lower().replace("&", "and")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def safe_json_loads(value: Optional[str]) -> Tuple[Optional[object], Optional[str]]:
    if value is None:
        return None, None
    text = value.strip()
    if not text:
        return None, None
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, str(exc)


def extract_company_tags(tags: Optional[str], metadata_json: Optional[str]) -> List[str]:
    matches = set()
    if tags:
        for tag in tags.split(","):
            clean = tag.strip().lower()
            if clean in KNOWN_COMPANY_TAGS:
                matches.add(clean)

    metadata, _ = safe_json_loads(metadata_json)
    if isinstance(metadata, dict):
        for tag in metadata.get("company_tags", []):
            clean = str(tag).strip().lower()
            if clean in KNOWN_COMPANY_TAGS:
                matches.add(clean)
    return sorted(matches)


def _load_active_premium_rows(db_path: Path) -> List[Dict[str, object]]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                p.problem_id,
                p.title,
                p.topic,
                p.pattern,
                p.difficulty,
                p.tags,
                p.description,
                p.constraints,
                p.examples,
                p.source_url,
                p.function_name,
                p.starter_code,
                p.test_cases,
                p.curriculum_version,
                p.time_complexity,
                p.space_complexity,
                p.metadata_json,
                p.learning_objectives_json,
                p.common_mistakes_json,
                p.recommendation_graph_json,
                v.statement_md,
                v.constraints_md,
                v.examples_md,
                v.editorial_md,
                v.reference_solution,
                v.starter_code AS version_starter_code
            FROM problems p
            LEFT JOIN premium_problem_versions v
                ON v.problem_id = p.problem_id AND v.is_current = 1
            WHERE p.dataset_tier = ? AND p.is_active = 1
            ORDER BY p.problem_id
        """,
            (PREMIUM_DATASET_TIER,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        conn.close()
        return []
    conn.close()
    return rows


def _load_counts(db_path: Path, table: str, query: str) -> Dict[str, int]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        conn.close()
        return {}
    conn.close()
    return {row["problem_id"]: int(row["count"]) for row in rows}


def load_inventory(
    db_path: Path,
    csv_path: Path = Path(""),
    markdown_path: Path = Path(""),
) -> Tuple[List[Dict[str, object]], Dict[str, int]]:
    rows = _load_active_premium_rows(db_path)
    hint_counts = _load_counts(
        db_path,
        "premium_problem_hints",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_hints
        GROUP BY problem_id
    """,
    )
    visible_counts = _load_counts(
        db_path,
        "premium_problem_tests",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_tests
        WHERE visibility = 'visible'
        GROUP BY problem_id
    """,
    )
    hidden_counts = _load_counts(
        db_path,
        "premium_problem_tests",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_tests
        WHERE visibility = 'hidden'
        GROUP BY problem_id
    """,
    )
    relationship_counts = _load_counts(
        db_path,
        "premium_problem_relationships",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_relationships
        GROUP BY problem_id
    """,
    )
    rag_counts = _load_counts(
        db_path,
        "premium_problem_rag_chunks",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_rag_chunks
        GROUP BY problem_id
    """,
    )
    rag_statement_counts = _load_counts(
        db_path,
        "premium_problem_rag_chunks",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_rag_chunks
        WHERE chunk_type = 'statement'
        GROUP BY problem_id
    """,
    )
    rag_editorial_counts = _load_counts(
        db_path,
        "premium_problem_rag_chunks",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_rag_chunks
        WHERE chunk_type = 'editorial'
        GROUP BY problem_id
    """,
    )
    rag_hint_counts = _load_counts(
        db_path,
        "premium_problem_rag_chunks",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_rag_chunks
        WHERE chunk_type = 'hints'
        GROUP BY problem_id
    """,
    )
    rag_mistake_counts = _load_counts(
        db_path,
        "premium_problem_rag_chunks",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_rag_chunks
        WHERE chunk_type = 'common_mistakes'
        GROUP BY problem_id
    """,
    )
    rag_objective_counts = _load_counts(
        db_path,
        "premium_problem_rag_chunks",
        """
        SELECT problem_id, COUNT(*) AS count
        FROM premium_problem_rag_chunks
        WHERE chunk_type = 'learning_objectives'
        GROUP BY problem_id
    """,
    )

    inventory: List[Dict[str, object]] = []
    for row in rows:
        problem_id = str(row["problem_id"])
        metadata_obj, metadata_error = safe_json_loads(row.get("metadata_json"))
        learning_obj, learning_error = safe_json_loads(row.get("learning_objectives_json"))
        mistake_obj, mistake_error = safe_json_loads(row.get("common_mistakes_json"))
        graph_obj, graph_error = safe_json_loads(row.get("recommendation_graph_json"))
        visible_tests_obj, visible_tests_error = safe_json_loads(row.get("test_cases"))
        reference_solution_obj, reference_solution_error = safe_json_loads(row.get("reference_solution"))

        statement = (row.get("statement_md") or row.get("description") or "").strip()
        constraints = (row.get("constraints_md") or row.get("constraints") or "").strip()
        examples = (row.get("examples_md") or row.get("examples") or "").strip()
        editorial = (row.get("editorial_md") or "").strip()
        starter_code = (row.get("version_starter_code") or row.get("starter_code") or "").strip()
        reference_solution_code = (
            reference_solution_obj.get("code")
            if isinstance(reference_solution_obj, dict)
            else ""
        )

        inventory.append(
            {
                "id": problem_id,
                "problem_id": problem_id,
                "title": (row.get("title") or "").strip(),
                "slug": slugify(row.get("title") or problem_id),
                "topic": (row.get("topic") or "").strip(),
                "subtopic": (row.get("pattern") or "").strip() or "Unspecified",
                "difficulty": (row.get("difficulty") or "").strip(),
                "pattern": (row.get("pattern") or "").strip(),
                "company_tags": extract_company_tags(row.get("tags"), row.get("metadata_json")),
                "source": (row.get("source_url") or "premium").strip(),
                "source_url": (row.get("source_url") or "").strip(),
                "description": statement,
                "constraints": constraints,
                "examples": examples,
                "editorial": editorial,
                "starter_code": starter_code,
                "reference_solution_code": (reference_solution_code or "").strip(),
                "time_complexity": (row.get("time_complexity") or "").strip(),
                "space_complexity": (row.get("space_complexity") or "").strip(),
                "visible_test_count": int(visible_counts.get(problem_id, 0)),
                "hidden_test_count": int(hidden_counts.get(problem_id, 0)),
                "hint_count": int(hint_counts.get(problem_id, 0)),
                "relationship_count": int(relationship_counts.get(problem_id, 0)),
                "rag_chunk_count": int(rag_counts.get(problem_id, 0)),
                "rag_statement_count": int(rag_statement_counts.get(problem_id, 0)),
                "rag_editorial_count": int(rag_editorial_counts.get(problem_id, 0)),
                "rag_hints_count": int(rag_hint_counts.get(problem_id, 0)),
                "rag_common_mistakes_count": int(rag_mistake_counts.get(problem_id, 0)),
                "rag_learning_objectives_count": int(rag_objective_counts.get(problem_id, 0)),
                "metadata_json_error": metadata_error,
                "learning_objectives_json_error": learning_error,
                "common_mistakes_json_error": mistake_error,
                "recommendation_graph_json_error": graph_error,
                "visible_tests_json_error": visible_tests_error,
                "reference_solution_json_error": reference_solution_error,
                "metadata_present": isinstance(metadata_obj, dict),
                "learning_objectives_count": len(learning_obj) if isinstance(learning_obj, list) else 0,
                "common_mistakes_count": len(mistake_obj) if isinstance(mistake_obj, list) else 0,
                "recommendation_graph_present": isinstance(graph_obj, dict),
                "recommendation_graph": graph_obj if isinstance(graph_obj, dict) else {},
                "visible_tests_inline_count": len(visible_tests_obj) if isinstance(visible_tests_obj, list) else 0,
                "dataset_tier": PREMIUM_DATASET_TIER,
            }
        )

    stats = {
        "premium_active_total": len(inventory),
        "topics_total": len({item["topic"] for item in inventory if item["topic"]}),
        "patterns_total": len({item["pattern"] for item in inventory if item["pattern"]}),
    }
    return inventory, stats


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_inventory_csv(path: Path, inventory: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "problem_id",
        "title",
        "slug",
        "topic",
        "subtopic",
        "difficulty",
        "pattern",
        "source_url",
        "time_complexity",
        "space_complexity",
        "visible_test_count",
        "hidden_test_count",
        "hint_count",
        "relationship_count",
        "rag_chunk_count",
        "learning_objectives_count",
        "common_mistakes_count",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in inventory:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def markdown_link_scan(markdown_path: Path) -> Dict[str, object]:
    return {"links": [], "images": [], "broken_url_format": []}


def severity_exit_code(critical_count: int) -> int:
    return 1 if critical_count > 0 else 0
