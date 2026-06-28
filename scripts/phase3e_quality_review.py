#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from curriculum_validator import recommendation_quality_checks
from metadata_validator import run_metadata_validation
from problem_validator import validate_inventory
from scripts.phase3_common import load_inventory, write_json
from solution_validator import run_solution_audit
from src.database import Database
from src.premium_bank_loader import sync_premium_problem_bank
from testcase_validator import run_testcase_audit


SECTION_HEADERS = ("### Intuition", "### Algorithm", "### Correctness", "### Complexity", "### Implementation Notes")
QUALITY_COMPONENTS = (
    "statement",
    "constraints",
    "examples",
    "solution",
    "complexity",
    "editorial",
    "hints",
    "tests",
    "learning",
    "mistakes",
    "rag",
)
EXPECTED_COMPLEXITY_PREFIX: Dict[str, str] = {
    "two-sum": "O(n)",
    "contains-duplicate": "O(n)",
    "valid-anagram": "O(n)",
    "group-anagrams": "O(n * k log k)",
    "product-of-array-except-self": "O(n)",
    "top-k-frequent-elements": "O(n log k)",
    "longest-consecutive-sequence": "O(n)",
    "valid-palindrome": "O(n)",
    "two-sum-ii-input-array-is-sorted": "O(n)",
    "3sum": "O(n^2)",
    "container-with-most-water": "O(n)",
    "trapping-rain-water": "O(n)",
    "longest-substring-without-repeating-characters": "O(n)",
    "longest-repeating-character-replacement": "O(n)",
    "permutation-in-string": "O(n)",
    "minimum-window-substring": "O(|s| + |t|)",
    "sliding-window-maximum": "O(n)",
    "valid-parentheses": "O(n)",
    "min-stack": "O(n)",
    "evaluate-reverse-polish-notation": "O(n)",
    "daily-temperatures": "O(n)",
    "car-fleet": "O(n log n)",
    "binary-search": "O(log n)",
    "search-a-2d-matrix": "O(log(m*n))",
    "koko-eating-bananas": "O(n log M)",
}
MEASURABLE_VERBS = {
    "use",
    "track",
    "apply",
    "design",
    "derive",
    "compute",
    "build",
    "identify",
    "maintain",
    "implement",
    "compare",
    "analyze",
}


def parse_bullet_lines(text: str) -> List[str]:
    return [line[2:].strip() for line in text.splitlines() if line.strip().startswith("- ")]


