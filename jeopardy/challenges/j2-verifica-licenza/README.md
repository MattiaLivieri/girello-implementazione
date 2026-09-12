# J2 — Verifica licenza

## Obiettivo

Il partecipante ricostruisce il codice accettato da un verificatore Java,
analizzando il solo JAR. La logica combina una permutazione, uno XOR
con chiave ripetuta e un'addizione dipendente dalla posizione modulo 256.
La soluzione non richiede di eseguire il programma della challenge.

L'input ha forma `XXXX-XXXX-XXXX`, con lettere ASCII o cifre.
I trattini sono obbligatori e gli spazi non sono ammessi.
Le minuscole sono accettate. Il codice normalizzato contiene dodici
caratteri senza trattini, con le lettere convertite in maiuscolo;
la flag è `CRCTF{CODICE_NORMALIZZATO}`.

Questo README documenta il lavoro degli autori e contiene dettagli
della logica di verifica. Le istruzioni distribuite ai partecipanti
sono in `player/README.txt`.

## Stato

Completati sul PC Windows di sviluppo:

- generazione della configurazione privata e compilazione del JAR;
- superamento dei controlli automatici della build;
- decompilazione con Vineflower e ricostruzione statica della licenza;
- confronto della soluzione ricostruita con la configurazione privata;
- verifica dell'accettazione della licenza nel JAR;
- creazione e verifica del pacchetto di distribuzione;
- configurazione della challenge, della flag e dei suggerimenti nel CTFd di sviluppo;
- verifica del checksum dello ZIP scaricato da CTFd;
- verifica degli invii e del punteggio con un account studente.

Restano l'integrazione nell'istanza CTFd sul Master, la verifica della distribuzione
nel laboratorio e la valutazione della difficoltà con partecipanti.
Le prove locali verificano il funzionamento tecnico; non costituiscono
una validazione su tutte le postazioni BYOD.

## Sorgenti

| File | Funzione |
| --- | --- |
| `author/Build.java` | Genera o riutilizza la licenza privata, compila, verifica e crea il JAR. |
| `author/BuildChecks.java` | Verifica input, normalizzazione e mutazioni del codice; escluso dal JAR. |
| `author/Package.java` | Confeziona e verifica lo ZIP a partire dal JAR già collaudato. |
| `author/src/Main.java` | Legge una riga dal terminale e mostra l'esito del controllo. |
| `author/src/LicenseValidator.java.template` | Definisce formato, normalizzazione e confronto con i valori generati. |
| `author/src/CodeTransformer.java` | Implementa permutazione, XOR e addizione modulo 256. |
| `player/README.txt` | Contiene le istruzioni del partecipante. |
| `README.md` | Documenta costruzione, rilascio, configurazione CTFd ed esiti. |

Il template viene completato soltanto nella directory locale di build.
La classe risultante nel JAR si chiama `LicenseValidator`.
Le tre classi applicative appartengono al package `girello.j2`.

## Costruzione del JAR

Serve un JDK 17 o successivo che supporti `--release 17`.
La build locale è stata eseguita con Temurin 21.0.12+8 su Windows.
Non occorrono Maven, Gradle o dipendenze applicative esterne.

Dalla radice del repository, verificare che `artifacts/` sia ignorata
da Git prima di generare la configurazione privata:

```powershell
git check-ignore -- artifacts/j2/private/scenario.properties
```

Il comando deve indicare il percorso richiesto. Eseguire quindi:

```powershell
java .\jeopardy\challenges\j2-verifica-licenza\author\Build.java
if ($LASTEXITCODE -ne 0) { throw "Build J2 non riuscita." }
```

La prima esecuzione genera dodici caratteri con `SecureRandom`.
La configurazione privata viene conservata nelle esecuzioni successive;
se presenta un formato non valido, la build si ferma senza sostituirla.

La build usa il compilatore del JDK tramite `JavaCompiler`, con
`--release 17`, UTF-8, informazioni di debug e senza annotation processor.
Compila anche i controlli degli autori, ma confeziona nel JAR soltanto
`Main.class`, `LicenseValidator.class`, `CodeTransformer.class` e manifest.

