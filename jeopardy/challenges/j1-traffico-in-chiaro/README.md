# J1 — Traffico in chiaro

## Obiettivo

La challenge richiede di analizzare una cattura HTTP, recuperare le
credenziali Basic, ricostruire un archivio trasferito e usare la password
recuperata per leggere la flag contenuta al suo interno.

Il riuso della password è una proprietà esplicita dello scenario.
I dati e le credenziali utilizzati sono fittizi.

Questo README documenta il lavoro degli autori e contiene dettagli
del percorso di soluzione. Le istruzioni distribuite ai partecipanti
sono in `player/README.txt`.

## Stato

Completate sul PC Windows di sviluppo:

- generazione dell'archivio ZIP AES-256;
- verifica del contenuto e del rifiuto di una password errata;
- acquisizione della comunicazione HTTP senza perdite segnalate;
- esportazione dello ZIP mediante Wireshark;
- confronto SHA-256 tra archivio originale ed esportato;
- recupero della flag con la password individuata nel traffico;
- creazione e verifica del pacchetto di distribuzione.

La successiva revisione delle intestazioni HTTP è stata verificata
analizzando la nuova cattura e ricostruendo l'archivio trasferito.
L'archivio interno e la flag sono rimasti invariati.

L'integrazione nel CTFd di sviluppo è stata verificata mediante un account
studente: la flag corretta viene accettata e assegna il punteggio
della challenge; lo sblocco del suggerimento a pagamento sottrae
10 punti.

La configurazione e gli esiti sono descritti nella sezione
Configurazione CTFd di questo documento.

Anche il pacchetto aggiornato è stato caricato in CTFd di sviluppo
e scaricato con l'account studente. Il confronto SHA-256 con il file
di rilascio ha confermato l'identità dello ZIP distribuito.
Questo controllo riguarda la distribuzione della versione aggiornata
ed è distinto dalle prove degli invii e dei suggerimenti,
eseguite prima della revisione HTTP.

Restano inoltre il caricamento nell'istanza CTFd sul Master, la verifica
dell'accesso e della distribuzione nella rete del laboratorio
e la valutazione della difficoltà con partecipanti.

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
| `README.md` | Documenta preparazione, rilascio, configurazione CTFd ed esiti. |

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

Il server indica il tipo e la lunghezza del contenuto nelle risposte.
L'intestazione `Content-Disposition` assegna il nome `riservato.zip`
soltanto alla risposta che trasferisce l'archivio.

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

### Preparazione degli autori

La generazione usa `author/generate.py`; la cattura è coordinata dai
servizi del Compose in `author/compose.yaml`; il confezionamento è
affidato a `author/package.py`, che richiede il checksum del PCAP
collaudato. Questi strumenti riguardano il laboratorio degli autori:
non vengono eseguiti sulla postazione del partecipante.

Le invocazioni complete di generazione e confezionamento, con i relativi
argomenti e percorsi montati nei container, devono essere ricavate dagli
script della versione utilizzata. Non sono registrate nel materiale
disponibile per questa revisione. I comandi riportati di seguito
permettono di controllare il rilascio già prodotto e la distribuzione;
non costituiscono una procedura completa di ricostruzione della cattura.

## Artefatti locali

I percorsi seguenti sono relativi alla radice del repository:

- `artifacts/j1/private/`: configurazione riservata e archivio originale.
- `artifacts/j1/capture/`: PCAP, log e rapporto della cattura aggiornata.
- `artifacts/j1/validation/`: archivio e testo recuperati durante la verifica mediante Wireshark.
- `artifacts/j1/release/`: pacchetto pubblico aggiornato e relativo checksum.
- `artifacts/j1/capture-fallita-01/`: evidenze del primo tentativo di cattura.
- `artifacts/j1/capture-prima-correzione-http/`: cattura precedente alla correzione delle intestazioni HTTP.
- `artifacts/j1/release-prima-correzione-http/`: pacchetto di distribuzione precedente.

La directory `artifacts/` rimane esclusa dal versionamento Git.
Configurazione riservata, testo estratto e log non sono inclusi
nel pacchetto destinato ai partecipanti.

## Esito della verifica nell'ambiente di sviluppo

La cattura aggiornata contiene 84 pacchetti e sette richieste HTTP.
Tcpdump riporta 84 pacchetti ricevuti dal filtro e zero pacchetti
persi dal kernel. Il PCAP ha una dimensione di 10 416 byte.

L'intestazione `Content-Disposition` identifica `riservato.zip` soltanto
nella risposta che trasferisce l'archivio. Le risposte alle risorse
pubbliche non contengono questa intestazione.

La prima versione della cattura è stata verificata mediante
esportazione dell'archivio con Wireshark. Dopo la correzione delle
intestazioni HTTP, la ricostruzione dei flussi TCP della nuova cattura
ha confermato che l'archivio trasferito è identico all'originale.

La password recuperata dalle credenziali HTTP Basic consente di
estrarre la flag prevista dalla configurazione. L'estrazione senza
password o con una password errata viene rifiutata.

