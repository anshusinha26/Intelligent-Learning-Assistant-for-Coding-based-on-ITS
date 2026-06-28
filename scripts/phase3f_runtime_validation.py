#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.judge import JudgeService
from src.premium_bank_loader import sync_premium_problem_bank
from src.problem_bank import PREMIUM_DATASET_TIER
from tests.test_phase2d_helpers import isolated_app, register_and_login


def _load_learning_path(path: Path) -> List[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        if isinstance(payload.get("linear_path"), list):
            return [str(item) for item in payload["linear_path"] if str(item).strip()]
        if isinstance(payload.get("learning_path"), list):
            return [str(item.get("slug")) for item in payload["learning_path"] if isinstance(item, dict) and item.get("slug")]
        if isinstance(payload.get("ordered_problems"), list):
            return [str(item) for item in payload["ordered_problems"] if str(item).strip()]
    if isinstance(payload, list):
        return [str(item) for item in payload if str(item).strip()]
    return []


def run_api_runtime_validation(bank_path: Path, learning_path_path: Path) -> Dict[str, Any]:
    report: Dict[str, Any] = {"statuses": {}, "checks": {}, "db_counts": {}, "api_sequence": []}
    with isolated_app() as (main_module, client):
        sync_premium_problem_bank(main_module.db, bank_path)

        session = register_and_login(client, "phase3f.runtime@example.com")
        headers = {"Authorization": f"Bearer {session['access_token']}"}

        problems_resp = client.get("/api/problems?limit=200", headers=headers)
        report["statuses"]["problems_list"] = problems_resp.status_code
        report["api_sequence"].append("GET /api/problems?limit=200")
        problems = problems_resp.json() if problems_resp.status_code == 200 else []
        problem_ids = [item["problem_id"] for item in problems]
        first_problem_id = problem_ids[0] if problem_ids else None

        search_resp = client.get("/api/problems?q=sum&limit=200", headers=headers)
        report["statuses"]["problems_search"] = search_resp.status_code
        report["api_sequence"].append("GET /api/problems?q=sum&limit=200")
        search_count = len(search_resp.json()) if search_resp.status_code == 200 else 0

        filter_resp = client.get(
            "/api/problems?topic=Arrays%20%26%20Hashing,dynamic-programming&difficulty=Easy,Medium&limit=200",
            headers=headers,
        )
        report["statuses"]["problems_filter_combo"] = filter_resp.status_code
        report["api_sequence"].append(
            "GET /api/problems?topic=Arrays%20%26%20Hashing,dynamic-programming&difficulty=Easy,Medium&limit=200"
        )
        filter_count = len(filter_resp.json()) if filter_resp.status_code == 200 else 0

        detail_status = None
        if first_problem_id:
            detail_resp = client.get(f"/api/problems/{first_problem_id}", headers=headers)
            detail_status = detail_resp.status_code
            report["api_sequence"].append(f"GET /api/problems/{first_problem_id}")
        report["statuses"]["problem_detail"] = detail_status

        attempt_status = None
        if first_problem_id:
            attempt_resp = client.post(
                "/api/attempts",
                headers=headers,
                json={"problem_id": first_problem_id, "verdict": "Accepted", "time_taken": 125, "error_type": None},
            )
            attempt_status = attempt_resp.status_code
            report["api_sequence"].append("POST /api/attempts")
        report["statuses"]["attempt_record"] = attempt_status

        rec_generate = client.post("/api/recommendations/generate?top_k=10&refresh=true", headers=headers)
        report["statuses"]["recommendations_generate"] = rec_generate.status_code
        report["api_sequence"].append("POST /api/recommendations/generate?top_k=10&refresh=true")
        rec_count = rec_generate.json().get("count", 0) if rec_generate.status_code == 200 else 0

        rec_list = client.get("/api/recommendations?status=pending&limit=20", headers=headers)
        report["statuses"]["recommendations_list"] = rec_list.status_code
        report["api_sequence"].append("GET /api/recommendations?status=pending&limit=20")
        rec_list_count = rec_list.json().get("count", 0) if rec_list.status_code == 200 else 0

        if rec_list.status_code == 200 and rec_list.json().get("recommendations"):
            rec_id = rec_list.json()["recommendations"][0]["rec_id"]
            complete_resp = client.post(f"/api/recommendations/{rec_id}/complete", headers=headers)
            report["statuses"]["recommendation_complete"] = complete_resp.status_code
            report["api_sequence"].append(f"POST /api/recommendations/{rec_id}/complete")
        else:
            report["statuses"]["recommendation_complete"] = None

        notes_create = client.post(
            "/api/notes",
            headers=headers,
            json={
                "problem_id": first_problem_id or "two-sum",
                "title": "Phase3F Runtime Note",
                "content": "Runtime validation note payload",
                "pinned": False,
            },
        )
        report["statuses"]["notes_create"] = notes_create.status_code
        report["api_sequence"].append("POST /api/notes")

        notes_list = client.get("/api/notes?limit=20", headers=headers)
        report["statuses"]["notes_list"] = notes_list.status_code
        report["api_sequence"].append("GET /api/notes?limit=20")
        notes_count = notes_list.json().get("count", 0) if notes_list.status_code == 200 else 0

        bookmarks_create = client.post(
            "/api/bookmarks",
            headers=headers,
            json={"problem_id": first_problem_id or "two-sum"},
        )
        report["statuses"]["bookmarks_create"] = bookmarks_create.status_code
        report["api_sequence"].append("POST /api/bookmarks")

        bookmarks_list = client.get("/api/bookmarks?limit=20", headers=headers)
        report["statuses"]["bookmarks_list"] = bookmarks_list.status_code
        report["api_sequence"].append("GET /api/bookmarks?limit=20")
        bookmarks_count = bookmarks_list.json().get("count", 0) if bookmarks_list.status_code == 200 else 0

        revisions_due = client.get("/api/revisions/due?limit=20", headers=headers)
        report["statuses"]["revisions_due"] = revisions_due.status_code
        report["api_sequence"].append("GET /api/revisions/due?limit=20")
        due_count = revisions_due.json().get("count", 0) if revisions_due.status_code == 200 else 0

        dashboard = client.get("/api/analytics/dashboard", headers=headers)
        report["statuses"]["analytics_dashboard"] = dashboard.status_code
        report["api_sequence"].append("GET /api/analytics/dashboard")

        weaknesses = client.get("/api/analytics/weaknesses?limit=10", headers=headers)
        report["statuses"]["analytics_weaknesses"] = weaknesses.status_code
        report["api_sequence"].append("GET /api/analytics/weaknesses?limit=10")

        errors = client.get("/api/analytics/errors", headers=headers)
        report["statuses"]["analytics_errors"] = errors.status_code
        report["api_sequence"].append("GET /api/analytics/errors")

        rag_health = client.get("/api/rag/health", headers=headers)
        report["statuses"]["rag_health"] = rag_health.status_code
        report["api_sequence"].append("GET /api/rag/health")

        rag_query = client.post(
            "/api/rag/query",
            headers=headers,
            json={"question": "Give a hint for this problem", "problem_id": first_problem_id or "two-sum"},
        )
        report["statuses"]["rag_query"] = rag_query.status_code
        report["api_sequence"].append("POST /api/rag/query")
        rag_payload = rag_query.json() if rag_query.status_code == 200 else {}

        submission_wa = client.post(
            "/api/submissions",
            headers=headers,
            json={"problem_id": first_problem_id or "two-sum", "language": "python", "code": "def solve(*args):\n    return None\n"},
        )
        report["statuses"]["submission_wa"] = submission_wa.status_code
        report["api_sequence"].append("POST /api/submissions (WA probe)")

        submissions_list = client.get("/api/submissions?limit=20", headers=headers)
        report["statuses"]["submissions_list"] = submissions_list.status_code
        report["api_sequence"].append("GET /api/submissions?limit=20")
        submissions_count = submissions_list.json().get("count", 0) if submissions_list.status_code == 200 else 0

        conn = main_module.db.get_connection()
        cursor = conn.cursor()
        active_problem_count = cursor.execute(
            "SELECT COUNT(*) AS c FROM problems WHERE dataset_tier = ? AND is_active = 1",
            (PREMIUM_DATASET_TIER,),
        ).fetchone()["c"]
        user = main_module.auth_service.get_current_user(session["access_token"])
        user_id = user["user_id"]
        user_attempts = cursor.execute(
            "SELECT COUNT(*) AS c FROM attempts WHERE user_id = ?",
            (user_id,),
        ).fetchone()["c"]
        user_submissions = cursor.execute(
            "SELECT COUNT(*) AS c FROM submissions WHERE user_id = ?",
            (user_id,),
        ).fetchone()["c"]
        user_recommendations = cursor.execute(
            "SELECT COUNT(*) AS c FROM recommendations WHERE user_id = ?",
            (user_id,),
        ).fetchone()["c"]
        user_notes = cursor.execute(
            "SELECT COUNT(*) AS c FROM notes WHERE user_id = ?",
            (user_id,),
        ).fetchone()["c"]
        user_bookmarks = cursor.execute(
            "SELECT COUNT(*) AS c FROM bookmarks WHERE user_id = ?",
            (user_id,),
        ).fetchone()["c"]
        relationship_count = cursor.execute(
            "SELECT COUNT(*) AS c FROM premium_problem_relationships",
        ).fetchone()["c"]
        relationship_problem_count = cursor.execute(
            "SELECT COUNT(DISTINCT problem_id) AS c FROM premium_problem_relationships",
        ).fetchone()["c"]
        conn.close()

        learning_path = _load_learning_path(learning_path_path)
        learning_path_set = set(learning_path)
        problem_id_set = set(problem_ids)

        report["checks"] = {
            "problems_count": len(problems),
            "search_count": search_count,
            "filter_count": filter_count,
            "recommendations_generated": rec_count,
            "recommendations_list_count": rec_list_count,
            "notes_count": notes_count,
            "bookmarks_count": bookmarks_count,
            "revisions_due_count": due_count,
            "submissions_count": submissions_count,
            "rag_source": rag_payload.get("source"),
            "learning_path_length": len(learning_path),
            "learning_path_matches_problem_set": learning_path_set == problem_id_set,
            "recommendation_graph_edge_count": relationship_count,
            "recommendation_graph_problem_count": relationship_problem_count,
        }
        report["db_counts"] = {
            "active_premium_problems": active_problem_count,
            "user_attempts": user_attempts,
            "user_submissions": user_submissions,
            "user_recommendations": user_recommendations,
            "user_notes": user_notes,
            "user_bookmarks": user_bookmarks,
        }

        status_values = [value for value in report["statuses"].values() if value is not None]
        report["all_status_ok"] = all(value == 200 for value in status_values)
        report["runtime_checks_ok"] = (
            len(problems) == 75
            and rec_count > 0
            and active_problem_count == 75
            and relationship_count > 0
            and report["checks"]["learning_path_matches_problem_set"]
            and rag_payload.get("source") == "local-rag"
        )
    return report


def run_judge_verdict_matrix(db_path: Path) -> Dict[str, Any]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT p.problem_id, p.function_name, p.test_cases, v.reference_solution
        FROM problems p
        JOIN premium_problem_versions v ON v.problem_id = p.problem_id AND v.is_current = 1
        WHERE p.dataset_tier = ? AND p.is_active = 1
        ORDER BY p.problem_id
        """,
        (PREMIUM_DATASET_TIER,),
    ).fetchall()
    conn.close()

    snippets = {
        "wa": "def solve(*args):\n    return None\n",
        "re": "def solve(*args):\n    raise RuntimeError('boom')\n",
        "ce": "def solve(*args)\n    return 0\n",
        "tle": "def solve(*args):\n    while True:\n        pass\n",
        "memory": "def solve(*args):\n    x = [0] * (10**8)\n    return len(x)\n",
    }
    judge = JudgeService(timeout_seconds=1)
    failures: List[Dict[str, Any]] = []
    matrix: List[Dict[str, Any]] = []

    for row in rows:
        pid = row["problem_id"]
        function_name = row["function_name"] or "solve"
        test_cases_json = row["test_cases"]
        reference_payload = json.loads(row["reference_solution"] or "{}")
        reference_code = reference_payload.get("code", "")

        accepted = judge.run_python(reference_code, function_name, test_cases_json).get("verdict")
        wa = judge.run_python(snippets["wa"], function_name, test_cases_json).get("verdict")
        re_verdict = judge.run_python(snippets["re"], function_name, test_cases_json).get("verdict")
        ce = judge.run_python(snippets["ce"], function_name, test_cases_json).get("verdict")
        tle = judge.run_python(snippets["tle"], function_name, test_cases_json).get("verdict")
        memory = judge.run_python(snippets["memory"], function_name, test_cases_json).get("verdict")

        row_result = {
            "problem_id": pid,
            "accepted": accepted,
            "wrong_answer_probe": wa,
            "runtime_error_probe": re_verdict,
            "compilation_error_probe": ce,
            "time_limit_probe": tle,
            "memory_pressure_probe": memory,
        }
        matrix.append(row_result)

        if accepted != "Accepted":
            failures.append({"problem_id": pid, "check": "accepted", "actual": accepted, "expected": "Accepted"})
        if wa != "Wrong Answer":
            failures.append({"problem_id": pid, "check": "wrong_answer_probe", "actual": wa, "expected": "Wrong Answer"})
        if re_verdict != "Runtime Error":
            failures.append({"problem_id": pid, "check": "runtime_error_probe", "actual": re_verdict, "expected": "Runtime Error"})
        if ce != "Compilation Error":
            failures.append({"problem_id": pid, "check": "compilation_error_probe", "actual": ce, "expected": "Compilation Error"})
        if tle != "Time Limit Exceeded":
            failures.append({"problem_id": pid, "check": "time_limit_probe", "actual": tle, "expected": "Time Limit Exceeded"})
        if memory not in {"Runtime Error", "Time Limit Exceeded", "Wrong Answer"}:
            failures.append(
                {
                    "problem_id": pid,
                    "check": "memory_pressure_probe",
                    "actual": memory,
                    "expected": "Runtime Error|Time Limit Exceeded|Wrong Answer",
                }
            )

    summary = {
        "problem_count": len(rows),
        "failure_count": len(failures),
        "all_passed": len(failures) == 0,
    }
    return {"summary": summary, "failures": failures, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3F runtime validation and verdict matrix.")
    parser.add_argument("--db-path", default="/tmp/ila_phase3f.db")
    parser.add_argument("--bank-path", default="data/premium/problem_bank.json")
    parser.add_argument("--learning-path-path", default="data/premium/curriculum/learning_path.json")
    parser.add_argument("--output-path", default="reports/phase3/phase3f_runtime_report.json")
    parser.add_argument("--judge-output-path", default="reports/phase3/phase3f_judge_verdict_report.json")
    args = parser.parse_args()

    runtime_report = run_api_runtime_validation(Path(args.bank_path), Path(args.learning_path_path))
    judge_report = run_judge_verdict_matrix(Path(args.db_path))

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(runtime_report, indent=2, ensure_ascii=False), encoding="utf-8")

    judge_output_path = Path(args.judge_output_path)
    judge_output_path.parent.mkdir(parents=True, exist_ok=True)
    judge_output_path.write_text(json.dumps(judge_report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        json.dumps(
            {
                "runtime_all_status_ok": runtime_report["all_status_ok"],
                "runtime_checks_ok": runtime_report["runtime_checks_ok"],
                "judge_all_passed": judge_report["summary"]["all_passed"],
                "judge_failure_count": judge_report["summary"]["failure_count"],
                "problems_checked": judge_report["summary"]["problem_count"],
            },
            indent=2,
        )
    )
    return 0 if runtime_report["all_status_ok"] and runtime_report["runtime_checks_ok"] and judge_report["summary"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