I controlli verificano il codice canonico, le minuscole, gli input
malformati, tutte le mutazioni di un carattere nell'alfabeto ammesso
e l'indipendenza della normalizzazione dalla lingua del sistema.
Seguono prove del JAR con codice corretto, errato ed EOF.
Vengono controllati il target bytecode 61 e l'assenza del codice
canonico e della flag in chiaro nei file class.

La permutazione è biunivoca; XOR e addizione modulo 256 sono invertibili
su un byte. Esiste quindi un solo codice normalizzato per l'array atteso.
Le varianti maiuscole/minuscole corrispondono alla stessa soluzione.

Il programma mostra soltanto se la licenza è valida. Modificare il ramo
di controllo per ottenere un messaggio positivo non fornisce il valore
corretto della flag, che dipende dal codice ricostruito.

## Artefatti locali

Percorsi relativi alla radice del repository:

| Percorso | Contenuto |
| --- | --- |
| `artifacts/j2/private/scenario.properties` | Codice canonico e flag, riservati. |
| `artifacts/j2/build/verifica-licenza.jar` | JAR prodotto dalla build. |
| `artifacts/j2/build/SHA256SUMS` | Checksum del JAR di build. |
| `artifacts/j2/build/build-report.txt` | Ambiente, controlli e hash dei sorgenti. |
| `artifacts/j2/build/work-*/` | Sorgente generato e classi dei controlli locali. |
| `artifacts/j2/tools/` | Decompilatore utilizzato nel collaudo. |
| `artifacts/j2/validation/` | Log di Vineflower e sorgenti decompilati. |
| `artifacts/j2/release/` | ZIP validato e relativo checksum esterno. |
| `artifacts/j2/download-check/` | Copia scaricata da CTFd per il confronto. |

Una nuova build aggiorna il JAR di lavoro e il rapporto, conservando
la configurazione privata. Le directory `work-*` vengono mantenute
come evidenze locali. Questi materiali rimangono esclusi da Git.
Il JAR di lavoro deve essere collaudato prima del confezionamento.

## Esito della verifica nell'ambiente di sviluppo

La build sul PC Windows ha superato **439 controlli automatici**.
Il JAR ottenuto è stato decompilato con Vineflower 1.12.0.
L'analisi di `LicenseValidator` e `CodeTransformer` ha permesso
di ricostruire la licenza partendo dai soli dati contenuti nel JAR.

La ricostruzione inverte l'addizione modulo 256, applica nuovamente
lo XOR e ricolloca i caratteri nelle posizioni indicate dalla permutazione.
Solo dopo questa analisi, il codice normalizzato e la flag risultante
sono stati confrontati con la configurazione privata: entrambi coincidono.
Il JAR ha inoltre accettato il codice ricostruito nel formato con trattini.

| Verifica | Esito |
| --- | --- |
| Controlli automatici della build | Superati. |
| Decompilazione delle tre classi applicative | Completata senza errori. |
| Ricostruzione statica della licenza dal solo JAR | Riuscita. |
| Confronto del codice e della flag con i valori canonici | Coincidenti. |
| Esecuzione del JAR con la licenza ricostruita | Licenza accettata. |

SHA256 del JAR collaudato:

```text
002e3a5ae3343712c195486b8b90034d4e3b651b76e4e93225f9255d11427ae9
```

Il rapporto automatico descrive la build e i controlli che essa esegue.
La ricostruzione con il decompilatore è una prova successiva e distinta,
documentata in questa sezione; non viene eseguita da `Build.java`.

### Procedura di decompilazione e verifica manuale

Il collaudo statico utilizza Vineflower 1.12.0, già predisposto in
`artifacts/j2/tools/vineflower-1.12.0.jar`. Lo strumento non è incluso
nel pacchetto pubblico della challenge. Il comando seguente documenta
come ripetere la decompilazione; non occorre rieseguirlo sul JAR
già collaudato.

