"""SQLite persistence for MindWatch 2.0.

Privacy-first:
- Raw text is NEVER stored unless MINDWATCH_STORE_TEXT=1 is explicitly enabled.
- Password hashes use modern cryptographic algorithms.
- Complete user data export (JSON) and cascading account deletion.
- Multi-category assessments table for PHQ-9, GAD-7, and student lifestyle screeners.
- Non-destructive schema migration preserving existing databases.
"""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import config

DB_PATH = config.DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL COLLATE NOCASE,
  pw_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  preferences TEXT
);

CREATE TABLE IF NOT EXISTS analyses(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  probability REAL,
  level TEXT NOT NULL,
  crisis INTEGER NOT NULL,
  themes TEXT,
  text TEXT,
  signals TEXT,
  key_terms TEXT,
  explanation TEXT
);

CREATE TABLE IF NOT EXISTS phq9(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  total INTEGER NOT NULL,
  band TEXT NOT NULL,
  item9 INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS assessments(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  category TEXT NOT NULL,
  test_type TEXT NOT NULL,
  total INTEGER NOT NULL,
  max_score INTEGER NOT NULL,
  band TEXT NOT NULL,
  item_flags TEXT,
  answers TEXT NOT NULL,
  guidance TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _migrate(conn: sqlite3.Connection):
    """Ensure non-destructive addition of new columns to pre-existing tables."""
    # Check users table
    user_cols = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "preferences" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN preferences TEXT")

    # Check analyses table
    analysis_cols = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)").fetchall()}
    if "signals" not in analysis_cols:
        conn.execute("ALTER TABLE analyses ADD COLUMN signals TEXT")
    if "key_terms" not in analysis_cols:
        conn.execute("ALTER TABLE analyses ADD COLUMN key_terms TEXT")
    if "explanation" not in analysis_cols:
        conn.execute("ALTER TABLE analyses ADD COLUMN explanation TEXT")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(SCHEMA)
    _migrate(c)
    return c


def _exec(sql: str, params: tuple = (), many: bool = False) -> Any:
    with closing(_conn()) as c, c:
        cur = c.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()] if cur.description else []
        return rows if many or rows else (cur.lastrowid if not cur.description else rows)


# ---------------------------------------------------------------- Accounts
def create_user(username: str, pw_hash: str) -> Optional[int]:
    try:
        return _exec(
            "INSERT INTO users(username, pw_hash, created_at, preferences) VALUES (?, ?, ?, ?)",
            (username, pw_hash, _now(), json.dumps({"theme": "light", "user_type": "student"}))
        )
    except sqlite3.IntegrityError:
        return None


def get_user_by_name(username: str) -> Optional[Dict[str, Any]]:
    r = _exec("SELECT * FROM users WHERE username = ?", (username,), many=True)
    return r[0] if r else None


def get_user(uid: int) -> Optional[Dict[str, Any]]:
    r = _exec("SELECT id, username, created_at, preferences FROM users WHERE id = ?", (uid,), many=True)
    if not r:
        return None
    user = r[0]
    if user.get("preferences"):
        try:
            user["preferences"] = json.loads(user["preferences"])
        except Exception:
            user["preferences"] = {}
    else:
        user["preferences"] = {}
    return user


def update_user_password(uid: int, new_pw_hash: str) -> None:
    _exec("UPDATE users SET pw_hash = ? WHERE id = ?", (new_pw_hash, uid))


def update_user_preferences(uid: int, prefs: Dict[str, Any]) -> None:
    _exec("UPDATE users SET preferences = ? WHERE id = ?", (json.dumps(prefs), uid))


# ---------------------------------------------------------------- Text Analyses
def save_analysis(result: Dict[str, Any], text: str, user_id: Optional[int] = None) -> int:
    signals_json = json.dumps(result.get("signals")) if result.get("signals") else None
    explanation_json = json.dumps(result.get("explanation")) if result.get("explanation") else None
    key_terms_str = ", ".join(result.get("key_terms", []))

    return _exec(
        "INSERT INTO analyses(user_id, created_at, probability, level, crisis, themes, text, signals, key_terms, explanation) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            _now(),
            result.get("probability"),
            result.get("level"),
            int(result.get("crisis", False)),
            ", ".join(result.get("themes", [])),
            text if config.STORE_RAW_TEXT else None,
            signals_json,
            key_terms_str,
            explanation_json
        )
    )


def user_history(uid: int, limit: int = 200) -> List[Dict[str, Any]]:
    """Retrieve private analysis history for a specific user."""
    rows = _exec(
        "SELECT id, created_at, probability, level, crisis, themes, signals, key_terms, explanation "
        "FROM analyses WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (uid, limit),
        many=True
    )
    for r in rows:
        if r.get("signals"):
            try:
                r["signals"] = json.loads(r["signals"])
            except Exception:
                r["signals"] = {}
        if r.get("explanation"):
            try:
                r["explanation"] = json.loads(r["explanation"])
            except Exception:
                r["explanation"] = {}
    return rows


def user_latest_analysis(uid: int) -> Optional[Dict[str, Any]]:
    rows = user_history(uid, limit=1)
    return rows[0] if rows else None


