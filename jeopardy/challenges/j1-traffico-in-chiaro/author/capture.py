"""Registra il traffico HTTP di J1 nel laboratorio degli autori."""

import argparse
import base64
import hashlib
import http.client
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time

import pyzipper

from generate import validate_config, verify_archive
from server import ARCHIVE_URL, PUBLIC_RESOURCES


def request(host, port, path, expected_status, token=None):
    headers = {"Connection": "close"}
    if token is not None:
        headers["Authorization"] = "Basic " + token

    connection = http.client.HTTPConnection(host, port, timeout=10)
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        body = response.read()

        if response.status != expected_status:
            raise RuntimeError(
                f"Risposta inattesa per {path}: {response.status}"
            )

        return response.getheader("Content-Type", ""), body
    finally:
        connection.close()


def exchange(host, port, config, original):
    token = base64.b64encode(
        f'{config["username"]}:{config["password"]}'.encode("ascii")
    ).decode("ascii")

    actions = [
        ("/", 200, None),
        ("/assets/style.css", 200, None),
        ("/avvisi.txt", 200, None),
        (ARCHIVE_URL, 401, None),
        ("/", 200, None),
        (ARCHIVE_URL, 200, token),
        ("/avvisi.txt", 200, None),
    ]

    for path, status, auth in actions:
        content_type, body = request(host, port, path, status, auth)

        if path in PUBLIC_RESOURCES and body != PUBLIC_RESOURCES[path][1]:
            raise RuntimeError(f"Contenuto inatteso per {path}.")

        if path == ARCHIVE_URL and status == 200:
            if content_type != "application/zip" or body != original:
                raise RuntimeError(
                    "Il download non coincide con lo ZIP originale."
                )

    return len(actions)


def record(args):
    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate_config(config)

    original = args.archive.read_bytes()
    verify_archive(original, config)
    address = socket.gethostbyname(args.host)

    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        raise RuntimeError("La cartella di cattura deve essere vuota.")

    partial = args.output / "traffico.pcap.partial"
    final = args.output / "traffico.pcap"
    messages = []
    ready = threading.Event()

    command = [
        "tcpdump", "-i", args.interface, "-p", "-nn", "-s", "0",
        "-B", "16384",
        "--immediate-mode", "-U", "-Z", "root", "-w", "-",
        "tcp", "and", "host", address, "and", "port", str(args.port),
    ]

    with tempfile.TemporaryFile(mode="w+b", dir="/tmp") as target:
        process = subprocess.Popen(
            command,
            stdout=target,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "LC_ALL": "C"},
        )

        def read_messages():
            for line in process.stderr:
                messages.append(line)
                if "listening on" in line:
                    ready.set()

        reader = threading.Thread(target=read_messages, daemon=True)
        reader.start()
        forced_stop = False

        try:
            if not ready.wait(timeout=10) or process.poll() is not None:
                raise RuntimeError(
                    "tcpdump non avviato; consultare capture.log."
                )

            count = exchange(args.host, args.port, config, original)

            # Attende la chiusura delle connessioni e la consegna dei pacchetti.
            time.sleep(0.5)
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)

            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                forced_stop = True
                process.kill()
                process.wait(timeout=3)

            reader.join(timeout=3)

            (args.output / "capture.log").write_text(
                "".join(messages), encoding="utf-8"
            )

            # Copia la cattura su disco dopo la chiusura di tcpdump.
            target.seek(0)
            with partial.open("xb") as destination:
                shutil.copyfileobj(target, destination)

    if forced_stop or process.returncode != 0:
        raise RuntimeError("Cattura interrotta; consultare capture.log.")

    log = "".join(messages)
    captured = re.search(r"(\d+) packets? captured", log)
    dropped = re.search(r"(\d+) packets? dropped by kernel", log)

    if not captured or int(captured.group(1)) == 0:
        raise RuntimeError("Nessun pacchetto acquisito.")
    if not dropped or int(dropped.group(1)) != 0:
        raise RuntimeError("Cattura non completa: controllare capture.log.")

    checked = subprocess.run(
        ["tcpdump", "-nn", "-Z", "root", "-r", str(partial)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=15,
    )
    if checked.returncode != 0:
        raise RuntimeError("Impossibile leggere interamente il file PCAP.")

    data = partial.read_bytes()
    if b"CRCTF{" in data:
        raise RuntimeError("La cattura contiene una flag in chiaro.")

    report = {
        "challenge": "J1",
        "stage": "capture",
        "pcap": final.name,
        "pcap_sha256": hashlib.sha256(data).hexdigest(),
        "archive_sha256": hashlib.sha256(original).hexdigest(),
        "http_requests": count,
        "packets_captured": int(captured.group(1)),
        "packets_dropped": int(dropped.group(1)),
        "download_matches_archive": True,
        "python_version": platform.python_version(),
        "tcpdump_version": subprocess.check_output(
            ["tcpdump", "--version"], text=True
        ).splitlines()[0],
        "source_sha256": {
            name: hashlib.sha256(
                Path(__file__).with_name(name).read_bytes()
            ).hexdigest()
            for name in (
                "server.py",
                "generate.py",
                "capture.py",
                "requirements.txt",
            )
        },
    }

    with (args.output / "capture.json").open("x", encoding="utf-8") as target:
        json.dump(report, target, indent=2)
        target.write("\n")

    partial.rename(final)

    print("Cattura completata:", final)
    print("Richieste HTTP:", count)
    print("Pacchetti acquisiti:", report["packets_captured"])
    print("Pacchetti persi:", report["packets_dropped"])
    print("SHA256 archivio:", report["archive_sha256"])
    print("SHA256 PCAP:", report["pcap_sha256"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="server")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--interface", default="eth0")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        record(args)
    except (
            OSError,
            ValueError,
            RuntimeError,
            subprocess.SubprocessError,
            http.client.HTTPException,
            pyzipper.BadZipFile,
    ) as error:
        parser.exit(1, f"Errore: {error}\n")


if __name__ == "__main__":
    main()