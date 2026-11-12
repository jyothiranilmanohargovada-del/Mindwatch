"""MindWatch 2.0 Flask Application.
Run:  python -m app.app   (from the project root)
"""
import io
import json
import os
import re
import secrets
import time
from collections import defaultdict
from datetime import date, datetime
from typing import Optional

from flask import (Flask, Response, abort, jsonify, redirect, render_template, request, session,
                   url_for)
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash

import config
from app import db
from src import assessments
from src import chat as chat_engine
from src import phq9
from src.assistant import build_response, load_resources
from src.predict import analyze_post
from src.timeline import (analyze_timeline, generate_timeline_csv, parse_upload)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
_LOGIN_ATTEMPTS = defaultdict(list)


def sparkline(values, width=600, height=120, pad=12):
    """Generate SVG sparkline curve with threshold guide."""
    if len(values) < 2:
        return Markup("")
    n = len(values)
    pts = " ".join(f"{pad + i * (width - 2 * pad) / (n - 1):.1f},{height - pad - float(v) * (height - 2 * pad):.1f}"
                   for i, v in enumerate(values))
    mod_thresh = config.thresholds()[0]
    mod_y = height - pad - mod_thresh * (height - 2 * pad)
    return Markup(
        f'<svg viewBox="0 0 {width} {height}" class="spark" role="img" aria-label="Risk over time">'
        f'<line x1="{pad}" x2="{width - pad}" y1="{mod_y:.1f}" y2="{mod_y:.1f}" stroke="#d97706" stroke-dasharray="4 4"/>'
        f'<polyline fill="none" stroke="#4f46e5" stroke-width="2.5" points="{pts}"/></svg>')


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        MAX_CONTENT_LENGTH=1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("MINDWATCH_HTTPS", "0") == "1"
    )
    if test_config:
        app.config.update(test_config)

    # ---------------------------------------------------------------- Security & Context
    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        return session["csrf"]

    @app.before_request
    def csrf_protect():
        if request.method == "POST" and request.path != "/api/analyze":
            sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            if not sent or not secrets.compare_digest(sent, session.get("csrf", "")):
                abort(400, "Invalid or missing CSRF token")

    @app.after_request
    def headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'"
        )
        if request.path.startswith(("/history", "/account", "/settings", "/dashboard")):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.context_processor
    def inject():
        uid = session.get("uid")
        user = db.get_user(uid) if uid else None
        return {"csrf_token": csrf_token, "user": user}

    def current_uid():
        return session.get("uid")

    def login_required():
        if not current_uid() or not db.get_user(current_uid()):
            session.pop("uid", None)
            abort(401)

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(404)
    @app.errorhandler(413)
    @app.errorhandler(429)
    def err(e):
        msg = {
            400: "Bad request.",
            401: "Please log in first to access this private page.",
            404: "Page not found.",
            413: "That file is too large (1 MB max).",
            429: "Too many login attempts. Please wait a few minutes."
        }
        return render_template("error.html", code=e.code, msg=msg.get(e.code, e.description)), e.code

    # ---------------------------------------------------------------- Analysis Routes
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/analyze")
    def analyze():
        text = (request.form.get("text") or "").strip()[: config.MAX_TEXT_CHARS]
        if len(text) < 5:
            return render_template("index.html", error="Please enter a longer text (minimum 5 characters)."), 400

        uid = current_uid()
        prev_analysis = db.user_latest_analysis(uid) if uid else None
        res = analyze_post(text, previous_analysis=prev_analysis)
        db.save_analysis(res, text, uid)

        return render_template("result.html", res=res, help=build_response(res["level"], res["themes"]))

    @app.post("/api/analyze")
    def api_analyze():
        data = request.get_json(silent=True) or {}
        text = str(data.get("text", "")).strip()[: config.MAX_TEXT_CHARS]
        if len(text) < 5:
            return jsonify(error="'text' must be at least 5 characters"), 400

        res = analyze_post(text)
        db.save_analysis(res, text, None)
        return jsonify(result=res, assistance=build_response(res["level"], res["themes"]))

    # ---------------------------------------------------------------- Self-Check Hub & Wizard
    @app.get("/self-check")
    def self_check_hub():
        uid = current_uid()
        previous_scores = {}
        if uid:
            for cat_id in assessments.CATEGORIES:
                latest = db.user_assessments(uid, category=cat_id, limit=1)
                if latest:
                    previous_scores[cat_id] = latest[0]

        return render_template("self_check_hub.html", categories=assessments.CATEGORIES, previous_scores=previous_scores)

    @app.route("/self-check/<cat_id>", methods=["GET", "POST"])
    def self_check_wizard(cat_id):
        cat = assessments.get_category(cat_id)
        if request.method == "GET":
            return render_template("self_check_wizard.html", cat=cat)

        try:
            answers = []
            for i in range(len(cat["items"])):
                val_str = request.form.get(f"q{i}")
                answers.append(int(val_str) if val_str is not None and val_str != "" else None)
            res = assessments.score_assessment(cat_id, answers, allow_skip=True)
        except (KeyError, ValueError) as ex:
            return render_template("self_check_wizard.html", cat=cat, error=str(ex)), 400

        db.save_assessment(res, current_uid())
        resources = load_resources() if res["high_distress"] else []
        return render_template("self_check_result.html", res=res, resources=resources)

    # ---------------------------------------------------------------- Legacy PHQ-9 Flow
    @app.route("/phq9", methods=["GET", "POST"])
    def phq9_page():
        if request.method == "GET":
            return render_template("phq9.html", items=phq9.ITEMS, options=phq9.OPTIONS)
        try:
            answers = [int(request.form[f"q{i}"]) for i in range(9)]
            res = phq9.score(answers)
        except (KeyError, ValueError):
            return render_template("phq9.html", items=phq9.ITEMS, options=phq9.OPTIONS,
                                   error="Please answer every question."), 400
        db.save_phq9(res, current_uid())
        resources = load_resources() if (res["item9_flag"] or res["total"] >= 10) else []
        return render_template("phq9_result.html", res=res, resources=resources,
                               disclaimer=build_response("LOW", [])["disclaimer"])

    # ---------------------------------------------------------------- Support Chat
    @app.get("/chat")
    def chat_page():
        session["chat"] = chat_engine.start_state()
        return render_template("chat.html")

    @app.post("/api/chat")
    def api_chat():
        data = request.get_json(silent=True) or {}
        msg = str(data.get("message", ""))[:1000]
        state = session.get("chat") or chat_engine.start_state()
        out = chat_engine.reply(msg, state)
        session["chat"] = state
        return jsonify(out)

    # ---------------------------------------------------------------- Timeline Analytics
    @app.route("/timeline", methods=["GET", "POST"])
    def timeline():
        out, raw, chart = None, request.form.get("posts", ""), ""
        start_date_str = request.form.get("start_date") or request.args.get("start_date")
        end_date_str = request.form.get("end_date") or request.args.get("end_date")

        start_d: Optional[date] = None
        end_d: Optional[date] = None
        if start_date_str:
            try:
                start_d = datetime.strptime(start_date_str[:10], "%Y-%m-%d").date()
            except ValueError:
                pass
        if end_date_str:
            try:
                end_d = datetime.strptime(end_date_str[:10], "%Y-%m-%d").date()
            except ValueError:
                pass

        if request.method == "POST":
            f = request.files.get("file")
            if f and f.filename:
                raw = f.read().decode("utf-8", errors="ignore")
                posts = parse_upload(f.filename, raw)
            else:
                posts = parse_upload("posts.txt", raw)

            out = analyze_timeline(posts[:2000], start_date=start_d, end_date=end_d)
            chart = sparkline([w["mean_risk"] for w in out["weeks"]])
            session["last_timeline"] = out

        return render_template("timeline.html", out=out, raw=raw if not request.files.get("file") else "",
                               chart=chart, start_date=start_date_str, end_date=end_date_str)

    @app.post("/timeline/load-saved")
    def timeline_load_saved():
        login_required()
        rows = db.user_history(current_uid(), limit=1000)
        formatted_posts = []
        for r in reversed(rows):
            if r.get("created_at") and r.get("probability") is not None:
                d_str = r["created_at"][:10]
                text_dummy = f"Themes: {r.get('themes', '')} | Distress Marker: {r.get('level')}"
                formatted_posts.append(f"{d_str} | {text_dummy}")

        raw = "\n".join(formatted_posts)
        posts = parse_upload("posts.txt", raw)
        out = analyze_timeline(posts)
        chart = sparkline([w["mean_risk"] for w in out["weeks"]])
        session["last_timeline"] = out
        return render_template("timeline.html", out=out, raw=raw, chart=chart)

    @app.get("/timeline/export")
    def timeline_export():
        out = session.get("last_timeline")
        fmt = request.args.get("format", "csv").lower()
        if not out:
            return redirect(url_for("timeline"))

        if fmt == "json":
            return Response(
                json.dumps(out, indent=2),
                mimetype="application/json",
                headers={"Content-Disposition": "attachment; filename=mindwatch-timeline.json"}
            )
        else:
            csv_str = generate_timeline_csv(out)
            return Response(
                csv_str,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=mindwatch-timeline.csv"}
            )

    # ---------------------------------------------------------------- Dashboard
    @app.get("/dashboard")
    def dashboard():
        uid = current_uid()
        s = db.summary()
        user_stats = None

        if uid:
            user = db.get_user(uid)
            analyses = db.user_history(uid, limit=100)
            assessments_list = db.user_assessments(uid, limit=100)
            latest_assessment = db.user_latest_assessment(uid)

            scored = [r for r in reversed(analyses) if r["probability"] is not None]
            chart = sparkline([r["probability"] for r in scored])

            # Trajectory trend status
            trend_label = "Steady"
            trend_desc = "Balanced recent emotional signals"
            if len(scored) >= 3:
                recent_p = [r["probability"] for r in scored[-3:]]
                earlier_p = [r["probability"] for r in scored[:3]]
                diff = (sum(recent_p) / len(recent_p)) - (sum(earlier_p) / len(earlier_p))
                if diff > 0.08:
                    trend_label = "Elevated"
                    trend_desc = "Higher distress markers recently"
                elif diff < -0.08:
                    trend_label = "Improving"
                    trend_desc = "Distress markers are decreasing"

            # Personalized daily coping tip
            daily_tip = (
                "Take a deliberate 15-minute break outdoors today. Stepping away from study screens "
                "gives your nervous system space to regulate and reset cognitive fatigue."
            )
            if analyses and analyses[0].get("themes"):
                first_theme = analyses[0]["themes"].split(",")[0].strip()
                if "academic" in first_theme.lower():
                    daily_tip = "Academic pressure flagged: Try using 25-minute study intervals with 5-minute restorative breaks to avoid mental exhaustion."
                elif "sleep" in first_theme.lower():
                    daily_tip = "Sleep concern noted: Protect your sleep architecture tonight by keeping screens off 45 minutes before bedtime."
                elif "alone" in first_theme.lower() or "lonely" in first_theme.lower():
                    daily_tip = "Low social energy: Reaching out with even a short 1-line text to a friend can gently soften feelings of isolation."

            user_stats = {
                "analyses_count": db.user_analyses_count(uid),
                "assessments_count": db.user_assessments_count(uid),
                "recent_analyses": analyses,
                "recent_assessments": assessments_list,
                "latest_assessment": latest_assessment,
                "chart": chart,
                "trend_label": trend_label,
                "trend_desc": trend_desc,
                "daily_tip": daily_tip
            }

        return render_template("dashboard.html", s=s, user_stats=user_stats)

    # ---------------------------------------------------------------- Account & Settings
    def _throttled():
        ip = request.remote_addr or "?"
        now = time.time()
        _LOGIN_ATTEMPTS[ip] = [t for t in _LOGIN_ATTEMPTS[ip] if now - t < 300]
        return len(_LOGIN_ATTEMPTS[ip]) >= 10

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            u, p, p2 = (request.form.get(k, "") for k in ("username", "password", "password2"))
            err_msg = None
            if not USERNAME_RE.match(u):
                err_msg = "Username must be 3-30 characters: letters, digits, . _ -"
            elif len(p) < 8:
                err_msg = "Password must be at least 8 characters."
            elif p != p2:
                err_msg = "Passwords do not match."
            elif not request.form.get("consent"):
                err_msg = "Please tick the consent box to continue."
            else:
                uid = db.create_user(u, generate_password_hash(p))
                if uid is None:
                    err_msg = "That username is taken."
                else:
                    session.clear()
                    session["uid"] = uid
                    return redirect(url_for("history"))
            return render_template("register.html", error=err_msg), 400
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            if _throttled():
                return render_template("login.html", error="Too many attempts. Try again in a few minutes."), 429
            u = db.get_user_by_name(request.form.get("username", ""))
            if u and check_password_hash(u["pw_hash"], request.form.get("password", "")):
                session.clear()
                session["uid"] = u["id"]
                return redirect(url_for("history"))
            _LOGIN_ATTEMPTS[request.remote_addr or "?"].append(time.time())
            return render_template("login.html", error="Wrong username or password."), 401
        return render_template("login.html")

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    @app.get("/history")
    def history():
        login_required()
        uid = current_uid()
        rows = db.user_history(uid)
        assessments_list = db.user_assessments(uid)
        scored = [r for r in reversed(rows) if r["probability"] is not None]
        return render_template(
            "history.html",
            rows=rows[:50],
            assessments=assessments_list[:50],
            phq=db.user_phq9(uid),
            chart=sparkline([r["probability"] for r in scored])
        )

    @app.route("/settings", methods=["GET"])
    def settings():
        login_required()
        return render_template("settings.html")

    @app.post("/settings/preferences")
    def settings_preferences():
        login_required()
        uid = current_uid()
        user = db.get_user(uid)
        prefs = user.get("preferences") or {}
        prefs["user_type"] = request.form.get("user_type", "undergraduate")
        prefs["theme"] = request.form.get("theme", "system")
        db.update_user_preferences(uid, prefs)
        return render_template("settings.html", success="Preferences successfully saved.")

    @app.post("/settings/password")
    def settings_password():
        login_required()
        uid = current_uid()
        u = db.get_user_by_name(db.get_user(uid)["username"])
        curr_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        if not check_password_hash(u["pw_hash"], curr_pw):
            return render_template("settings.html", error="Current password is incorrect."), 400
        if len(new_pw) < 8:
            return render_template("settings.html", error="New password must be at least 8 characters."), 400
        if new_pw != confirm_pw:
            return render_template("settings.html", error="New passwords do not match."), 400

        db.update_user_password(uid, generate_password_hash(new_pw))
        return render_template("settings.html", success="Password successfully updated.")

    @app.get("/account/export")
    def export():
        login_required()
        return Response(
            json.dumps(db.export_user(current_uid()), indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=mindwatch-my-data.json"}
        )

    @app.post("/account/delete")
    def delete_account():
        login_required()
        u = db.get_user_by_name(db.get_user(current_uid())["username"])
        if not check_password_hash(u["pw_hash"], request.form.get("password", "")):
            return render_template("error.html", code=400, msg="Password incorrect - account not deleted."), 400
        db.delete_user(current_uid())
        session.clear()
        return render_template("error.html", code=200, msg="Your account and all linked data were permanently deleted.")

    # ---------------------------------------------------------------- Directory & Health
    @app.get("/resources")
    def resources():
        return render_template("resources.html", resources=load_resources())

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
