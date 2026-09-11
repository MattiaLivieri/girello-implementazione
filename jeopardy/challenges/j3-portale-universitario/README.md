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
CTFd sul Master distribuisce i materiali, presenta i suggerimenti
e riceve la flag. La preparazione dell'ambiente avviene prima
dell'inizio del tempo di risoluzione.

Questo README documenta il lavoro degli autori e contiene dettagli
del percorso di soluzione. Le istruzioni distribuite ai partecipanti
sono in `player/README.txt`.

## Stato

Completati sul PC Windows di sviluppo:

- costruzione dell'immagine Docker con configurazione privata;
- superamento dei 18 test automatici durante la build;
- avvio del container e superamento del controllo di salute;
- correzione della configurazione di rete per l'accesso dal browser;
- verifica del login con l'account fornito;
- verifica dei collegamenti e del download dei documenti personali;
- recupero del documento dell'altro studente mediante l'IDOR prevista.

Restano da completare il confezionamento dei materiali di distribuzione,
la verifica del caricamento dell'immagine esportata, la configurazione
di J3 nel CTFd locale e le prove degli invii con un account studente.

Restano inoltre l'integrazione nel CTFd del Master, la verifica della
distribuzione nel laboratorio e la valutazione della difficoltà con
partecipanti. Le prove locali verificano il funzionamento tecnico;
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
dell'immagine e gli hash dei sorgenti utilizzati.

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
e `no-new-privileges`. I limiti configurati sono 256 MB di memoria,
una CPU e 64 processi. Questi valori sono impostazioni del container,
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

L'immagine `girello/j3-portale-universitario:1.0` è presente nel runtime
Docker utilizzato per la build. Finché non viene esportata, non esiste
automaticamente un file TAR distribuibile nella cartella del progetto.

I materiali sotto `artifacts/` rimangono esclusi da Git.
La copia privata di `scenario.json` non viene distribuita come allegato
separato. L'immagine contiene necessariamente i dati utilizzati
dall'applicazione per presentare il documento con la flag.

## Esito della verifica locale

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

Il confezionamento non è ancora completato. I materiali previsti sono:

- immagine Docker esportata in un file TAR;
- `compose.yaml`, copiato dalla directory `player`;
- `README.txt`, con preparazione, accesso e gestione del container;
- checksum dei materiali distribuiti.

I nomi definitivi, i checksum e la procedura di confezionamento saranno
registrati dopo la preparazione e la verifica dei file di rilascio.
Il solo completamento della build non costituisce il collaudo
del pacchetto esportato.

Il partecipante carica l'immagine già costruita con `docker load`,
avvia il portale mediante Docker Compose e accede dal browser locale.
Non deve eseguire `Build.ps1` né costruire l'applicazione dai sorgenti.
Caricamento e avvio rientrano nella preparazione precedente al tempo
di risoluzione.

Prima della distribuzione occorre verificare il caricamento del TAR,
l'avvio con il Compose consegnato, il funzionamento offline e
la corrispondenza della flag con il valore configurato in CTFd.

Il README tecnico e i controlli degli autori non sono allegati
destinati ai partecipanti. Il percorso didattico avviene attraverso
il portale con l'account assegnato; l'amministrazione del PC BYOD
non impedisce tecnicamente l'ispezione dell'immagine Docker.

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

Una modifica applicativa richiede una nuova build e un nuovo collaudo.
Una modifica al Compose richiede una verifica dell'avvio e della rete,
oltre all'aggiornamento dei materiali di distribuzione. Una modifica
al README dei partecipanti richiede l'aggiornamento della sua copia
distribuita e del relativo checksum.

Se viene generata una nuova flag, occorre allineare l'immagine,
la copia canonica e il valore atteso in CTFd.

## Configurazione CTFd

La configurazione seguente è prevista per J3; il caricamento
e le prove nel CTFd locale non risultano ancora completati.

### Parametri della challenge

| Campo | Configurazione prevista |
| --- | --- |
| Nome | J3 - Portale universitario |
| Tipo | Standard |
| Categoria | Web |
| Punteggio | 150, provvisorio fino alla valutazione didattica |
| Flag | Statica, confronto case sensitive |
| Limite totale degli invii | Nessuno (`Max Attempts` pari a 0) |
| Prerequisiti della challenge | Nessuno |
| Primo suggerimento | Gratuito |
| Secondo suggerimento | 15 punti, con il primo come prerequisito |
| Allegati | Immagine esportata, Compose, istruzioni e checksum da predisporre. |

La flag attesa deve corrispondere alla configurazione privata
in `artifacts/j3/private/scenario.json` relativa all'immagine collaudata.
Il valore effettivo non viene riportato in questo README.

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

Caricare soltanto i materiali di rilascio dopo il loro collaudo.
Le istruzioni devono distinguere l'accesso a CTFd sul Master
dall'accesso al portale locale su `http://127.0.0.1:18083`.

La copia privata della configurazione, i rapporti di build
e questo README tecnico rimangono nei materiali degli autori.

### Suggerimenti

Primo suggerimento: **Orientamento**, costo 0, senza prerequisiti.

```text
Osserva i collegamenti usati per scaricare i tuoi documenti.
Quale parte del collegamento distingue un documento dall'altro?
```

Secondo suggerimento: **Procedura operativa**, costo 15,
con Orientamento come prerequisito.

```text
Copia un collegamento di download e modifica l'identificativo
del documento nell'URL, mantenendo la sessione di Alice.
Osserva i numeri presenti nei collegamenti del tuo elenco
e prova il valore intermedio. Il server controlla anche
che il documento richiesto appartenga al tuo account?
```

Il secondo suggerimento costa il 10% del punteggio iniziale.
La consegna indica l'obiettivo; la modifica esplicita dell'URL
viene descritta nel suggerimento operativo.

### Verifica funzionale locale

Da completare dopo il confezionamento e il caricamento in CTFd:

- download degli allegati e confronto con i checksum del rilascio;
- rifiuto di una flag errata senza incremento del punteggio;
- accettazione della flag corretta;
- incremento di 150 punti per la soluzione senza acquisto di suggerimenti;
- controllo della configurazione dei due suggerimenti.

Durante la configurazione mantenere la challenge nascosta e renderla
visibile per la prova con l'account studente. La pubblicazione
nella sessione di laboratorio e la verifica tramite il Master
restano attività successive.