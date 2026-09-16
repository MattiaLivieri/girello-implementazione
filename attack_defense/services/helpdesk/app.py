"""HelpDesk API: gestione di ticket personali con accesso autenticato."""

import os
import re
import secrets
import sqlite3
from contextlib import closing
from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, g, jsonify, request
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash


MAX_BODY_SIZE = 16 * 1024

def search_tickets(connection, owner_id, q):
    query = (
        "SELECT id, owner_id, title, status, created_at FROM tickets "
        f"WHERE owner_id = ? AND instr(title, '{q}') > 0 "
        "ORDER BY created_at DESC, rowid DESC LIMIT 50"
    )
    rows = connection.execute(query, (owner_id,)).fetchall()
    return [dict(row) for row in rows]

def create_app(data_dir=None):
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 128 * 1024

    storage_dir = Path(
        data_dir or os.environ.get("HELPDESK_DATA_DIR", "/data")
    ).resolve()
    files_dir = storage_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    database_path = storage_dir / "helpdesk.sqlite3"

    with closing(sqlite3.connect(database_path)) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                owner_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'closed')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS tickets_owner_created
                ON tickets(owner_id, created_at);
        """)

    def get_db(read_only=False):
        # La ricerca usa una connessione distinta, aperta con mode=ro.
        key = "read_db" if read_only else "db"
        if key not in g:
            mode = "ro" if read_only else "rw"
            db = sqlite3.connect(
                f"{database_path.as_uri()}?mode={mode}", timeout=5, uri=True
            )
            db.row_factory = sqlite3.Row
            setattr(g, key, db)
            db.execute("PRAGMA foreign_keys = ON")
        return getattr(g, key)

    @app.teardown_appcontext
    def close_db(_error):
        for key in ("db", "read_db"):
            db = g.pop(key, None)
            if db is not None:
                db.close()

    def require_login(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            scheme, _, token = request.headers.get("Authorization", "").partition(" ")
            if scheme.lower() != "bearer" or not 1 <= len(token) <= 128:
                abort(401, description="Accesso richiesto.")

            g.user = get_db().execute(
                "SELECT u.id, u.username FROM users u JOIN sessions s "
                "ON s.user_id = u.id WHERE s.token = ?",
                (token,),
            ).fetchone()
            if g.user is None:
                abort(401, description="Sessione non valida.")

            g.token = token
            return view(*args, **kwargs)

        return wrapped

    def read_json(fields):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != set(fields):
            abort(400, description="Inviare un oggetto JSON con i campi richiesti.")
        return data

    def text_bytes(value, field):
        if not isinstance(value, str):
            abort(400, description=f"Il campo {field} deve essere testo.")
        try:
            return value.encode("utf-8")
        except UnicodeEncodeError:
            abort(400, description=f"Il campo {field} deve essere testo UTF-8.")

    def read_credentials():
        data = read_json(("username", "password"))
        username = data["username"]
        password = data["password"]

        if not isinstance(username, str) or not re.fullmatch(
            r"[A-Za-z0-9_]{3,32}", username
        ):
            abort(400, description="Username: 3-32 lettere ASCII, numeri o underscore.")

        text_bytes(password, "password")
        if not 8 <= len(password) <= 128:
            abort(400, description="Password: da 8 a 128 caratteri.")

        return username, password

    def read_ticket():
        data = read_json(("title", "body"))
        title = data["title"]
        text_bytes(title, "title")
        if not 1 <= len(title) <= 120 or not title.strip():
            abort(400, description="Titolo: 1-120 caratteri, non solo spazi.")

        content = text_bytes(data["body"], "body")
        if not 1 <= len(content) <= MAX_BODY_SIZE:
            abort(400, description="Il contenuto deve avere da 1 byte a 16 KiB.")

        return title, content

    def owned_ticket(ticket_id):
        row = get_db().execute(
            "SELECT id, owner_id, title, status, created_at FROM tickets "
            "WHERE id = ? AND owner_id = ?",
            (ticket_id, g.user["id"]),
        ).fetchone()
        if row is None:
            abort(404, description="Ticket non trovato.")
        return dict(row)

    @app.before_request
    def limit_request_body():
        # Applica il limite anche agli endpoint che non leggono un JSON.
        limit = app.config["MAX_CONTENT_LENGTH"]
        # Un byte in piu' distingue il limite esatto nei corpi a streaming.
        request.max_content_length = limit + 1
        if len(request.get_data()) > limit:
            abort(413, description="Corpo HTTP superiore a 128 KiB.")

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()
        response.data = app.json.dumps({"error": error.description})
        response.content_type = "application/json"
        return response

    @app.errorhandler(sqlite3.Error)
    @app.errorhandler(OSError)
    @app.errorhandler(UnicodeDecodeError)
    def storage_error(_error):
        app.logger.exception("Errore nell'archivio del servizio.")
        return jsonify(error="Archivio temporaneamente non disponibile."), 503

    @app.after_request
    def response_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/health")
    def health():
        # Una lettura reale rileva anche un database mancante o danneggiato.
        get_db().execute("SELECT id FROM users LIMIT 1").fetchone()
        return jsonify(status="ok")

    @app.post("/api/v1/register")
    def register():
        username, password = read_credentials()
        password_hash = generate_password_hash(password, method="scrypt")
        db = get_db()

        try:
            with db:
                cursor = db.execute(
                    "INSERT INTO users(username, password_hash) VALUES (?, ?)",
                    (username, password_hash),
                )
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                abort(409, description="Username gia' utilizzato.")
            raise

        return jsonify(id=cursor.lastrowid, username=username), 201

    @app.post("/api/v1/login")
    def login():
        username, password = read_credentials()
        db = get_db()
        user = db.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            abort(401, description="Credenziali non valide.")

        token = secrets.token_urlsafe(32)
        with db:
            db.execute(
                "INSERT INTO sessions(token, user_id) VALUES (?, ?)",
                (token, user["id"]),
            )

        return jsonify(
            token=token,
            user={"id": user["id"], "username": user["username"]},
        )

    @app.get("/api/v1/me")
    @require_login
    def me():
        return jsonify(dict(g.user))

    @app.post("/api/v1/logout")
    @require_login
    def logout():
        db = get_db()
        with db:
            db.execute("DELETE FROM sessions WHERE token = ?", (g.token,))
        return "", 204

    @app.post("/api/v1/tickets")
    @require_login
    def create_ticket():
        title, content = read_ticket()
        ticket_id = uuid4().hex
        user_dir = files_dir / str(g.user["id"])
        user_dir.mkdir(exist_ok=True)
        target = user_dir / ticket_id
        db = get_db()

        try:
            with db:
                # Il file e' completo prima che i metadati diventino visibili.
                target.write_bytes(content)
                db.execute(
                    "INSERT INTO tickets(id, owner_id, title) VALUES (?, ?, ?)",
                    (ticket_id, g.user["id"], title),
                )
        except (sqlite3.Error, OSError):
            # Il rollback SQLite non rimuove il file.
            target.unlink(missing_ok=True)
            raise

        ticket = owned_ticket(ticket_id)
        ticket["body"] = content.decode("utf-8")
        return jsonify(ticket), 201

    @app.get("/api/v1/tickets")
    @require_login
    def list_tickets():
        rows = get_db().execute(
            "SELECT id, owner_id, title, status, created_at FROM tickets "
            "WHERE owner_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 50",
            (g.user["id"],),
        ).fetchall()
        return jsonify(tickets=[dict(row) for row in rows])

    @app.get("/api/v1/tickets/search")
    @require_login
    def find_tickets():
        values = request.args.getlist("q")
        if len(values) != 1 or not 1 <= len(values[0]) <= 256:
            abort(400, description="Specificare q una sola volta, con 1-256 caratteri.")
        q = values[0]
        text_bytes(q, "q")
        tickets = search_tickets(get_db(read_only=True), g.user["id"], q)
        return jsonify(tickets=tickets)

    @app.get("/api/v1/tickets/<ticket_id>")
    @require_login
    def get_ticket(ticket_id):
        ticket = owned_ticket(ticket_id)
        target = files_dir / str(ticket["owner_id"]) / ticket["id"]
        ticket["body"] = target.read_bytes().decode("utf-8")
        return jsonify(ticket)

    @app.patch("/api/v1/tickets/<ticket_id>")
    @require_login
    def update_ticket(ticket_id):
        ticket = owned_ticket(ticket_id)
        data = read_json(("status",))
        status = data["status"]
        if status not in ("open", "closed"):
            abort(400, description="Stato ammesso: open oppure closed.")

        db = get_db()
        with db:
            db.execute(
                "UPDATE tickets SET status = ? WHERE id = ? AND owner_id = ?",
                (status, ticket_id, g.user["id"]),
            )
        ticket["status"] = status
        return jsonify(ticket)

    return app
