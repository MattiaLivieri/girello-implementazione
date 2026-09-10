# CTFd di sviluppo per Jeopardy

Questa directory contiene un'istanza CTFd destinata al collaudo locale
del flusso Jeopardy, usando account, challenge e flag di prova.

L'ambiente viene eseguito sul PC di sviluppo e usa un proprio database.
Sul Master rimane valido il vincolo di sola lettura.

## Configurazione

- CTFd 3.8.7, MariaDB 10.11.19 e Redis 7.4.11.
- Immagini vincolate agli stessi digest del Compose comune.
- Piattaforma dei container: linux/amd64.
- Progetto Compose: girello-jeopardy-dev.
- Portale: http://127.0.0.1:18080.
- Database e Redis senza porte pubblicate sul PC.
- Volumi dedicati per database, Redis, upload e log.
- Avvio manuale dei servizi.
- Accesso diretto a CTFd, senza reverse proxy.

## Credenziali locali

Il file `.env.example` documenta le quattro variabili richieste.
I valori effettivi appartengono al file `.env` di questa directory,
già escluso da Git dalle regole del repository.

Ogni valore deve essere generato casualmente e rappresentato da
64 caratteri esadecimali. Questa rappresentazione evita caratteri
speciali negli URL di connessione.

Le credenziali devono essere conservate insieme ai dati dell'istanza:
cambiare le variabili non aggiorna automaticamente le password di
un database già inizializzato.

## Comandi operativi

I comandi seguenti sono destinati a PowerShell su Windows,
dalla radice del repository, con Docker Desktop avviato.

Validazione della configurazione senza stampare le credenziali:

```powershell
docker --context desktop-linux compose -p girello-jeopardy-dev --env-file jeopardy/dev/.env -f jeopardy/dev/compose.yaml config --quiet
```

Download iniziale delle immagini, con connessione Internet:

```powershell
docker --context desktop-linux compose -p girello-jeopardy-dev --env-file jeopardy/dev/.env -f jeopardy/dev/compose.yaml pull
```

Avvio usando le immagini già scaricate:

```powershell
docker --context desktop-linux compose -p girello-jeopardy-dev --env-file jeopardy/dev/.env -f jeopardy/dev/compose.yaml up -d --pull never --wait --wait-timeout 300
```

Consultazione dello stato:

```powershell
docker --context desktop-linux compose -p girello-jeopardy-dev --env-file jeopardy/dev/.env -f jeopardy/dev/compose.yaml ps
```

Arresto dei servizi locali conservando i dati:

```powershell
docker --context desktop-linux compose -p girello-jeopardy-dev --env-file jeopardy/dev/.env -f jeopardy/dev/compose.yaml stop
```

## Perimetro delle verifiche

L'ambiente serve a verificare accesso, distribuzione dei materiali,
orari della prova, invio delle flag, punteggi, suggerimenti e classifica.

La disponibilità dei servizi non dimostra da sola la correttezza
del flusso di gara. Gli esiti delle prove devono essere registrati
dopo la loro esecuzione.

Le verifiche locali non coprono il reverse proxy del Master,
l'isolamento Wi-Fi o il dimensionamento della sessione in aula.