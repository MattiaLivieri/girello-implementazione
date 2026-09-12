# Girello — Modalità Jeopardy

Questa directory raccoglie le quattro challenge Jeopardy, le istruzioni
dei partecipanti e la configurazione del CTFd di sviluppo.
Per l'architettura complessiva consultare il [README generale](../README.md);
per rete, servizi e profili del Master consultare il
[README comune](../common/README.md).

## Organizzazione del laboratorio

La modalità Jeopardy prevede `User Mode`, con account individuali
predisposti dagli organizzatori, registrazione autonoma disabilitata
e account amministrativi separati. Le challenge sono indipendenti
e risolvibili nell'ordine scelto dal partecipante.
CTFd presenta consegne e suggerimenti, distribuisce i materiali,
verifica le flag e aggiorna la classifica.

L'analisi di J1 e J2 avviene con strumenti locali. J3 viene eseguita
in un container Docker e J4 in una VM VirtualBox sulla postazione
del partecipante. CTFd non avvia né ripristina questi ambienti.
Strumenti e materiali vengono predisposti prima del tempo di soluzione,
così da consentire lo svolgimento senza accesso a Internet.

### Preparazione e avvio della prova

La sessione distingue due fasi:

1. **Preparazione:** distribuzione dei materiali e dei `README.txt`,
   download, estrazione degli ZIP, caricamento dell'immagine Docker,
   importazione della VM e controlli di avvio e accesso. Per J4 comprende
   anche la creazione dello snapshot `iniziale`.
2. **Risoluzione:** dall'avvio ufficiale, analisi delle challenge,
   recupero delle flag e invio delle risposte nel periodo previsto.

Durante la preparazione non è consentito iniziare l'analisi delle challenge.
Il rispetto di questa regola richiede la supervisione degli organizzatori,
poiché i partecipanti amministrano i propri PC e dispongono già dei materiali.

Gli allegati e le istruzioni devono essere accessibili prima dell'inizio
del tempo di risoluzione. Se gli orari impostati in CTFd ne impediscono
il download anticipato, occorre predisporre una consegna separata
nella rete locale oppure una fase preliminare di accesso al portale,
verificandone il funzionamento nella configurazione utilizzata.
L'assenza di accesso a Internet riguarda lo svolgimento della prova;
gli strumenti e le dipendenze possono essere predisposti in precedenza.

Gli stati `Hidden` e `Visible` riguardano la visibilità delle schede.
Il passaggio a `Visible` non sostituisce il controllo degli orari
di accesso ai materiali e di invio delle flag. Nelle prove di sviluppo
le schede vengono rese visibili all'account studente per il collaudo;
questo non dimostra da solo la corretta organizzazione temporale
della sessione sul Master.

## Challenge

| Challenge | Categoria | Obiettivo didattico | Punti fissi |
| --- | --- | --- | --- |
| [J1 - Traffico in chiaro](challenges/j1-traffico-in-chiaro/README.md) | Analisi di rete | Interpretare HTTP Basic e ricostruire un documento dal traffico. | 100 |
| [J2 - Verifica licenza](challenges/j2-verifica-licenza/README.md) | Reverse engineering | Ricostruire una licenza analizzando le trasformazioni nel JAR. | 200 |
| [J3 - Portale universitario](challenges/j3-portale-universitario/README.md) | Web | Comprendere la distinzione fra autenticazione e autorizzazione. | 150 |
| [J4 - Privilegi Linux](challenges/j4-privilegi-linux/README.md) | Sicurezza Linux | Riconoscere una delega sudo eccessiva. | 250 |

Le quattro challenge utilizzano il tipo `standard`, punteggi fissi
e flag statiche con confronto che distingue maiuscole e minuscole.
I punteggi sono stati assegnati sulla base di una stima iniziale
della difficoltà e delle conoscenze richieste per risolvere le prove.
Il loro valore non diminuisce all'aumentare del numero di risoluzioni.
La prima soluzione corretta assegna i punti all'account; gli invii
duplicati non attribuiscono ulteriori punti.

Ogni challenge prevede `Orientamento`, gratuito, e `Procedura operativa`,
con costo pari al 10% del punteggio e il primo suggerimento come
prerequisito. Il costo viene sottratto al momento dello sblocco
e richiede un saldo sufficiente. Il ripristino di un ambiente locale
non cancella le soluzioni né gli acquisti registrati in CTFd.
La valutazione didattica della difficoltà rimane distinta dal collaudo
tecnico delle challenge.

## Sorgenti e istruzioni

| Percorso relativo a questa directory | Contenuto |
| --- | --- |
| `challenges/` | Sorgenti e documentazione delle quattro challenge. |
| `challenges/*/author/` | Strumenti di costruzione, configurazione e controllo degli autori. |
| `challenges/*/player/` | Istruzioni e configurazioni destinate ai partecipanti. |
| `dev/` | Configurazione dell'istanza CTFd di sviluppo. |

