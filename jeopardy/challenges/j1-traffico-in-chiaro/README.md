# J1 — Traffico in chiaro

## Obiettivo

La challenge richiede di analizzare una cattura HTTP, recuperare le
credenziali Basic, ricostruire un archivio trasferito e usare la password
recuperata per leggere la flag contenuta al suo interno.

Il riuso della password è una proprietà esplicita dello scenario.
I dati e le credenziali utilizzati sono fittizi.

## Stato

Completate sul PC Windows di sviluppo:

- generazione dell'archivio ZIP AES-256;
- verifica del contenuto e del rifiuto di una password errata;
- acquisizione della comunicazione HTTP senza perdite segnalate;
- esportazione dello ZIP mediante Wireshark;
- confronto SHA-256 tra archivio originale ed esportato;
- recupero della flag con la password individuata nel traffico;
- creazione e verifica del pacchetto di distribuzione.

L'integrazione nel CTFd locale è stata verificata mediante un account
studente: la flag corretta viene accettata e assegna il punteggio
della challenge; lo sblocco del suggerimento a pagamento sottrae
10 punti.

La configurazione e gli esiti sono descritti nella sezione
Configurazione CTFd di questo documento.

Restano da completare il caricamento sul CTFd del Master e la verifica
dell'accesso e della distribuzione nella rete del laboratorio.

## Sorgenti

| File | Funzione |
| --- | --- |
| `author/generate.py` | Genera la configurazione riservata e lo ZIP cifrato. |
| `author/server.py` | Espone le risorse pubbliche e l'archivio protetto da HTTP Basic. |
| `author/capture.py` | Genera le richieste HTTP, coordina tcpdump e controlla la cattura. |
| `author/compose.yaml` | Definisce i container server e capture e la rete interna. |
| `author/Dockerfile` | Predispone Python, tcpdump e le dipendenze. |
| `author/requirements.txt` | Fissa le versioni delle dipendenze Python. |
| `author/.dockerignore` | Limita i file inclusi nel contesto di costruzione. |
| `author/package.py` | Confeziona il PCAP validato e verifica il pacchetto. |
| `player/README.txt` | Contiene le istruzioni distribuite al partecipante. |

## Costruzione della cattura

Il laboratorio degli autori utilizza due container Linux collegati
alla rete Docker interna `lab`, senza pubblicare porte sull'host.

Il servizio `server` espone un archivio documentale HTTP. Dopo il
superamento del controllo di salute del server, il servizio `capture`
avvia tcpdump e attende che sia pronto prima di generare le richieste.

Lo scambio comprende sette richieste:

- cinque richieste alle risorse pubbliche;
- una richiesta dell'archivio senza credenziali, con risposta HTTP 401;
- una richiesta autenticata, con risposta HTTP 200 e trasferimento dello ZIP.

Il filtro acquisisce il traffico TCP con il server sulla porta 8000.
La cattura usa un buffer da 16 MiB e scrive inizialmente in un file
temporaneo su tmpfs. Dopo l'arresto di tcpdump, il file viene copiato
nella directory di output condivisa con Windows.

Lo script rifiuta la cattura se tcpdump termina in errore, se non
risultano pacchetti acquisiti o se sono segnalate perdite dal kernel.
Controlla inoltre la leggibilità del PCAP e l'assenza del prefisso
delle flag nei byte acquisiti.

Il file assume il nome finale `traffico.pcap` soltanto dopo il
superamento dei controlli. Il laboratorio viene arrestato al termine.

## Artefatti locali

I percorsi seguenti sono relativi alla radice del repository:

- `artifacts/j1/private/`: configurazione riservata e archivio originale.
- `artifacts/j1/capture/`: PCAP, log e rapporto della cattura.
- `artifacts/j1/validation/`: archivio e testo recuperati durante la verifica.
- `artifacts/j1/release/`: pacchetto pubblico e relativo checksum.
- `artifacts/j1/capture-fallita-01/`: evidenze del primo tentativo di cattura.

La directory `artifacts/` rimane esclusa dal versionamento Git.
Configurazione riservata, testo estratto e log non sono inclusi
nel pacchetto destinato ai partecipanti.

## Esito della verifica locale

La cattura validata contiene 84 pacchetti e sette richieste HTTP.
Tcpdump riporta 84 pacchetti ricevuti dal filtro e zero pacchetti
persi dal kernel. Il PCAP ha una dimensione di 10 711 byte.

Lo ZIP esportato con Wireshark ha lo stesso SHA-256 dell'originale.
La flag recuperata coincide con quella prevista dalla configurazione.

SHA-256 dell'archivio interno:

```text
7ad5df79df9905599cf8dffb64e45df008a90b78c2463018dbb2c4ace365aae0
```

SHA-256 del PCAP validato:

```text
2f0e24b2c61608aca330379f8e9a49dbb6f3ee351e36a1f2091ed85047d54758
```

## Pacchetto di distribuzione

`j1-traffico-in-chiaro.zip` è uno ZIP esterno senza password
contenente esclusivamente:

