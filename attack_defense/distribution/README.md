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
- i Dockerfile di distribuzione e il Compose;
- la base runtime esportata in `runtime.tar`;
- il riferimento al commit dei sorgenti e all'immagine runtime.

Lo script esporta una selezione esplicita di file e non include
la cronologia Git, i checker o i volumi di sviluppo.
