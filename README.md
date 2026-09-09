# Girello

Cyber Range didattico locale e portatile, sviluppato nell'ambito della
tesi di Informatica presso l'Università di Camerino.


## Obiettivo

Realizzare esercitazioni Jeopardy e Attack & Defense utilizzando un
nodo centrale e i PC dei partecipanti, con risorse e complessità di
gestione contenute.

Le sessioni si svolgono su una rete locale. Materiali, strumenti e
dipendenze devono essere predisposti prima dell'esercitazione, così
da consentirne lo svolgimento senza accesso a Internet.

## Architettura di riferimento

Il nodo centrale, denominato Master, è un ODROID H4+ con Debian 13.
Ospita il portale CTFd, il database MariaDB e la cache Redis tramite
Docker Compose. Nginx, eseguito sul Master, gestisce gli accessi
previsti dalla modalità selezionata.

I PC dei partecipanti eseguono localmente gli ambienti delle
esercitazioni. Le due modalità vengono utilizzate in sessioni distinte:

- Jeopardy: laboratorio con account individuali, accesso Wi-Fi al
  portale e una copia locale dei materiali per ciascun partecipante.
- Attack & Defense: esercitazione fra due team, con accesso ai servizi
  avversari attraverso i collegamenti predisposti sul Master.

Sono previsti tre profili di rete: `default` per l'uso ordinario del
Master, `jeopardy` e `ad` per le rispettive esercitazioni.

## Organizzazione

| Cartella | Contenuto |
| --- | --- |
| `common/` | Servizi del Master, configurazioni di rete, Nginx e script comuni. |
| `jeopardy/` | Sorgenti, materiali e istruzioni delle challenge. |
| `attack_defense/` | Servizi vulnerabili, checker e gestione dell'esercitazione. |
| `docs/` | Preparazione del sistema, procedure operative e resoconti delle verifiche. |


## Criteri di sviluppo


Le configurazioni di rete e Nginx sono conservate in file statici.
La preparazione iniziale viene documentata attraverso istruzioni
manuali. Gli script sono riservati alle operazioni ricorrenti che
richiedono una sequenza coordinata di azioni.

## Dati locali

La repository contiene sorgenti, configurazioni senza credenziali
reali e documentazione.

Credenziali, dati dei servizi, backup, log delle sessioni e pacchetti
generati vengono conservati separatamente dalla repository.