Gli hash del PCAP e dell'archivio ricostruito corrispondono ai valori
registrati in `capture.json`. I checksum contenuti nel pacchetto
di distribuzione corrispondono ai file inclusi.

SHA-256 dell'archivio interno `riservato.zip`:

```text
7ad5df79df9905599cf8dffb64e45df008a90b78c2463018dbb2c4ace365aae0
```

SHA-256 del PCAP validato `traffico.pcap`:

```text
c0e821b72c01b0c21f4676af820dc384a22e13c7bdc1690726f4099f8be9770f
```

## Pacchetto di distribuzione

`j1-traffico-in-chiaro.zip` è uno ZIP esterno senza password
contenente esclusivamente:

- `traffico.pcap`;
- `README.txt`;
- `SHA256SUMS`, con gli hash dei due file precedenti.

Il pacchetto verificato ha una dimensione di 3 971 byte.
Il suo checksum viene salvato separatamente
in `j1-traffico-in-chiaro.zip.sha256`.

SHA-256 del pacchetto verificato:

```text
70985dd05c6f613a78453a43c8ee613e7f7d03ea016b8833ac81608ded68f543
```

`package.py` richiede l'hash del PCAP validato, controlla i file
inclusi e ne confronta il contenuto dopo la scrittura dello ZIP.
Una nuova esecuzione con gli stessi materiali verifica il pacchetto
esistente; un pacchetto diverso non viene sovrascritto.

Il checksum esterno si riferisce all'intero ZIP. Il file `SHA256SUMS`
interno riguarda invece `traffico.pcap` e `README.txt` estratti.
Non occorre aggiungere un ulteriore README come allegato separato.

La distribuzione prevista sul Master avviene tramite CTFd.
Lo studente analizza il PCAP sul proprio computer con Wireshark
e un programma compatibile con ZIP AES-256, come 7-Zip.
Non è previsto un servizio J1 attivo durante la gara.

### Controllo del rilascio conservato

Il blocco seguente confronta lo ZIP locale con l'impronta del rilascio
descritto in questo documento. Eseguirlo dalla radice del repository,
in PowerShell. Non ricostruisce né modifica i materiali.

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j1Zip = ".\artifacts\j1\release\j1-traffico-in-chiaro.zip"
    $j1Expected = "70985dd05c6f613a78453a43c8ee613e7f7d03ea016b8833ac81608ded68f543"
    if (-not (Test-Path -LiteralPath $j1Zip -PathType Leaf)) {
        throw "Pacchetto j1 mancante."
    }
    $j1Actual = (Get-FileHash -LiteralPath $j1Zip -Algorithm SHA256).Hash
    if ($j1Actual -ne $j1Expected) { throw "Pacchetto diverso dal rilascio collaudato." }
    Write-Output "Rilascio j1: OK"
}
```

L'impronta identifica questa versione del pacchetto. Una revisione
dei materiali richiede il confezionamento e l'aggiornamento dei checksum;
non basta sostituire il valore atteso per dichiarare collaudata una
versione differente.

## Riproducibilità

Gli script consentono di ricostruire lo scenario. Nuove catture
possono avere timestamp, parametri TCP e byte differenti.

Per ripetere l'esercitazione con gli stessi materiali si conserva
e distribuisce il pacchetto validato, identificato dal suo SHA-256.
Una modifica al PCAP richiede un nuovo controllo del contenuto prima
del confezionamento. Una modifica al README del partecipante richiede
l'aggiornamento dello ZIP e dei relativi checksum. Una nuova flag
richiede anche l'allineamento del valore atteso in CTFd.

L'aggiornamento di questo README tecnico non modifica lo ZIP distribuito
e non richiede una nuova cattura.

## Configurazione CTFd

### Parametri della challenge

| Campo | Valore |
| --- | --- |
| Nome | J1 - Traffico in chiaro |
| Categoria | Analisi di rete |
| Tipo | `standard` |
| Punteggio | 100 punti, fisso |
| Tipo di flag | `static` |
| Confronto della flag | Case Sensitive |
| Max Attempts | 0, senza limite totale |
| Connection Info | Vuoto |
| Prerequisiti della challenge | Nessuno |

Punteggi e suggerimenti seguono le [regole comuni Jeopardy](../../README.md#challenge).

Durante la configurazione si mantiene lo stato `Hidden`.
Per le prove in CTFd di sviluppo con l'account studente
si imposta `Visible`.

La distribuzione nel laboratorio segue la distinzione tra
[preparazione e avvio della prova](../../README.md#preparazione-e-avvio-della-prova):
materiali e istruzioni devono essere accessibili prima del tempo
di risoluzione. Il passaggio a `Visible` non basta se gli orari
configurati impediscono il download anticipato.

Il valore effettivo della flag si legge dal campo `flag` di
`artifacts/j1/private/scenario.json`, relativo al pacchetto validato.
Il file rimane escluso dal versionamento Git e dagli allegati pubblici.

### Descrizione per i partecipanti

Una postazione ha consultato un archivio documentale interno.
La cattura contiene le richieste alle risorse pubbliche e il trasferimento
di un documento riservato. L'utente riutilizza la stessa password per
l'accesso al servizio e per proteggere l'archivio trasferito.

Analizza `traffico.pcap`, ricostruisci il documento trasferito e recupera
la flag contenuta al suo interno.

Durante la preparazione scarica ed estrai `j1-traffico-in-chiaro.zip`
e leggi `README.txt`. Inizia l'analisi soltanto all'avvio della prova.
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

```text
70985dd05c6f613a78453a43c8ee613e7f7d03ea016b8833ac81608ded68f543
```

Il file esterno `j1-traffico-in-chiaro.zip.sha256` viene conservato
tra i materiali dell'autore. Non viene allegato alla challenge.

Il pacchetto mantiene al proprio interno `traffico.pcap`, `README.txt`
e `SHA256SUMS`. Il controllo degli hash non è richiesto per risolvere J1.

### Confronto dello ZIP scaricato da CTFd

Caricare lo ZIP di `artifacts/j1/release/` nella scheda della challenge.
Con l'account studente scaricarlo dal portale e salvarlo con il nome
originale in `artifacts/j1/download-check/`. La directory è destinata
al controllo degli autori; il suo nome non è un requisito della challenge.

Per predisporla, dalla radice del repository:

```powershell
New-Item -ItemType Directory -Force -Path .\artifacts\j1\download-check | Out-Null
```

Conservare qui il download effettivo, senza copiarlo da `release/`.
Se il browser aggiunge un suffisso come `(1)`, identificare la copia
appena scaricata e ripristinare il nome originale. Eseguire quindi:

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j1Original = ".\artifacts\j1\release\j1-traffico-in-chiaro.zip"
    $j1Downloaded = ".\artifacts\j1\download-check\j1-traffico-in-chiaro.zip"
    foreach ($j1Path in @($j1Original, $j1Downloaded)) {
        if (-not (Test-Path -LiteralPath $j1Path -PathType Leaf)) {
            throw "File mancante: $j1Path"
        }
    }
    $j1OriginalHash = (Get-FileHash -LiteralPath $j1Original -Algorithm SHA256).Hash
    $j1DownloadHash = (Get-FileHash -LiteralPath $j1Downloaded -Algorithm SHA256).Hash
    if ($j1OriginalHash -ne $j1DownloadHash) { throw "Download differente dal rilascio." }
    Write-Output "Download j1: OK"
}
```

