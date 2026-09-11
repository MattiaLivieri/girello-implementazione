J3 - Portale universitario

SCENARIO
Hai accesso al profilo di Alice Rossi nel portale studenti UniGirello.
Un documento riservato a un altro personaggio contiene la flag.
Individua il problema nell'accesso ai documenti e recupera la risposta.
Tutti i personaggi e i dati appartengono a questa copia locale.

PREPARAZIONE (PRIMA DEL TEMPO DI SOLUZIONE)
Occorrono Docker con motore Linux amd64, Docker Compose e un browser.
Su Windows utilizzare Docker Desktop in modalità Linux containers.
L'immagine contiene già le dipendenze e le risorse web.
Non occorre installare Python e non serve Internet durante la prova.

Materiali della distribuzione finale:
- j3-portale-universitario.tar
- compose.yaml
- README.txt
- SHA256SUMS

Confrontare i checksum dei materiali con SHA256SUMS.
Da un terminale nella cartella ricevuta, caricare l'immagine:

docker load --input j3-portale-universitario.tar

AVVIO
Nella stessa cartella:

docker compose -f compose.yaml up -d --wait

Aprire nel browser:
http://127.0.0.1:18083

Credenziali del personaggio:
Utente: alice
Password: LaboratorioJ3!

Queste credenziali sono diverse da quelle del portale CTFd.
La porta 18083 deve essere libera; avviare una sola copia di J3.

OBIETTIVO E PERIMETRO
Il percorso previsto usa il browser e le richieste HTTP alla propria
copia del portale. Non richiede attacchi ad altri studenti, servizi
esterni, tentativi sulle password o modifiche alla configurazione Docker.
L'ispezione diretta dell'immagine, del filesystem o del database è
esterna al percorso dell'esercitazione.
Inserire in CTFd la flag completa nel formato CRCTF{...}.

ARRESTO E RIPRISTINO
Per rimuovere la propria istanza e la rete dedicata:

docker compose -f compose.yaml down

Per ricrearla nello stato iniziale:

docker compose -f compose.yaml up -d --wait

Il database e le sessioni sono temporanei: anche arrestando il container
si perde lo stato locale. Dopo il ripristino accedere nuovamente.
La flag rimane quella contenuta nell'immagine distribuita.
Il ripristino locale non annulla la soluzione o i punti registrati in CTFd.