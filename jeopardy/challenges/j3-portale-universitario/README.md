# J3 — Portale universitario

## Obiettivo

Il partecipante accede a un portale universitario con l'account di uno
studente fittizio e recupera un documento riservato a un altro studente
della stessa applicazione. La challenge introduce la distinzione tra
autenticazione e autorizzazione.

L'elenco mostra correttamente soltanto i documenti dell'utente autenticato.
Il download verifica la presenza della sessione, ma omette intenzionalmente
il controllo del proprietario del documento richiesto. Modificando
l'identificativo nella richiesta, il partecipante può quindi scaricare
un documento che non compare nel proprio elenco. Questa vulnerabilità
è un caso di IDOR (Insecure Direct Object Reference).

Il portale viene eseguito in un container sul PC del partecipante.
Nell'assetto del laboratorio, CTFd sul Master distribuisce i materiali,
presenta i suggerimenti e riceve la flag. La preparazione dell'ambiente
avviene prima dell'inizio del tempo di risoluzione.

Questo README documenta il lavoro degli autori e contiene dettagli
del percorso di soluzione. Le istruzioni distribuite ai partecipanti
sono in `player/README.txt`.

## Stato

Completati sul PC Windows di sviluppo:

- costruzione dell'immagine Docker con configurazione privata e 18 test automatici superati;
- avvio del container e correzione della rete per l'accesso dal browser;
- login, elenco e download dei documenti personali di Alice;
- recupero del documento di Marco mediante l'IDOR prevista;
- esportazione dell'immagine e preparazione dei quattro file di rilascio;
- caricamento del TAR e corrispondenza dell'immagine con il rapporto di build;
- avvio e percorso di soluzione offline, con la stessa flag canonica;
- configurazione della challenge nel CTFd di sviluppo;
- confronto SHA-256 dei quattro file scaricati dal portale con il rilascio;
- rifiuto della flag errata e accettazione della flag corretta, con 150 punti.

Il collaudo locale di J3 è completato. Restano l'integrazione nell'istanza CTFd
sul Master, la verifica della distribuzione nella rete del laboratorio
e la valutazione della difficoltà con partecipanti. Le prove locali
non costituiscono una validazione su tutte le postazioni BYOD.

## Sorgenti

| File | Funzione |
| --- | --- |
| `README.md` | Documenta costruzione, artefatti, verifiche e configurazione CTFd. |
| `Dockerfile` | Installa le dipendenze, esegue i test e prepara l'immagine applicativa. |
| `requirements.txt` | Elenca le dipendenze Python e le versioni da installare. |
| `app/portal.py` | Implementa utenti, database, login, elenco e download dei documenti. |
| `app/templates/base.html` | Definisce la struttura comune delle pagine. |
| `app/templates/login.html` | Contiene il modulo di accesso. |
| `app/templates/documents.html` | Presenta i documenti dell'utente autenticato. |
| `app/static/style.css` | Definisce l'aspetto grafico del portale. |
| `author/Build.ps1` | Prepara la configurazione privata, costruisce l'immagine e salva il rapporto. |
| `author/test_portal.py` | Verifica il comportamento del portale e del controllo di autorizzazione corretto. |
| `player/compose.yaml` | Definisce avvio, porta locale, limiti e impostazioni del container. |
| `player/README.txt` | Contiene le istruzioni del partecipante. |

Flask gestisce l'applicazione web; Gunicorn la esegue nel container.
Il `Dockerfile` installa le librerie elencate in `requirements.txt`.
Il partecipante riceve l'immagine già costruita e non deve installare
separatamente queste dipendenze sul proprio PC.

Il database SQLite viene inizializzato dall'applicazione all'avvio
nel container. Non deve essere aggiunto come database precompilato
alla cartella dei sorgenti.

## Costruzione dell'immagine

### Ambiente utilizzato