Un file mancante viene segnalato separatamente da una differenza di
checksum. La corrispondenza con il rilascio già collaudato conferma
che il download contiene gli stessi byte, senza richiedere di ripetere
la soluzione su una copia identica.

Il confronto sullo ZIP aggiornato è stato completato con esito
coincidente. Il blocco permette di ripetere il controllo su una nuova
distribuzione. Gli acquisti dei suggerimenti non sono stati ripetuti,
poiché la configurazione CTFd e la flag sono rimaste invariate.

### Suggerimenti

#### Orientamento

- Costo: 0 punti.
- Prerequisiti: nessuno.

Concentrati sulle richieste HTTP. Distingui le risorse pubbliche
dal documento riservato e osserva come viene autenticato l'accesso.

#### Procedura operativa

- Costo: 10 punti.
- Prerequisito: Orientamento.

Nell'header Authorization, HTTP Basic rappresenta la coppia
nomeutente:password in Base64, che è una codifica reversibile.

Recupera la password, poi usa File → Export Objects → HTTP
in Wireshark per esportare l'oggetto di tipo application/zip.
Apri l'archivio con un programma compatibile con ZIP AES-256
e utilizza la password recuperata.

CTFd richiede un saldo sufficiente per acquistare il suggerimento
a pagamento. Il costo viene sottratto al momento dello sblocco.

### Verifica funzionale in CTFd di sviluppo

Ambiente: CTFd 3.8.7, istanza Girello - Jeopardy DEV sul PC di sviluppo,
raggiungibile all'indirizzo [http://127.0.0.1:18080](http://127.0.0.1:18080).

Le prove manuali con un account studente hanno confermato:

- visualizzazione della challenge e dei suggerimenti;
- accettazione della flag corretta e assegnazione del punteggio;
- sblocco dei suggerimenti e sottrazione di 10 punti per quello a pagamento.

Queste prove sono state svolte prima della revisione delle intestazioni
HTTP. La revisione conserva lo stesso archivio interno e la stessa flag;
il pacchetto aggiornato è identificato nella sezione Allegato.
Il caricamento e il confronto SHA-256 del download della versione
aggiornata sono stati completati con esito coincidente.
Questo risultato riguarda la distribuzione dello ZIP aggiornato;
le prove degli invii e dei suggerimenti rimangono riferite
alla configurazione verificata prima della revisione HTTP.

Il caricamento sul Master e la verifica dalla rete del laboratorio
restano attività successive.
