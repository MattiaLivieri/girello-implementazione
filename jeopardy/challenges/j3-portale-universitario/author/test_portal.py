"""Controlli offline: dati sintetici, versione vulnerabile e copia corretta."""

import importlib.util
import json
import re
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

import portal

FLAG = "CRCTF{" + "a1" * 16 + "}"
MARKER = "        # J3_AUTHORIZATION_CHECK: controllo del proprietario intenzionalmente assente."
FIX = '        if document["owner_id"] != g.user["id"]:\n            abort(403)'


def fixed_factory():
    """Copia corretta in memoria: non viene inclusa nell'immagine finale."""
    path = Path(portal.__file__)
    source = path.read_text(encoding="utf-8")
    if source.count(MARKER) != 1:
        raise AssertionError("Punto della correzione non univoco.")
    spec = importlib.util.spec_from_file_location("portal_fixed", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(source.replace(MARKER, FIX), str(path), "exec"), module.__dict__)
    return module.create_app


class PortalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixed = staticmethod(fixed_factory())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scenario = self.root / "scenario.json"
        self.scenario.write_text(json.dumps({"flag": FLAG}), encoding="utf-8")
        self.app = portal.create_app(self.scenario, self.root / "vulnerable")
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def token(self, client, path="/login"):
        response = client.get(path)
        match = re.search(rb'name="csrf" value="([a-f0-9]+)"', response.data)
        self.assertIsNotNone(match)
        return match.group(1).decode()

    def login(self, client=None, username="alice", password="LaboratorioJ3!"):
        client = client or self.client
        return client.post("/login", data={
            "csrf": self.token(client), "username": username, "password": password,
        })

    def test_login_and_own_download(self):
        self.assertEqual(self.login().status_code, 302)
        for doc_id in (1001, 1003):
            response = self.client.get(f"/documents/{doc_id}/download")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Alice Rossi", response.data)
            self.assertIn("attachment", response.headers["Content-Disposition"])
            self.assertNotIn(FLAG.encode(), response.data)

    def test_listing_filters_owner(self):
        self.login()
        response = self.client.get("/")
        self.assertIn(b"/documents/1001/download", response.data)
        self.assertIn(b"/documents/1003/download", response.data)
        self.assertNotIn(b"1002", response.data)
        self.assertNotIn(FLAG.encode(), response.data)

    def test_intentional_idor(self):
        self.login()
        response = self.client.get("/documents/1002/download")
        self.assertEqual(response.status_code, 200)
        self.assertIn(FLAG.encode(), response.data)

    def test_anonymous_cannot_download(self):
        for path in ("/", "/documents/1001/download", "/documents/1002/download"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], "/login")
                self.assertNotIn(FLAG.encode(), response.data)

    def test_invalid_credentials_and_sql_input(self):
        for username, password in (("alice", "errata"), ("inesistente", "x"),
                                   ("' OR 1=1 --", "x"), ("marco", "LaboratorioJ3!")):
            with self.subTest(username=username):
                self.assertEqual(self.login(username=username, password=password).status_code, 401)
                self.assertEqual(self.client.get("/documents/1002/download").status_code, 302)

    def test_csrf_required(self):
        self.client.get("/login")
        for token in ("", "errato", "\u2603"):
            with self.subTest(token=token):
                response = self.client.post("/login", data={
                    "username": "alice", "password": "LaboratorioJ3!", "csrf": token,
                })
                self.assertEqual(response.status_code, 400)

    def test_logout_removes_access(self):
        self.login()
        token = self.token(self.client, "/")
        self.assertEqual(self.client.post("/logout", data={"csrf": token}).status_code, 302)
        self.assertEqual(self.client.get("/documents/1002/download").status_code, 302)

    def test_unknown_and_malformed_ids(self):
        self.login()
        for value in ("0", "9999", "-1", "abc", "1%20OR%201=1", "9" * 100):
            with self.subTest(value=value):
                response = self.client.get(f"/documents/{value}/download")
                self.assertEqual(response.status_code, 404)
                self.assertNotIn(FLAG.encode(), response.data)

    def test_no_arbitrary_file_download(self):
        self.login()
        for path in ("/scenario.json", "/portal.py", "/static/../scenario.json",
                     "/documents/../../etc/passwd/download"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn(FLAG.encode(), response.data)

    def test_form_limits(self):
        token = self.token(self.client)
        self.assertEqual(self.client.post("/login", data={
            "csrf": token, "username": "x" * 81, "password": "x",
        }).status_code, 400)
        self.assertEqual(self.client.post("/login", data={
            "csrf": token, "username": "alice", "password": "x" * 9000,
        }).status_code, 413)

    def test_no_client_selected_owner(self):
        self.login()
        response = self.client.get("/?user_id=2&owner_id=2")
        self.assertNotIn(b"1002", response.data)

    def test_security_headers_and_offline_assets(self):
        response = self.client.get("/login")
        self.assertFalse(self.app.debug)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("HttpOnly", response.headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", response.headers["Set-Cookie"])
        self.assertNotIn(b"https://", response.data)
        with self.client.get("/static/style.css") as response:
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/healthz").data, b"ok\n")

    def test_passwords_hashed(self):
        with closing(sqlite3.connect(self.app.config["DATABASE"])) as db, db:
            passwords = [row[0] for row in db.execute("SELECT password_hash FROM users")]
        self.assertTrue(all(value.startswith("scrypt:") for value in passwords))
        self.assertNotIn("LaboratorioJ3!", passwords)

    def test_fixed_copy_denies_other_owner(self):
        fixed = self.fixed(self.scenario, self.root / "fixed")
        client = fixed.test_client()
        self.assertEqual(self.login(client).status_code, 302)
        self.assertEqual(client.get("/documents/1001/download").status_code, 200)
        response = client.get("/documents/1002/download")
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(FLAG.encode(), response.data)
        self.assertEqual(client.get("/documents/9999/download").status_code, 404)
        anonymous = fixed.test_client()
        self.assertEqual(anonymous.get("/documents/1002/download").status_code, 302)

    def test_fixed_copy_allows_real_owner(self):
        fixed = self.fixed(self.scenario, self.root / "fixed-owner")
        client = fixed.test_client()
        # Sessione sintetica del secondo utente, soltanto nel collaudo.
        with client.session_transaction() as state:
            state["user_id"] = 2
        response = client.get("/documents/1002/download")
        self.assertEqual(response.status_code, 200)
        self.assertIn(FLAG.encode(), response.data)
        self.assertEqual(client.get("/documents/1001/download").status_code, 403)

    def test_new_state_restores_dataset_and_invalidates_session(self):
        self.login()
        cookie = self.client.get_cookie("girello_j3").value
        with closing(sqlite3.connect(self.app.config["DATABASE"])) as db, db:
            db.execute("UPDATE documents SET body = 'modificato' WHERE id = 1002")
        rebuilt = portal.create_app(self.scenario, self.root / "reset")
        client = rebuilt.test_client()
        client.set_cookie("girello_j3", cookie)
        self.assertEqual(client.get("/documents/1002/download").status_code, 302)
        self.login(client)
        self.assertIn(FLAG.encode(), client.get("/documents/1002/download").data)

    def test_existing_state_is_preserved(self):
        cookie_before = self.app.secret_key
        again = portal.create_app(self.scenario, self.root / "vulnerable")
        self.assertEqual(again.secret_key, cookie_before)
        with closing(sqlite3.connect(again.config["DATABASE"])) as db, db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM documents").fetchone()[0], 3)

    def test_invalid_scenario_rejected(self):
        self.scenario.write_text('{"flag":"errata"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            portal.create_app(self.scenario, self.root / "invalid")


if __name__ == "__main__":
    unittest.main()