def user_analyses_count(uid: int) -> int:
    rows = _exec("SELECT COUNT(*) AS c FROM analyses WHERE user_id = ?", (uid,), many=True)
    return rows[0]["c"] if rows else 0


# ---------------------------------------------------------------- Assessments
def save_phq9(res: Dict[str, Any], user_id: Optional[int] = None) -> None:
    """Save to legacy phq9 table and assessments table for full synchronization."""
    _exec(
        "INSERT INTO phq9(user_id, created_at, total, band, item9) VALUES (?, ?, ?, ?, ?)",
        (user_id, _now(), res["total"], res["band"], int(res.get("item9_flag", False)))
    )

    # Synchronize into assessments table
    answers = res.get("answers", [])
    _exec(
        "INSERT INTO assessments(user_id, created_at, category, test_type, total, max_score, band, item_flags, answers, guidance) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            _now(),
            "phq9",
            "Mood (PHQ-9)",
            res["total"],
            27,
            res["band"],
            json.dumps({"item9_flag": res.get("item9_flag", False)}),
            json.dumps(answers),
            res.get("guidance", "")
        )
    )


def save_assessment(res: Dict[str, Any], user_id: Optional[int] = None) -> int:
    """Save an assessment result across any category."""
    cat_id = res.get("category_id", "phq9")

    # If it is phq9, keep legacy table in sync
    if cat_id == "phq9":
        _exec(
            "INSERT INTO phq9(user_id, created_at, total, band, item9) VALUES (?, ?, ?, ?, ?)",
            (user_id, _now(), res["total"], res["band"], int(res.get("item9_flag", False)))
        )

    return _exec(
        "INSERT INTO assessments(user_id, created_at, category, test_type, total, max_score, band, item_flags, answers, guidance) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            _now(),
            cat_id,
            res.get("category_title", cat_id.upper()),
            res["total"],
            res.get("max_score", 27),
            res["band"],
            json.dumps({"item9_flag": res.get("item9_flag", False), "high_distress": res.get("high_distress", False)}),
            json.dumps(res.get("answers", [])),
            res.get("guidance", "")
        )
    )


def user_phq9(uid: int) -> List[Dict[str, Any]]:
    return _exec(
        "SELECT created_at, total, band, item9 FROM phq9 WHERE user_id = ? ORDER BY id DESC",
        (uid,),
        many=True
    )


def user_assessments(uid: int, category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    if category:
        rows = _exec(
            "SELECT id, created_at, category, test_type, total, max_score, band, item_flags, answers, guidance "
            "FROM assessments WHERE user_id = ? AND category = ? ORDER BY id DESC LIMIT ?",
            (uid, category, limit),
            many=True
        )
    else:
        rows = _exec(
            "SELECT id, created_at, category, test_type, total, max_score, band, item_flags, answers, guidance "
            "FROM assessments WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (uid, limit),
            many=True
        )

    for r in rows:
        if r.get("item_flags"):
            try:
                r["item_flags"] = json.loads(r["item_flags"])
            except Exception:
                r["item_flags"] = {}
        if r.get("answers"):
            try:
                r["answers"] = json.loads(r["answers"])
            except Exception:
                r["answers"] = []
    return rows


def user_latest_assessment(uid: int) -> Optional[Dict[str, Any]]:
    rows = user_assessments(uid, limit=1)
    return rows[0] if rows else None


def user_assessments_count(uid: int) -> int:
    rows = _exec("SELECT COUNT(*) AS c FROM assessments WHERE user_id = ?", (uid,), many=True)
    return rows[0]["c"] if rows else 0


# ---------------------------------------------------------------- Dashboard & Privacy
def summary() -> Dict[str, Any]:
    """Anonymous aggregate statistics for public dashboard."""
    total_analyses = _exec("SELECT COUNT(*) AS n FROM analyses", many=True)[0]["n"]
    by_level = {
        r["level"]: r["n"]
        for r in _exec("SELECT level, COUNT(*) AS n FROM analyses GROUP BY level", many=True)
    }
    avg = _exec("SELECT AVG(probability) AS a FROM analyses WHERE probability IS NOT NULL", many=True)[0]["a"]
    total_assessments = _exec("SELECT COUNT(*) AS n FROM assessments", many=True)[0]["n"]

    return {
        "total": total_analyses,
        "total_assessments": total_assessments,
        "by_level": by_level,
        "avg_probability": round(avg, 3) if avg is not None else None
    }


def delete_user(uid: int) -> None:
    """Cascade delete user account and all private associated data."""
    _exec("DELETE FROM assessments WHERE user_id = ?", (uid,))
    _exec("DELETE FROM phq9 WHERE user_id = ?", (uid,))
    _exec("DELETE FROM analyses WHERE user_id = ?", (uid,))
    _exec("DELETE FROM users WHERE id = ?", (uid,))


def export_user(uid: int) -> Dict[str, Any]:
    """Export complete private data package for the authenticated user."""
    return {
        "user": get_user(uid),
        "analyses": user_history(uid, 10000),
        "assessments": user_assessments(uid, limit=10000),
        "phq9": user_phq9(uid)
    }
