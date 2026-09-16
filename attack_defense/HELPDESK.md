# HelpDesk API

HelpDesk è il secondo servizio della modalità Attack & Defense di Girello.
Utilizza Flask, SQLite e Gunicorn e offre un'API per account individuali,
sessioni persistenti e ticket personali.

Il servizio viene utilizzato nelle VM del laboratorio didattico locale.
Tutti gli utenti sono ordinari, senza ruoli amministrativi.

## Avvio locale

Dalla radice della repository:

```bash
sudo docker compose -f attack_defense/compose.yaml up -d --build helpdesk
```

La configurazione di sviluppo pubblica il servizio su `127.0.0.1:8082`.
L'esposizione sulla rete dei team sarà configurata durante la preparazione
delle VM di gara.

Per controllare lo stato e la risposta del servizio:

```bash
sudo docker compose -f attack_defense/compose.yaml ps helpdesk
curl -i http://127.0.0.1:8082/health
```

La risposta attesa è `200` con `{"status":"ok"}`.

Per consultare i log e arrestare il servizio:

```bash
sudo docker compose -f attack_defense/compose.yaml logs --tail=50 helpdesk
sudo docker compose -f attack_defense/compose.yaml stop helpdesk
```

Dopo una modifica ai sorgenti, ripetere il comando di avvio con `--build`.

## API

Le richieste con dati utilizzano oggetti JSON.
Gli endpoint privati richiedono `Authorization: Bearer TOKEN`.
Registrazione, login e `/health` sono pubblici.

Un riepilogo contiene `id`, `owner_id`, `title`, `status`, `created_at`.
Il ticket completo contiene anche `body`.

| Metodo | Percorso | Dati | Risposta riuscita |
| --- | --- | --- | --- |
| POST | `/api/v1/register` | `username`, `password` | `201`: identificativo e username |
| POST | `/api/v1/login` | `username`, `password` | `200`: token e dati dell'utente |
| GET | `/api/v1/me` | Nessuno | `200`: identificativo e username |
| POST | `/api/v1/logout` | Nessuno | `204`, corpo vuoto |
| POST | `/api/v1/tickets` | `title`, `body` | `201`: ticket completo |
| GET | `/api/v1/tickets` | Nessuno | `200`: `{"tickets": [...]}` |
| GET | `/api/v1/tickets/search` | Query string `q` | `200`: `{"tickets": [...]}` nel funzionamento ordinario |
| GET | `/api/v1/tickets/{id}` | Identificativo | `200`: ticket completo |
| PATCH | `/api/v1/tickets/{id}` | `status` | `200`: riepilogo aggiornato |
| GET | `/health` | Nessuno | `200`: `{"status":"ok"}` dopo una lettura da SQLite |

La registrazione non apre una sessione. Ogni login crea un nuovo token senza
revocare quelli esistenti. Il logout revoca esclusivamente il token ricevuto.

Il server assegna identificativo, proprietario, data e stato iniziale `open`.
Titolo e contenuto non sono modificabili. Lo stato può essere `open` oppure
`closed`; impostare lo stato già presente è valido.

La lettura diretta e l'aggiornamento richiedono la proprietà del ticket.
Un ticket inesistente o altrui produce `404`. I ticket chiusi rimangono
leggibili e compaiono nell'elenco e nella ricerca ordinaria.

Elenco e ricerca restituiscono al massimo 50 riepiloghi, dai più recenti.
A parità di data, precede il ticket inserito dopo.

## Validazione ed errori

| Campo | Limite |
| --- | --- |
| `username` | 3–32 lettere ASCII, numeri o underscore |
| `password` | 8–128 caratteri |
| `title` | 1–120 caratteri, non composto soltanto da spazi |
| `body` | Testo UTF-8 da 1 byte a 16 KiB |
| `q` | Obbligatorio una sola volta, 1–256 caratteri |
| Corpo HTTP | Massimo 128 KiB, inclusa la codifica JSON |

I campi mancanti, aggiuntivi o di tipo errato producono `400`.
I testi validi vengono conservati senza troncamento o normalizzazione.

Gli errori hanno formato `{"error":"..."}`.

