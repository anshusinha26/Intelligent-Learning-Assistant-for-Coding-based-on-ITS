#!/usr/bin/env python3
import argparse
from collections import Counter
from pathlib import Path

from scripts.phase3_common import ALLOWED_DIFFICULTIES, load_inventory, write_json


def run_metadata_validation(inventory):
    issues = {"critical": [], "high": [], "medium": [], "low": []}
    id_counter = Counter(item["problem_id"] for item in inventory)
    title_counter = Counter((item["title"] or "").strip().lower() for item in inventory if item["title"])

    for pid, count in id_counter.items():
        if count > 1:
            issues["critical"].append({"type": "duplicate_id", "problem_id": pid, "count": count})
    for title, count in title_counter.items():
        if count > 1:
            issues["medium"].append({"type": "duplicate_title", "title": title, "count": count})

    for item in inventory:
        pid = item["problem_id"]
        if not item["topic"]:
            issues["high"].append({"type": "missing_topic", "problem_id": pid})
        if not item["subtopic"] or item["subtopic"] == "Unspecified":
            issues["medium"].append({"type": "missing_subtopic", "problem_id": pid})
        if item["difficulty"] not in ALLOWED_DIFFICULTIES:
            issues["critical"].append(
                {"type": "invalid_difficulty", "problem_id": pid, "difficulty": item["difficulty"]}
            )
        if not item.get("metadata_present"):
            issues["critical"].append({"type": "missing_metadata_json", "problem_id": pid})
        if not item.get("time_complexity") or not item.get("space_complexity"):
            issues["high"].append({"type": "missing_complexity_metadata", "problem_id": pid})
        if item.get("learning_objectives_count", 0) <= 0:
            issues["high"].append({"type": "missing_learning_objectives", "problem_id": pid})
        if item.get("common_mistakes_count", 0) <= 0:
            issues["high"].append({"type": "missing_common_mistakes", "problem_id": pid})
        if not item.get("recommendation_graph_present"):
            issues["high"].append({"type": "missing_recommendation_graph_json", "problem_id": pid})
        if not item["source_url"]:
            issues["low"].append({"type": "missing_source_url", "problem_id": pid})
        if not item["pattern"]:
            issues["low"].append({"type": "missing_pattern", "problem_id": pid})
        if not item["company_tags"]:
            issues["low"].append({"type": "missing_company_tags", "problem_id": pid})
        if item.get("relationship_count", 0) <= 0:
            issues["medium"].append({"type": "missing_recommendation_edges", "problem_id": pid})

    if not inventory:
        issues["high"].append({"type": "empty_premium_problem_bank"})
    return issues


def apply_autofix(csv_path: Path, inventory):
    return {
        "applied": False,
        "reason": "Autofix disabled for premium validator. Fixes must be applied in premium problem JSON source.",
        "updated_rows": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 metadata validator.")
    parser.add_argument("--db-path", default="data/coding_assistant.db")
    parser.add_argument("--csv-path", default="data/archive/legacy_problem_bank/problem_bank_topic_pattern.csv")
    parser.add_argument("--markdown-path", default="data/archive/legacy_problem_bank/dsa_problems.md")
    parser.add_argument("--output-dir", default="reports/phase3")
    parser.add_argument("--autofix", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory, _ = load_inventory(Path(args.db_path), Path(args.csv_path), Path(args.markdown_path))
    autofix_result = {"applied": False}
    if args.autofix:
        autofix_result = apply_autofix(Path(args.csv_path), inventory)
        inventory, _ = load_inventory(Path(args.db_path), Path(args.csv_path), Path(args.markdown_path))

    issues = run_metadata_validation(inventory)
    report = {
        "summary": {
            "total_problems": len(inventory),
            "critical_issues": len(issues["critical"]),
            "high_issues": len(issues["high"]),
            "medium_issues": len(issues["medium"]),
            "low_issues": len(issues["low"]),
        },
        "issues": issues,
        "autofix": autofix_result,
    }
    report_path = output_dir / "metadata_validation_report.json"
    write_json(report_path, report)
    print(f"Report written: {report_path}")
    print(report["summary"])
    return 1 if issues["critical"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
