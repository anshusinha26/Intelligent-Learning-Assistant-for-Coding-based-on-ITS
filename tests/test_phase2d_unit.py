import os
import tempfile
import unittest

from src.auth import AuthService
from src.database import Database


class Phase2DUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "unit.db")
        self.db = Database(self.db_path)
        self.auth = AuthService(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _register(self, email="phase2d.unit@example.com", password="demo123"):
        return self.auth.register_user(
            name="Unit User",
            email=email,
            password=password,
            target_level="medium",
        )

    def test_password_reset_with_otp(self):
        user = self._register()

        forgot = self.auth.request_password_reset("phase2d.unit@example.com")
        self.assertTrue(forgot["otp_sent"])
        self.assertIsNotNone(forgot["dev_otp"])

        verified = self.auth.verify_otp(
            email="phase2d.unit@example.com",
            otp=forgot["dev_otp"],
            purpose="password_reset",
        )
        self.assertTrue(verified["verified"])
        self.assertIsNotNone(verified["reset_token"])

        self.auth.reset_password(verified["reset_token"], "newpass123")
        relogin = self.auth.login_user("phase2d.unit@example.com", "newpass123")
        self.assertEqual(relogin["user_id"], user["user_id"])

        with self.assertRaises(ValueError):
            self.auth.login_user("phase2d.unit@example.com", "demo123")

    def test_email_verification_with_otp(self):
        user = self._register(email="verify@example.com")
        request = self.auth.request_email_verification(user["user_id"])
        self.assertTrue(request["otp_sent"])
        self.assertIsNotNone(request["dev_otp"])

        result = self.auth.verify_email_otp(user["user_id"], request["dev_otp"])
        self.assertEqual(result["purpose"], "email_verification")
        self.assertTrue(result["verified"])

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email_verified FROM users WHERE user_id = ?", (user["user_id"],))
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(int(row["email_verified"]), 1)

    def test_change_password_requires_current_password(self):
        user = self._register(email="change@example.com")

        with self.assertRaises(ValueError):
            self.auth.change_password(user["user_id"], "wrong-pass", "newpass123")

        self.auth.change_password(user["user_id"], "demo123", "newpass123")
        relogin = self.auth.login_user("change@example.com", "newpass123")
        self.assertEqual(relogin["user_id"], user["user_id"])

    def test_invalid_otp_raises(self):
        self._register(email="otp-invalid@example.com")
        self.auth.request_password_reset("otp-invalid@example.com")

        with self.assertRaises(ValueError):
            self.auth.verify_otp(
                email="otp-invalid@example.com",
                otp="000000",
                purpose="password_reset",
            )


if __name__ == "__main__":
    unittest.main()