| Componente | Configurazione utilizzata |
| --- | --- |
| Host di costruzione e collaudo | PC Windows, PowerShell |
| Runtime | Docker Desktop, contesto `desktop-linux` |
| Piattaforma dell'immagine | `linux/amd64` |
| Base Python | Python 3.13 slim Bookworm, identificata mediante digest |
| Applicazione | Python, Flask e SQLite |
| Server applicativo | Gunicorn |
| Immagine prodotta | `girello/j3-portale-universitario:1.0` |

La costruzione richiede la disponibilità della base Docker e delle
dipendenze Python. L'immagine esportata deve invece consentire
la preparazione e l'esecuzione della challenge senza download da Internet.

### Procedura degli autori

Dalla radice del repository, verificare che la configurazione privata
sia esclusa dal versionamento:

```powershell
git check-ignore -- artifacts/j3/private/scenario.json
```

Il comando deve indicare il percorso richiesto. Eseguire quindi:

```powershell
& .\jeopardy\challenges\j3-portale-universitario\author\Build.ps1
```

Lo script prepara o riutilizza la configurazione privata e avvia
la costruzione Docker. La build installa le dipendenze, ne controlla
la compatibilità con `pip check` ed esegue i test automatici.
L'immagine finale utilizza un utente non root.

La flag canonica è conservata nei materiali privati e riutilizzata
nelle build successive. Il rapporto registra gli identificativi
dell'immagine e gli hash dei sorgenti utilizzati. Il suo campo
`runtime_validation` è un promemoria generato dalla build e non viene
aggiornato automaticamente dalle prove manuali. Gli esiti successivi
sono documentati nelle sezioni di verifica di questo README.

### Avvio per il collaudo

Dalla radice del repository:

```powershell
docker --context desktop-linux compose -f .\jeopardy\challenges\j3-portale-universitario\player\compose.yaml up -d --wait

docker --context desktop-linux compose -f .\jeopardy\challenges\j3-portale-universitario\player\compose.yaml ps
```

Aprire nel browser dello stesso PC:

```text
http://127.0.0.1:18083
```

Credenziali dell'account fittizio assegnato al partecipante:

| Campo | Valore |
| --- | --- |
| Utente | `alice` |
| Password | `LaboratorioJ3!` |

Queste credenziali appartengono al portale della challenge e sono
distinte dall'account personale utilizzato per accedere a CTFd.

### Rete e impostazioni di esecuzione

La configurazione collaudata pubblica la porta del servizio con:

```yaml
ports:
  - "127.0.0.1:18083:8000"
```

La rete del Compose utilizza il driver `bridge`, senza `internal: true`:

```yaml
networks:
  local:
    driver: bridge
```

Nel collaudo con Docker Desktop, la configurazione precedente con
la sola rete interna non rendeva effettiva la pubblicazione della porta.
Dopo la rimozione dell'opzione e la ricreazione di container e rete,
il portale è risultato raggiungibile. L'output di `compose ps` ha mostrato:

```text
127.0.0.1:18083->8000/tcp
```

Il binding su loopback limita l'accesso alla porta pubblicata al PC
del partecipante. La rete bridge adottata non blocca le connessioni
in uscita del container verso le reti raggiungibili dal PC.
L'esecuzione offline è quindi distinta dal filtraggio del traffico
in uscita. Durante il laboratorio si applicano anche le regole
generali sulla disconnessione dalle reti esterne.

Il Compose imposta l'utente `10001:10001`, il filesystem in sola lettura,
una directory temporanea in `tmpfs`, la rimozione delle capability
e `no-new-privileges`. I limiti configurati sono 256 MiB di memoria,
una quota CPU equivalente a una CPU logica e un limite PID di 64, che comprende
anche i thread. Questi valori sono impostazioni del container,
non i requisiti complessivi di Docker Desktop sulla postazione.

Il controllo di salute interroga `/healthz` dall'interno del container.
Lo stato `healthy` deve essere accompagnato dalla verifica dell'accesso
dal browser, poiché non dimostra da solo la pubblicazione della porta.

## Artefatti locali

Percorsi relativi alla radice del repository:

| Percorso | Contenuto |
| --- | --- |
| `artifacts/j3/private/scenario.json` | Configurazione privata con la flag canonica. |
| `artifacts/j3/private/build-lock.json` | Riferimento alla base Docker utilizzata. |
| `artifacts/j3/build/context-*/` | Copie dei materiali passati a Docker durante le build. |
| `artifacts/j3/build/build-report.json` | Rapporto di costruzione e hash dei sorgenti. |
| `artifacts/j3/release/` | TAR, Compose, README del partecipante e checksum del rilascio. |
| `artifacts/j3/download-check/` | Copie scaricate dal CTFd di sviluppo e confrontate con il rilascio. |

L'immagine `girello/j3-portale-universitario:1.0` è stata esportata in
`artifacts/j3/release/j3-portale-universitario.tar`. La build e
l'esportazione sono passaggi distinti: `Build.ps1` costruisce l'immagine
e salva il rapporto, ma non genera automaticamente il TAR.

`download-check/` conserva le copie realmente scaricate da CTFd;
non viene distribuita ai partecipanti e non contiene una nuova build.

I materiali sotto `artifacts/` rimangono esclusi da Git.
La copia privata di `scenario.json` non viene distribuita come allegato
separato. L'immagine contiene necessariamente i dati utilizzati
dall'applicazione per presentare il documento con la flag.

## Esito della verifica nell'ambiente di sviluppo

La build ha superato **18 test automatici**. I controlli riguardano
il comportamento dell'applicazione, compresa la vulnerabilità prevista
e la variante con il controllo di autorizzazione corretto.

Il collaudo manuale è stato eseguito dal browser del PC Windows.

| Verifica | Esito |
| --- | --- |
| Build e test automatici | Completati; 18 test superati. |
| Avvio del container | Stato `healthy`. |
| Pubblicazione della porta locale | Confermata dopo la modifica della rete. |
| Accesso dal browser | Pagina del portale raggiungibile. |
| Login come Alice | Riuscito. |
| Elenco dei documenti personali | Collegamenti ai documenti `1001` e `1003`. |
| Download di un documento personale | Riuscito. |
| Download autenticato del documento `1002` | Riuscito; confermata l'IDOR prevista. |
| Caricamento del TAR esportato | Riuscito; identificativo dell'immagine coincidente con il rapporto di build. |
| Avvio e utilizzo offline | Riusciti, con Wi-Fi disattivato. |
| Flag nel documento di Marco dopo il caricamento | Coincidente con il valore canonico. |

I collegamenti osservati nell'elenco sono:

```text
/documents/1001/download
/documents/1003/download
```

La richiesta del documento `1002`, mantenendo la sessione di Alice,
consente di recuperare il documento di Marco Bianchi, personaggio
fittizio della stessa istanza. Il salto fra gli identificativi facilita
la scoperta; la causa della vulnerabilità è l'assenza del controllo
di proprietà sul download.

La correzione deve verificare che il documento richiesto appartenga
all'utente autenticato prima di restituirne il contenuto. Il confronto
con la variante corretta è verificato nei test degli autori; l'immagine
della challenge mantiene intenzionalmente il comportamento vulnerabile.

La semplicità degli identificativi è coerente con un esercizio
introduttivo. La difficoltà effettiva e la comprensione del controllo
mancante restano da valutare con partecipanti.

## Pacchetto di distribuzione

Il rilascio collaudato è conservato in `artifacts/j3/release/` e comprende
quattro file separati, senza un ulteriore archivio ZIP:

| File | Contenuto | Dimensione del rilascio verificato |
| --- | --- | --- |
| `j3-portale-universitario.tar` | Immagine Docker esportata. | 46 330 880 byte |
| `compose.yaml` | Copia della configurazione in `player/`. | 850 byte |
| `README.txt` | Copia delle istruzioni in `player/`. | 2 073 byte |
| `SHA256SUMS` | Impronte SHA-256 dei tre file precedenti. | 254 byte |

