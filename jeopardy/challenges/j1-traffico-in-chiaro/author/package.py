"""Prepara il pacchetto pubblico di J1 dal PCAP validato."""

import argparse
import hashlib
import io
from pathlib import Path
import zipfile


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def package(args):
    pcap = args.pcap.read_bytes()
    if sha256(pcap) != args.expected_pcap_sha256.lower():
        raise ValueError("Il PCAP non coincide con la cattura validata.")

    readme = args.readme.read_text(encoding="utf-8-sig").rstrip() + "\n"
    members = {"traffico.pcap": pcap, "README.txt": readme.encode("utf-8")}
    members["SHA256SUMS"] = "".join(
        f"{sha256(data)}  {name}\n" for name, data in members.items()
    ).encode("ascii")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in members.items():
            # Metadati fissi: non dipendono dalla data o dal PC di costruzione.
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
            )
    payload = buffer.getvalue()

    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / "j1-traffico-in-chiaro.zip"
    checksum = args.output / "j1-traffico-in-chiaro.zip.sha256"
    checksum_data = f"{sha256(payload)}  {target.name}\n".encode("ascii")

    if target.exists() or checksum.exists():
        if not (target.is_file() and checksum.is_file()):
            raise ValueError("Uscita incompleta: conservare i file e controllarli.")
        if target.read_bytes() != payload or checksum.read_bytes() != checksum_data:
            raise ValueError("Esiste un pacchetto diverso: non viene sovrascritto.")
    else:
        with target.open("xb") as destination:
            destination.write(payload)
        with checksum.open("xb") as destination:
            destination.write(checksum_data)

    if sha256(target.read_bytes()) != sha256(payload):
        raise ValueError("Il pacchetto salvato non coincide con quello preparato.")

    with zipfile.ZipFile(target) as archive:
        if archive.namelist() != list(members):
            raise ValueError("Il pacchetto contiene file inattesi.")
        for name, data in members.items():
            if archive.read(name) != data:
                raise ValueError(f"Contenuto non corrispondente: {name}.")

    print("Pacchetto verificato:", target.name)
    print("File inclusi:", ", ".join(members))
    print("SHA256 PCAP:", sha256(pcap))
    print("SHA256 pacchetto:", sha256(payload))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcap", type=Path, required=True)
    parser.add_argument("--readme", type=Path, required=True)
    parser.add_argument("--expected-pcap-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        package(args)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Errore: {error}\n")


if __name__ == "__main__":
    main()