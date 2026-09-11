"""Portale didattico J3: omissione intenzionale dell'autorizzazione al download."""

import io
import json
import re
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, abort, g, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def create_app(scenario_path="/app/scenario.json", state_dir="/tmp/j3"):
    state = Path(state_dir)
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8-sig"))
    flag = scenario.get("flag", "")
    if not re.fullmatch(r"CRCTF\{[a-f0-9]{32}\}", flag):
        raise ValueError("Configurazione J3 non valida.")

    key_path = state / "session.key"
    if not key_path.exists():
        with key_path.open("x", encoding="ascii") as key_file:
            key_file.write(secrets.token_hex(32))
        key_path.chmod(0o600)
    key = key_path.read_text(encoding="ascii")
    if not re.fullmatch(r"[a-f0-9]{64}", key):
        raise ValueError("Chiave di sessione non valida.")

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=key,
        DATABASE=str(state / "portal.sqlite3"),
        SESSION_COOKIE_NAME="girello_j3",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=False,  # Accesso HTTP locale sul loopback.
        MAX_CONTENT_LENGTH=8192,
        DEBUG=False,
        TESTING=False,
    )

    with closing(sqlite3.connect(app.config["DATABASE"])) as db, db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, full_name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL,
                title TEXT NOT NULL, filename TEXT NOT NULL, body TEXT NOT NULL,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            );
        """)
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            db.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", [
                (1, "alice", generate_password_hash("LaboratorioJ3!"), "Alice Rossi"),
                (2, "marco", generate_password_hash(secrets.token_urlsafe(32)), "Marco Bianchi"),
            ])
            db.executemany("INSERT INTO documents VALUES (?, ?, ?, ?, ?)", [
                (1001, 1, "Conferma iscrizione", "conferma-iscrizione.txt",
                 "Segreteria studenti\nIntestataria: Alice Rossi\nIscrizione acquisita.\n"),
                (1002, 2, "Comunicazione riservata", "comunicazione-riservata.txt",
                 "Segreteria studenti\nIntestatario: Marco Bianchi\n"
                 "Codice riservato della pratica:\n" + flag + "\n"),
                (1003, 1, "Ricevuta richiesta", "ricevuta-richiesta.txt",
                 "Segreteria studenti\nIntestataria: Alice Rossi\nRichiesta registrata.\n"),
            ])

    def database():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_database(_error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.before_request
    def load_user_and_check_csrf():
        user_id = session.get("user_id")
        g.user = database().execute(
            "SELECT id, username, full_name FROM users WHERE id = ?", (user_id,)
        ).fetchone() if isinstance(user_id, int) else None
        if request.method == "POST":
            supplied = request.form.get("csrf", "")
            expected = session.get("csrf")
            if not isinstance(expected, str) or not secrets.compare_digest(
                supplied.encode("utf-8"), expected.encode("utf-8")
            ):
                abort(400)

    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(24)
        return session["csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.after_request
    def response_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'self'; img-src 'self'; "
            "form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
        )
        return response

    @app.get("/healthz")
    def health():
        database().execute("SELECT 1").fetchone()
        return "ok\n", 200, {"Content-Type": "text/plain; charset=utf-8"}

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user is not None:
            return redirect(url_for("documents"))
        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            if len(username) > 80 or len(password) > 128:
                abort(400)
            user = database().execute(
                "SELECT id, password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("documents"))
            error = "Credenziali non valide."
        return render_template("login.html", error=error), 401 if error else 200

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    def documents():
        if g.user is None:
            return redirect(url_for("login"))
        rows = database().execute(
            "SELECT id, title FROM documents WHERE owner_id = ? ORDER BY id", (g.user["id"],)
        ).fetchall()
        return render_template("documents.html", documents=rows)

    @app.get("/documents/<int:document_id>/download")
    def download(document_id):
        if g.user is None:
            return redirect(url_for("login"))
        if not 1 <= document_id <= 2147483647:
            abort(404)
        document = database().execute(
            "SELECT owner_id, filename, body FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        if document is None:
            abort(404)
        # J3_AUTHORIZATION_CHECK: controllo del proprietario intenzionalmente assente.
        return send_file(
            io.BytesIO(document["body"].encode("utf-8")),
            mimetype="text/plain",
            as_attachment=True,
            download_name=document["filename"],
        )

    return app