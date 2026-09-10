"""Server HTTP usato dagli autori per generare la cattura di J1."""

import argparse
import base64
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ARCHIVE_URL = "/documenti/riservato.zip"

PUBLIC_RESOURCES = {
    "/": (
        "text/html; charset=utf-8",
        """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>Archivio documentale</title>
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<main>
<h1>Archivio documentale</h1>
<p>Consultazione dei documenti interni.</p>
<ul>
<li><a href="/avvisi.txt">Avvisi</a></li>
<li><a href="/documenti/riservato.zip">Documentazione riservata</a></li>
</ul>
</main>
</body>
</html>
""".encode("utf-8"),
    ),
    "/assets/style.css": (
        "text/css; charset=utf-8",
        b"body { font-family: sans-serif; margin: 2rem; }\n"
        b"main { max-width: 48rem; margin: auto; }\n",
    ),
    "/avvisi.txt": (
        "text/plain; charset=utf-8",
        b"Gli avvisi pubblici sono disponibili senza autenticazione.\n"
        b"I documenti riservati richiedono le credenziali assegnate.\n",
    ),
}


def make_handler(archive_data, username, password):
    token = base64.b64encode(
        f"{username}:{password}".encode("ascii")
    ).decode("ascii")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):
            path = urlsplit(self.path).path
            if path in PUBLIC_RESOURCES:
                content_type, body = PUBLIC_RESOURCES[path]
                self.reply(200, body, content_type)
                return

            if path != ARCHIVE_URL:
                self.reply(404, b"Not found\n", "text/plain")
                return

            scheme, _, supplied_token = self.headers.get(
                "Authorization", ""
            ).partition(" ")

            if scheme.lower() != "basic" or supplied_token != token:
                self.reply(401, b"Authentication required\n", "text/plain")
                return

            self.reply(200, archive_data, "application/zip")

        def reply(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")

            if status == 401:
                self.send_header("WWW-Authenticate", 'Basic realm="Archivio"')
            elif status == 200:
                self.send_header(
                    "Content-Disposition", 'attachment; filename="riservato.zip"'
                )

            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def log_message(self, format, *args):
            # La cattura PCAP conserva lo scambio; non servono log applicativi.
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        parser.error("La configurazione deve essere un oggetto JSON.")

    username = config.get("username")
    password = config.get("password")
    if not all(isinstance(v, str) and v and v.isascii()
               for v in (username, password)):
        parser.error("Username e password devono essere stringhe ASCII non vuote.")
    if ":" in username:
        parser.error("Lo username non deve contenere due punti.")

    handler = make_handler(args.archive.read_bytes(), username, password)
    with HTTPServer((args.host, args.port), handler) as server:
        print(f"Server J1 pronto sulla porta {server.server_port}.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()