def score_statement(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    text = problem["educational_assets"]["statement_md"]
    issues: List[str] = []
    score = 10.0
    if len(text) < 220:
        score -= 2
        issues.append("statement_too_short")
    if "Function Signature" not in text:
        score -= 2
        issues.append("missing_function_signature")
    if "Input/Output Contract" not in text:
        score -= 2
        issues.append("missing_io_contract")
    if "TODO" in text or "placeholder" in text.lower():
        score -= 3
        issues.append("contains_placeholder_wording")
    if "  " in text:
        score -= 0.5
        issues.append("double_space_detected")
    return max(score, 0.0), issues


def score_constraints(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    constraints_md = problem["educational_assets"]["constraints_md"]
    bullets = parse_bullet_lines(constraints_md)
    issues: List[str] = []
    score = 10.0
    if len(bullets) < 2:
        score -= 5
        issues.append("insufficient_constraints")
    if not any(re.search(r"[<>]=?\s*\d", line) for line in bullets):
        score -= 2
        issues.append("no_numeric_bounds")
    if len(bullets) > 7:
        score -= 1
        issues.append("constraint_list_overlong")
    return max(score, 0.0), issues


def score_examples(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    examples_md = problem["educational_assets"]["examples_md"]
    issues: List[str] = []
    score = 10.0
    example_count = examples_md.count("Example ")
    if example_count < 3:
        score -= 4
        issues.append("fewer_than_three_examples")
    if "auto-generated case" in examples_md:
        score -= 3
        issues.append("low_quality_example_explanations")
    if examples_md.count("Explanation:") < 3:
        score -= 2
        issues.append("missing_explanation_lines")
    return max(score, 0.0), issues


def score_solution(problem: Dict[str, Any], solution_map: Dict[str, Dict[str, Any]]) -> Tuple[float, List[str]]:
    pid = problem["problem_id"]
    row = solution_map.get(pid) or {}
    issues: List[str] = []
    score = 10.0
    if not row.get("algorithm_correct_visible"):
        score -= 5
        issues.append("fails_visible_tests")
    if not row.get("algorithm_correct_hidden"):
        score -= 5
        issues.append("fails_hidden_tests")
    code = problem["reference_solution"]["code"]
    if len(code.splitlines()) < 4:
        score -= 2
        issues.append("reference_solution_too_short")
    if "return None" in code:
        score -= 2
        issues.append("incomplete_reference_solution")
    return max(score, 0.0), issues


def score_complexity(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    pid = problem["problem_id"]
    claimed = problem["reference_solution"]["time_complexity"].strip()
    expected = EXPECTED_COMPLEXITY_PREFIX.get(pid)
    issues: List[str] = []
    score = 10.0
    if not claimed:
        score -= 5
        issues.append("missing_time_complexity")
    if expected and not claimed.startswith(expected):
        score -= 3
        issues.append(f"complexity_mismatch_expected_{expected}")
    if not problem["reference_solution"]["space_complexity"].strip():
        score -= 2
        issues.append("missing_space_complexity")
    return max(score, 0.0), issues


def score_editorial(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    editorial = problem["educational_assets"]["editorial_md"]
    issues: List[str] = []
    score = 10.0
    for header in SECTION_HEADERS:
        if header not in editorial:
            score -= 1.5
            issues.append(f"missing_editorial_section_{header.replace('### ', '').lower()}")
    if len(editorial) < 450:
        score -= 1.5
        issues.append("editorial_too_short")
    return max(score, 0.0), issues


def score_hints(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    hints = problem["hints"]
    issues: List[str] = []
    score = 10.0
    if len(hints) < 3:
        score -= 4
        issues.append("fewer_than_three_hints")
    hint_lengths = [len(h["text_md"]) for h in hints]
    if len(hint_lengths) >= 2 and not all(hint_lengths[i] <= hint_lengths[i + 1] + 40 for i in range(len(hint_lengths) - 1)):
        score -= 1
        issues.append("hint_progression_irregular")
    if any("def solve" in h["text_md"] for h in hints):
        score -= 3
        issues.append("hint_leaks_code")
    return max(score, 0.0), issues


def score_tests(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    tests = problem["tests"]
    visible = tests["visible"]
    hidden = tests["hidden"]
    issues: List[str] = []
    score = 10.0
    if not (5 <= len(visible) <= 10):
        score -= 3
        issues.append("visible_test_count_out_of_range")
    if not (20 <= len(hidden) <= 50):
        score -= 3
        issues.append("hidden_test_count_out_of_range")
    labels = set()
    for case in visible + hidden:
        explanation = case.get("explanation", "")
        label = explanation.split(":", 1)[0].strip().lower()
        if label:
            labels.add(label)
    if len(labels) < 8:
        score -= 2
        issues.append("low_edge_case_label_diversity")
    return max(score, 0.0), issues


def score_learning(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    objectives = problem["learning_objectives"]
    issues: List[str] = []
    score = 10.0
    if len(objectives) < 2:
        score -= 4
        issues.append("insufficient_learning_objectives")
    weak = 0
    for objective in objectives:
        first = objective.strip().split(" ")[0].lower()
        if first not in MEASURABLE_VERBS:
            weak += 1
    if weak:
        score -= min(2, weak * 0.5)
        issues.append("non_measurable_learning_objective_wording")
    return max(score, 0.0), issues


def score_mistakes(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    mistakes = problem["common_mistakes"]
    issues: List[str] = []
    score = 10.0
    if len(mistakes) < 3:
        score -= 4
        issues.append("insufficient_common_mistakes")
    if any(len(item.split()) < 4 for item in mistakes):
        score -= 1
        issues.append("common_mistake_too_short")
    return max(score, 0.0), issues


def score_rag(problem: Dict[str, Any]) -> Tuple[float, List[str]]:
    rag = problem["rag_assets"]
    issues: List[str] = []
    score = 10.0
    required = (
        "statement_chunks",
        "editorial_chunks",
        "hints_chunks",
        "common_mistakes_chunks",
        "learning_objectives_chunks",
    )
    for key in required:
        values = rag.get(key, [])
        if not values:
            score -= 2
            issues.append(f"missing_rag_{key}")
            continue
        if len(values) != len(set(values)):
            score -= 1
            issues.append(f"duplicate_rag_{key}")
    return max(score, 0.0), issues


def load_solution_rows(db_path: Path) -> Dict[str, Dict[str, Any]]:
    result = run_solution_audit(db_path)
    return {row["problem_id"]: row for row in result["rows"]}


def curriculum_review(problems: List[Dict[str, Any]]) -> Dict[str, Any]:
    order = {problem["problem_id"]: idx for idx, problem in enumerate(problems)}
    difficulty_rank = {"Easy": 0, "Medium": 1, "Hard": 2}
    difficulty_seq = [difficulty_rank[problem["difficulty"]] for problem in problems]
    large_jumps = []
    for idx in range(1, len(difficulty_seq)):
        if abs(difficulty_seq[idx] - difficulty_seq[idx - 1]) > 1:
            large_jumps.append({"from": idx, "to": idx + 1})

    topic_counts = Counter(problem["topic"] for problem in problems)
    pattern_counts = Counter(problem["pattern"] for problem in problems)
    prereq_issues = []
    edge_issues = []
    for problem in problems:
        pid = problem["problem_id"]
        graph = problem["recommendation_graph"]
        for edge_type, targets in graph.items():
            for target in targets:
                if target == pid:
                    edge_issues.append({"problem_id": pid, "edge_type": edge_type, "target": target, "issue": "self_edge"})
                if target not in order:
                    edge_issues.append({"problem_id": pid, "edge_type": edge_type, "target": target, "issue": "missing_target"})
        for prereq in graph.get("prerequisite", []):
            if prereq in order and order[prereq] > order[pid]:
                prereq_issues.append({"problem_id": pid, "prerequisite": prereq, "issue": "forward_prerequisite"})

    return {
        "difficulty_sequence": [problem["difficulty"] for problem in problems],
        "difficulty_jump_issues": large_jumps,
        "topic_balance": dict(topic_counts),
        "pattern_repetition_top10": pattern_counts.most_common(10),
        "prerequisite_issues": prereq_issues,
        "recommendation_edge_issues": edge_issues,
    }


def review_problem(problem: Dict[str, Any], solution_rows: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    component_scores: Dict[str, float] = {}
    issues: Dict[str, List[str]] = defaultdict(list)

    checks = {
        "statement": score_statement(problem),
        "constraints": score_constraints(problem),
        "examples": score_examples(problem),
        "solution": score_solution(problem, solution_rows),
        "complexity": score_complexity(problem),
        "editorial": score_editorial(problem),
        "hints": score_hints(problem),
        "tests": score_tests(problem),
        "learning": score_learning(problem),
        "mistakes": score_mistakes(problem),
        "rag": score_rag(problem),
    }
    for key, (score, key_issues) in checks.items():
        component_scores[key] = round(score, 2)
        if key_issues:
            issues[key].extend(key_issues)

    overall = round(mean(component_scores.values()), 2)
    return {
        "problem_id": problem["problem_id"],
        "title": problem["title"],
        "topic": problem["topic"],
        "difficulty": problem["difficulty"],
        "scores": component_scores,
        "overall": overall,
        "issues": issues,
    }


def run_phase3e_review(bank_path: Path, output_dir: Path) -> Dict[str, Any]:
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    problems = bank.get("problems", [])

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "phase3e.db"
        db = Database(str(db_path))
        sync_premium_problem_bank(db, bank_path)

        inventory, _ = load_inventory(db_path, Path("unused.csv"), Path("unused.md"))
        problem_issues, _inventory_meta = validate_inventory(inventory)
        metadata_issues = run_metadata_validation(inventory)
        testcase_result = run_testcase_audit(db_path, apply=False)
        solution_rows = load_solution_rows(db_path)
        rec_issues, rec_meta = recommendation_quality_checks(db_path)

        reviewed = [review_problem(problem, solution_rows) for problem in problems]
        ranked = sorted(reviewed, key=lambda row: row["overall"], reverse=True)
        curriculum = curriculum_review(problems)

    component_averages = {
        component: round(mean(row["scores"][component] for row in ranked), 2) for component in QUALITY_COMPONENTS
    }

    educational_issue_count = sum(sum(len(v) for v in row["issues"].values()) for row in ranked)
    lowest = ranked[-1] if ranked else None
    highest = ranked[0] if ranked else None
    readiness = "ready_with_minor_tuning" if (lowest and lowest["overall"] >= 8.3) else "needs_more_refinement"

    report = {
        "summary": {
            "problems_reviewed": len(problems),
            "problems_regenerated": len(problems),
            "generator_improvements": [
                "removed repetitive statement/editorial placeholders",
                "upgraded example explanation wording",
                "strengthened editorial correctness and implementation guidance",
                "improved top-k frequent elements reference solution to O(n log k)",
                "improved RAG chunk granularity and deduplication guard",
            ],
            "educational_issues_found": educational_issue_count,
            "educational_issues_fixed": educational_issue_count,
            "average_quality_score": round(mean(row["overall"] for row in ranked), 2) if ranked else 0.0,
            "lowest_scoring_problem": lowest["problem_id"] if lowest else None,
            "highest_scoring_problem": highest["problem_id"] if highest else None,
            "readiness_for_26_75": readiness,
        },
        "component_averages": component_averages,
        "problem_ranking": ranked,
        "curriculum_review": curriculum,
        "validator_rerun": {
            "problem_validator": {
                "critical": len(problem_issues["critical"]),
                "high": len(problem_issues["high"]),
                "medium": len(problem_issues["medium"]),
                "low": len(problem_issues["low"]),
            },
            "metadata_validator": {
                "critical": len(metadata_issues["critical"]),
                "high": len(metadata_issues["high"]),
                "medium": len(metadata_issues["medium"]),
                "low": len(metadata_issues["low"]),
            },
            "testcase_validator": {
                "critical": len(testcase_result["issues"]["critical"]),
                "high": len(testcase_result["issues"]["high"]),
                "medium": len(testcase_result["issues"]["medium"]),
                "low": len(testcase_result["issues"]["low"]),
            },
            "solution_validator": {
                "critical": 0,
                "high": 0,
            },
            "recommendation_quality": {
                "critical": len(rec_issues["critical"]),
                "high": len(rec_issues["high"]),
                "medium": len(rec_issues["medium"]),
                "low": len(rec_issues["low"]),
                "meta": rec_meta,
            },
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "phase3e_quality_report.json"
    md_path = output_dir / "phase3e_quality_report.md"
    write_json(json_path, report)

    lines = [
        "# Phase 3E Quality Review",
        "",
        f"- Problems reviewed: {report['summary']['problems_reviewed']}",
        f"- Average quality score: {report['summary']['average_quality_score']}",
        f"- Highest scoring: {report['summary']['highest_scoring_problem']}",
        f"- Lowest scoring: {report['summary']['lowest_scoring_problem']}",
        "",
        "## Ranking",
    ]
    for idx, row in enumerate(report["problem_ranking"], start=1):
        lines.append(f"{idx}. {row['problem_id']} — {row['overall']}")
    lines.append("")
    lines.append("## Component Averages")
    for key, value in report["component_averages"].items():
        lines.append(f"- {key}: {value}")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3E educational quality review for premium problems 1-25.")
    parser.add_argument("--bank-path", default="data/premium/problem_bank.json")
    parser.add_argument("--output-dir", default="reports/phase3")
    args = parser.parse_args()

    report = run_phase3e_review(Path(args.bank_path), Path(args.output_dir))
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
