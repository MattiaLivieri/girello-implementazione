"""Download delle due VM A&D, assegnate esplicitamente a utenti CTFd."""

import os

from flask import Blueprint, Response, abort, render_template

from CTFd.plugins import register_user_page_menu_bar
from CTFd.utils.decorators import authed_only
from CTFd.utils.user import get_current_user


# Metadati delle OVA già esportate sul Master.
VERSION = "v1"
VMS = {
    "team1": {
        "label": "Team 1",
        "filename": "girello-team1.ova",
        "address": "10.77.1.10/24",
        "sha256": "29a76ae656c9e718412c3a5c95ddb5714c8d82063486a8c97562ade5ffe12442",
    },
    "team2": {
        "label": "Team 2",
        "filename": "girello-team2.ova",
        "address": "10.77.2.10/24",
        "sha256": "2a5de0f6be4a6aed54d9d201d566c3cf2fdba94dd987ccb9eed7d6771d3886c9",
    },
}

vm_pages = Blueprint("girello_vm", __name__, url_prefix="/girello/vm")


def assigned_vm():
    """Ricava la VM dalla sessione; nessun nome di file arriva dal browser."""
    user = get_current_user()
    if user is None or user.banned or user.type != "user":
        abort(403, description="Questo account non puo' scaricare una VM.")

    # Le assegnazioni rimangono nel file di ambiente locale, fuori da Git.
    try:
        team1_id = int(os.environ.get("GIRELLO_VM_TEAM1_USER_ID", "0"))
        team2_id = int(os.environ.get("GIRELLO_VM_TEAM2_USER_ID", "0"))
    except ValueError:
        abort(503, description="Assegnazioni VM non valide: contatta l'organizzatore.")

    if min(team1_id, team2_id) < 0 or (team1_id != 0 and team1_id == team2_id):
        abort(503, description="Assegnazioni VM non valide: contatta l'organizzatore.")

    if team1_id > 0 and user.id == team1_id:
        return VMS["team1"]
    if team2_id > 0 and user.id == team2_id:
        return VMS["team2"]

    abort(403, description="Nessuna VM assegnata a questo account. Contatta l'organizzatore.")


@vm_pages.after_request
def private_response(response):
    # Impedisce a una cache condivisa di riutilizzare risposte di altri utenti.
    response.headers["Cache-Control"] = "private, no-store"
    return response


@vm_pages.get("")
@authed_only
def index():
    return render_template(
        "plugins/girello_vm/templates/download.html",
        vm=assigned_vm(),
        version=VERSION,
    )


@vm_pages.get("/download")
@authed_only
def download():
    vm = assigned_vm()

    # Nginx trasferisce la OVA. Flask restituisce soltanto gli header.
    response = Response(content_type="application/octet-stream")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{vm["filename"]}"'
    )
    response.headers["X-Accel-Redirect"] = (
        f'/_girello_vm/{VERSION}/{vm["filename"]}'
    )
    return response


@vm_pages.get("/checksum")
@authed_only
def checksum():
    vm = assigned_vm()
    response = Response(
        f'{vm["sha256"]}  {vm["filename"]}\n',
        content_type="text/plain; charset=utf-8",
    )
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{vm["filename"]}.sha256"'
    )
    return response


def load(app):
    app.register_blueprint(vm_pages)
    register_user_page_menu_bar("VM A&D", route="girello/vm")
