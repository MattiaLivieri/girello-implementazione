"""Configura J4 nella VM Debian degli autori."""

import grp
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import socket
import stat
import subprocess
import tempfile


FLAG = Path("/root/flag.txt")
SUDO_FILE = Path("/etc/sudoers.d/j4-ctf")
SSH_FILE = Path("/etc/ssh/sshd_config.d/00-j4.conf")
SUDO_RULE = "ctf ALL=(root) NOPASSWD: /usr/bin/find\n"
SSH_RULES = "PermitRootLogin no\nPasswordAuthentication yes\nAllowUsers ctf\n"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(*args):
    return subprocess.run(
        args, check=True, text=True, capture_output=True
    ).stdout


def check_target(path, expected=None):
    require(not path.is_symlink(), f"Collegamento simbolico inatteso: {path}")
    if path.exists():
        info = path.stat()
        require(stat.S_ISREG(info.st_mode), f"File non regolare: {path}")
        require(info.st_uid == 0, f"Proprietario inatteso: {path}")
        if expected is not None:
            require(path.read_bytes() == expected, f"Contenuto diverso: {path}")


def install_config(path, text, mode, validator):
    data = text.encode("ascii")
    check_target(path, data)
    fd, name = tempfile.mkstemp(prefix=".j4-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as target:
            target.write(data)
        temporary.chmod(mode)
        os.chown(temporary, 0, 0)
        run(*validator, str(temporary))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_flag(path):
    check_target(path)
    if path.exists():
        data = path.read_bytes()
    else:
        data = (
                "CRCTF{sudo_find_" + secrets.token_hex(12) + "}\n"
        ).encode("ascii")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as target:
            target.write(data)

    require(
        re.fullmatch(rb"CRCTF\{sudo_find_[0-9a-f]{24}\}\n", data) is not None,
        "Formato della flag esistente non valido; il file viene conservato.",
        )
    os.chown(path, 0, 0)
    path.chmod(0o600)
    return hashlib.sha256(data).hexdigest()


def main():
    require(os.geteuid() == 0, "Eseguire come root nella VM J4.")
    require(socket.gethostname() == "j4-linux", "Hostname diverso da j4-linux.")
    require(
        Path("/sys/class/dmi/id/product_name").read_text().strip() == "VirtualBox",
        "La macchina non risulta una VM VirtualBox.",
        )
    require(
        "ID=debian" in Path("/etc/os-release").read_text().splitlines(),
        "Sistema diverso da Debian.",
        )

    account = pwd.getpwnam("ctf")
    require(account.pw_uid != 0, "ctf non deve avere UID 0.")
    groups = {
        grp.getgrgid(g).gr_name
        for g in os.getgrouplist("ctf", account.pw_gid)
    }
    require(
        not groups.intersection(
            {"root", "sudo", "admin", "docker", "lxd", "disk"}
        ),
        "ctf appartiene a un gruppo privilegiato inatteso.",
    )

    interfaces = json.loads(
        run("ip", "-j", "-4", "address", "show", "dev", "enp0s3")
    )
    require(
        any(
            a.get("local") == "192.168.56.10"
            and a.get("prefixlen") == 24
            for i in interfaces
            for a in i["addr_info"]
        ),
        "Indirizzo host-only previsto non presente.",
    )
    for family in ("-4", "-6"):
        require(
            not run("ip", family, "route", "show", "default").strip(),
            "La VM presenta ancora una rotta predefinita.",
        )

    require(Path("/usr/bin/find").is_file(), "find non disponibile.")
    check_target(FLAG)
    check_target(SUDO_FILE, SUDO_RULE.encode("ascii"))
    check_target(SSH_FILE, SSH_RULES.encode("ascii"))
    run("/usr/sbin/visudo", "-c")
    run("/usr/sbin/sshd", "-t")

    flag_hash = ensure_flag(FLAG)
    Path("/root").chmod(0o700)

    install_config(
        SUDO_FILE, SUDO_RULE, 0o440,
        ("/usr/sbin/visudo", "-cf"),
    )
    install_config(
        SSH_FILE, SSH_RULES, 0o644,
        ("/usr/sbin/sshd", "-t", "-f"),
    )

    run("/usr/sbin/visudo", "-c")
    run("/usr/sbin/sshd", "-t")

    effective = run(
        "/usr/sbin/sshd", "-T", "-C",
        "user=ctf,host=j4-linux,addr=192.168.56.1",
    ).splitlines()
    for setting in (
            "permitrootlogin no",
            "passwordauthentication yes",
            "allowusers ctf",
    ):
        require(
            setting in effective,
            f"Impostazione SSH non applicata: {setting}",
            )

    root_settings = run(
        "/usr/sbin/sshd", "-T", "-C",
        "user=root,host=j4-linux,addr=192.168.56.1",
    ).splitlines()
    require(
        "permitrootlogin no" in root_settings,
        "Accesso SSH di root non disabilitato.",
        )

    run("systemctl", "reload", "ssh")
    print("Configurazione J4 completata.")
    print("Flag: /root/flag.txt, proprietario root, permessi 0600.")
    print("SHA256 file flag:", flag_hash)
    print("Regola sudo: validata; accesso SSH diretto di root disabilitato.")
    print("La flag non viene stampata e viene conservata alle successive esecuzioni.")


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError):
            detail = error.stderr or error.stdout or str(error)
        else:
            detail = str(error)
        raise SystemExit(f"Errore: {detail}")