import json
import unittest

from tests.test_phase2d_helpers import isolated_app, register_and_login


def _seed_problem(main_module, problem_id: str, title: str, dataset_tier: str, is_active: int):
    conn = main_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO problems (
            problem_id, title, topic, pattern, difficulty, tags, description,
            constraints, examples, source_url, function_name, starter_code, test_cases,
            dataset_tier, is_active, curriculum_version, time_complexity, space_complexity,
            metadata_json, learning_objectives_json, common_mistakes_json, recommendation_graph_json
        ) VALUES (?, ?, 'Arrays', 'Hash Map', 'Easy', 'array,hash-table', ?, 'n>=2',
                  'sample', 'https://example.com', 'solve', ?, ?, ?, ?, 1, 'O(n)', 'O(n)', ?, ?, ?, ?)
    """,
        (
            problem_id,
            title,
            f"{title} description",
            "def solve(nums, target):\n    return []\n",
            json.dumps([{"input": [[2, 7, 11, 15], 9], "expected": [0, 1]}]),
            dataset_tier,
            is_active,
            json.dumps({"company_tags": ["google"], "source": "test", "tags": ["array"]}),
            json.dumps(["objective"]),
            json.dumps(["mistake"]),
            json.dumps({"prerequisite": [], "alternative": [], "follow_up": [], "review": [], "recovery": []}),
        ),
    )
    conn.commit()
    conn.close()


class Phase3BPremiumIntegrationTests(unittest.TestCase):
    def test_legacy_rows_hidden_from_problem_api_and_recommendations(self):
        with isolated_app() as (main_module, client):
            _seed_problem(main_module, "legacy-two-sum", "Legacy Two Sum", "legacy", 0)
            _seed_problem(main_module, "premium-two-sum", "Premium Two Sum", "premium", 1)

            session = register_and_login(client, "phase3b.integration@example.com")
            headers = {"Authorization": f"Bearer {session['access_token']}"}

            problems_resp = client.get("/api/problems?limit=20", headers=headers)
            self.assertEqual(problems_resp.status_code, 200, problems_resp.text)
            problem_ids = {item["problem_id"] for item in problems_resp.json()}
            self.assertIn("premium-two-sum", problem_ids)
            self.assertNotIn("legacy-two-sum", problem_ids)

            premium_detail = client.get("/api/problems/premium-two-sum", headers=headers)
            self.assertEqual(premium_detail.status_code, 200, premium_detail.text)

            legacy_detail = client.get("/api/problems/legacy-two-sum", headers=headers)
            self.assertEqual(legacy_detail.status_code, 404, legacy_detail.text)

            rec_resp = client.post("/api/recommendations/generate?top_k=5", headers=headers)
            self.assertEqual(rec_resp.status_code, 200, rec_resp.text)
            rec_ids = {item["problem_id"] for item in rec_resp.json()["recommendations"]}
            self.assertNotIn("legacy-two-sum", rec_ids)

    def test_rag_and_submission_resolve_only_against_premium_problem(self):
        with isolated_app() as (main_module, client):
            _seed_problem(main_module, "legacy-a", "Legacy A", "legacy", 0)
            _seed_problem(main_module, "premium-a", "Premium A", "premium", 1)
            conn = main_module.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO premium_problem_rag_chunks (
                    chunk_id, problem_id, version, chunk_type, chunk_text, embedding_model, embedding_vector, content_hash
                ) VALUES (1, 'premium-a', 1, 'statement', 'premium chunk', 'sha256-lite', '[0.1]', 'hash')
            """
            )
            conn.commit()
            conn.close()

            session = register_and_login(client, "phase3b.rag@example.com")
            headers = {"Authorization": f"Bearer {session['access_token']}"}

            bad_submit = client.post(
                "/api/submissions",
                headers=headers,
                json={"problem_id": "legacy-a", "language": "python", "code": "def solve(*args):\n    return []"},
            )
            self.assertEqual(bad_submit.status_code, 404, bad_submit.text)

            good_submit = client.post(
                "/api/submissions",
                headers=headers,
                json={
                    "problem_id": "premium-a",
                    "language": "python",
                    "code": "def solve(nums, target):\n    return [0, 1]",
                },
            )
            self.assertEqual(good_submit.status_code, 200, good_submit.text)

            rag_resp = client.post(
                "/api/rag/query",
                headers=headers,
                json={"question": "hint", "problem_id": "premium-a"},
            )
            self.assertEqual(rag_resp.status_code, 200, rag_resp.text)
            self.assertTrue(rag_resp.json()["rag_available"])

            rag_legacy = client.post(
                "/api/rag/query",
                headers=headers,
                json={"question": "hint", "problem_id": "legacy-a"},
            )
            self.assertEqual(rag_legacy.status_code, 200, rag_legacy.text)
            self.assertEqual(rag_legacy.json()["source"], "local-rag")


if __name__ == "__main__":
    unittest.main()
