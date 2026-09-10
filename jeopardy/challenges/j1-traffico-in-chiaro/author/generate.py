"""Genera i materiali riservati necessari alla cattura di J1."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets

import pyzipper


def validate_config(config):
    if not isinstance(config, dict) or config.get("challenge") != "J1":
        raise ValueError("Configurazione J1 non valida.")

    username = config.get("username")
    password = config.get("password")
    flag = config.get("flag")

    if not isinstance(username, str) or not username.isascii() or not username:
        raise ValueError("Username non valido.")
    if ":" in username:
        raise ValueError("Lo username non deve contenere due punti.")

    if not isinstance(password, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{24,}", password
    ):
        raise ValueError("Password non valida: usare almeno 24 caratteri ASCII.")

    if not isinstance(flag, str) or not re.fullmatch(
            r"CRCTF\{[A-Za-z0-9_-]+\}", flag
    ):
        raise ValueError("Formato della flag non valido.")


def verify_archive(data, config):
    password = config["password"].encode("ascii")
    expected = (config["flag"] + "\n").encode("ascii")

    if b"CRCTF{" in data:
        raise ValueError("L'archivio contiene una flag in chiaro.")

    with pyzipper.AESZipFile(io.BytesIO(data)) as archive:
        if archive.namelist() != ["esito.txt"]:
            raise ValueError("Contenuto inatteso nell'archivio.")

        info = archive.getinfo("esito.txt")
        if not (info.flag_bits & 1) or info.wz_aes_strength != 3:
            raise ValueError("L'archivio non usa AES-256.")

        if archive.read("esito.txt", pwd=password) != expected:
            raise ValueError("La flag nell'archivio non coincide.")

    with pyzipper.AESZipFile(io.BytesIO(data)) as archive:
        try:
            archive.read("esito.txt", pwd=password + b"_errata")
        except (RuntimeError, pyzipper.BadZipFile):
            pass
        else:
            raise ValueError("L'archivio accetta una password errata.")


def generate(output):
    private = output / "private"
    private.mkdir(parents=True, exist_ok=True)

    config_path = private / "scenario.json"
    archive_path = private / "riservato.zip"

    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        validate_config(config)
    else:
        if archive_path.exists():
            raise ValueError(
                "Archivio presente senza la configurazione originale."
            )

        config = {
            "challenge": "J1",
            "username": "archivista",
            "password": secrets.token_urlsafe(24),
            "flag": "CRCTF{http_basic_" + secrets.token_hex(12) + "}",
        }
        validate_config(config)

        with config_path.open("x", encoding="utf-8", newline="\n") as target:
            json.dump(config, target, indent=2)
            target.write("\n")

    created = not archive_path.exists()

    if created:
        buffer = io.BytesIO()
        with pyzipper.AESZipFile(
                buffer, "w", compression=pyzipper.ZIP_DEFLATED
        ) as archive:
            archive.setpassword(config["password"].encode("ascii"))
            archive.setencryption(pyzipper.WZ_AES, nbits=256)
            archive.writestr("esito.txt", config["flag"] + "\n")

        data = buffer.getvalue()
        verify_archive(data, config)

        with archive_path.open("xb") as target:
            target.write(data)
    else:
        data = archive_path.read_bytes()
        verify_archive(data, config)

    print(
        "Materiale J1 creato."
        if created
        else "Materiale J1 esistente verificato."
    )
    print("AES-256, contenuto e rifiuto password errata: OK")
    print("Flag assente in chiaro dall'archivio: OK")
    print("Archivio:", archive_path)
    print("SHA256:", hashlib.sha256(data).hexdigest())
    print("Configurazione riservata:", config_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    os.umask(0o077)

    try:
        generate(args.output)
    except (OSError, ValueError, RuntimeError, pyzipper.BadZipFile) as error:
        parser.exit(1, f"Errore: {error}\n")


if __name__ == "__main__":
    main()