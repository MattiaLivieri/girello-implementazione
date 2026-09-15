#!/usr/bin/env python3
"""Checker di Document Vault per il protocollo pfr di ForcAD.

ForcAD avvia un processo per ciascuna azione:
    checker.py check TARGET
    checker.py put TARGET STATE FLAG PLACE
    checker.py get TARGET STATE FLAG PLACE

Il PUT restituisce i dati pubblici su stdout e lo stato privato su stderr.
ForcAD conserva quest'ultimo e lo passa ai GET successivi: il checker non
deve quindi mantenere credenziali o identificativi in file locali.
"""

import json
import re
import secrets
import sys

import requests


# Sono codici di uscita del processo: per ForcAD il successo corrisponde a 101.
UP = 101            # Operazione riuscita.
CORRUPT = 102       # Una flag depositata non viene recuperata correttamente.
MUMBLE = 103        # Il servizio risponde, ma non rispetta il comportamento atteso.
DOWN = 104          # Connessione fallita o timeout HTTP.
CHECK_FAILED = 110  # Problema negli argomenti, nello stato privato o nel checker.

# Il timeout riguarda connessione e attesa dei dati; ForcAD limita la durata
# complessiva del processo. Il limite alle risposte contiene l'uso di memoria.
HTTP_TIMEOUT = 3
MAX_RESPONSE = 128 * 1024


class CheckerError(Exception):
    """Interrompe l'azione con un esito ForcAD e un messaggio pubblico.

    I messaggi non devono contenere flag, password o token di sessione.
    Il blocco finale del programma traduce l'eccezione nel codice di uscita.
    """

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def require(condition, message, status=MUMBLE):
    """Interrompe il controllo se una condizione necessaria non e' rispettata."""
    if not condition:
        raise CheckerError(status, message)


def valid_document_id(value):
    """Accetta un identificativo semplice, senza separatori di percorso."""
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value))


