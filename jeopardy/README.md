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
| [jeopardy/](jeopardy/README.md) | Sorgenti, materiali e istruzioni delle challenge. |
| `attack_defense/` | Servizi vulnerabili, checker e gestione dell'esercitazione. |
| `docs/` | Preparazione del sistema, procedure operative e resoconti delle verifiche. |

## Stato del ramo Jeopardy

Le quattro challenge sono state implementate e sottoposte a prove locali.
Per J3 sono stati completati anche l'esportazione dell'immagine Docker,
il caricamento del TAR, l'avvio offline e il percorso di soluzione.
Nel CTFd locale sono stati verificati gli allegati scaricati e gli invii
della flag, con assegnazione dei 150 punti previsti.

I materiali destinati ai partecipanti sono:

| Challenge | Materiali di distribuzione |
| --- | --- |
| J1 - Traffico in chiaro | ZIP con PCAP, `README.txt` e checksum interni. |
| J2 - Verifica licenza | ZIP con JAR, `README.txt` e checksum interni. |
| J3 - Portale universitario | TAR dell'immagine Docker, `compose.yaml`, `README.txt` e `SHA256SUMS`. |
| J4 - Privilegi Linux | Appliance OVA, `README.txt` e `SHA256SUMS` dell'OVA. |

Le procedure operative, con i comandi di preparazione e controllo,
sono raccolte nei README delle singole challenge:

- [J1 - Traffico in chiaro](jeopardy/challenges/j1-traffico-in-chiaro/README.md).
- [J2 - Verifica licenza](jeopardy/challenges/j2-verifica-licenza/README.md).
- [J3 - Portale universitario](jeopardy/challenges/j3-portale-universitario/README.md).
- [J4 - Privilegi Linux](jeopardy/challenges/j4-privilegi-linux/README.md).

Questi documenti distinguono le istruzioni per ripetere una preparazione
dagli esiti già confermati e dalle attività residue. Per J4 l'aggiunta del README
agli allegati accompagna l'OVA già collaudata e non richiede una nuova
esportazione. La sua disponibilità va controllata con l'account studente.

Le prove locali non completano l'integrazione sul Master: restano
il caricamento e la verifica dei materiali sul portale del laboratorio,
l'accesso dalle postazioni attraverso la rete Wi-Fi e la valutazione
con partecipanti.

## Criteri di sviluppo

Le configurazioni di rete e Nginx sono conservate in file statici.
La preparazione iniziale viene documentata attraverso istruzioni
manuali. Gli script sono riservati alle operazioni ricorrenti che
richiedono una sequenza coordinata di azioni.

## Dati locali

La repository contiene sorgenti, configurazioni senza credenziali
reali e documentazione.

Le configurazioni private degli scenari, i prodotti di costruzione,
i pacchetti di rilascio e le copie usate nei controlli locali sono
conservati sotto `artifacts/`, esclusa dal versionamento Git.
Le directory `release/` raccolgono i materiali distribuibili;
le directory `private/` contengono i valori canonici e i dati riservati.
Il README del partecipante appartiene ai materiali di rilascio.

Credenziali dei servizi, dati persistenti, backup e log delle sessioni
sono conservati nelle posizioni locali previste dalle procedure comuni.
Il solo clone della repository non recupera questi dati né gli artefatti:
per riutilizzare lo stesso rilascio occorre trasferire anche i materiali
collaudati e, separatamente, i valori riservati necessari agli autori.

Le istruzioni per predisporre il Master e utilizzare i profili sono disponibili
in [Preparazione e utilizzo del Master](common/README.md).