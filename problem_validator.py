#!/usr/bin/env python3
import argparse
import re
from collections import Counter
from pathlib import Path

from scripts.phase3_common import (
    ALLOWED_DIFFICULTIES,
    load_inventory,
    markdown_link_scan,
    severity_exit_code,
    write_inventory_csv,
    write_json,
)


def validate_inventory(inventory):
    issues = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
    }

    id_counter = Counter(item["problem_id"] for item in inventory)
    title_counter = Counter((item["title"] or "").strip().lower() for item in inventory if item["title"])
    source_counter = Counter(item["source"] for item in inventory)
    slug_pattern = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    for pid, count in id_counter.items():
        if count > 1:
            issues["critical"].append({"type": "duplicate_problem_id", "problem_id": pid, "count": count})

    for title, count in title_counter.items():
        if count > 1:
            issues["medium"].append({"type": "duplicate_title", "title": title, "count": count})

    for item in inventory:
        pid = item["problem_id"]
        title = item["title"]
        slug = item["slug"]
        difficulty = item["difficulty"]

        if not title:
            issues["critical"].append({"type": "missing_title", "problem_id": pid})
        if not item["description"]:
            issues["high"].append({"type": "missing_statement", "problem_id": pid})
        if not item["constraints"]:
            issues["high"].append({"type": "missing_constraints", "problem_id": pid})
        if not item["examples"]:
            issues["high"].append({"type": "missing_examples", "problem_id": pid})
        if not item["editorial"]:
            issues["high"].append({"type": "missing_editorial", "problem_id": pid})
        if not item["reference_solution_code"]:
            issues["critical"].append({"type": "missing_reference_solution", "problem_id": pid})
        if not item["starter_code"]:
            issues["critical"].append({"type": "missing_starter_code", "problem_id": pid})
        if item["visible_test_count"] <= 0:
            issues["critical"].append({"type": "missing_visible_tests", "problem_id": pid})
        if item["hidden_test_count"] <= 0:
            issues["critical"].append({"type": "missing_hidden_tests", "problem_id": pid})
        if item["hint_count"] <= 0:
            issues["high"].append({"type": "missing_hints", "problem_id": pid})
        if not item["time_complexity"] or not item["space_complexity"]:
            issues["high"].append({"type": "missing_complexity_metadata", "problem_id": pid})
        if item["learning_objectives_count"] <= 0:
            issues["high"].append({"type": "missing_learning_objectives", "problem_id": pid})
        if not item["metadata_present"]:
            issues["high"].append({"type": "missing_metadata", "problem_id": pid})
        if item["common_mistakes_count"] <= 0:
            issues["high"].append({"type": "missing_common_mistakes", "problem_id": pid})
        if not item["recommendation_graph_present"]:
            issues["high"].append({"type": "missing_recommendation_graph", "problem_id": pid})
        if item["relationship_count"] <= 0:
            issues["medium"].append({"type": "missing_recommendation_edges", "problem_id": pid})
        if item["rag_statement_count"] <= 0:
            issues["high"].append({"type": "missing_rag_statement_chunks", "problem_id": pid})
        if item["rag_editorial_count"] <= 0:
            issues["high"].append({"type": "missing_rag_editorial_chunks", "problem_id": pid})
        if item["rag_hints_count"] <= 0:
            issues["high"].append({"type": "missing_rag_hint_chunks", "problem_id": pid})
        if item["rag_common_mistakes_count"] <= 0:
            issues["high"].append({"type": "missing_rag_common_mistakes_chunks", "problem_id": pid})
        if item["rag_learning_objectives_count"] <= 0:
            issues["high"].append({"type": "missing_rag_learning_objective_chunks", "problem_id": pid})
        if not item["source_url"]:
            issues["low"].append({"type": "missing_source_url", "problem_id": pid})
        if not item["pattern"]:
            issues["low"].append({"type": "missing_pattern", "problem_id": pid})
        if not slug or not slug_pattern.match(slug):
            issues["high"].append({"type": "broken_slug", "problem_id": pid, "slug": slug, "title": title})
        if difficulty not in ALLOWED_DIFFICULTIES:
            issues["critical"].append(
                {"type": "invalid_difficulty", "problem_id": pid, "difficulty": difficulty}
            )
        if item["visible_tests_json_error"]:
            issues["critical"].append(
                {
                    "type": "invalid_visible_tests_json",
                    "problem_id": pid,
                    "error": item["visible_tests_json_error"],
                }
            )
        for key in (
            "metadata_json_error",
            "learning_objectives_json_error",
            "common_mistakes_json_error",
            "recommendation_graph_json_error",
            "reference_solution_json_error",
        ):
            if item.get(key):
                issues["critical"].append(
                    {"type": f"invalid_{key}", "problem_id": pid, "error": item[key]}
                )

    if not inventory:
        issues["high"].append({"type": "empty_premium_problem_bank"})

    inventory_health = {
        "total_problems": len(inventory),
        "difficulty_distribution": dict(Counter(item["difficulty"] for item in inventory)),
        "topic_distribution_top15": Counter(item["topic"] for item in inventory).most_common(15),
        "source_distribution_top10": source_counter.most_common(10),
    }
    return issues, inventory_health


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 problem bank inventory and structural validation.")
    parser.add_argument("--db-path", default="data/coding_assistant.db")
    parser.add_argument("--csv-path", default="data/archive/legacy_problem_bank/problem_bank_topic_pattern.csv")
    parser.add_argument("--markdown-path", default="data/archive/legacy_problem_bank/dsa_problems.md")
    parser.add_argument("--output-dir", default="reports/phase3")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory, source_stats = load_inventory(
        db_path=Path(args.db_path),
        csv_path=Path(args.csv_path),
        markdown_path=Path(args.markdown_path),
    )
    issues, health = validate_inventory(inventory)
    link_scan = markdown_link_scan(Path(args.markdown_path))

    inventory_csv = output_dir / "problem_inventory.csv"
    inventory_json = output_dir / "problem_inventory.json"
    write_inventory_csv(inventory_csv, inventory)
    write_json(inventory_json, inventory)

    report = {
        "summary": {
            "total_problems": len(inventory),
            "critical_issues": len(issues["critical"]),
            "high_issues": len(issues["high"]),
            "medium_issues": len(issues["medium"]),
            "low_issues": len(issues["low"]),
        },
        "source_stats": source_stats,
        "inventory_health": health,
        "issues": issues,
        "markdown_scan": {
            "link_count": len(link_scan["links"]),
            "image_count": len(link_scan["images"]),
            "broken_url_format_count": len(link_scan["broken_url_format"]),
            "broken_url_format_examples": link_scan["broken_url_format"][:50],
        },
        "artifacts": {
            "inventory_csv": str(inventory_csv),
            "inventory_json": str(inventory_json),
        },
    }
    report_path = output_dir / "problem_validation_report.json"
    write_json(report_path, report)

    print(f"Inventory written: {inventory_csv}")
    print(f"Inventory written: {inventory_json}")
    print(f"Report written: {report_path}")
    print(report["summary"])
    return severity_exit_code(len(issues["critical"]))


if __name__ == "__main__":
    raise SystemExit(main())
