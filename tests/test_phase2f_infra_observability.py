import os
import tempfile
import unittest

import yaml

from scripts.db_backup import backup_database
from scripts.db_integrity_check import run_integrity_check
from scripts.db_restore import restore_database
from src.database import Database
from src.migrations import apply_pending_migrations, list_migration_status, rollback_last_migration
from tests.test_phase2d_helpers import isolated_app, register_and_login, seed_problem


class Phase2FInfraObservabilityTests(unittest.TestCase):
    def test_metrics_endpoint_and_domain_metrics(self):
        with isolated_app({"METRICS_ENABLED": "true"}) as (main_module, client):
            seed_problem(main_module, "two-sum")
            session = register_and_login(client, "metrics@example.com", password="demo123")
            headers = {"Authorization": f"Bearer {session['access_token']}"}

            recommend = client.post("/api/recommendations/generate", headers=headers)
            self.assertEqual(recommend.status_code, 200, recommend.text)

            rag = client.post(
                "/api/rag/query",
                headers=headers,
                json={"question": "Give first hint for two sum", "problem_id": "two-sum"},
            )
            self.assertEqual(rag.status_code, 200, rag.text)

            submission = client.post(
                "/api/submissions",
                headers=headers,
                json={
                    "problem_id": "two-sum",
                    "language": "python",
                    "code": "def solve(nums, target):\n    return [0, 1]",
                },
            )
            self.assertEqual(submission.status_code, 200, submission.text)

            metrics = client.get("/api/metrics")
            self.assertEqual(metrics.status_code, 200, metrics.text)
            text = metrics.text
            self.assertIn("ila_http_requests_total", text)
            self.assertIn("ila_db_queries_total", text)
            self.assertIn("ila_judge_executions_total", text)
            self.assertIn("ila_rag_queries_total", text)
            self.assertIn("ila_recommendation_generations_total", text)

    def test_migrations_upgrade_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "migration.db")
            Database(db_path)
            upgrade = apply_pending_migrations(db_path)
            self.assertGreaterEqual(upgrade["total"], 1)
            status_after_upgrade = list_migration_status(db_path)
            self.assertEqual(status_after_upgrade["pending"], [])
            self.assertGreaterEqual(len(status_after_upgrade["applied"]), 1)

            rollback = rollback_last_migration(db_path)
            self.assertIn(rollback["status"], {"rolled_back", "noop"})
            status_after_rollback = list_migration_status(db_path)
            self.assertGreaterEqual(len(status_after_rollback["pending"]), 1)

    def test_database_backup_restore_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_db = os.path.join(tmp_dir, "source.db")
            restored_db = os.path.join(tmp_dir, "restored.db")
            backups_dir = os.path.join(tmp_dir, "backups")

            db = Database(source_db)
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                ("Infra User", "infra@example.com", "hash", "user"),
            )
            conn.commit()
            conn.close()

            backup_path = backup_database(source_db, backups_dir)
            self.assertTrue(os.path.exists(backup_path))

            restore_database(backup_path, restored_db)
            self.assertTrue(os.path.exists(restored_db))

            integrity = run_integrity_check(restored_db)
            self.assertTrue(integrity["quick_check_ok"])
            self.assertTrue(integrity["foreign_key_ok"])

    def test_compose_profiles_healthchecks_and_persistent_volume(self):
        compose_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docker-compose.yml",
        )
        with open(compose_path, "r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)

        services = payload["services"]
        self.assertIn("backend", services)
        self.assertIn("frontend", services)
        self.assertIn("backend-dev", services)
        self.assertIn("frontend-dev", services)
        self.assertIn("prometheus", services)
        self.assertIn("grafana", services)

        self.assertIn("prod", services["backend"]["profiles"])
        self.assertIn("dev", services["backend-dev"]["profiles"])
        self.assertIn("healthcheck", services["backend"])
        self.assertIn("healthcheck", services["frontend"])
        self.assertIn("db_data", payload["volumes"])

    def test_environment_examples_present(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name in (".env.example", ".env.development.example", ".env.production.example"):
            path = os.path.join(root, name)
            self.assertTrue(os.path.exists(path), f"Missing {name}")
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("APP_ENV=", content)
            self.assertIn("SECRET_KEY=", content)

    def test_ci_workflow_contains_required_stages(self):
        workflow_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".github",
            "workflows",
            "ci.yml",
        )
        self.assertTrue(os.path.exists(workflow_path))
        with open(workflow_path, "r", encoding="utf-8") as handle:
            workflow = handle.read()
        for required in (
            "Lint",
            "Formatting",
            "Backend tests with coverage",
            "Security scan",
            "Dependency audit (Python)",
            "Frontend build",
            "Dependency audit (Node)",
            "Docker build backend",
            "Upload backend artifacts",
        ):
            self.assertIn(required, workflow)


if __name__ == "__main__":
    unittest.main()
