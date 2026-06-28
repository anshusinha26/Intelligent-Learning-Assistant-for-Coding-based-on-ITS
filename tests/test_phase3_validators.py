import json
import tempfile
import unittest
from pathlib import Path

from curriculum_validator import curriculum_checks, recommendation_quality_checks
from metadata_validator import run_metadata_validation
from problem_validator import validate_inventory
from scripts.phase3_common import load_inventory
from solution_validator import run_solution_audit
from src.database import Database
from src.migrations import apply_pending_migrations
from testcase_validator import run_testcase_audit


def _seed_complete_premium(db_path: Path):
    db = Database(str(db_path))
    conn = db.get_connection()
    cursor = conn.cursor()

    for table in (
        "premium_problem_rag_chunks",
        "premium_problem_relationships",
        "premium_problem_tests",
        "premium_problem_hints",
        "premium_problem_versions",
        "recommendations",
        "revision_schedule",
        "submissions",
        "attempts",
        "problems",
    ):
        cursor.execute(f"DELETE FROM {table}")

    graph_a = {"prerequisite": [], "alternative": [], "follow_up": ["contains-duplicate"], "review": [], "recovery": []}
    graph_b = {"prerequisite": ["two-sum"], "alternative": [], "follow_up": [], "review": [], "recovery": []}
    metadata = {"company_tags": ["google"], "source": "premium-internal", "tags": ["array", "hash"]}

    cursor.executemany(
        """
        INSERT INTO problems (
            problem_id, title, topic, pattern, difficulty, tags, description, constraints, examples,
            source_url, function_name, starter_code, test_cases, dataset_tier, is_active,
            curriculum_version, time_complexity, space_complexity, metadata_json,
            learning_objectives_json, common_mistakes_json, recommendation_graph_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'premium', 1, 1, ?, ?, ?, ?, ?, ?)
    """,
        [
            (
                "two-sum",
                "Two Sum",
                "Arrays",
                "Hash Map",
                "Easy",
                "array,hash-table,google",
                "Find two numbers that sum to target.",
                "n >= 2",
                "nums=[2,7,11,15], target=9 -> [0,1]",
                "https://leetcode.com/problems/two-sum/",
                "solve",
                "def solve(nums, target):\n    return []\n",
                json.dumps(
                    [
                        {"input": [[2, 7, 11, 15], 9], "expected": [0, 1]},
                        {"input": [[3, 2, 4], 6], "expected": [1, 2]},
                        {"input": [[3, 3], 6], "expected": [0, 1]},
                    ]
                ),
                "O(n)",
                "O(n)",
                json.dumps(metadata),
                json.dumps(["Use hashmap complement lookup"]),
                json.dumps(["Forgetting to check seen map before insert"]),
                json.dumps(graph_a),
            ),
            (
                "contains-duplicate",
                "Contains Duplicate",
                "Arrays",
                "Hash Set",
                "Easy",
                "array,set,google",
                "Check duplicate values.",
                "n >= 1",
                "nums=[1,2,3,1] -> true",
                "https://leetcode.com/problems/contains-duplicate/",
                "solve",
                "def solve(nums):\n    return False\n",
                json.dumps(
                    [
                        {"input": [[1, 2, 3, 1]], "expected": True},
                        {"input": [[1, 2, 3, 4]], "expected": False},
                        {"input": [[1, 1]], "expected": True},
                    ]
                ),
                "O(n)",
                "O(n)",
                json.dumps(metadata),
                json.dumps(["Use set cardinality check"]),
                json.dumps(["Returning true for empty array"]),
                json.dumps(graph_b),
            ),
        ],
    )

    version_rows = [
        (
            "two-sum",
            1,
            "Two Sum statement",
            "Two Sum constraints",
            "Two Sum examples",
            "Use complement hashmap",
            json.dumps(
                {
                    "language": "python",
                    "code": "def solve(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        need = target - num\n        if need in seen:\n            return [seen[need], i]\n        seen[num] = i\n    return []\n",
                }
            ),
            "def solve(nums, target):\n    return []\n",
            "O(n)",
            "O(n)",
            json.dumps(metadata),
            json.dumps(["Hash lookup"]),
            json.dumps(["Wrong index order"]),
            json.dumps(graph_a),
        ),
        (
            "contains-duplicate",
            1,
            "Contains Duplicate statement",
            "Contains Duplicate constraints",
            "Contains Duplicate examples",
            "Use set length comparison",
            json.dumps(
                {
                    "language": "python",
                    "code": "def solve(nums):\n    return len(set(nums)) != len(nums)\n",
                }
            ),
            "def solve(nums):\n    return False\n",
            "O(n)",
            "O(n)",
            json.dumps(metadata),
            json.dumps(["Set usage"]),
            json.dumps(["Not handling empty input"]),
            json.dumps(graph_b),
        ),
    ]
    cursor.executemany(
        """
        INSERT INTO premium_problem_versions (
            problem_id, version, statement_md, constraints_md, examples_md, editorial_md,
            reference_solution, starter_code, time_complexity, space_complexity,
            metadata_json, learning_objectives_json, common_mistakes_json, recommendation_graph_json, is_current
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """,
        version_rows,
    )

    hints = [
        ("two-sum", 1, 1, "Think in complements"),
        ("contains-duplicate", 1, 1, "Set tracks uniqueness"),
    ]
    cursor.executemany(
        "INSERT INTO premium_problem_hints (problem_id, version, hint_order, hint_md) VALUES (?, ?, ?, ?)",
        hints,
    )

    tests = [
        ("two-sum", 1, "visible", json.dumps([[2, 7, 11, 15], 9]), json.dumps([0, 1]), "minimum_input"),
        ("two-sum", 1, "visible", json.dumps([[3, 2, 4], 6]), json.dumps([1, 2]), "duplicates"),
        ("two-sum", 1, "visible", json.dumps([[3, 3], 6]), json.dumps([0, 1]), "boundary_conditions"),
        ("two-sum", 1, "hidden", json.dumps([[0, 4, 3, 0], 0]), json.dumps([0, 3]), "large_values"),
        ("two-sum", 1, "hidden", json.dumps([[-1, -2, -3, -4, -5], -8]), json.dumps([2, 4]), "negative_values"),
        ("two-sum", 1, "hidden", json.dumps([[1, 5], 6]), json.dumps([0, 1]), "single_element"),
        ("contains-duplicate", 1, "visible", json.dumps([[1, 2, 3, 1]]), json.dumps(True), "duplicates"),
        ("contains-duplicate", 1, "visible", json.dumps([[1, 2, 3, 4]]), json.dumps(False), "sorted_input"),
        ("contains-duplicate", 1, "visible", json.dumps([[1, 1]]), json.dumps(True), "minimum_input"),
        ("contains-duplicate", 1, "hidden", json.dumps([[]]), json.dumps(False), "empty_input"),
        ("contains-duplicate", 1, "hidden", json.dumps([[42]]), json.dumps(False), "single_element"),
        ("contains-duplicate", 1, "hidden", json.dumps([[9, 8, 7, 6, 5]]), json.dumps(False), "reverse_sorted"),
    ]
    cursor.executemany(
        """
        INSERT INTO premium_problem_tests (problem_id, version, visibility, input_json, expected_json, explanation)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        tests,
    )

    cursor.executemany(
        """
        INSERT INTO premium_problem_relationships (problem_id, related_problem_id, edge_type, weight, metadata_json)
        VALUES (?, ?, ?, 1.0, ?)
    """,
        [
            ("two-sum", "contains-duplicate", "follow_up", "{}"),
            ("contains-duplicate", "two-sum", "prerequisite", "{}"),
        ],
    )

    rag_rows = []
    for pid in ("two-sum", "contains-duplicate"):
        for chunk_type, text in (
            ("statement", f"{pid} statement chunk"),
            ("editorial", f"{pid} editorial chunk"),
            ("hints", f"{pid} hints chunk"),
            ("common_mistakes", f"{pid} common mistakes chunk"),
            ("learning_objectives", f"{pid} learning objectives chunk"),
        ):
            rag_rows.append((pid, 1, chunk_type, text, "sha256-lite", "[0.1,0.2]", "hash"))
    cursor.executemany(
        """
        INSERT INTO premium_problem_rag_chunks (
            problem_id, version, chunk_type, chunk_text, embedding_model, embedding_vector, content_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        rag_rows,
    )

    conn.commit()
    conn.close()


class Phase3ValidatorTests(unittest.TestCase):
    def test_migration_archives_existing_rows_to_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "migrate.db"
            db = Database(str(db_path))
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO problems (
                    problem_id, title, topic, pattern, difficulty, tags, description, function_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                ("legacy-problem", "Legacy", "Arrays", "Hash Map", "Easy", "legacy", "legacy", "solve"),
            )
            conn.commit()
            conn.close()

            apply_pending_migrations(str(db_path))

            conn = db.get_connection()
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT dataset_tier, is_active FROM problems WHERE problem_id = ?",
                ("legacy-problem",),
            ).fetchone()
            conn.close()
            self.assertEqual(row["dataset_tier"], "legacy")
            self.assertEqual(row["is_active"], 0)

    def test_premium_validators_on_complete_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "premium.db"
            _seed_complete_premium(db_path)

            inventory, _ = load_inventory(db_path, Path("unused.csv"), Path("unused.md"))
            issues, _ = validate_inventory(inventory)
            self.assertEqual(len(issues["critical"]), 0)

            metadata_issues = run_metadata_validation(inventory)
            self.assertEqual(len(metadata_issues["critical"]), 0)

            curriculum_issues, _ = curriculum_checks(inventory)
            self.assertEqual(len(curriculum_issues["critical"]), 0)

            rec_issues, rec_meta = recommendation_quality_checks(db_path)
            self.assertIn("cold_start_count", rec_meta)
            self.assertEqual(len(rec_issues["critical"]), 0)

            solution = run_solution_audit(db_path)
            self.assertEqual(len(solution["issues"]["critical"]), 0)

            testcase = run_testcase_audit(db_path, apply=False)
            self.assertEqual(len(testcase["issues"]["critical"]), 0)

    def test_problem_validator_detects_missing_required_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "premium.db"
            _seed_complete_premium(db_path)
            db = Database(str(db_path))
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE premium_problem_versions SET editorial_md = '' WHERE problem_id = 'two-sum'"
            )
            cursor.execute(
                "DELETE FROM premium_problem_tests WHERE problem_id = 'two-sum' AND visibility = 'hidden'"
            )
            conn.commit()
            conn.close()

            inventory, _ = load_inventory(db_path, Path("unused.csv"), Path("unused.md"))
            issues, _ = validate_inventory(inventory)
            critical_types = {item["type"] for item in issues["critical"]}
            high_types = {item["type"] for item in issues["high"]}
            self.assertIn("missing_hidden_tests", critical_types)
            self.assertIn("missing_editorial", high_types)


if __name__ == "__main__":
    unittest.main()
