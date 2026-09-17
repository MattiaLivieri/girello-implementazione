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


Successivamente sono stati preparati i cloni `girello-team1` e
`girello-team2`, con hostname e machine-id distinti e indirizzi statici
rispettivamente `10.77.1.10/24` e `10.77.2.10/24`,
senza gateway o DNS e con IPv6 disabilitato.

Dopo gli stalli RCU osservati su Team2, i moduli `vboxguest` e `vboxsf`
sono stati esclusi persistentemente tramite GRUB nelle due VM e nella
golden. Nei successivi avvii controllati gli stalli non si sono ripresentati
e i servizi hanno risposto correttamente. Questa configurazione costituisce
un workaround verificato; la causa precisa non è stata accertata.
Gli appunti condivisi e le cartelle condivise VirtualBox non sono disponibili.

La golden aggiornata è conservata nello snapshot `golden-pronta-v2`.
Le OVA sono state esportate in `/srv/girello/distribution/ad/v1/`.
La distribuzione attraverso CTFd è descritta in [CTFD.md](CTFD.md).
## Prova integrata — 17 settembre 2026

La prova è stata eseguita con il Master e due PC partecipanti,
ciascuno con la VM della propria squadra.

Risultati verificati:

- download delle due OVA tramite CTFd, checksum SHA-256 corrispondenti,
  importazione e avvio sui PC partecipanti;
- raggiungibilità di entrambi i servizi di entrambe le squadre
  dal worker attraverso i proxy del Master;
- esecuzione ForcAD fino al round 6, con round da 300 secondi;
- deposito e recupero delle flag riusciti per entrambi i servizi
  di entrambe le squadre;
- accettazione di una flag di Document Vault di Team 2 inviata
  da Team 1, con aggiornamento dei contatori e dei punti;
- rilevazione dell'arresto di HelpDesk di Team 2 al round 5,
  mentre gli altri servizi restavano disponibili;
- ritorno del servizio a UP al round 6, conservando il conteggio
  di cinque controlli superati su sei;
- arresto di ForcAD e ripristino del profilo default del Master.

La classifica pubblica viene aggiornata al cambio di round con
i risultati del round appena concluso. Il punteggio totale somma,
per ciascun servizio, i punti flag moltiplicati per il rapporto
tra controlli superati e controlli eseguiti.

La prova di invio usa una flag recuperata dal Master e verifica
ricezione, attribuzione e punteggio. Non documenta l'acquisizione
tramite exploit, l'invio nella direzione opposta o il rifiuto
di una submission duplicata.

L'implementazione funzionale A&D del prototipo è conclusa nel
perimetro verificato. Il modulo web per l'invio delle flag
rimane uno sviluppo successivo.