class Vault:
    """Raccoglie le operazioni HTTP usate dal checker.

    La sessione mantiene il token durante una singola azione. Ogni nuovo
    processo riparte senza autenticazione ed esegue il proprio login.
    """

    def __init__(self, session, target):
        self.session = session
        self.base_url = f"http://{target}:8081"
        self.user_id = None

        # Evita che proxy o credenziali dell'ambiente alterino le richieste.
        self.session.trust_env = False

    def request(self, method, path, expected=200, known_flag=False, **kwargs):
        """Esegue una richiesta e restituisce il corpo come bytes.

        expected indica lo stato HTTP atteso. known_flag viene usato
        nell'azione GET: account o documento inaccessibili significano che
        non riusciamo a recuperare una flag gia' depositata.
        kwargs contiene gli eventuali parametri, JSON o file della richiesta.
        """
        with self.session.request(
            method,
            self.base_url + path,
            timeout=HTTP_TIMEOUT,
            allow_redirects=False,
            stream=True,
            **kwargs,
        ) as response:
            if known_flag and response.status_code in (401, 403, 404):
                raise CheckerError(
                    CORRUPT, "Account o documento della flag non accessibile."
                )

            require(
                response.status_code == expected,
                f"{method} {path}: risposta HTTP {response.status_code}, attesa {expected}.",
            )

            # Leggiamo a blocchi per poter interrompere una risposta troppo grande.
            content = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                content.extend(chunk)
                require(
                    len(content) <= MAX_RESPONSE,
                    "Risposta del servizio troppo grande.",
                )
            return bytes(content)

    def request_json(self, method, path, **kwargs):
        """Esegue una richiesta che deve restituire un oggetto JSON."""
        content = self.request(method, path, **kwargs)
        try:
            data = json.loads(content)
        except ValueError:
            raise CheckerError(MUMBLE, "Risposta JSON non valida.") from None

        require(isinstance(data, dict), "Oggetto JSON atteso nella risposta.")
        return data

    def login(self, credentials, known_flag=False):
        """Accede e prepara il token Bearer per le richieste successive."""
        payload = {
            "username": credentials["username"],
            "password": credentials["password"],
        }
        data = self.request_json(
            "POST", "/api/v1/login",
            known_flag=known_flag,
            json=payload,
        )
        user = data.get("user")
        token = data.get("token")

        # Il login deve restituire l'identita' dell'account richiesto.
        require(isinstance(user, dict), "Identita' assente nella risposta al login.")
        user_id = user.get("id")
        require(
            type(user_id) is int
            and 0 < user_id < 2**63
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
        """Registra un nuovo account, esegue il login e restituisce le credenziali."""
        credentials = {
            "username": "user_" + secrets.token_hex(8),
            "password": secrets.token_hex(16),
        }
        user = self.request_json(
            "POST", "/api/v1/register", expected=201, json=credentials,
        )

        # La registrazione crea l'account; il login apre la sessione.
        self.login(credentials)
        require(
            type(user.get("id")) is int
            and user["id"] == self.user_id
            and user.get("username") == credentials["username"],
            "Registrazione e login restituiscono identita' diverse.",
        )
        return credentials

    def upload(self, content):
        """Carica un documento di testo e verifica i metadati restituiti."""
        name = "documento_" + secrets.token_hex(4) + ".txt"
        document = self.request_json(
            "POST", "/api/v1/documents", expected=201,
            files={"file": (name, content, "text/plain")},
        )
        require(
            valid_document_id(document.get("id")),
            "Identificativo del documento non valido.",
        )
        require(
            document.get("owner_id") == self.user_id
            and document.get("name") == name
            and document.get("size") == len(content),
            "Metadati del documento caricato non coerenti.",
        )
        return document

    def download(self, document_id, known_flag=False):
        """Scarica un documento usando il suo ID e la sessione del proprietario."""
        return self.request(
            "GET", "/api/v1/documents/download",
            params={"file": document_id},
            known_flag=known_flag,
        )

    def logout(self, verify=False):
        """Chiude la sessione; CHECK verifica anche la revoca del vecchio token."""
        self.request("POST", "/api/v1/logout", expected=204)
        if verify:
            # Manteniamo il token nella richiesta per verificare che venga rifiutato.
            self.request("GET", "/api/v1/me", expected=401)
        self.session.headers.pop("Authorization", None)


def check(vault):
    """Verifica il normale utilizzo del servizio con un documento senza flag."""
    health = vault.request_json("GET", "/health")
    require(health.get("status") == "ok", "Health check non riuscito.")

    # Creiamo un account e controlliamo l'identita' associata alla sessione.
    credentials = vault.new_account()
    user = vault.request_json("GET", "/api/v1/me")
    require(
        user.get("id") == vault.user_id
        and user.get("username") == credentials["username"],
        "Identita' della sessione non coerente.",
    )

    content = ("Documento di verifica " + secrets.token_hex(16) + ".\n").encode()
    document = vault.upload(content)
    listing = vault.request_json("GET", "/api/v1/documents")
    documents = listing.get("documents")
    require(isinstance(documents, list), "Elenco documenti non valido.")

    # Il documento appena caricato deve comparire nell'elenco del proprietario.
    found = False
    for item in documents:
        if not isinstance(item, dict):
            continue
        if item.get("id") == document["id"] and item.get("owner_id") == vault.user_id:
            found = True
            break
    require(found, "Documento caricato assente dall'elenco.")

    downloaded = vault.download(document["id"])
    require(downloaded == content, "Contenuto del documento non coerente.")
    vault.logout(verify=True)


def put(vault, flag):
    """Deposita una flag e restituisce separatamente dati pubblici e privati."""
    credentials = vault.new_account()
    content = flag.encode("utf-8")
    document = vault.upload(content)

    # Confermiamo il deposito solo dopo aver riletto lo stesso contenuto.
    downloaded = vault.download(document["id"])
    require(downloaded == content, "Deposito del documento non riuscito.")
    vault.logout()

    # Questi identificativi saranno pubblicati dal motore per le squadre.
    public = {
        "owner_id": vault.user_id,
        "document_id": document["id"],
    }

    # Questi dati rimangono privati e permettono un nuovo login nei GET successivi.
    private = {
        "username": credentials["username"],
        "password": credentials["password"],
        "document_id": document["id"],
    }
    return public, private


def get(vault, private_data, flag):
    """Recupera una flag come legittimo proprietario e ne controlla il contenuto."""
    try:
        state = json.loads(private_data)
    except ValueError:
        raise CheckerError(CHECK_FAILED, "Stato privato del checker non valido.") from None

    # Uno stato inutilizzabile e' un problema del checker, non del servizio.
    require(
        isinstance(state, dict),
        "Stato privato del checker incompleto.", CHECK_FAILED,
    )
    for key in ("username", "password", "document_id"):
        value = state.get(key)
        require(
            isinstance(value, str) and value,
            "Stato privato del checker incompleto.", CHECK_FAILED,
        )
    require(
        valid_document_id(state["document_id"]),
        "Stato privato del checker incompleto.", CHECK_FAILED,
    )

    # Il GET apre una nuova sessione: non riutilizza il token del PUT.
    vault.login(state, known_flag=True)
    content = vault.download(state["document_id"], known_flag=True)
    require(
        content == flag.encode("utf-8"),
        "Contenuto della flag perso o alterato.", CORRUPT,
    )
    vault.logout()


def main():
    """Legge gli argomenti ForcAD, esegue l'azione e restituisce UP se riesce."""
    args = sys.argv[1:]
    require(
        len(args) >= 2,
        "Uso: checker.py check TARGET oppure put/get TARGET STATE FLAG PLACE.",
        CHECK_FAILED,
    )
    action, target = args[:2]

    # CHECK riceve azione e bersaglio; PUT e GET ricevono anche stato, flag e posto.
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
        require(
            place == "1",
            "Document Vault usa un solo posto per le flag: PLACE=1.", CHECK_FAILED,
        )
        require(
            1 <= len(flag.encode("utf-8")) <= 64 * 1024,
            "Flag vuota o troppo grande.", CHECK_FAILED,
        )

    with requests.Session() as session:
        vault = Vault(session, target)
        if action == "check":
            check(vault)
        elif action == "put":
            # Il PUT sostituisce lo stato iniziale di ForcAD con i dati del deposito.
            public, private = put(vault, flag)
            public_json = json.dumps(public, separators=(",", ":"))
            private_json = json.dumps(private, separators=(",", ":"))
            require(
                len(public_json.encode("utf-8")) <= 1024
                and len(private_json.encode("utf-8")) <= 1024,
                "Stato del checker oltre il limite pfr.", CHECK_FAILED,
            )

            # pfr interpreta i due canali come dati: non aggiungiamo messaggi di log.
            print(public_json)
            print(private_json, file=sys.stderr)
        else:
            get(vault, private_data, flag)

    return UP


if __name__ == "__main__":
    # Tutte le azioni terminano attraverso gli stessi esiti, senza traceback pubblici.
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
        # Il tipo aiuta la diagnosi senza pubblicare credenziali o contenuti ricevuti.
        print("Errore interno del checker.")
        print(type(error).__name__, file=sys.stderr)
        result = CHECK_FAILED

    sys.exit(result)