- `traffico.pcap`;
- `README.txt`;
- `SHA256SUMS`, con gli hash dei due file precedenti.

Il checksum del pacchetto esterno viene salvato separatamente
in `j1-traffico-in-chiaro.zip.sha256`.

SHA-256 del pacchetto verificato:

```text
b70f8f7f14c755f5198fa20c4e501b9d383d8335bc27384aae03a21f06d2a4ca
```

`package.py` richiede l'hash del PCAP validato, controlla i file
inclusi e ne confronta il contenuto dopo la scrittura dello ZIP.
Una nuova esecuzione con gli stessi materiali verifica il pacchetto
esistente; un pacchetto diverso non viene sovrascritto.

Durante l'esercitazione il Master distribuisce il materiale tramite
CTFd. Lo studente analizza il PCAP sul proprio computer con Wireshark
e un programma compatibile con ZIP AES-256, come 7-Zip.
Non è previsto un servizio J1 attivo durante la gara.

## Riproducibilità

Gli script consentono di ricostruire lo scenario. Nuove catture
possono avere timestamp, parametri TCP e byte differenti.

Per ripetere l'esercitazione con gli stessi materiali si conserva
e distribuisce il pacchetto validato, identificato dal suo SHA-256.

## Configurazione CTFd

### Parametri della challenge

| Campo | Valore |
| --- | --- |
| Nome | J1 - Traffico in chiaro |
| Categoria | Analisi di rete |
| Tipo | standard |
| Punteggio | 100, fisso |
| Flag | static |
| Confronto della flag | Case Sensitive |
| Max Attempts | 0, senza limite totale |
| Connection Info | Vuoto |
| Prerequisiti della challenge | Nessuno |

Durante il caricamento si mantiene lo stato Hidden.
Dopo aver completato la configurazione si imposta Visible.

Il valore effettivo della flag si legge dal campo `flag` di
`artifacts/j1/private/scenario.json`, relativo al pacchetto validato.
Il file rimane fuori dalla repository e dagli allegati pubblici.

### Descrizione per i partecipanti

Una postazione ha consultato un archivio documentale interno.
La cattura contiene le richieste alle risorse pubbliche e il trasferimento
di un documento riservato. L'utente riutilizza la stessa password per
l'accesso al servizio e per proteggere l'archivio trasferito.

Analizza `traffico.pcap`, ricostruisci il documento trasferito e recupera
la flag contenuta al suo interno.

Scarica ed estrai `j1-traffico-in-chiaro.zip`, quindi leggi `README.txt`.
Lo ZIP di distribuzione si estrae senza password; l'archivio presente
nel traffico richiede invece la password da recuperare.

Strumenti: Wireshark e un programma compatibile con ZIP AES-256,
come 7-Zip. L'analisi si svolge offline sul proprio PC:
non occorre contattare gli indirizzi presenti nella cattura.

Inserisci la flag rispettando maiuscole, minuscole e simboli.

### Allegato

L'unico allegato da caricare su CTFd è:

`artifacts/j1/release/j1-traffico-in-chiaro.zip`

SHA-256 del pacchetto validato:

`b70f8f7f14c755f5198fa20c4e501b9d383d8335bc27384aae03a21f06d2a4ca`

Il file esterno `j1-traffico-in-chiaro.zip.sha256` viene conservato
tra i materiali dell'autore. Non viene allegato alla challenge.

Il pacchetto mantiene al proprio interno `traffico.pcap`, `README.txt`
e `SHA256SUMS`. Il controllo degli hash non è richiesto per risolvere J1.

### Suggerimenti

#### Orientamento

- Costo: 0 punti.
- Prerequisiti: nessuno.

Concentrati sulle richieste HTTP. Distingui le risorse pubbliche
dal documento riservato e osserva come viene autenticato l'accesso.

#### Procedura operativa

- Costo: 10 punti.
- Prerequisito configurato: Orientamento.

Nell'header Authorization, HTTP Basic rappresenta la coppia
nomeutente:password in Base64, che è una codifica reversibile.

Recupera la password, poi usa File → Export Objects → HTTP
in Wireshark per esportare l'oggetto di tipo application/zip.
Apri l'archivio con un programma compatibile con ZIP AES-256
e utilizza la password recuperata.

CTFd richiede un saldo sufficiente per acquistare il suggerimento
a pagamento. Il costo viene sottratto al momento dello sblocco.

### Verifica funzionale locale

Ambiente: CTFd 3.8.7, istanza Girello - Jeopardy DEV sul PC di sviluppo,
raggiungibile all'indirizzo http://127.0.0.1:18080.

Le prove manuali con un account studente hanno confermato:

- visualizzazione della challenge e dei suggerimenti;
- accettazione della flag corretta e assegnazione del punteggio;
- sblocco dei suggerimenti e sottrazione di 10 punti per quello a pagamento.

La generazione del PCAP e la soluzione mediante Wireshark sono
documentate nel README della challenge.

Il caricamento sul Master e la verifica dalla rete del laboratorio
restano attività successive.