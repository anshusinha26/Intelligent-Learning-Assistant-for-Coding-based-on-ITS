import json
import tempfile
import unittest
from pathlib import Path

from src.database import Database
from src.migrations import apply_pending_migrations
from src.premium_bank_loader import sync_premium_problem_bank


def _premium_problem(problem_id: str, related: str):
    return {
        "problem_id": problem_id,
        "title": f"Title {problem_id}",
        "topic": "Arrays",
        "subtopic": "Hashing",
        "pattern": "Hash Map",
        "difficulty": "Easy",
        "metadata": {"company_tags": ["google"], "source": "internal", "tags": ["array"]},
        "educational_assets": {
            "statement_md": "statement",
            "constraints_md": "constraints",
            "examples_md": "examples",
            "editorial_md": "editorial",
        },
        "hints": [{"order": 1, "text_md": "hint"}],
        "reference_solution": {
            "language": "python",
            "code": "def solve(*args):\n    return 1",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
        },
        "starter_code": {"language": "python", "function_name": "solve", "code": "def solve(*args):\n    return 0"},
        "tests": {
            "visible": [{"input": [1], "expected": 1, "explanation": "minimum_input"}],
            "hidden": [{"input": [2], "expected": 2, "explanation": "boundary_conditions"}],
        },
        "recommendation_graph": {
            "prerequisite": [related] if related else [],
            "alternative": [],
            "follow_up": [],
            "review": [],
            "recovery": [],
        },
        "learning_objectives": ["objective"],
        "common_mistakes": ["mistake"],
        "prerequisites": [],
        "related_problems": [related] if related else [],
        "rag_assets": {
            "statement_chunks": ["statement chunk"],
            "editorial_chunks": ["editorial chunk"],
            "hints_chunks": ["hint chunk"],
            "common_mistakes_chunks": ["mistake chunk"],
            "learning_objectives_chunks": ["objective chunk"],
        },
        "version": 1,
    }


class Phase3BPremiumLoaderTests(unittest.TestCase):
    def test_sync_premium_problem_bank_inserts_core_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "loader.db"
            bank_path = tmp / "problem_bank.json"
            Database(str(db_path))

            payload = {"schema_version": "1.0", "problems": [_premium_problem("p1", "p2"), _premium_problem("p2", "p1")]}
            bank_path.write_text(json.dumps(payload), encoding="utf-8")

            db = Database(str(db_path))
            result = sync_premium_problem_bank(db, bank_path)
            self.assertEqual(result.loaded_count, 2)
            self.assertGreaterEqual(result.relationship_count, 2)
            self.assertGreaterEqual(result.rag_chunk_count, 10)

            conn = db.get_connection()
            cursor = conn.cursor()
            premium_count = cursor.execute(
                "SELECT COUNT(*) AS c FROM problems WHERE dataset_tier = 'premium' AND is_active = 1"
            ).fetchone()["c"]
            hint_count = cursor.execute("SELECT COUNT(*) AS c FROM premium_problem_hints").fetchone()["c"]
            hidden_test_count = cursor.execute(
                "SELECT COUNT(*) AS c FROM premium_problem_tests WHERE visibility = 'hidden'"
            ).fetchone()["c"]
            rag_statement_count = cursor.execute(
                "SELECT COUNT(*) AS c FROM premium_problem_rag_chunks WHERE chunk_type = 'statement'"
            ).fetchone()["c"]
            conn.close()

            self.assertEqual(premium_count, 2)
            self.assertEqual(hint_count, 2)
            self.assertEqual(hidden_test_count, 2)
            self.assertEqual(rag_statement_count, 2)

    def test_sync_premium_problem_bank_rejects_incomplete_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "loader.db"
            bank_path = tmp / "problem_bank.json"
            Database(str(db_path))

            broken = _premium_problem("p1", "")
            del broken["educational_assets"]
            bank_path.write_text(json.dumps({"problems": [broken]}), encoding="utf-8")
            db = Database(str(db_path))
            with self.assertRaises(ValueError):
                sync_premium_problem_bank(db, bank_path)

    def test_migration_does_not_archive_seeded_premium_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "loader.db"
            bank_path = tmp / "problem_bank.json"
            db = Database(str(db_path))

            payload = {"schema_version": "1.0", "problems": [_premium_problem("p1", "p2"), _premium_problem("p2", "p1")]}
            bank_path.write_text(json.dumps(payload), encoding="utf-8")
            sync_premium_problem_bank(db, bank_path)

            apply_pending_migrations(str(db_path))

            conn = db.get_connection()
            cursor = conn.cursor()
            premium_active = cursor.execute(
                "SELECT COUNT(*) AS c FROM problems WHERE dataset_tier = 'premium' AND is_active = 1"
            ).fetchone()["c"]
            conn.close()
            self.assertEqual(premium_active, 2)


if __name__ == "__main__":
    unittest.main()