Dalla radice del repository, in PowerShell:

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j2Decompiler = ".\artifacts\j2\tools\vineflower-1.12.0.jar"
    $j2Jar = ".\artifacts\j2\build\verifica-licenza.jar"
    $j2Output = ".\artifacts\j2\validation\decompiled"
    foreach ($j2Path in @($j2Decompiler, $j2Jar)) {
        if (-not (Test-Path -LiteralPath $j2Path -PathType Leaf)) {
            throw "File mancante: $j2Path"
        }
    }
    $j2Expected = "002e3a5ae3343712c195486b8b90034d4e3b651b76e4e93225f9255d11427ae9"
    if ((Get-FileHash -LiteralPath $j2Jar -Algorithm SHA256).Hash -ne $j2Expected) {
        throw "JAR diverso dalla versione descritta in questo README."
    }
    if (Test-Path -LiteralPath $j2Output) {
        throw "Output di verifica gia presente: conservarlo o scegliere una nuova cartella."
    }
    New-Item -ItemType Directory -Path $j2Output -Force | Out-Null
    java -jar $j2Decompiler --folder $j2Jar $j2Output
    if ($LASTEXITCODE -ne 0) { throw "Decompilazione J2 non riuscita." }
    Get-ChildItem -LiteralPath $j2Output -Recurse -File
}
```

Analizzare le tre classi ottenute, seguendo l'input fino all'array di
confronto. Ricostruire il codice invertendo addizione modulo 256, XOR
e permutazione. Solo dopo la ricostruzione confrontare il risultato
con la configurazione privata degli autori, per mantenere indipendente
la prova della soluzione dal materiale consegnato.

Per la prova facoltativa di esecuzione:

```powershell
java -jar .\artifacts\j2\build\verifica-licenza.jar
```

Inserire il codice ricostruito nel formato con trattini. Nella prova
già conclusa il verificatore lo ha accettato; codice e flag coincidevano
con i valori canonici. Non riportare tali valori nel README pubblico.

## Pacchetto di distribuzione

Il file `artifacts/j2/release/j2-verifica-licenza.zip` contiene
esclusivamente, nella radice dell'archivio:

- `verifica-licenza.jar`;
- `README.txt`, copiato da `player/README.txt`;
- `SHA256SUMS`, con gli hash dei due file precedenti.

Sorgenti, controlli degli autori e configurazione privata sono esclusi.
Non è previsto un servizio J2 sul Master durante l'esercitazione.

Per confezionare il JAR della versione collaudata, dalla radice
del repository:

```powershell
java .\jeopardy\challenges\j2-verifica-licenza\author\Package.java `
    002e3a5ae3343712c195486b8b90034d4e3b651b76e4e93225f9255d11427ae9
if ($LASTEXITCODE -ne 0) { throw "Confezionamento J2 non riuscito." }
```

Lo script richiede il checksum del JAR validato e si ferma se il file
di build non coincide. Non ricompila il programma e non legge
la configurazione privata. Dopo la creazione riapre lo ZIP e verifica
i nomi e i byte delle voci. Un pacchetto esistente con contenuto diverso
non viene sovrascritto.

Il pacchetto collaudato ha dimensione **4199 byte** e SHA256:

```text
e88fcc3d3ebb38301ffa3ca1c270509a35533dba557a867aa3c609ce7d317a6c
```

Il checksum esterno è conservato in
`artifacts/j2/release/j2-verifica-licenza.zip.sha256` per le verifiche
degli autori. Il file `SHA256SUMS` interno riguarda invece i contenuti
estratti dallo ZIP.

### Controllo del rilascio conservato

