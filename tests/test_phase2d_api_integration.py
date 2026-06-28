import unittest

from tests.test_phase2d_helpers import isolated_app, register_and_login, seed_problem


class Phase2DAPIIntegrationTests(unittest.TestCase):
    def test_auth_recovery_and_settings_endpoints(self):
        with isolated_app() as (main_module, client):
            seed_problem(main_module, "two-sum")
            session = register_and_login(client, "api.auth@example.com")
            headers = {"Authorization": f"Bearer {session['access_token']}"}

            settings_resp = client.get("/api/settings", headers=headers)
            self.assertEqual(settings_resp.status_code, 200, settings_resp.text)
            self.assertEqual(settings_resp.json()["editor_language"], "python")

            update_resp = client.put(
                "/api/settings",
                headers=headers,
                json={"theme": "dark", "daily_goal": 4, "email_notifications": False},
            )
            self.assertEqual(update_resp.status_code, 200, update_resp.text)
            self.assertEqual(update_resp.json()["theme"], "dark")
            self.assertEqual(update_resp.json()["daily_goal"], 4)
            self.assertFalse(update_resp.json()["email_notifications"])

            forgot = client.post(
                "/api/auth/forgot-password",
                json={"email": "api.auth@example.com"},
            )
            self.assertEqual(forgot.status_code, 200, forgot.text)
            otp = forgot.json()["dev_otp"]
            self.assertIsNotNone(otp)

            bad_verify = client.post(
                "/api/auth/verify-otp",
                json={
                    "email": "api.auth@example.com",
                    "otp": "111111",
                    "purpose": "password_reset",
                },
            )
            self.assertEqual(bad_verify.status_code, 400, bad_verify.text)

            verify = client.post(
                "/api/auth/verify-otp",
                json={
                    "email": "api.auth@example.com",
                    "otp": otp,
                    "purpose": "password_reset",
                },
            )
            self.assertEqual(verify.status_code, 200, verify.text)
            reset_token = verify.json()["reset_token"]
            self.assertTrue(reset_token)

            reset = client.post(
                "/api/auth/reset-password",
                json={"reset_token": reset_token, "new_password": "newpass123"},
            )
            self.assertEqual(reset.status_code, 200, reset.text)

            old_login = client.post(
                "/api/auth/login",
                json={"email": "api.auth@example.com", "password": "demo123"},
            )
            self.assertEqual(old_login.status_code, 401)

            new_login = client.post(
                "/api/auth/login",
                json={"email": "api.auth@example.com", "password": "newpass123"},
            )
            self.assertEqual(new_login.status_code, 200, new_login.text)

    def test_notes_and_bookmarks_crud_endpoints(self):
        with isolated_app() as (main_module, client):
            seed_problem(main_module, "two-sum")
            seed_problem(main_module, "contains-duplicate")
            session = register_and_login(client, "api.notes@example.com")
            headers = {"Authorization": f"Bearer {session['access_token']}"}

            create_note = client.post(
                "/api/notes",
                headers=headers,
                json={
                    "title": "Two Sum Approach",
                    "content": "Use hash map to track complements.",
                    "problem_id": "two-sum",
                    "pinned": True,
                },
            )
            self.assertEqual(create_note.status_code, 200, create_note.text)
            note = create_note.json()
            self.assertTrue(note["pinned"])

            list_notes = client.get("/api/notes?limit=10&q=hash", headers=headers)
            self.assertEqual(list_notes.status_code, 200, list_notes.text)
            self.assertEqual(list_notes.json()["count"], 1)

            update_note = client.put(
                f"/api/notes/{note['note_id']}",
                headers=headers,
                json={"title": "Updated Note", "content": "Optimized with map", "pinned": False},
            )
            self.assertEqual(update_note.status_code, 200, update_note.text)
            self.assertEqual(update_note.json()["title"], "Updated Note")
            self.assertFalse(update_note.json()["pinned"])

            bookmark = client.post(
                "/api/bookmarks",
                headers=headers,
                json={"problem_id": "contains-duplicate"},
            )
            self.assertEqual(bookmark.status_code, 200, bookmark.text)
            self.assertEqual(bookmark.json()["problem_id"], "contains-duplicate")

            list_bookmarks = client.get("/api/bookmarks?limit=10", headers=headers)
            self.assertEqual(list_bookmarks.status_code, 200, list_bookmarks.text)
            self.assertEqual(list_bookmarks.json()["count"], 1)

            delete_bookmark = client.delete(
                "/api/bookmarks/contains-duplicate",
                headers=headers,
            )
            self.assertEqual(delete_bookmark.status_code, 200, delete_bookmark.text)

            delete_note = client.delete(f"/api/notes/{note['note_id']}", headers=headers)
            self.assertEqual(delete_note.status_code, 200, delete_note.text)


if __name__ == "__main__":
    unittest.main()
