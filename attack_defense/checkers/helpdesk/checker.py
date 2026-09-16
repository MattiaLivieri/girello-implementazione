#!/usr/bin/env python3
"""Checker HelpDesk per il protocollo pfr di ForcAD.

Invocazioni del motore:
    checker.py check TARGET
    checker.py put TARGET STATE FLAG PLACE
    checker.py get TARGET STATE FLAG PLACE

PUT restituisce identificativi pubblici su stdout e stato privato su stderr.
ForcAD conserva lo stato e lo passa ai GET: il checker non usa file locali.
"""

import json
import re
import secrets
import sys

import requests


# Sono codici di uscita del processo: per ForcAD il successo e' 101.
UP = 101
CORRUPT = 102       # Flag persa, alterata o non piu' accessibile.
MUMBLE = 103        # Risposta o comportamento del servizio non coerenti.
DOWN = 104          # Connessione fallita o timeout HTTP.
CHECK_FAILED = 110  # Argomenti, stato privato o errore interno del checker.

# ForcAD applica separatamente il timeout complessivo dell'azione.
HTTP_TIMEOUT = 3
MAX_RESPONSE = 128 * 1024
SUMMARY_FIELDS = ("id", "owner_id", "title", "status", "created_at")


class CheckerError(Exception):
    """Associa un esito ForcAD a un messaggio privo di dati riservati."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def require(condition, message, status=MUMBLE):
    """Interrompe l'azione se il servizio non soddisfa una condizione."""
    if not condition:
        raise CheckerError(status, message)


def valid_ticket_id(value):
    """Accetta identificativi semplici, utilizzabili nel percorso HTTP."""
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value))


def validate_summary(ticket, owner_id):
    """Verifica i campi comuni al riepilogo e al ticket completo."""
    require(isinstance(ticket, dict), "Ticket non valido.")
    require(valid_ticket_id(ticket.get("id")), "Identificativo del ticket non valido.")
    require(
        type(ticket.get("owner_id")) is int and ticket["owner_id"] == owner_id,
        "Proprietario del ticket non coerente.",
    )
    title = ticket.get("title")
    require(
        isinstance(title, str) and 1 <= len(title) <= 120 and bool(title.strip()),
        "Titolo del ticket non valido.",
    )
    require(ticket.get("status") in ("open", "closed"), "Stato del ticket non valido.")
    require(
        isinstance(ticket.get("created_at"), str) and bool(ticket["created_at"]),
        "Data del ticket non valida.",
    )


def ticket_summary(ticket):
    """Estrae i metadati da un ticket gia' validato."""
    return {field: ticket[field] for field in SUMMARY_FIELDS}