Il blocco seguente confronta lo ZIP locale con l'impronta del rilascio
descritto in questo documento. Eseguirlo dalla radice del repository,
in PowerShell. Non ricostruisce né modifica i materiali.

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j2Zip = ".\artifacts\j2\release\j2-verifica-licenza.zip"
    $j2Expected = "e88fcc3d3ebb38301ffa3ca1c270509a35533dba557a867aa3c609ce7d317a6c"
    if (-not (Test-Path -LiteralPath $j2Zip -PathType Leaf)) {
        throw "Pacchetto j2 mancante."
    }
    $j2Actual = (Get-FileHash -LiteralPath $j2Zip -Algorithm SHA256).Hash
    if ($j2Actual -ne $j2Expected) { throw "Pacchetto diverso dal rilascio collaudato." }
    Write-Output "Rilascio j2: OK"
}
```

L'impronta identifica questa versione del pacchetto. Una revisione
dei materiali richiede il confezionamento e l'aggiornamento dei checksum;
non basta sostituire il valore atteso per dichiarare collaudata una
versione differente.

## Riproducibilità

La configurazione privata associa le build allo stesso codice canonico.
Il rapporto registra gli strumenti e gli hash dei sorgenti utilizzati.
Una build con un diverso JDK può produrre byte differenti: per distribuire
materiali identici si conserva il pacchetto validato con il suo checksum.

Una modifica al JAR richiede un nuovo collaudo prima del confezionamento.
Una modifica alle istruzioni richiede l'aggiornamento del pacchetto
e dei checksum. La rigenerazione della licenza richiede anche
l'allineamento della flag configurata in CTFd.
L'aggiornamento del README tecnico degli autori non modifica il JAR
né lo ZIP già distribuito e non richiede di ricompilarli.

## Configurazione CTFd

J2 è configurata e verificata nel CTFd di sviluppo, versione 3.8.7,
raggiungibile su `http://127.0.0.1:18080`.
L'integrazione nell'istanza CTFd sul Master rimane da eseguire.

### Parametri della challenge

| Campo | Valore |
| --- | --- |
| Nome | J2 - Verifica licenza |
| Categoria | Reverse engineering |
| Tipo | `standard` |
| Punteggio | 200 punti, fisso |
| Tipo di flag | `static` |
| Confronto della flag | Case Sensitive |
| Limite totale degli invii | Nessuno (`Max Attempts` pari a 0) |
| Prerequisiti della challenge | Nessuno |
| Primo suggerimento | Gratuito |
| Secondo suggerimento | 20 punti, con il primo come prerequisito |
| Allegato | `j2-verifica-licenza.zip` |

