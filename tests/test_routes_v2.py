"""Tests for MindWatch 2.0 new routes and user flows."""
import json
import tempfile
import unittest
from pathlib import Path

from app import db


class TestRoutesV2(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db.DB_PATH = Path(self.tmp.name)
        from app.app import create_app
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-v2"})
        self.c = self.app.test_client()
        self.c.get("/")
        with self.c.session_transaction() as s:
            self.tok = s["csrf"]

    def token(self):
        with self.c.session_transaction() as s:
            tok = s.get("csrf")
        if not tok:
            self.c.get("/")
            with self.c.session_transaction() as s:
                tok = s["csrf"]
        return tok

    def register(self, u="charlie", p="strong-pass-123"):
        return self.c.post("/register", data={
            "csrf_token": self.token(),
            "username": u,
            "password": p,
            "password2": p,
            "consent": "1"
        })

    def test_self_check_hub_page(self):
        r = self.c.get("/self-check")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"PHQ-9", r.data)
        self.assertIn(b"GAD-7", r.data)
        self.assertIn(b"Sleep", r.data)
        self.assertIn(b"Academic", r.data)
        self.assertIn(b"Motivation", r.data)

    def test_self_check_wizard_flow(self):
        # GET category wizard
        r_get = self.c.get("/self-check/gad7")
        self.assertEqual(r_get.status_code, 200)
        self.assertIn(b"GAD-7", r_get.data)

        # POST complete GAD-7 answers
        data = {"csrf_token": self.token()}
        for i in range(7):
            data[f"q{i}"] = "1"
        r_post = self.c.post("/self-check/gad7", data=data)
        self.assertEqual(r_post.status_code, 200)
        self.assertIn(b"Mild", r_post.data)

    def test_settings_flow(self):
        # Settings requires login
        self.assertEqual(self.c.get("/settings").status_code, 401)

        # Register and access settings
        self.register("maya", "secret-key-123")
        r_set = self.c.get("/settings")
        self.assertEqual(r_set.status_code, 200)
        self.assertIn(b"maya", r_set.data)

        # Update preferences
        r_pref = self.c.post("/settings/preferences", data={
            "csrf_token": self.token(),
            "user_type": "postgraduate",
            "theme": "dark"
        })
        self.assertEqual(r_pref.status_code, 200)
        u = db.get_user_by_name("maya")
        self.assertIn("postgraduate", u["preferences"])

        # Update password
        r_pw = self.c.post("/settings/password", data={
            "csrf_token": self.token(),
            "current_password": "secret-key-123",
            "new_password": "brand-new-password",
            "confirm_password": "brand-new-password"
        })
        self.assertEqual(r_pw.status_code, 200)

    def test_timeline_export(self):
        # Analyze a timeline first
        with self.c.session_transaction() as s:
            s["last_timeline"] = {
                "weeks": [{"week": "2026-W40", "mean_risk": 0.45, "posts": 2}],
                "months": [{"month": "2026-10", "mean_risk": 0.45, "posts": 2}],
                "days": []
            }
        r_csv = self.c.get("/timeline/export?format=csv")
        self.assertEqual(r_csv.status_code, 200)
        self.assertIn(b"2026-W40", r_csv.data)

        r_json = self.c.get("/timeline/export?format=json")
        self.assertEqual(r_json.status_code, 200)
        data = json.loads(r_json.data)
        self.assertEqual(data["weeks"][0]["week"], "2026-W40")


if __name__ == "__main__":
    unittest.main()