class HelpDesk:
    """Raccoglie le operazioni HTTP usate dalle tre azioni del checker."""

    def __init__(self, session, target):
        self.session = session
        self.base_url = f"http://{target}:8082"
        self.user_id = None
        # Le richieste devono raggiungere il bersaglio senza proxy dell'ambiente.
        self.session.trust_env = False

    def request(self, method, path, expected=200, known_flag=False, **kwargs):
        """Controlla lo stato HTTP e legge una risposta di dimensione limitata.

        Nel GET, credenziali rifiutate o un ticket scomparso indicano CORRUPT.
        Gli altri stati HTTP inattesi indicano MUMBLE, come in Document Vault.
        Gli errori di connessione sono tradotti in DOWN dal blocco finale.
        """
        with self.session.request(
            method, self.base_url + path,
            timeout=HTTP_TIMEOUT,
            allow_redirects=False,
            stream=True,
            **kwargs,
        ) as response:
            if known_flag and response.status_code in (401, 403, 404):
                raise CheckerError(CORRUPT, "Account o ticket della flag non accessibile.")
            require(
                response.status_code == expected,
                f"{method} {path}: HTTP {response.status_code}, atteso {expected}.",
            )
            content = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                content.extend(chunk)
                require(len(content) <= MAX_RESPONSE, "Risposta del servizio troppo grande.")
            return bytes(content)

    def request_json(self, method, path, **kwargs):
        """Richiede una risposta contenente un oggetto JSON."""
        content = self.request(method, path, **kwargs)
        try:
            data = json.loads(content)
        except ValueError:
            raise CheckerError(MUMBLE, "Risposta JSON non valida.") from None
        require(isinstance(data, dict), "Oggetto JSON atteso nella risposta.")
        return data

    def login(self, credentials, known_flag=False):
        """Apre una nuova sessione e prepara l'header Bearer."""
        data = self.request_json(
            "POST", "/api/v1/login", known_flag=known_flag,
            json={"username": credentials["username"], "password": credentials["password"]},
        )
        user = data.get("user")
        token = data.get("token")
        require(isinstance(user, dict), "Identita' assente nella risposta al login.")
        user_id = user.get("id")
        require(
            type(user_id) is int and 0 < user_id < 2**63
            and user.get("username") == credentials["username"],
            "Identita' non coerente nella risposta al login.",
        )
        require(
            isinstance(token, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", token),
            "Token di sessione non valido.",
        )
        self.user_id = user_id
        self.session.headers["Authorization"] = f"Bearer {token}"

    def new_account(self):
        """Crea un account distinto per questa azione ed esegue il login."""
        credentials = {
            "username": "user_" + secrets.token_hex(8),
            "password": secrets.token_hex(16),
        }
        user = self.request_json(
            "POST", "/api/v1/register", expected=201, json=credentials,
        )
        self.login(credentials)
        require(
            type(user.get("id")) is int and user["id"] == self.user_id
            and user.get("username") == credentials["username"],
            "Registrazione e login restituiscono identita' diverse.",
        )
        return credentials

    def create_ticket(self, title, body):
        """Crea un ticket e verifica proprietario, stato e contenuto restituiti."""
        ticket = self.request_json(
            "POST", "/api/v1/tickets", expected=201,
            json={"title": title, "body": body},
        )
        validate_summary(ticket, self.user_id)
        require(
            ticket["title"] == title and ticket.get("body") == body
            and ticket["status"] == "open",
            "Ticket creato non coerente con la richiesta.",
        )
        return ticket

    def read_ticket(self, ticket_id, known_flag=False):
        """Legge il ticket usando la sessione del proprietario, anche se chiuso."""
        ticket = self.request_json(
            "GET", f"/api/v1/tickets/{ticket_id}", known_flag=known_flag,
        )
        validate_summary(ticket, self.user_id)
        require(ticket["id"] == ticket_id, "Identificativo del ticket non coerente.")
        require(isinstance(ticket.get("body"), str), "Contenuto del ticket non valido.")
        return ticket

    def list_tickets(self, q=None):
        """Legge i riepiloghi; se q e' presente usa l'endpoint di ricerca."""
        if q is None:
            data = self.request_json("GET", "/api/v1/tickets")
        else:
            data = self.request_json("GET", "/api/v1/tickets/search", params={"q": q})
        tickets = data.get("tickets")
        require(isinstance(tickets, list) and len(tickets) <= 50, "Elenco ticket non valido.")
        for ticket in tickets:
            validate_summary(ticket, self.user_id)
            require("body" not in ticket, "Il riepilogo include il contenuto del ticket.")
        return tickets

    def logout(self, verify=False):
        """Revoca il token corrente; CHECK ne verifica anche il rifiuto successivo."""
        content = self.request("POST", "/api/v1/logout", expected=204)
        require(content == b"", "Il logout deve restituire un corpo vuoto.")
        if verify:
            self.request("GET", "/api/v1/me", expected=401)
        self.session.headers.pop("Authorization", None)


def check(desk):
    """Verifica il normale ciclo di vita di un ticket senza depositare flag."""
    health = desk.request_json("GET", "/health")
    require(health.get("status") == "ok", "Health check non riuscito.")
    credentials = desk.new_account()
    user = desk.request_json("GET", "/api/v1/me")
    require(
        type(user.get("id")) is int and user["id"] == desk.user_id
        and user.get("username") == credentials["username"],
        "Identita' della sessione non coerente.",
    )

    # Usiamo dati ordinari e distinti da quelli dei depositi delle flag.
    marker = "Rete_" + secrets.token_hex(8)
    title = "Assistenza " + marker + "%_CPU"
    body = "Richiesta di verifica " + secrets.token_hex(16) + ".\n"
    ticket = desk.create_ticket(title, body)
    summary = ticket_summary(ticket)
    require(summary in desk.list_tickets(), "Ticket creato assente dall'elenco.")
    require(
        summary in desk.list_tickets(q=marker + "%_"),
        "Ticket creato assente dalla ricerca.",
    )
    # La variante in minuscolo non compare nel titolo: verifica anche il caso vuoto.
    require(not desk.list_tickets(q=marker.lower()), "Ricerca non coerente con il titolo.")

    # Chiusura, ripetizione dello stesso stato e riapertura devono conservare i dati.
    for status in ("closed", "closed", "open"):
        updated = desk.request_json(
            "PATCH", f"/api/v1/tickets/{ticket['id']}", json={"status": status},
        )
        ticket["status"] = status
        require(updated == ticket_summary(ticket), "Aggiornamento dello stato non coerente.")
        require(desk.read_ticket(ticket["id"]) == ticket, "Dati del ticket alterati.")
    desk.logout(verify=True)


def put(desk, flag):
    """Deposita la flag nel corpo di un nuovo ticket e conferma la rilettura."""
    credentials = desk.new_account()
    ticket = desk.create_ticket("Richiesta " + secrets.token_hex(8), flag)
    stored = desk.read_ticket(ticket["id"])
    require(stored == ticket, "Deposito del ticket non riuscito.")

    # La sessione del PUT resta valida per lo scenario didattico.
    # Chiudere requests.Session libera le connessioni HTTP, ma non esegue il logout.
    public = {"owner_id": desk.user_id, "ticket_id": ticket["id"]}
    private = {
        "username": credentials["username"],
        "password": credentials["password"],
        "ticket_id": ticket["id"],
    }
    return public, private


def get(desk, private_data, flag):
    """Recupera la flag con un nuovo login e chiude soltanto questa sessione."""
    try:
        state = json.loads(private_data)
    except ValueError:
        raise CheckerError(CHECK_FAILED, "Stato privato non valido.") from None
    require(isinstance(state, dict), "Stato privato incompleto.", CHECK_FAILED)
    require(
        isinstance(state.get("username"), str)
        and re.fullmatch(r"[A-Za-z0-9_]{3,32}", state["username"])
        and isinstance(state.get("password"), str)
        and 8 <= len(state["password"]) <= 128
        and valid_ticket_id(state.get("ticket_id")),
        "Stato privato incompleto.", CHECK_FAILED,
    )

    desk.login(state, known_flag=True)
    ticket = desk.read_ticket(state["ticket_id"], known_flag=True)
    require(ticket["body"] == flag, "Contenuto della flag perso o alterato.", CORRUPT)
    desk.logout()


def main():
    """Valida gli argomenti del motore ed esegue una sola azione."""
    args = sys.argv[1:]
    require(
        len(args) >= 2,
        "Uso: checker.py check TARGET oppure put/get TARGET STATE FLAG PLACE.",
        CHECK_FAILED,
    )
    action, target = args[:2]
    expected_arguments = {"check": 2, "put": 5, "get": 5}
    require(
        len(args) == expected_arguments.get(action),
        "Azione o numero di argomenti non valido.", CHECK_FAILED,
    )
    require(
        re.fullmatch(r"[A-Za-z0-9.-]+", target),
        "TARGET deve essere un IPv4 o un hostname, senza porta.", CHECK_FAILED,
    )
    if action != "check":
        private_data, flag, place = args[2:]
        require(place == "1", "HelpDesk usa un solo posto: PLACE=1.", CHECK_FAILED)
        require(
            1 <= len(flag.encode("utf-8")) <= 16 * 1024,
            "Flag vuota o troppo grande.", CHECK_FAILED,
        )

    with requests.Session() as session:
        desk = HelpDesk(session, target)
        if action == "check":
            check(desk)
        elif action == "put":
            # Lo stato iniziale passato da ForcAD viene sostituito dal nostro JSON.
            public, private = put(desk, flag)
            public_json = json.dumps(public, separators=(",", ":"))
            private_json = json.dumps(private, separators=(",", ":"))
            require(
                len(public_json.encode("utf-8")) + 1 <= 1024
                and len(private_json.encode("utf-8")) + 1 <= 1024,
                "Stato del checker oltre il limite pfr.", CHECK_FAILED,
            )
            # Non aggiungere log: ForcAD interpreta questi canali come dati.
            print(public_json)
            print(private_json, file=sys.stderr)
        else:
            get(desk, private_data, flag)
    return UP


if __name__ == "__main__":
    try:
        result = main()
    except CheckerError as error:
        print(str(error))
        result = error.status
    except (requests.Timeout, requests.ConnectionError):
        print("Servizio non raggiungibile o timeout HTTP.")
        result = DOWN
    except requests.RequestException:
        print("Comunicazione HTTP non valida.")
        result = MUMBLE
    except Exception as error:
        # Il tipo aiuta la diagnosi senza esporre flag, password o token.
        print("Errore interno del checker.")
        print(type(error).__name__, file=sys.stderr)
        result = CHECK_FAILED
    sys.exit(result)
