# File per la distribuzione Attack & Defense

## Dockerfile.runtime

Costruisce l'immagine `girello/ad-runtime:1`, contenente Python
e le dipendenze comuni a Document Vault e HelpDesk.

Usa la stessa base Python fissata tramite digest dei servizi
e legge le dipendenze dai loro requirements.txt originali.

La costruzione di questa immagine richiede accesso a Internet.
L'immagine ottenuta è destinata alla golden image come base
locale per i Dockerfile di distribuzione dei servizi.

Questo permette di predisporre la ricostruzione dei servizi
con le librerie già installate, senza doverle scaricare durante
l'esercitazione.


## Dockerfile.document-vault e Dockerfile.helpdesk

Costruiscono i servizi usando la base locale `girello/ad-runtime:1`.
Controllano che le dipendenze richieste siano disponibili senza
consultare indici di pacchetti, quindi copiano i sorgenti applicativi.

## compose.team.yaml

Definisce la configurazione dei servizi per le VM delle squadre:
porte 8081 e 8082, volumi persistenti separati e politica di riavvio
`unless-stopped`.

## prepare-package.sh

Prepara una nuova directory esterna alla repository contenente:

- i sorgenti applicativi tracciati nel commit corrente;
- i Dockerfile di distribuzione, il Compose e la guida operativa;
- la base runtime esportata in `runtime.tar`;
- il riferimento al commit dei sorgenti e all'immagine runtime.

Lo script esporta una selezione esplicita di file e non include
la cronologia Git, i checker o i volumi di sviluppo.


## README.team.md

Guida operativa destinata alle squadre. Viene inclusa nel pacchetto
come `README.md` e descrive accesso ai servizi, sorgenti, ricostruzione
offline, avvio, log e persistenza.

## Verifiche della golden — 17 settembre 2026

Verifiche eseguite sulla VM Debian dedicata alla distribuzione,
con sorgenti applicativi riferiti al commit `57ab325`:

- importazione della base `girello/ad-runtime:1`, con ID corrispondente
  a quello registrato nel pacchetto;
- costruzione iniziale e avvio di entrambi i servizi con rete scollegata;
- ricostruzione senza cache dopo una modifica temporanea ai sorgenti
  Python, verificata attraverso le risposte HTTP;
- persistenza di sessioni e contenuti dopo ricreazione dei container;
- ripristino dei sorgenti originali e avvio automatico dopo reboot;
- persistenza delle sessioni dopo reboot;
- pulizia finale: utenti, sessioni, documenti, ticket e cartelle
  dei contenuti vuoti; dati delle sessioni rimossi da Firefox;
- nome di sistema `girello-golden` e risoluzione IPv4 locale verificati.

Restano da completare la preparazione delle due VM delle squadre,
la validazione del percorso worker-proxy-servizi, i round reali
ForcAD e l'esportazione degli artefatti finali.
