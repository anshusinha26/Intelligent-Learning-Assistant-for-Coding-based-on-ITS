import unittest

from tests.test_phase2d_helpers import isolated_app, register_and_login, seed_problem


class Phase2DE2ERegressionTests(unittest.TestCase):
    def test_complete_phase2d_user_journey(self):
        with isolated_app() as (main_module, client):
            seed_problem(main_module, "two-sum")
            seed_problem(main_module, "contains-duplicate")

            session = register_and_login(client, "e2e.user@example.com")
            headers = {"Authorization": f"Bearer {session['access_token']}"}

            me_before = client.get("/api/auth/me", headers=headers)
            self.assertEqual(me_before.status_code, 200, me_before.text)
            self.assertFalse(me_before.json()["email_verified"])

            request_verification = client.post(
                "/api/auth/email-verification/request",
                headers=headers,
            )
            self.assertEqual(request_verification.status_code, 200, request_verification.text)
            verify_otp = request_verification.json().get("dev_otp")
            self.assertTrue(verify_otp)

            verify_email = client.post(
                "/api/auth/email-verification/verify",
                headers=headers,
                json={"otp": verify_otp},
            )
            self.assertEqual(verify_email.status_code, 200, verify_email.text)

            me_after = client.get("/api/auth/me", headers=headers)
            self.assertTrue(me_after.json()["email_verified"])

            create_note = client.post(
                "/api/notes",
                headers=headers,
                json={
                    "title": "Session Note",
                    "content": "Remember edge cases and dry run.",
                    "problem_id": "two-sum",
                    "pinned": False,
                },
            )
            self.assertEqual(create_note.status_code, 200, create_note.text)
            note_id = create_note.json()["note_id"]

            update_note = client.put(
                f"/api/notes/{note_id}",
                headers=headers,
                json={"pinned": True, "content": "Remember edge cases first."},
            )
            self.assertEqual(update_note.status_code, 200, update_note.text)
            self.assertTrue(update_note.json()["pinned"])

            bookmark = client.post(
                "/api/bookmarks",
                headers=headers,
                json={"problem_id": "two-sum"},
            )
            self.assertEqual(bookmark.status_code, 200, bookmark.text)

            bookmarks = client.get("/api/bookmarks", headers=headers)
            self.assertEqual(bookmarks.status_code, 200, bookmarks.text)
            self.assertEqual(bookmarks.json()["count"], 1)

            settings = client.put(
                "/api/settings",
                headers=headers,
                json={
                    "theme": "dark",
                    "editor_language": "python",
                    "daily_goal": 5,
                    "ai_assistant_enabled": True,
                    "email_notifications": True,
                },
            )
            self.assertEqual(settings.status_code, 200, settings.text)
            self.assertEqual(settings.json()["daily_goal"], 5)

            change_password = client.post(
                "/api/auth/change-password",
                headers=headers,
                json={
                    "current_password": "demo123",
                    "new_password": "changed123",
                },
            )
            self.assertEqual(change_password.status_code, 200, change_password.text)

            logout = client.post("/api/auth/logout", headers=headers, json={})
            self.assertEqual(logout.status_code, 200, logout.text)

            old_login = client.post(
                "/api/auth/login",
                json={"email": "e2e.user@example.com", "password": "demo123"},
            )
            self.assertEqual(old_login.status_code, 401)

            new_login = client.post(
                "/api/auth/login",
                json={"email": "e2e.user@example.com", "password": "changed123"},
            )
            self.assertEqual(new_login.status_code, 200, new_login.text)

            forgot = client.post(
                "/api/auth/forgot-password",
                json={"email": "e2e.user@example.com"},
            )
            self.assertEqual(forgot.status_code, 200, forgot.text)
            reset_otp = forgot.json()["dev_otp"]
            self.assertTrue(reset_otp)

            verify_reset_otp = client.post(
                "/api/auth/verify-otp",
                json={
                    "email": "e2e.user@example.com",
                    "otp": reset_otp,
                    "purpose": "password_reset",
                },
            )
            self.assertEqual(verify_reset_otp.status_code, 200, verify_reset_otp.text)
            reset_token = verify_reset_otp.json()["reset_token"]
            self.assertTrue(reset_token)

            reset = client.post(
                "/api/auth/reset-password",
                json={"reset_token": reset_token, "new_password": "final1234"},
            )
            self.assertEqual(reset.status_code, 200, reset.text)

            post_reset_login = client.post(
                "/api/auth/login",
                json={"email": "e2e.user@example.com", "password": "final1234"},
            )
            self.assertEqual(post_reset_login.status_code, 200, post_reset_login.text)

            new_headers = {
                "Authorization": f"Bearer {post_reset_login.json()['access_token']}",
            }
            remove_bookmark = client.delete("/api/bookmarks/two-sum", headers=new_headers)
            self.assertEqual(remove_bookmark.status_code, 200, remove_bookmark.text)
            delete_note = client.delete(f"/api/notes/{note_id}", headers=new_headers)
            self.assertEqual(delete_note.status_code, 200, delete_note.text)


if __name__ == "__main__":
    unittest.main()