L'esportazione è stata eseguita con `docker image save` dopo aver
confrontato l'identificativo dell'immagine con il rapporto di build.
Compose e README sono stati copiati da `player/`; successivamente
sono stati calcolati i checksum dei tre materiali da distribuire.
Le dimensioni riportate descrivono questo rilascio e possono cambiare
quando vengono aggiornati i materiali.

Per verificare il TAR, il container è stato arrestato e rimosso tramite
Compose; l'immagine nominata è stata rimossa dal runtime e caricata
nuovamente dal file esportato. L'identificativo recuperato coincideva
con quello registrato nel rapporto di costruzione. Una successiva prova
con Wi-Fi disattivato ha confermato caricamento, avvio, login, download
e recupero della stessa flag attraverso il documento `1002`.

Il partecipante segue `README.txt`: carica l'immagine con `docker load`,
avvia il portale mediante il Compose consegnato e accede dal browser
locale. Non deve eseguire `Build.ps1` né costruire l'applicazione dai
sorgenti. La preparazione precede il tempo dedicato alla soluzione.

I quattro allegati scaricati dal CTFd di sviluppo sono stati confrontati
tramite SHA-256 con gli originali in `release/`: tutti coincidevano,
compreso il file `SHA256SUMS`. Il controllo del manifest stesso è
un confronto separato; il manifest elenca soltanto gli altri tre file.

Il README tecnico e i controlli degli autori non sono allegati
destinati ai partecipanti. Il percorso didattico avviene attraverso
il portale con l'account assegnato; l'amministrazione del PC BYOD
non impedisce tecnicamente l'ispezione dell'immagine Docker.

### Comandi per preparare un rilascio

I blocchi seguenti documentano la procedura usata e permettono di
ripeterla su una nuova preparazione. Il rilascio locale descritto sopra
è già collaudato: non occorre ricrearlo per aggiornare questo README.
Eseguire ogni blocco completo in PowerShell dalla radice del repository.
La creazione si ferma se `release/` esiste già, per conservare il rilascio.

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j3Release = ".\artifacts\j3\release"
    $j3Report = Get-Content -Raw .\artifacts\j3\build\build-report.json | ConvertFrom-Json
    $j3Image = "girello/j3-portale-universitario:1.0"

    git check-ignore -- artifacts/j3/release/j3-portale-universitario.tar
    if ($LASTEXITCODE -ne 0) { throw "Il rilascio J3 deve essere escluso da Git." }

    $j3Id = docker --context desktop-linux image inspect $j3Image --format '{{.Id}}'
    if ($LASTEXITCODE -ne 0) { throw "Immagine J3 non disponibile." }
    if ($j3Id -ne $j3Report.image_id) { throw "Immagine diversa da quella del rapporto." }
    if (Test-Path -LiteralPath $j3Release) { throw "Release gia presente: conservarla." }

    New-Item -ItemType Directory -Path $j3Release | Out-Null
    docker --context desktop-linux image save --output "$j3Release\j3-portale-universitario.tar" $j3Image
    if ($LASTEXITCODE -ne 0) { throw "Esportazione J3 non riuscita; rilascio incompleto." }

    Copy-Item .\jeopardy\challenges\j3-portale-universitario\player\compose.yaml $j3Release
    Copy-Item .\jeopardy\challenges\j3-portale-universitario\player\README.txt $j3Release
    $j3Sums = foreach ($j3File in @("j3-portale-universitario.tar", "compose.yaml", "README.txt")) {
        $j3Hash = (Get-FileHash -LiteralPath (Join-Path $j3Release $j3File) -Algorithm SHA256).Hash.ToLowerInvariant()
        "$j3Hash  $j3File"
    }
    $j3Sums | Set-Content -LiteralPath "$j3Release\SHA256SUMS" -Encoding ASCII
    Get-ChildItem -LiteralPath $j3Release -File | Select-Object Name, Length
    Get-Content -LiteralPath "$j3Release\SHA256SUMS"
}
```

Un errore dopo la creazione della cartella lascia un rilascio incompleto:
non caricarlo su CTFd. La procedura non aggiorna automaticamente un
rilascio già esistente né sostituisce la sua verifica.

### Controllo dei checksum del rilascio

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j3Release = ".\artifacts\j3\release"
    $j3ExpectedNames = @("j3-portale-universitario.tar", "compose.yaml", "README.txt")
    $j3Seen = @()
    foreach ($j3Line in Get-Content -LiteralPath "$j3Release\SHA256SUMS") {
        if ($j3Line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Riga checksum non valida." }
        $j3Expected = $Matches[1]
        $j3File = $Matches[2]
        if ($j3File -cnotin $j3ExpectedNames -or $j3File -cin $j3Seen) {
            throw "Nome inatteso o duplicato nel manifest."
        }
        $j3Seen += $j3File
        $j3Path = Join-Path $j3Release $j3File
        if (-not (Test-Path -LiteralPath $j3Path -PathType Leaf)) { throw "File mancante: $j3File" }
        $j3Actual = (Get-FileHash -LiteralPath $j3Path -Algorithm SHA256).Hash
        if ($j3Actual -ne $j3Expected) { throw "Checksum non coincidente: $j3File" }
        Write-Output "${j3File}: OK"
    }
    if ($j3Seen.Count -ne 3) { throw "Manifest incompleto." }
}
```

