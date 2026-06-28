#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path

from scripts.phase3_common import write_json
from src.judge import JudgeService
from src.problem_bank import PREMIUM_DATASET_TIER


NEGATIVE_CASES = {
    "wrong_answer": "def solve(*args):\n    return None\n",
    "runtime_error": "def solve(*args):\n    raise RuntimeError('boom')\n",
    "time_limit": "def solve(*args):\n    while True:\n        pass\n",
    "compilation_error": "def solve(\n    return 1\n",
}


def _load_tests(cursor, problem_id: str, visibility: str):
    rows = cursor.execute(
        """
        SELECT input_json, expected_json
        FROM premium_problem_tests
        WHERE problem_id = ? AND visibility = ?
        ORDER BY test_id
    """,
        (problem_id, visibility),
    ).fetchall()
    tests = []
    for row in rows:
        try:
            tests.append({"input": json.loads(row["input_json"]), "expected": json.loads(row["expected_json"])})
        except json.JSONDecodeError:
            return [], "invalid_test_json"
    return tests, None


def load_premium_problems(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT p.problem_id, p.title, p.function_name, p.test_cases,
               v.reference_solution, v.time_complexity, v.space_complexity
        FROM problems p
        LEFT JOIN premium_problem_versions v
          ON v.problem_id = p.problem_id AND v.is_current = 1
        WHERE p.dataset_tier = ? AND p.is_active = 1
        ORDER BY p.problem_id
    """,
        (PREMIUM_DATASET_TIER,),
    ).fetchall()

    problems = []
    for row in rows:
        visible_tests, visible_error = _load_tests(cursor, row["problem_id"], "visible")
        hidden_tests, hidden_error = _load_tests(cursor, row["problem_id"], "hidden")

        reference_solution = {}
        reference_error = None
        raw_reference = row["reference_solution"]
        if raw_reference:
            try:
                reference_solution = json.loads(raw_reference)
            except json.JSONDecodeError:
                reference_error = "invalid_reference_solution_json"

        if not visible_tests and row["test_cases"]:
            try:
                parsed = json.loads(row["test_cases"])
                if isinstance(parsed, list):
                    visible_tests = parsed
            except json.JSONDecodeError:
                visible_error = "invalid_inline_visible_tests"

        problems.append(
            {
                "problem_id": row["problem_id"],
                "title": row["title"],
                "function_name": row["function_name"] or "solve",
                "reference_solution": reference_solution,
                "reference_error": reference_error,
                "time_complexity": row["time_complexity"],
                "space_complexity": row["space_complexity"],
                "visible_tests": visible_tests,
                "hidden_tests": hidden_tests,
                "visible_error": visible_error,
                "hidden_error": hidden_error,
            }
        )
    conn.close()
    return problems


def run_solution_audit(db_path: Path):
    judge = JudgeService()
    problems = load_premium_problems(db_path)
    rows = []
    issues = {"critical": [], "high": [], "medium": [], "low": []}

    if not problems:
        issues["high"].append({"type": "empty_premium_problem_bank"})

    for problem in problems:
        pid = problem["problem_id"]
        reference = problem["reference_solution"]
        row = {
            "problem_id": pid,
            "title": problem["title"],
            "has_reference_solution": bool(reference.get("code")),
            "algorithm_correct_visible": None,
            "algorithm_correct_hidden": None,
            "time_complexity": problem["time_complexity"],
            "space_complexity": problem["space_complexity"],
            "negative_verdicts": {},
        }

        if problem["reference_error"]:
            issues["critical"].append(
                {"type": "invalid_reference_solution_json", "problem_id": pid, "error": problem["reference_error"]}
            )
            rows.append(row)
            continue
        if not reference.get("code"):
            issues["critical"].append({"type": "missing_reference_solution", "problem_id": pid})
            rows.append(row)
            continue
        if problem["visible_error"]:
            issues["critical"].append(
                {"type": "invalid_visible_tests_json", "problem_id": pid, "error": problem["visible_error"]}
            )
        if problem["hidden_error"]:
            issues["critical"].append(
                {"type": "invalid_hidden_tests_json", "problem_id": pid, "error": problem["hidden_error"]}
            )
        if not problem["visible_tests"]:
            issues["critical"].append({"type": "missing_visible_tests", "problem_id": pid})
            rows.append(row)
            continue
        if not problem["hidden_tests"]:
            issues["critical"].append({"type": "missing_hidden_tests", "problem_id": pid})
            rows.append(row)
            continue

        visible_result = judge.run_python(
            reference["code"],
            problem["function_name"],
            json.dumps(problem["visible_tests"]),
        )
        hidden_result = judge.run_python(
            reference["code"],
            problem["function_name"],
            json.dumps(problem["hidden_tests"]),
        )

        row["algorithm_correct_visible"] = visible_result.get("verdict") == "Accepted"
        row["algorithm_correct_hidden"] = hidden_result.get("verdict") == "Accepted"
        row["accepted_runtime_ms_visible"] = visible_result.get("runtime_ms")
        row["accepted_runtime_ms_hidden"] = hidden_result.get("runtime_ms")

        if not row["algorithm_correct_visible"]:
            issues["critical"].append(
                {
                    "type": "reference_solution_failed_visible_tests",
                    "problem_id": pid,
                    "verdict": visible_result.get("verdict"),
                }
            )
        if not row["algorithm_correct_hidden"]:
            issues["critical"].append(
                {
                    "type": "reference_solution_failed_hidden_tests",
                    "problem_id": pid,
                    "verdict": hidden_result.get("verdict"),
                }
            )

        for label, code in NEGATIVE_CASES.items():
            result = judge.run_python(code, problem["function_name"], json.dumps(problem["visible_tests"]))
            row["negative_verdicts"][label] = result.get("verdict")

        if row["negative_verdicts"].get("wrong_answer") != "Wrong Answer":
            issues["high"].append({"type": "negative_case_mismatch", "problem_id": pid, "case": "wrong_answer"})
        if row["negative_verdicts"].get("runtime_error") != "Runtime Error":
            issues["high"].append({"type": "negative_case_mismatch", "problem_id": pid, "case": "runtime_error"})
        if row["negative_verdicts"].get("compilation_error") != "Compilation Error":
            issues["high"].append({"type": "negative_case_mismatch", "problem_id": pid, "case": "compilation_error"})
        if row["negative_verdicts"].get("time_limit") != "Time Limit Exceeded":
            issues["high"].append({"type": "negative_case_mismatch", "problem_id": pid, "case": "time_limit"})

        rows.append(row)

    return {"executed_problem_count": len(problems), "rows": rows, "issues": issues, "manual_review_count": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 solution and judge validation.")
    parser.add_argument("--db-path", default="data/coding_assistant.db")
    parser.add_argument("--output-dir", default="reports/phase3")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_solution_audit(Path(args.db_path))
    report = {
        "summary": {
            "executed_problem_count": result["executed_problem_count"],
            "critical_issues": len(result["issues"]["critical"]),
            "high_issues": len(result["issues"]["high"]),
            "medium_issues": len(result["issues"]["medium"]),
            "low_issues": len(result["issues"]["low"]),
            "manual_review_count": result["manual_review_count"],
        },
        "issues": result["issues"],
        "results": result["rows"],
    }
    report_path = output_dir / "solution_validation_report.json"
    write_json(report_path, report)
    print(f"Report written: {report_path}")
    print(report["summary"])
    return 1 if report["summary"]["critical_issues"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
