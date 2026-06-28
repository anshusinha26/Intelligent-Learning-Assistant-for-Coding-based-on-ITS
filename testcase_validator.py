#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path

from scripts.phase3_common import write_json
from src.problem_bank import PREMIUM_DATASET_TIER


REQUIRED_CATEGORIES = [
    "minimum_input",
    "maximum_input",
    "negative_values",
    "duplicates",
    "sorted_input",
    "reverse_sorted",
    "empty_input",
    "single_element",
    "large_values",
    "randomized",
    "boundary_conditions",
]


def load_problem_tests(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT problem_id, title
        FROM problems
        WHERE dataset_tier = ? AND is_active = 1
        ORDER BY problem_id
    """,
        (PREMIUM_DATASET_TIER,),
    ).fetchall()

    out = []
    for row in rows:
        visible = cursor.execute(
            """
            SELECT input_json, expected_json, explanation
            FROM premium_problem_tests
            WHERE problem_id = ? AND visibility = 'visible'
            ORDER BY test_id
        """,
            (row["problem_id"],),
        ).fetchall()
        hidden = cursor.execute(
            """
            SELECT input_json, expected_json, explanation
            FROM premium_problem_tests
            WHERE problem_id = ? AND visibility = 'hidden'
            ORDER BY test_id
        """,
            (row["problem_id"],),
        ).fetchall()
        out.append(
            {
                "problem_id": row["problem_id"],
                "title": row["title"],
                "visible_tests": [dict(item) for item in visible],
                "hidden_tests": [dict(item) for item in hidden],
            }
        )
    conn.close()
    return out


def run_testcase_audit(db_path: Path, apply: bool):
    problems = load_problem_tests(db_path)
    issues = {"critical": [], "high": [], "medium": [], "low": []}
    generated = {}

    if not problems:
        issues["high"].append({"type": "empty_premium_problem_bank"})

    for problem in problems:
        pid = problem["problem_id"]
        visible = problem["visible_tests"]
        hidden = problem["hidden_tests"]
        if not visible:
            issues["critical"].append({"type": "missing_visible_tests", "problem_id": pid})
        if not hidden:
            issues["critical"].append({"type": "missing_hidden_tests", "problem_id": pid})
        if len(visible) < 3:
            issues["medium"].append(
                {"type": "insufficient_visible_tests", "problem_id": pid, "count": len(visible), "expected_min": 3}
            )
        if len(hidden) < 3:
            issues["medium"].append(
                {"type": "insufficient_hidden_tests", "problem_id": pid, "count": len(hidden), "expected_min": 3}
            )
        categories = set()
        for row in visible + hidden:
            explanation = str(row.get("explanation") or "").strip().lower()
            for category in REQUIRED_CATEGORIES:
                if category in explanation:
                    categories.add(category)
        missing_categories = sorted(set(REQUIRED_CATEGORIES) - categories)
        if missing_categories:
            issues["low"].append(
                {
                    "type": "missing_category_coverage_labels",
                    "problem_id": pid,
                    "missing_categories": missing_categories,
                }
            )
        generated[pid] = []

    return {
        "total_problems": len(problems),
        "problems_with_visible_tests": sum(1 for p in problems if p["visible_tests"]),
        "generated": generated,
        "generated_problem_count": 0,
        "category_coverage": {cat: 0 for cat in REQUIRED_CATEGORIES},
        "updated_count": 0,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 testcase validator.")
    parser.add_argument("--db-path", default="data/coding_assistant.db")
    parser.add_argument("--output-dir", default="reports/phase3")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_testcase_audit(Path(args.db_path), apply=args.apply)
    report = {
        "summary": {
            "total_problems": result["total_problems"],
            "problems_with_visible_tests": result["problems_with_visible_tests"],
            "generated_problem_count": result["generated_problem_count"],
            "critical_issues": len(result["issues"]["critical"]),
            "high_issues": len(result["issues"]["high"]),
            "medium_issues": len(result["issues"]["medium"]),
            "low_issues": len(result["issues"]["low"]),
            "updated_count": result["updated_count"],
        },
        "issues": result["issues"],
        "category_coverage": result["category_coverage"],
        "generated_testcases": result["generated"],
    }
    report_path = output_dir / "testcase_validation_report.json"
    generated_path = output_dir / "generated_testcases.json"
    write_json(report_path, report)
    write_json(generated_path, result["generated"])
    print(f"Report written: {report_path}")
    print(f"Generated cases written: {generated_path}")
    print(report["summary"])
    return 1 if report["summary"]["critical_issues"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
