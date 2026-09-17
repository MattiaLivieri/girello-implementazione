# Girello — Guida della VM

## Servizi e sorgenti

Il collegamento Girello sul Desktop apre `/home/girello/girello`.

| Servizio | Indirizzo da Firefox nella VM | Sorgenti |
|---|---|---|
| Document Vault | http://127.0.0.1:8081 | services/document-vault/ |
| HelpDesk | http://127.0.0.1:8082 | services/helpdesk/ |

Ogni servizio contiene `app.py`, la cartella `static`, il Dockerfile
e il file `requirements.txt`.

## Stato e log

Esegui i comandi dal terminale della VM, nella directory del progetto:

```bash
cd /home/girello/girello
```

Controlla i container e consulta gli ultimi log:

```bash
sudo docker compose -f compose.yaml ps -a
sudo docker compose -f compose.yaml logs --tail=50
```

## Applicare modifiche ai sorgenti

Dopo aver modificato Python, HTML, CSS o JavaScript, ricostruisci
l'immagine del servizio e applicala al container.

Per Document Vault:

```bash
sudo docker compose -f compose.yaml build document-vault &&
sudo docker compose -f compose.yaml up -d --no-build --pull never document-vault
```

Per HelpDesk:

```bash
sudo docker compose -f compose.yaml build helpdesk &&
sudo docker compose -f compose.yaml up -d --no-build --pull never helpdesk
```

La ricostruzione funziona senza Internet usando la base locale
`girello/ad-runtime:1` e le dipendenze già incluse.
L'aggiunta di nuove librerie richiede che siano disponibili localmente.

## Avvio e persistenza

Per creare o avviare entrambi i container dalle immagini presenti:

```bash
sudo docker compose -f compose.yaml up -d --no-build --pull never
```

I container lasciati in esecuzione ripartono automaticamente al riavvio
della VM. Un container arrestato esplicitamente resta fermo finché
non viene avviato di nuovo.

Account, sessioni, documenti e ticket sono conservati in volumi separati
e persistono dopo la ricreazione dei container e il riavvio della VM.

Il comando `docker compose down --volumes` elimina questi dati.

## Verifica rapida

```bash
curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8081/health
curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8082/health
```

Entrambe le risposte devono contenere `"status":"ok"`.

## Ripristinare la base Docker

Se la base locale è stata rimossa, puoi importarla nuovamente:

```bash
sudo docker image load --input runtime.tar
```

Poi ricostruisci i servizi con i comandi precedenti.
`runtime.tar` contiene la base Docker, non i dati applicativi.
