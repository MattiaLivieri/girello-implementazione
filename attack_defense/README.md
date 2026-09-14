# Attack & Defense

Questa cartella contiene i servizi e la configurazione di sviluppo della
modalità Attack & Defense di Girello. Attualmente è presente Document Vault,
un servizio di archiviazione documentale basato su Flask e SQLite.

## Document Vault

Il servizio offre una pagina web e un'API per:

- creare un account, accedere e terminare la sessione;
- caricare documenti `.txt` in UTF-8, da 1 byte a 64 KiB;
- elencare i propri documenti;
- scaricare un documento tramite il suo identificativo.

L'autenticazione usa token Bearer. Le sessioni rimangono valide fino al logout,
che revoca il token utilizzato per la richiesta.

## Struttura

| Percorso | Contenuto |
| --- | --- |
| `compose.yaml` | Avvio del container, pubblicazione della porta e volume persistente |
| `services/document-vault/app.py` | Backend Flask e accesso a SQLite |
| `services/document-vault/static/` | Pagina HTML, stile CSS e codice JavaScript |
| `services/document-vault/requirements.txt` | Dipendenze Python con versioni fissate |
| `services/document-vault/Dockerfile` | Costruzione dell'immagine e avvio con Gunicorn |

## Avvio nella VM

Sono necessari Docker Engine e il plugin Docker Compose.
I comandi seguenti vanno eseguiti dalla cartella `attack_defense`.

```bash
sudo docker compose up -d --build document-vault
```

Aprire `http://127.0.0.1:8081` nel browser della VM.
La configurazione attuale pubblica il servizio soltanto sul localhost della
VM di sviluppo.

Dopo una modifica ai sorgenti, ripetere il comando di avvio per ricostruire
l'immagine e aggiornare il container.

## Gestione del servizio

Per visualizzare lo stato del container:

```bash
sudo docker compose ps
```

Per consultare gli ultimi messaggi di log:

```bash
sudo docker compose logs --tail=50 document-vault
```

Per arrestare il servizio:

```bash
sudo docker compose stop document-vault
```

## Persistenza

SQLite conserva utenti, hash delle password, hash dei token e metadati dei
documenti. Il contenuto dei documenti viene salvato su file.

Database e documenti risiedono nel volume `vault-data`, montato in `/data`.
Il volume conserva i dati durante l'arresto, la ricostruzione dell'immagine e
la ricreazione del container. La cancellazione del volume elimina anche i dati.

## API

Registrazione e login ricevono un oggetto JSON con i campi `username` e
`password`. Gli endpoint `/api/v1/me`, `/api/v1/logout` e quelli dei documenti
richiedono l'header `Authorization: Bearer TOKEN`.

| Metodo | Percorso | Operazione |
| --- | --- | --- |
| POST | `/api/v1/register` | Crea un account |
| POST | `/api/v1/login` | Restituisce il token e i dati dell'utente |
| GET | `/api/v1/me` | Restituisce i dati dell'utente autenticato |
| POST | `/api/v1/logout` | Revoca il token corrente |
| GET | `/api/v1/documents` | Elenca i documenti dell'utente autenticato |
| POST | `/api/v1/documents` | Carica un documento mediante il campo multipart `file` |
| GET | `/api/v1/documents/download?file=ID` | Scarica il documento indicato |
| GET | `/health` | Restituisce lo stato di risposta del servizio e di accesso a SQLite |

L'endpoint `/health` non richiede autenticazione.

## Vulnerabilità didattica

Document Vault contiene una path traversal di sola lettura nel download.
I documenti sono archiviati in `files/<owner_id>/<document_id>` all'interno
della directory dati del servizio.

Il download interpreta il parametro `file` a partire dalla cartella dell'utente
autenticato. Dopo aver risolto il percorso, controlla che il file appartenga
all'archivio globale, ma non che rimanga nella cartella di quell'utente.

Conoscendo il proprietario e l'identificativo di un documento altrui, un utente
autenticato può quindi richiederlo passando
`../<owner_id>/<document_id>` nel parametro `file`. La sola sostituzione
dell'identificativo del documento non consente lo stesso accesso.

Il percorso risolto deve comunque rimanere nell'archivio globale e corrispondere
a un documento registrato in SQLite. Gli accessi esterni all'archivio e i
percorsi assoluti vengono rifiutati. L'upload assegna identificativo e
proprietario sul server: il nome ricevuto dal client rimane un metadato e
non determina il percorso di scrittura.

La correzione prevista consiste nel vincolare il percorso risolto alla cartella
dell'utente autenticato, mantenendo operative le funzioni legittime. Nel codice
attuale questo corrisponde a sostituire `target.is_relative_to(files_dir)` con
`target.is_relative_to(user_dir)`. La correzione non è applicata alla versione
iniziale del servizio destinata all'esercitazione.

## Distribuzione ai team

Questo README è documentazione per gli autori e non viene incluso nella VM dei
team. La VM conterrà i servizi, i sorgenti modificabili, le configurazioni Docker
e le risorse necessarie al loro funzionamento. La repository completa, la sua
cronologia e i materiali riservati agli autori restano fuori dalla distribuzione.

I team potranno analizzare il codice sorgente e modificarlo per applicare le
correzioni difensive. Il codice mantiene commenti tecnici neutrali, senza
indicazioni esplicite sulla vulnerabilità o sulla sua soluzione.

La stessa versione dei sorgenti viene usata nello sviluppo e nella preparazione
della golden image. Le spiegazioni didattiche rimangono nella documentazione
degli autori, così non è necessario ripulire nuovamente i commenti al momento
della distribuzione. La configurazione di rete del servizio verrà adattata
all'ambiente di gara durante la preparazione delle VM.
