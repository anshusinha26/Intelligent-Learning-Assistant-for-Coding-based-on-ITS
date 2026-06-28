import json
import tempfile
import unittest
from pathlib import Path

from curriculum_validator import recommendation_quality_checks
from metadata_validator import run_metadata_validation
from problem_validator import validate_inventory
from scripts.phase3_common import load_inventory
from solution_validator import run_solution_audit
from src.database import Database
from src.migrations import apply_pending_migrations
from src.premium_bank_loader import sync_premium_problem_bank
from testcase_validator import run_testcase_audit
from tests.test_phase2d_helpers import isolated_app, register_and_login


BANK_PATH = Path("data/premium/problem_bank.json")
CURRICULUM_PATH = Path("data/premium/curriculum/curriculum.json")


class Phase3DPremiumGenerationTests(unittest.TestCase):
    def test_problem_bank_contains_first_25_curriculum_problems(self):
        bank_payload = json.loads(BANK_PATH.read_text(encoding="utf-8"))
        curriculum_payload = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
        total_curriculum = len(curriculum_payload["problems"])

        self.assertEqual(bank_payload.get("problem_count"), total_curriculum)
        problems = bank_payload.get("problems") or []
        self.assertEqual(len(problems), total_curriculum)

        expected_slugs = [item["slug"] for item in curriculum_payload["problems"]]
        actual_slugs = [problem["problem_id"] for problem in problems]
        self.assertEqual(actual_slugs, expected_slugs)

        for problem in problems:
            self.assertGreaterEqual(len(problem["tests"]["visible"]), 5)
            self.assertLessEqual(len(problem["tests"]["visible"]), 10)
            self.assertGreaterEqual(len(problem["tests"]["hidden"]), 20)
            self.assertLessEqual(len(problem["tests"]["hidden"]), 50)
            self.assertEqual(problem["starter_code"]["language"], "python")
            self.assertEqual(problem["reference_solution"]["language"], "python")
            self.assertTrue(problem["educational_assets"]["statement_md"].strip())
            self.assertTrue(problem["educational_assets"]["constraints_md"].strip())
            self.assertTrue(problem["educational_assets"]["examples_md"].strip())
            self.assertTrue(problem["educational_assets"]["editorial_md"].strip())
            self.assertGreaterEqual(len(problem["hints"]), 3)

    def test_loader_and_validators_pass_without_critical_issues(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "phase3d.db"
            db = Database(str(db_path))
            total_curriculum = len(json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))["problems"])
            result = sync_premium_problem_bank(db, BANK_PATH)
            self.assertEqual(result.loaded_count, total_curriculum)

            apply_pending_migrations(str(db_path))
            conn = db.get_connection()
            cursor = conn.cursor()
            active_count = cursor.execute(
                "SELECT COUNT(*) AS c FROM problems WHERE dataset_tier='premium' AND is_active=1"
            ).fetchone()["c"]
            conn.close()
            self.assertEqual(active_count, total_curriculum)

            inventory, _ = load_inventory(db_path, Path("unused.csv"), Path("unused.md"))
            issues, _ = validate_inventory(inventory)
            self.assertEqual(len(issues["critical"]), 0)

            metadata_issues = run_metadata_validation(inventory)
            self.assertEqual(len(metadata_issues["critical"]), 0)

            solution = run_solution_audit(db_path)
            self.assertEqual(len(solution["issues"]["critical"]), 0)

            testcase = run_testcase_audit(db_path, apply=False)
            self.assertEqual(len(testcase["issues"]["critical"]), 0)

            rec_issues, _rec_meta = recommendation_quality_checks(db_path)
            self.assertEqual(len(rec_issues["critical"]), 0)

    def test_api_integration_lists_and_fetches_generated_problems(self):
        with isolated_app() as (main_module, client):
            sync_premium_problem_bank(main_module.db, BANK_PATH)
            session = register_and_login(client, "phase3d.integration@example.com")
            headers = {"Authorization": f"Bearer {session['access_token']}"}
            total_curriculum = len(json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))["problems"])

            list_resp = client.get("/api/problems?limit=100", headers=headers)
            self.assertEqual(list_resp.status_code, 200, list_resp.text)
            payload = list_resp.json()
            self.assertEqual(len(payload), total_curriculum)

            first_problem_id = payload[0]["problem_id"]
            detail_resp = client.get(f"/api/problems/{first_problem_id}", headers=headers)
            self.assertEqual(detail_resp.status_code, 200, detail_resp.text)
            detail = detail_resp.json()
            self.assertTrue(detail["description"])
            self.assertTrue(detail["constraints"])
            self.assertTrue(detail["examples"])


if __name__ == "__main__":
    unittest.main()