Punteggi e suggerimenti seguono le [regole comuni Jeopardy](../../README.md#challenge).

La flag attesa è il valore del campo `flag` in
`artifacts/j2/private/scenario.properties`, relativo al JAR collaudato.
Il file privato non viene allegato alla challenge.

La distribuzione nel laboratorio segue la distinzione tra
[preparazione e avvio della prova](../../README.md#preparazione-e-avvio-della-prova):
materiali e istruzioni devono essere accessibili prima del tempo
di risoluzione. Il passaggio a `Visible` non basta se gli orari
configurati impediscono il download anticipato.

### Descrizione per i partecipanti

```text
Un programma verifica un codice di licenza prima di consentire
l'accesso. Il controllo e i dati necessari alla verifica sono
contenuti nel JAR.

Scarica ed estrai j2-verifica-licenza.zip, quindi leggi README.txt.
Analizza verifica-licenza.jar e ricostruisci il codice accettato.

Il codice ha formato XXXX-XXXX-XXXX: ogni X rappresenta una
lettera ASCII o una cifra. I trattini sono obbligatori e gli
spazi non sono ammessi. Il verificatore accetta anche le minuscole.

Per costruire la flag, converti il codice in maiuscolo e rimuovi
i trattini. Inserisci la risposta nel formato
CRCTF{CODICE_NORMALIZZATO}, sostituendo CODICE_NORMALIZZATO
con i dodici caratteri ricostruiti.

L'analisi statica con un decompilatore Java offline, come
Vineflower, è sufficiente. L'esecuzione del verificatore
è facoltativa e richiede Java 17 o successivo.
```

### Allegato

In CTFd viene caricato soltanto lo ZIP della directory `release`.
L'archivio comprende già le istruzioni e i checksum dei contenuti.
Il README tecnico, i sorgenti e i materiali privati rimangono
nei materiali degli autori.

### Confronto dello ZIP scaricato da CTFd

Caricare lo ZIP di `artifacts/j2/release/` nella scheda della challenge.
Con l'account studente scaricarlo dal portale e salvarlo con il nome
originale in `artifacts/j2/download-check/`. La directory è destinata
al controllo degli autori; il suo nome non è un requisito della challenge.

Per predisporla, dalla radice del repository:

```powershell
New-Item -ItemType Directory -Force -Path .\artifacts\j2\download-check | Out-Null
```

Conservare qui il download effettivo, senza copiarlo da `release/`.
Se il browser aggiunge un suffisso come `(1)`, identificare la copia
appena scaricata e ripristinare il nome originale. Eseguire quindi:

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j2Original = ".\artifacts\j2\release\j2-verifica-licenza.zip"
    $j2Downloaded = ".\artifacts\j2\download-check\j2-verifica-licenza.zip"
    foreach ($j2Path in @($j2Original, $j2Downloaded)) {
        if (-not (Test-Path -LiteralPath $j2Path -PathType Leaf)) {
            throw "File mancante: $j2Path"
        }
    }
    $j2OriginalHash = (Get-FileHash -LiteralPath $j2Original -Algorithm SHA256).Hash
    $j2DownloadHash = (Get-FileHash -LiteralPath $j2Downloaded -Algorithm SHA256).Hash
    if ($j2OriginalHash -ne $j2DownloadHash) { throw "Download differente dal rilascio." }
    Write-Output "Download j2: OK"
}
```

Un file mancante viene segnalato separatamente da una differenza di
checksum. La corrispondenza con il rilascio già collaudato conferma
che il download contiene gli stessi byte, senza richiedere di ripetere
la soluzione su una copia identica.

Per J2 questo confronto è già stato completato con esito coincidente.
Il blocco serve a ripetere il controllo su una nuova distribuzione,
ad esempio dopo il caricamento sul Master.

### Suggerimenti

#### Orientamento

- Costo: 0 punti.
- Prerequisiti: nessuno.

```text
Segui il percorso dall'input al confronto finale. Distingui
i controlli sul formato dalle trasformazioni applicate ai
caratteri e individua i valori con cui viene confrontato il risultato.
```

#### Procedura operativa

- Costo: 20 punti.
- Prerequisito: Orientamento.

```text
Decompila il JAR e osserva LicenseValidator e CodeTransformer.
Parti dall'array EXPECTED: per ciascuna posizione sottrai
il contributo aritmetico, riportando il risultato nell'intervallo
0–255, poi applica nuovamente lo XOR con la chiave corrispondente.

La permutazione indica dove ricollocare ciascun carattere
nel codice normalizzato. Per provarlo nel verificatore,
reinserisci i trattini ogni quattro caratteri.
```

Il secondo suggerimento costa il 10% del punteggio della challenge.
I controlli generali sul saldo necessario e sull'addebito al momento
dello sblocco, già eseguiti con J1, non sono stati ripetuti per J2.

### Verifica funzionale in CTFd di sviluppo

La challenge è stata mantenuta nello stato `Hidden` durante
la configurazione e resa `Visible` per la prova con l'account studente
in CTFd di sviluppo.

| Verifica | Esito |
| --- | --- |
| Download dello ZIP da CTFd e confronto SHA256 | Identico al pacchetto collaudato. |
| Invio di una flag errata | Rifiutato, senza incremento del punteggio. |
| Invio della flag corretta | Accettato; challenge risolta. |
| Punteggio della soluzione senza acquisto di suggerimenti | Incremento di 200 punti. |

Il confronto dello ZIP scaricato conferma la distribuzione degli stessi
byte già collaudati. La decompilazione non è stata ripetuta sulla copia
identica. Questi esiti riguardano il CTFd di sviluppo; la distribuzione
tramite il Master richiede una verifica dedicata.