L'organizzazione dei sorgenti applicativi dipende dalla challenge:
per esempio J3 mantiene `app/`, `Dockerfile` e `requirements.txt`
nella propria directory principale. I README tecnici collegati sopra
documentano le procedure e i comandi disponibili, i risultati delle prove
e le eventuali lacune ancora da completare.

I README tecnici degli autori contengono dettagli delle soluzioni.
Agli studenti viene distribuito il `README.txt` della cartella `player/`.

## Materiali di distribuzione

| Challenge | Allegati della scheda CTFd |
| --- | --- |
| J1 | `j1-traffico-in-chiaro.zip`, contenente PCAP, `README.txt` e `SHA256SUMS`. |
| J2 | `j2-verifica-licenza.zip`, contenente JAR, `README.txt` e `SHA256SUMS`. |
| J3 | `j3-portale-universitario.tar`, `compose.yaml`, `README.txt` e `SHA256SUMS`, separati. |
| J4 | `j4-privilegi-linux.ova`, `README.txt` e `SHA256SUMS`, separati. |

Per J1 e J2 il checksum esterno dello ZIP rimane nei materiali degli
autori; il file `SHA256SUMS` interno permette di verificare i contenuti
estratti. Per J3 `SHA256SUMS` elenca il TAR, `compose.yaml` e `README.txt`;
per J4 contiene il solo checksum dell'OVA. I checksum servono
a confrontare i materiali distribuiti con il rilascio collaudato.

Gli hash e le dimensioni riportati nei README tecnici identificano
i rilasci documentati. Non cambiano per una modifica ai soli README.md.
Se vengono modificati gli allegati destinati ai partecipanti,
occorre aggiornare il rilascio e i riferimenti interessati secondo
le procedure della singola challenge; il confronto tra originale
e download non identifica da solo quale versione sia stata distribuita.

I rilasci sono conservati in `artifacts/j1/release/` fino a
`artifacts/j4/release/`, con percorsi relativi alla radice del repository.
La directory `artifacts/` è esclusa da Git. Le sottocartelle `private/`
conservano i valori canonici e i materiali riservati; `validation/`
e le eventuali `download-check/` raccolgono le verifiche degli autori.
Non è necessario che tutte le challenge abbiano le stesse sottocartelle.

Per J4 `README.txt` viene copiato da `player/README.txt` in `release/`
e allegato alla scheda, senza modificare l'OVA. Non appartiene ai
materiali privati. Per riutilizzare gli stessi rilasci su un altro PC
o sul Master occorre trasferire anche gli artefatti: il solo clone
del repository non recupera i pacchetti né i valori canonici delle flag.

## Stato delle verifiche di sviluppo

Le quattro challenge sono implementate e configurate nel CTFd
di sviluppo, raggiungibile su `http://127.0.0.1:18080`.

| Challenge | Verifiche concluse e attività residue |
| --- | --- |
| J1 | Cattura aggiornata, soluzione, confezionamento e confronto SHA-256 dello ZIP aggiornato scaricato da CTFd verificati. Le prove degli invii e dei suggerimenti precedono la revisione HTTP, che ha mantenuto invariati archivio interno e flag. |
| J2 | 439 controlli automatici, ricostruzione con Vineflower, rilascio, confronto del download e invii della flag verificati. |
| J3 | 18 test automatici, login e IDOR, esportazione e caricamento del TAR, prova offline, confronto dei quattro allegati e invii con assegnazione di 150 punti verificati. |
| J4 | OVA importata, accesso SSH, soluzione e ripristino verificati. Caricamento e confronto SHA-256 dei tre allegati, compreso `README.txt`, e invii della flag verificati. |

Questi risultati riguardano la postazione di sviluppo. Non costituiscono
una verifica su tutte le postazioni BYOD né una misura della difficoltà
per studenti che non conoscono già le soluzioni.

## Configurazione sul Master

Nell'assetto del laboratorio i partecipanti raggiungono CTFd sul Master
attraverso Nginx e la rete Wi-Fi dedicata. La predisposizione comprende
il trasferimento dei rilasci verificati e la configurazione di schede,
flag, suggerimenti, account e orari nell'istanza CTFd sul Master.

Il collaudo nell'ambiente di sviluppo non comprende questa integrazione.
La verifica sul Master deve coprire i download, gli invii delle flag
e la disponibilità anticipata dei materiali secondo la distinzione
tra preparazione e risoluzione descritta sopra.

Le procedure comuni gestiscono rete e servizi; il cambio del profilo
del Master non importa automaticamente le challenge o i dati CTFd.
Un push su GitHub pubblica sorgenti e documentazione, ma non trasferisce
gli artefatti esclusi da Git e non aggiorna da solo il portale del Master.