### Caricamento del TAR e collaudo offline

Nel collaudo è stata rimossa l'immagine nominata prima del caricamento,
per verificare il recupero dal TAR. Il blocco seguente arresta e rimuove
il container del progetto J3 e azzera il suo stato temporaneo.
Eseguirlo soltanto quando si intende ripetere il collaudo, dopo il
controllo dei checksum. Per la prova offline disattivare le connessioni
esterne del PC prima di eseguirlo; nella prova svolta è stato disattivato
il Wi-Fi. Docker Desktop deve rimanere avviato.

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j3Compose = ".\artifacts\j3\release\compose.yaml"
    $j3Tar = ".\artifacts\j3\release\j3-portale-universitario.tar"
    $j3Image = "girello/j3-portale-universitario:1.0"
    $j3Report = Get-Content -Raw .\artifacts\j3\build\build-report.json | ConvertFrom-Json
    if (-not (Test-Path -LiteralPath $j3Tar -PathType Leaf)) { throw "TAR J3 mancante." }
    if (-not (Test-Path -LiteralPath $j3Compose -PathType Leaf)) { throw "Compose J3 mancante." }

    docker --context desktop-linux compose -f $j3Compose down
    if ($LASTEXITCODE -ne 0) { throw "Arresto J3 non riuscito." }
    docker --context desktop-linux image rm --no-prune $j3Image
    if ($LASTEXITCODE -ne 0) { throw "Rimozione immagine non riuscita; non usare --force." }
    docker --context desktop-linux load --input $j3Tar
    if ($LASTEXITCODE -ne 0) { throw "Caricamento TAR non riuscito." }
    $j3Id = docker --context desktop-linux image inspect $j3Image --format '{{.Id}}'
    if ($LASTEXITCODE -ne 0) { throw "Immagine caricata non trovata." }
    if ($j3Id -ne $j3Report.image_id) { throw "Image ID diverso dal rapporto." }
    docker --context desktop-linux compose -f $j3Compose up -d --wait --pull never
    if ($LASTEXITCODE -ne 0) { throw "Avvio J3 non riuscito." }
    docker --context desktop-linux compose -f $j3Compose ps
    if ($LASTEXITCODE -ne 0) { throw "Lettura stato J3 non riuscita." }
}
```

Il blocco presuppone che l'immagine sia presente all'inizio, come nella
prova eseguita. Su una postazione nuova basta caricare il TAR e avviare
il Compose seguendo `player/README.txt`; non serve il rapporto degli autori.

Dal browser verificare il portale su `http://127.0.0.1:18083`, accedere
come Alice e scaricare un documento personale. Nella stessa scheda
autenticata inserire poi:

```text
http://127.0.0.1:18083/documents/1002/download
```

Il documento riservato deve contenere la stessa flag canonica. Gli autori
possono leggere il valore di confronto con:

