import json
import tempfile
import unittest
from pathlib import Path

from app import db


class AppBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db.DB_PATH = Path(self.tmp.name)
        from app.app import create_app
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test"})
        self.c = self.app.test_client()
        self.c.get("/")
        with self.c.session_transaction() as s:
            self.tok = s["csrf"]

    def token(self):
        with self.c.session_transaction() as s:
            tok = s.get("csrf")
        if not tok:                       # session was cleared (login/logout) - a page view issues a new token
            self.c.get("/")
            with self.c.session_transaction() as s:
                tok = s["csrf"]
        return tok

    def post(self, url, **data):
        data["csrf_token"] = self.token()
        return self.c.post(url, data=data)

    def register(self, u="alice", p="correct-horse"):
        return self.post("/register", username=u, password=p, password2=p, consent="1")


class TestPages(AppBase):
    def test_pages(self):
        for url in ["/", "/timeline", "/phq9", "/chat", "/login", "/register", "/dashboard", "/resources", "/about", "/health"]:
            self.assertEqual(self.c.get(url).status_code, 200, url)

    def test_headers(self):
        r = self.c.get("/")
        self.assertEqual(r.headers["X-Frame-Options"], "DENY"); self.assertIn("script-src 'self'", r.headers["Content-Security-Policy"])

    def test_404(self):
        self.assertEqual(self.c.get("/nope").status_code, 404)


class TestSecurity(AppBase):
    def test_csrf_required(self):
        self.assertEqual(self.c.post("/analyze", data={"text": "i feel empty"}).status_code, 400)
        self.assertEqual(self.c.post("/analyze", data={"text": "i feel empty", "csrf_token": "bad"}).status_code, 400)

    def test_history_requires_login(self):
        self.assertEqual(self.c.get("/history").status_code, 401)

    def test_xss_escaped(self):
        r = self.post("/analyze", text="<script>alert(1)</script> i feel empty and hopeless")
        self.assertNotIn(b"<script>alert(1)</script>", r.data)

    def test_oversize_upload(self):
        r = self.c.post("/timeline", data={"csrf_token": self.tok, "file": (__import__("io").BytesIO(b"x" * 1_200_000), "a.txt")},
                        content_type="multipart/form-data")
        self.assertEqual(r.status_code, 413)


class TestAnalysis(AppBase):
    def test_api(self):
        r = self.c.post("/api/analyze", json={"text": "i feel empty and alone and tired of everything"})
        self.assertEqual(r.status_code, 200); self.assertIn("level", r.get_json()["result"])
        self.assertEqual(self.c.post("/api/analyze", json={"text": "hi"}).status_code, 400)

    def test_crisis_page_shows_helpline(self):
        self.assertIn(b"14416", self.post("/analyze", text="i want to kill myself").data)

    def test_unsupported_language(self):
        r = self.post("/analyze", text="நான் மிகவும் சோகமாக இருக்கிறேன்")
        self.assertIn(b"UNSUPPORTED", r.data)

    def test_timeline_upload(self):
        raw = Path("data/sample_timeline.txt").read_bytes()
        r = self.c.post("/timeline", data={"csrf_token": self.tok, "file": (__import__("io").BytesIO(raw), "t.txt")},
                        content_type="multipart/form-data")
        self.assertEqual(r.status_code, 200); self.assertIn(b"worsening", r.data)

    def test_chat_api(self):
        self.c.get("/chat")
        r = self.c.post("/api/chat", json={"message": "i want to die"}, headers={"X-CSRF-Token": self.tok})
        self.assertEqual(r.get_json()["level"], "CRISIS")
        self.assertEqual(self.c.post("/api/chat", json={"message": "hi"}).status_code, 400)

    def test_phq9_flow(self):
        r = self.post("/phq9", **{f"q{i}": "1" for i in range(9)})
        self.assertIn(b"Mild", r.data)
        r = self.post("/phq9", **{**{f"q{i}": "0" for i in range(8)}, "q8": "2"})
        self.assertIn(b"14416", r.data)
        self.assertEqual(self.post("/phq9", q0="1").status_code, 400)


class TestAccounts(AppBase):
    def test_register_login_history_delete(self):
        self.assertEqual(self.register().status_code, 302)
        self.post("/analyze", text="i feel empty and hopeless and alone")
        h = self.c.get("/history")
        self.assertEqual(h.status_code, 200); self.assertIn(b"alice", h.data)
        exp = json.loads(self.c.get("/account/export").data)
        self.assertEqual(len(exp["analyses"]), 1); self.assertIsNone(exp["analyses"][0].get("text"))
        self.assertEqual(self.post("/account/delete", password="wrong").status_code, 400)
        self.assertEqual(self.post("/account/delete", password="correct-horse").status_code, 200)
        self.assertIsNone(db.get_user_by_name("alice")); self.assertEqual(self.c.get("/history").status_code, 401)

    def test_validation_and_duplicates(self):
        self.assertEqual(self.post("/register", username="a", password="longenough", password2="longenough", consent="1").status_code, 400)
        self.assertEqual(self.post("/register", username="bobby", password="short", password2="short", consent="1").status_code, 400)
        self.assertEqual(self.post("/register", username="bobby", password="longenough", password2="longenough").status_code, 400)
        self.register("carol"); self.post("/logout")
        self.assertEqual(self.register("Carol").status_code, 400)

    def test_login_wrong_password(self):
        self.register("dave"); self.post("/logout")
        self.assertEqual(self.post("/login", username="dave", password="nope-nope").status_code, 401)
        self.assertEqual(self.post("/login", username="dave", password="correct-horse").status_code, 302)

    def test_password_not_stored_plain(self):
        self.register("erin")
        self.assertNotIn("correct-horse", db.get_user_by_name("erin")["pw_hash"])

    def test_no_raw_text_stored(self):
        self.register("fred"); self.post("/analyze", text="i feel empty and hopeless and alone")
        self.assertIsNone(db._exec("SELECT text FROM analyses", many=True)[0]["text"])


if __name__ == "__main__":
    unittest.main()
