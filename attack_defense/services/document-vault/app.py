"""Document Vault: archivio di documenti testuali con accesso autenticato."""

import hashlib
import os
import re
import secrets
import sqlite3
from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, g, jsonify, request, send_file
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


MAX_DOCUMENT_SIZE = 64 * 1024


def create_app(data_dir=None):
    app = Flask(__name__)
    # Il limite HTTP include anche i campi e i separatori del multipart.
    app.config["MAX_CONTENT_LENGTH"] = 96 * 1024

    storage_dir = Path(data_dir or os.environ.get("VAULT_DATA_DIR", "/data")).resolve()
    files_dir = storage_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    database_path = storage_dir / "vault.sqlite3"

    # Schema inizializzato anche sul primo avvio di un volume vuoto.
    with sqlite3.connect(database_path) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                owner_id INTEGER NOT NULL REFERENCES users(id),
                name TEXT NOT NULL,
                size INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def get_db():
        # Ogni richiesta usa una connessione propria, chiusa al termine.
        if "db" not in g:
            g.db = sqlite3.connect(database_path, timeout=5)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def require_login(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            scheme, _, token = request.headers.get("Authorization", "").partition(" ")

            if scheme.lower() != "bearer" or not 1 <= len(token) <= 128:
                abort(401, description="Accesso richiesto.")

            # Nel database cerchiamo l'impronta, non il token in chiaro.
            g.token_hash = hashlib.sha256(token.encode()).hexdigest()
            g.user = get_db().execute(
                "SELECT u.id, u.username FROM users u JOIN sessions s "
                "ON s.user_id = u.id WHERE s.token_hash = ?",
                (g.token_hash,),
            ).fetchone()

            if g.user is None:
                abort(401, description="Sessione non valida.")

            return view(*args, **kwargs)

        return wrapped

    def read_credentials():
        body = request.get_json(silent=True)

        if not isinstance(body, dict):
            abort(400, description="Inviare username e password in JSON.")

        username = body.get("username")
        password = body.get("password")

        if not isinstance(username, str) or not re.fullmatch(
            r"[A-Za-z0-9_]{3,32}", username
        ):
            abort(400, description="Username: 3-32 lettere, numeri o underscore.")

        if not isinstance(password, str) or not 8 <= len(password) <= 128:
            abort(400, description="Password: da 8 a 128 caratteri.")

        return username, password

    def read_document_upload():
        """Valida nome, dimensione e codifica prima di scrivere nell'archivio."""
        upload = request.files.get("file")
        name = secure_filename(upload.filename or "") if upload is not None else ""

        if not name.lower().endswith(".txt") or len(name) > 100:
            abort(
                400,
                description="Caricare un file .txt con nome fino a 100 caratteri.",
            )

        content = upload.stream.read(MAX_DOCUMENT_SIZE + 1)

        if not 1 <= len(content) <= MAX_DOCUMENT_SIZE:
            abort(
                400,
                description="Il documento deve contenere da 1 byte a 64 KiB.",
            )

        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            abort(400, description="Il documento deve essere testo UTF-8.")

        return name, content

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(sqlite3.Error)
    @app.errorhandler(OSError)
    def storage_error(_error):
        app.logger.exception("Errore nell'archivio del servizio.")
        return jsonify(error="Archivio temporaneamente non disponibile."), 503

    @app.after_request
    def response_headers(response):
        # Evita la cache dei dati riservati e limita le risorse della pagina.
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'none'; object-src 'none'; "
            "frame-ancestors 'none'"
        )
        return response

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return jsonify(status="ok")

    @app.post("/api/v1/register")
    def register():
        username, password = read_credentials()
        db = get_db()

        try:
            with db:
                cursor = db.execute(
                    "INSERT INTO users(username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
        except sqlite3.IntegrityError:
            abort(409, description="Username gia' utilizzato.")

        return jsonify(id=cursor.lastrowid, username=username), 201

    @app.post("/api/v1/login")
    def login():
        username, password = read_credentials()
        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            abort(401, description="Credenziali non valide.")

        # Ogni login crea una sessione persistente, valida fino al logout.
        token = secrets.token_urlsafe(32)

        with db:
            db.execute(
                "INSERT INTO sessions(token_hash, user_id) VALUES (?, ?)",
                (hashlib.sha256(token.encode()).hexdigest(), user["id"]),
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
            db.execute(
                "DELETE FROM sessions WHERE token_hash = ?", (g.token_hash,)
            )

        return "", 204

    @app.get("/api/v1/documents")
    @require_login
    def list_documents():
        rows = get_db().execute(
            "SELECT * FROM documents WHERE owner_id = ? ORDER BY created_at, id",
            (g.user["id"],),
        ).fetchall()

        return jsonify(documents=[dict(row) for row in rows])

    @app.post("/api/v1/documents")
    @require_login
    def upload_document():
        name, content = read_document_upload()

        # Nome fisico e proprietario sono decisi dal server, non dall'upload.
        document_id = uuid4().hex
        user_dir = files_dir / str(g.user["id"])
        user_dir.mkdir(exist_ok=True)
        target = user_dir / document_id
        db = get_db()

        try:
            with db:
                target.write_bytes(content)
                db.execute(
                    "INSERT INTO documents(id, owner_id, name, size) "
                    "VALUES (?, ?, ?, ?)",
                    (document_id, g.user["id"], name, len(content)),
                )
        except (sqlite3.Error, OSError):
            # Il rollback SQLite non cancella il file: lo rimuoviamo qui.
            target.unlink(missing_ok=True)
            raise

        row = db.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()

        return jsonify(dict(row)), 201

    @app.get("/api/v1/documents/download")
    @require_login
    def download_document():
        requested = request.args.get("file", "")

        if not requested or len(requested) > 256 or "\x00" in requested:
            abort(400, description="Identificatore del documento non valido.")

        if Path(requested).is_absolute():
            abort(404)

        user_dir = files_dir / str(g.user["id"])

        try:
            target = (user_dir / requested).resolve()
        except (ValueError, RuntimeError):
            abort(400, description="Percorso non valido.")

        if not target.is_relative_to(files_dir):
            abort(404)

        if not target.is_file():
            abort(404)

        document = get_db().execute(
            "SELECT name FROM documents WHERE id = ? AND owner_id = ?",
            (target.name, target.parent.name),
        ).fetchone()

        if document is None:
            abort(404)

        return send_file(
            target,
            as_attachment=True,
            download_name=document["name"],
            mimetype="text/plain",
            conditional=False,
        )

    return app
