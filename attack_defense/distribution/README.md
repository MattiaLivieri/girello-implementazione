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
