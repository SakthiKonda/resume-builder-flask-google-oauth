import os
# Only for development (allows OAuth without HTTPS)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import json
import sqlite3
from io import BytesIO

from flask import (
    Flask, render_template, request, redirect,
    session, url_for, send_file, flash
)
from flask_dance.contrib.google import make_google_blueprint, google
from xhtml2pdf import pisa
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------------------------------
# Flask config
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# -----------------------------------------------------------------------------
# Google OAuth
# -----------------------------------------------------------------------------
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_to="dashboard",
    scope=["https://www.googleapis.com/auth/userinfo.email",
       "https://www.googleapis.com/auth/userinfo.profile",
       "openid"]
)
app.register_blueprint(google_bp, url_prefix="/login")

# -----------------------------------------------------------------------------
# Load roles.json
# -----------------------------------------------------------------------------
try:
    with open("roles.json", "r", encoding="utf-8") as f:
        ROLES = json.load(f)
except FileNotFoundError:
    ROLES = {}
    print("WARNING: roles.json not found. /learn route will fail until you add it.")

# -----------------------------------------------------------------------------
# DB helpers
# -----------------------------------------------------------------------------
DB_PATH = "database.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS resume (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT UNIQUE,
                name TEXT,
                title TEXT,
                summary TEXT,
                skills TEXT,
                experience TEXT,
                projects TEXT,
                education TEXT,
                certifications TEXT,
                github TEXT,
                linkedin TEXT,
                job_role TEXT
            )
        ''')

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Google login failed", "danger")
        return redirect(url_for("home"))

    info = resp.json()
    session["user_email"] = info["email"]
    session["user_name"] = info.get("name", "")
    return redirect(url_for("resume"))


@app.route("/resume", methods=["GET", "POST"])
def resume():
    if "user_email" not in session:
        return redirect(url_for("home"))

    user_email = session["user_email"]

    with get_conn() as conn:
        cur = conn.cursor()

        if request.method == "POST":
            data = (
                user_email,
                request.form.get("name", ""),
                request.form.get("title", ""),
                request.form.get("summary", ""),
                request.form.get("skills", ""),
                request.form.get("experience", ""),
                request.form.get("projects", ""),
                request.form.get("education", ""),
                request.form.get("certifications", ""),
                request.form.get("github", ""),
                request.form.get("linkedin", ""),
                request.form.get("job_role", "")
            )

            # Upsert (delete + insert simplest for SQLite)
            cur.execute("DELETE FROM resume WHERE user_email=?", (user_email,))
            cur.execute("""
                INSERT INTO resume (
                    user_email, name, title, summary, skills, experience,
                    projects, education, certifications, github, linkedin, job_role
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()
            return redirect(url_for("learn"))

        cur.execute("SELECT * FROM resume WHERE user_email=?", (user_email,))
        data = cur.fetchone()

    return render_template(
        "resume.html",
        data=data,
        roles=list(ROLES.keys())
    )


@app.route("/learn")
def learn():
    if "user_email" not in session:
        return redirect(url_for("home"))

    user_email = session["user_email"]

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM resume WHERE user_email=?", (user_email,))
        data = cur.fetchone()

    if not data:
        flash("Please create your resume first.", "warning")
        return redirect(url_for("resume"))

    user_skills = [s.strip().lower() for s in (data["skills"] or "").split(",") if s.strip()]
    job_role = data["job_role"]

    if job_role not in ROLES:
        flash("Selected job role is not configured in roles.json", "warning")
        return redirect(url_for("resume"))

    required_skills = ROLES[job_role]["skills"]
    resources = ROLES[job_role]["resources"]

    missing_skills = [s for s in required_skills if s.lower() not in user_skills]

    return render_template(
        "learn.html",
        data=data,
        job_role=job_role,
        user_skills=user_skills,
        required_skills=required_skills,
        missing_skills=missing_skills,
        resources=resources
    )


@app.route("/export")
def export():
    if "user_email" not in session:
        return redirect(url_for("home"))

    user_email = session["user_email"]
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM resume WHERE user_email=?", (user_email,))
        data = cur.fetchone()

    if not data:
        flash("Please create your resume first.", "warning")
        return redirect(url_for("resume"))

    return render_template("export.html", data=data)


@app.route("/export/pdf")
def export_pdf():
    if "user_email" not in session:
        return redirect(url_for("home"))

    user_email = session["user_email"]
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM resume WHERE user_email=?", (user_email,))
        data = cur.fetchone()

    if not data:
        flash("Please create your resume first.", "warning")
        return redirect(url_for("resume"))

    html = render_template("export.html", data=data)
    pdf_io = BytesIO()
    pisa.CreatePDF(html, dest=pdf_io)
    pdf_io.seek(0)
    return send_file(pdf_io, download_name="resume.pdf", as_attachment=True)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
