# J3 Portale universitario

La challenge usa una piccola applicazione web con dati fittizi per osservare
la distinzione tra autenticazione e autorizzazione nell'accesso ai documenti.

## Stato

Specifica iniziale. Applicazione, immagine, pacchetto e collaudo non ancora realizzati.

## Materiali previsti

- Applicazione Flask con SQLite e risorse web disponibili offline.
- Immagine Linux amd64 esportata in TAR, con versione e checksum identificabili.
- Istruzioni per caricamento, avvio e reset della copia locale.
- Controlli funzionali, di gestione degli input e del percorso didattico previsto.

L'applicazione deve essere eseguita sul PC dello studente, con porta
pubblicata solo sul loopback, processo non root e debugger disabilitato.
L'immagine comprende le dipendenze; l'avvio non deve richiedere Internet.
Il ripristino riguarda soltanto il container della challenge.

La soluzione, i valori canonici e la copia corretta usata nel collaudo
rimangono nei materiali riservati degli autori.