```powershell
(Get-Content -Raw .\artifacts\j3\private\scenario.json | ConvertFrom-Json).flag
```

Non copiare tale valore nella documentazione pubblica. Dopo una
ricreazione del container occorre autenticarsi nuovamente. Se il browser
rimanda al login, completarlo e reinserire l'indirizzo del documento
nella scheda autenticata: il login riporta all'elenco personale.

### Confronto degli allegati scaricati da CTFd

Caricare i quattro file di `release/` nella scheda J3. Con l'account
studente scaricarli e conservarli in `artifacts/j3/download-check/`,
mantenendo i nomi originali. Rimuovere eventuali suffissi aggiunti dal
browser, come `(1)`, dopo aver identificato la copia appena scaricata.
Non riempire questa cartella copiando gli originali da `release/`:
il controllo deve riguardare i download effettivi.

Per predisporre la cartella:

```powershell
New-Item -ItemType Directory -Force -Path .\artifacts\j3\download-check | Out-Null
```

Dopo avervi salvato i download:

```powershell
& {
    $ErrorActionPreference = "Stop"
    foreach ($j3File in @("j3-portale-universitario.tar", "compose.yaml", "README.txt", "SHA256SUMS")) {
        $j3Original = Join-Path ".\artifacts\j3\release" $j3File
        $j3Downloaded = Join-Path ".\artifacts\j3\download-check" $j3File
        foreach ($j3Path in @($j3Original, $j3Downloaded)) {
            if (-not (Test-Path -LiteralPath $j3Path -PathType Leaf)) {
                throw "File mancante: $j3Path"
            }
        }
        $j3OriginalHash = (Get-FileHash -LiteralPath $j3Original -Algorithm SHA256).Hash
        $j3DownloadHash = (Get-FileHash -LiteralPath $j3Downloaded -Algorithm SHA256).Hash
        if ($j3OriginalHash -ne $j3DownloadHash) { throw "Download differente: $j3File" }
        Write-Output "${j3File}: OK"
    }
}
```

La prova svolta ha restituito `OK` per tutti e quattro i file. In un primo
tentativo mancava il TAR nella cartella di controllo: il file assente
non costituiva un'evidenza di corruzione. Il blocco sopra distingue
esplicitamente un file mancante da una differenza di checksum.

Le prove degli invii si eseguono dall'interfaccia CTFd: inviare prima
`CRCTF{prova_errata}` e verificare il rifiuto senza incremento dei punti;
inviare poi la flag canonica e verificare l'assegnazione di 150 punti
senza acquisto di suggerimenti. Questi esiti sono già stati confermati
nel collaudo locale; un account che ha già risolto J3 non riceve
nuovamente i punti.

## Riproducibilità

La configurazione privata conserva la flag canonica fra le build.
Il riferimento alla base Docker, le versioni delle dipendenze e
gli hash dei sorgenti permettono di documentare la costruzione.
Non viene dichiarata la produzione di immagini o TAR identici
byte per byte mediante una nuova build.

Per distribuire gli stessi materiali a tutti i partecipanti si conserva
il rilascio collaudato, identificato dai checksum. Il tag `1.0` da solo
non garantisce l'identità dell'immagine, perché può essere riutilizzato
da una build successiva.

Il rapporto conserva gli hash dei file presenti al momento della build,
compreso il README tecnico. L'aggiornamento di questo documento non
modifica l'immagine collaudata e non richiede di riscrivere il rapporto
storico né di ricostruire l'immagine.

Una modifica applicativa richiede una nuova build e un nuovo collaudo.
Una modifica al Compose richiede una verifica dell'avvio e della rete,
oltre all'aggiornamento dei materiali di distribuzione. Una modifica
al README dei partecipanti richiede l'aggiornamento della sua copia
distribuita e del relativo checksum.

Se viene generata una nuova flag, occorre allineare l'immagine,
la copia canonica e il valore atteso in CTFd.

## Configurazione CTFd