| Codice | Significato |
| --- | --- |
| `400` | Richiesta o dati non validi |
| `401` | Credenziali o autenticazione assenti o non valide |
| `404` | Ticket inesistente o altrui |
| `409` | Username già utilizzato |
| `413` | Corpo HTTP superiore al limite |
| `503` | Errore di accesso all'archivio o di esecuzione SQLite |

## Ricerca e vulnerabilità didattica

La funzione `search_tickets(connection, owner_id, q)` contiene la query
e la lettura dei risultati. L'endpoint gestisce autenticazione, validazione
di `q` e risposta JSON. La ricerca utilizza una connessione SQLite distinta,
aperta in sola lettura, e non legge i file dei ticket.

Nel funzionamento ordinario, la ricerca riguarda una sottostringa del titolo,
distingue maiuscole e minuscole e restituisce i ticket del proprietario.
I caratteri `%` e `_` non sono interpretati come wildcard.

La versione iniziale dell'esercitazione contiene una vulnerabilità
intenzionale nella costruzione della query: il proprietario è passato come
parametro, mentre `q` viene inserito direttamente nel testo SQL.

Di conseguenza, il valore di `q` non viene sempre trattato come testo
letterale e può modificare il significato della query. La connessione
in sola lettura impedisce le scritture al database, ma non garantisce
l'isolamento delle letture.

Una ricerca ordinaria contenente un apostrofo può causare un errore SQL,
restituito dall'applicazione come `503`. Questo è uno scostamento noto
rispetto al contratto iniziale della ricerca letterale.

Le spiegazioni didattiche restano nella documentazione degli autori.
La verifica dello scenario di attacco e della relativa correzione difensiva
appartiene alla validazione dell'esercitazione.

## Persistenza

Il volume `helpdesk-data`, montato in `/data`, contiene:

- `helpdesk.sqlite3`: utenti, hash delle password, sessioni e metadati;
- `files/<owner_id>/<ticket_id>`: contenuto UTF-8 dei ticket.

Le password sono memorizzate mediante scrypt. I token sono generati con
`secrets.token_urlsafe(32)` e conservati nella tabella delle sessioni insieme
all'identificativo dell'utente. Restano validi fino al logout.

I percorsi dei file sono determinati dal server. Prima della lettura del
contenuto, l'applicazione verifica la proprietà del ticket.

Il volume conserva i dati dopo riavvio e ricreazione del container.
La rimozione esplicita del volume elimina i dati.

## Stato delle verifiche

Sono stati verificati sul codice della revisione `1da8dc2`:

- account, autenticazione, sessioni multiple e logout tramite HTTP;
- creazione, lettura, elenco e aggiornamento dello stato dei ticket;
- controllo del proprietario nella lettura diretta e nell'aggiornamento;
- ricerca ordinaria, ordine e limite dei risultati;
- validazione degli input e limiti delle dimensioni;
- apertura in sola lettura della connessione di ricerca;
- persistenza dopo la ricreazione dell'applicazione;
- gestione degli errori dei file e rollback dei metadati.

Build Docker, avvio del container e risposta di `/health` sono stati
verificati nella VM di sviluppo.

I test non sono inclusi nella repository in questa fase.
La validazione nelle VM definitive e l'integrazione con il checker ForcAD
sono attività successive.

## Interfaccia web

L'interfaccia è disponibile su `http://127.0.0.1:8082/` nel browser
della VM di sviluppo. Usa HTML, CSS e JavaScript locali, senza dipendenze
da servizi esterni.

Permette di registrarsi, accedere, creare ticket, consultarli, cercarli
nel titolo e modificarne lo stato. Titolo e contenuto dei ticket esistenti
sono mostrati in sola lettura.

La registrazione crea l'account; l'accesso avviene successivamente con
il pulsante Accedi. Il token è conservato in sessionStorage e viene
verificato tramite `/api/v1/me` al ricaricamento della pagina.
Il logout revoca la sessione corrente e rimuove il token dalla scheda.

I file della pagina si trovano in `services/helpdesk/static/`.
Flask serve la pagina iniziale su `/` e le risorse sotto `/static/`.
Tutte le operazioni applicative utilizzano gli endpoint API esistenti.
