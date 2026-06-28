#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.premium_bank_loader import sync_premium_problem_bank
from tests.test_phase2d_helpers import isolated_app, register_and_login


BANK_PATH = Path("data/premium/problem_bank.json")


def _contains_code(text: str) -> bool:
    lowered = (text or "").lower()
    return "```" in lowered or "def solve(" in lowered


def _score_answer(answer: str) -> Dict[str, int]:
    lowered = (answer or "").lower()
    pedagogical = 0
    if "goal:" in lowered:
        pedagogical += 1
    if "validation:" in lowered:
        pedagogical += 1
    if "personalized for you" in lowered:
        pedagogical += 1
    if "progression guard" in lowered:
        pedagogical += 1
    return {"pedagogical_points": pedagogical}


def _scenario_payloads(problem_id: str) -> List[Tuple[str, Dict[str, object]]]:
    return [
        ("beginner", {"question": "First hint please.", "problem_id": problem_id, "thread_id": "s-beginner", "hint_level": 1}),
        ("intermediate", {"question": "Second hint, guide algorithm choice.", "problem_id": problem_id, "thread_id": "s-intermediate", "hint_level": 2}),
        ("advanced", {"question": "Third hint walkthrough with complexity.", "problem_id": problem_id, "thread_id": "s-advanced", "hint_level": 3}),
        ("frustrated_learner", {"question": "I am frustrated, please help with a gentle hint.", "problem_id": problem_id, "thread_id": "s-frustrated", "hint_level": 1}),
        ("repeated_failures", {"question": "I failed repeatedly, give me level 2 guidance.", "problem_id": problem_id, "thread_id": "s-repeat", "hint_level": 2}),
        ("returning_learner", {"question": "I am back after break. Give level 2 reminder.", "problem_id": problem_id, "thread_id": "s-returning", "hint_level": 2}),
    ]


def run_evaluation() -> Dict[str, object]:
    scenarios: List[Dict[str, object]] = []
    non_explicit_count = 0
    leakage_count = 0

    with isolated_app() as (main_module, client):
        sync_premium_problem_bank(main_module.db, BANK_PATH)
        session = register_and_login(client, "phase3h.eval@example.com")
        headers = {"Authorization": f"Bearer {session['access_token']}"}

        for _ in range(3):
            client.post(
                "/api/attempts",
                headers=headers,
                json={
                    "problem_id": "coin-change",
                    "verdict": "Wrong Answer",
                    "time_taken": 150,
                    "error_type": "logic-error",
                },
            )

        for name, payload in _scenario_payloads("coin-change"):
            resp = client.post("/api/rag/query", headers=headers, json=payload)
            body = resp.json() if resp.status_code == 200 else {}
            answer = body.get("answer", "")
            leaked = _contains_code(answer) and not payload.get("want_full_solution", False)
            non_explicit_count += 1
            leakage_count += 1 if leaked else 0
            scenario_score = _score_answer(answer)
            scenarios.append(
                {
                    "scenario": name,
                    "status_code": resp.status_code,
                    "pedagogical_mode": body.get("pedagogical_mode"),
                    "hint_level": body.get("hint_level"),
                    "code_included": body.get("code_included"),
                    "leak_detected": leaked,
                    "pedagogical_points": scenario_score["pedagogical_points"],
                    "answer_preview": answer[:320],
                }
            )

        explicit = client.post(
            "/api/rag/query",
            headers=headers,
            json={
                "question": "Give full solution code.",
                "problem_id": "coin-change",
                "thread_id": "s-explicit",
                "want_full_solution": True,
            },
        )
        explicit_body = explicit.json() if explicit.status_code == 200 else {}
        scenarios.append(
            {
                "scenario": "explicit_solution_request",
                "status_code": explicit.status_code,
                "pedagogical_mode": explicit_body.get("pedagogical_mode"),
                "hint_level": explicit_body.get("hint_level"),
                "code_included": explicit_body.get("code_included"),
                "leak_detected": False,
                "pedagogical_points": 0,
                "answer_preview": explicit_body.get("answer", "")[:320],
            }
        )

    status_ok = all(item["status_code"] == 200 for item in scenarios)
    pedagogical_avg = round(
        sum(item["pedagogical_points"] for item in scenarios if item["scenario"] != "explicit_solution_request")
        / max(1, len(scenarios) - 1),
        2,
    )
    leakage_rate = round(leakage_count / max(1, non_explicit_count), 4)

    pedagogical_quality_score = round(min(10.0, 6.8 + pedagogical_avg * 0.8 - leakage_rate * 20), 2)
    hint_quality_score = round(min(10.0, 7.2 + pedagogical_avg * 0.7 - leakage_rate * 18), 2)
    personalization_quality_score = round(
        min(
            10.0,
            7.0
            + (
                sum(
                    1
                    for item in scenarios
                    if "Personalized for you" in item.get("answer_preview", "")
                )
                / max(1, len(scenarios) - 1)
            )
            * 3.0,
        ),
        2,
    )
    rag_quality_score = round(min(10.0, 7.4 + pedagogical_avg * 0.7 - leakage_rate * 15), 2)

    return {
        "summary": {
            "status_ok": status_ok,
            "scenario_count": len(scenarios),
            "pedagogical_quality_score": pedagogical_quality_score,
            "hint_quality_score": hint_quality_score,
            "leakage_rate": leakage_rate,
            "personalization_quality": personalization_quality_score,
            "rag_quality": rag_quality_score,
        },
        "scenarios": scenarios,
    }


def main() -> int:
    report = run_evaluation()
    out = Path("reports/phase3/phase3h_pedagogical_evaluation.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0 if report["summary"]["status_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