J3 è configurata e verificata nel CTFd di sviluppo, versione 3.8.7,
raggiungibile su `http://127.0.0.1:18080`.
L'integrazione nell'istanza CTFd sul Master rimane da eseguire.

### Parametri della challenge

| Campo | Valore |
| --- | --- |
| Nome | J3 - Portale universitario |
| Categoria | Web |
| Tipo | `standard` |
| Punteggio | 150 punti, fisso |
| Tipo di flag | `static` |
| Confronto della flag | Case Sensitive |
| Limite totale degli invii | Nessuno (`Max Attempts` pari a 0) |
| Prerequisiti della challenge | Nessuno |
| Primo suggerimento | Gratuito |
| Secondo suggerimento | 15 punti, con il primo come prerequisito |
| Allegati | `j3-portale-universitario.tar`, `compose.yaml`, `README.txt`, `SHA256SUMS`. |

Punteggi e suggerimenti seguono le [regole comuni Jeopardy](../../README.md#challenge).

La flag attesa deve corrispondere alla configurazione privata
in `artifacts/j3/private/scenario.json` relativa all'immagine collaudata.
Il valore effettivo non viene riportato in questo README.

La distribuzione nel laboratorio segue la distinzione tra
[preparazione e avvio della prova](../../README.md#preparazione-e-avvio-della-prova):
materiali e istruzioni devono essere accessibili prima del tempo
di risoluzione. Il passaggio a `Visible` non basta se gli orari
configurati impediscono il download anticipato.

### Descrizione per i partecipanti

```text
Il portale universitario permette agli studenti di consultare
e scaricare i propri documenti.

Utilizza il portale J3 preparato sulla tua postazione e accedi
con l'account di Alice indicato nel README.txt.

Il tuo obiettivo è recuperare il documento riservato a Marco Bianchi,
un altro studente fittizio della stessa applicazione, utilizzando
l'account fornito. Il documento contiene la flag.

Inserisci in CTFd la flag completa nel formato CRCTF{...},
rispettando maiuscole, minuscole e simboli.
```

### Allegati

Nel CTFd di sviluppo sono stati caricati i quattro file di `release/`
elencati nella tabella. Le copie scaricate sono risultate identiche
agli originali mediante confronto SHA-256.
Le istruzioni distinguono l'accesso a CTFd dall'accesso al portale
locale su `http://127.0.0.1:18083`.

La copia privata della configurazione, i rapporti di build
e questo README tecnico rimangono nei materiali degli autori.

### Suggerimenti

#### Orientamento

- Costo: 0 punti.
- Prerequisiti: nessuno.

```text
Osserva i collegamenti usati per scaricare i tuoi documenti.
Quale parte del collegamento distingue un documento dall'altro?
```

#### Procedura operativa

- Costo: 15 punti.
- Prerequisito: Orientamento.

```text
Copia un collegamento di download e modifica l'identificativo
del documento nell'URL, mantenendo la sessione di Alice.
Osserva i numeri presenti nei collegamenti del tuo elenco
e prova il valore intermedio. Il server controlla anche
che il documento richiesto appartenga al tuo account?
```

Il secondo suggerimento costa il 10% del punteggio della challenge.
La consegna indica l'obiettivo; la modifica esplicita dell'URL
viene descritta nel suggerimento operativo.

### Verifica funzionale in CTFd di sviluppo

Le prove con un account studente hanno confermato:

- download dei quattro allegati e corrispondenza SHA-256 con il rilascio;
- rifiuto di una flag errata senza incremento del punteggio;
- accettazione della flag canonica recuperata dal portale;
- assegnazione di 150 punti senza acquisto di suggerimenti.

I suggerimenti seguono la configurazione descritta sopra. Queste prove
non comprendono un nuovo acquisto del suggerimento a pagamento:
il comportamento generale di sblocco e addebito era già stato verificato
con J1.

Durante la configurazione mantenere la challenge nello stato `Hidden`
e impostare `Visible` per la prova con l'account studente
in CTFd di sviluppo. Il collaudo sul Master rimane distinto
da queste verifiche.
