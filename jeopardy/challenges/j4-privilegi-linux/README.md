# J4 — Privilegi Linux

## Obiettivo

La challenge richiede di analizzare i privilegi assegnati a un account
ordinario Linux e individuare una delega sudo eccessiva che consenta
di leggere la flag conservata in `/root/flag.txt`.

Il partecipante accede alla VM tramite SSH con l'utente `ctf`.
La possibilità di eseguire `/usr/bin/find` come root senza password
è una proprietà intenzionale dello scenario.

La VM viene eseguita sul PC del partecipante con una rete VirtualBox
host-only. La preparazione dell'ambiente avviene prima dell'inizio
del tempo di risoluzione.

Questo documento contiene i dettagli tecnici destinati agli autori.
Le istruzioni distribuite ai partecipanti sono contenute nel relativo
`README.txt` e nei materiali di preparazione.

## Stato

Completate sul PC Windows di sviluppo:

- installazione del guest Debian e configurazione della rete host-only;
- predisposizione della challenge mediante lo script di configurazione;
- verifica dell'accesso SSH e del percorso di soluzione;
- esportazione dell'appliance OVA e calcolo del checksum;
- importazione dell'OVA in una nuova VM e verifica della flag;
- verifica del ripristino dello snapshot iniziale;
- caricamento dell'OVA, di `README.txt` e di `SHA256SUMS` in CTFd di sviluppo;
- confronto SHA-256 dei tre allegati scaricati con i corrispondenti file di rilascio.

L'integrazione nel CTFd di sviluppo è stata verificata mediante un account
studente: la flag errata viene rifiutata e quella corretta viene accettata.
La configurazione e gli esiti sono descritti nella sezione
Configurazione CTFd di questo documento.

Il README del partecipante è mantenuto in `player/README.txt`.
Il rilascio comprende anche una copia in `artifacts/j4/release/README.txt`,
allegata alla scheda CTFd insieme all'OVA e a `SHA256SUMS`.
L'aggiunta delle istruzioni non richiede una nuova esportazione della VM.

Il controllo della distribuzione comprende tutti e tre gli allegati,
scaricati con l'account studente e confrontati mediante SHA-256
con i corrispondenti file di rilascio. Il controllo di `README.txt`
è distinto dal collaudo funzionale dell'appliance: l'aggiunta
delle istruzioni non modifica l'OVA già verificata.

Restano inoltre il caricamento nell'istanza CTFd sul Master, la verifica della
distribuzione nella rete del laboratorio e la valutazione della
difficoltà con partecipanti.

## Sorgenti

| File | Funzione |
| --- | --- |
| `author/configure.py` | Controlla i prerequisiti del guest e predispone flag, delega sudo e accesso SSH. |
| `README.md` | Documenta costruzione, artefatti, verifiche e configurazione CTFd. |
| `player/README.txt` | Istruzioni destinate al partecipante, da includere nel rilascio e negli allegati CTFd. |

La copia originale delle istruzioni è versionata in `player/README.txt`.
La copia da distribuire è conservata in `artifacts/j4/release/README.txt`;
non deve essere collocata in `private/` e non sostituisce questo README
tecnico degli autori.

Lo script di configurazione viene eseguito come root esclusivamente
nel guest di costruzione. La flag canonica, le credenziali amministrative
e la soluzione operativa rimangono nei materiali riservati degli autori.

## Costruzione della VM

### Ambiente utilizzato

| Componente | Configurazione verificata |
| --- | --- |
| Host di costruzione e collaudo | Windows 11, x86-64 |
| Hypervisor | VirtualBox 7.2.16 r174877 |
| Guest | Debian GNU/Linux 13.6, amd64 |
| ISO di installazione | `debian-13.6.0-amd64-netinst.iso` |
| Memoria della VM | 2048 MB |
| Processori virtuali | 1 |
| Firmware | BIOS, EFI disabilitato |
| Disco iniziale | VDI da 16 GiB, allocazione dinamica |
| Partizionamento | Partizione principale ext4 e swap |
| Ambiente grafico nel guest | Non installato |
| Nome host | `j4-linux` |
| Account del partecipante | `ctf` |
| VM di costruzione | `Girello-J4-build` |
| VM di verifica dell'OVA | `Girello-J4-validation` |

### Installazione e rete

Il sistema viene installato dall'ISO Debian dopo la verifica del suo
checksum, disabilitando l'installazione non presidiata di VirtualBox.
Si utilizzano il nome host `j4-linux`, un dominio vuoto e l'account
ordinario `ctf`, con una password amministrativa distinta e riservata
agli autori.

L'installazione comprende il server SSH e le utilità di sistema standard.
GRUB viene installato sul disco virtuale `/dev/sda`.
Durante la costruzione si utilizza temporaneamente una scheda NAT
per scaricare aggiornamenti e pacchetti.

Prima di rimuovere la connettività Internet, come root:

```bash
apt update
apt upgrade
apt install --no-install-recommends sudo findutils python3 openssh-server ca-certificates
```

L'utente `ctf` non appartiene ai gruppi privilegiati `root`, `sudo`,
`admin`, `docker`, `lxd` o `disk`.

La configurazione finale utilizza una sola scheda host-only:

| Elemento | Valore |
| --- | --- |
| Interfaccia host-only del PC | `192.168.56.1/24` |
| Interfaccia del guest | `enp0s3` |
| Indirizzo del guest | `192.168.56.10/24` |
| Gateway del guest | Assente |
| DHCP VirtualBox sulla rete dedicata | Disabilitato |
| IPv6 su `enp0s3` | Disabilitato |
| Schede aggiuntive | Disabilitate |

Nel guest verificato la rete è gestita da ifupdown.
Il file `/etc/network/interfaces` contiene:

```text
source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

auto enp0s3
iface enp0s3 inet static
    address 192.168.56.10/24
    pre-up /usr/sbin/sysctl -q -w net.ipv6.conf.enp0s3.disable_ipv6=1
```

La directory `/etc/network/interfaces.d/` non contiene configurazioni
aggiuntive. Dopo aver predisposto il file, si spegne il guest e si
sostituisce la connessione NAT con quella host-only nelle impostazioni
VirtualBox, rimuovendo eventuali regole temporanee di inoltro delle porte.

La VM finale non utilizza NAT, bridge, cartelle condivise, appunti
condivisi o trascinamento tra host e guest.

Al successivo avvio si verificano indirizzi e rotte:

```bash
ip -br address
ip route
ip -6 route show default
```

Il guest presenta l'indirizzo `192.168.56.10/24` su `enp0s3` e la rotta
della rete host-only, senza rotte predefinite IPv4 o IPv6.
Il tipo di collegamento viene controllato anche nelle impostazioni
VirtualBox: l'indirizzo del guest, da solo, non dimostra la modalità
della scheda virtuale.

### Configurazione della challenge

Prima dell'esecuzione di `configure.py` devono essere disponibili
il guest Debian in VirtualBox, il nome host `j4-linux`, l'account `ctf`,
i pacchetti richiesti e la rete statica senza rotte predefinite.

Dalla radice del repository, in PowerShell, si trasferisce lo script:

```powershell
scp .\jeopardy\challenges\j4-privilegi-linux\author\configure.py ctf@192.168.56.10:j4-configure.py
```

Nel guest, come root:

```bash
install -o root -g root -m 0700 /home/ctf/j4-configure.py /root/configure-j4.py
python3 /root/configure-j4.py
```

Lo script controlla i prerequisiti e rifiuta collegamenti simbolici
o file di destinazione inattesi. Genera la flag se assente e conserva
una flag esistente conforme al formato previsto.

La flag viene assegnata a root con permessi `0600`, mentre `/root`
mantiene permessi `0700`. La regola in `/etc/sudoers.d/j4-ctf` consente
intenzionalmente a `ctf` di eseguire `/usr/bin/find` come root senza
password. La delega è eccessiva perché il programma autorizzato può
eseguire altri comandi con i privilegi ricevuti.

La configurazione SSH disabilita l'accesso diretto di root e permette
l'autenticazione con password per `ctf`. Lo script valida i file
temporanei prima dell'installazione, verifica le configurazioni sudo
e SSH, controlla le impostazioni SSH effettive e ricarica il servizio.
Al termine stampa il checksum del file della flag senza mostrarne
il contenuto.

I controlli di permessi e autorizzazioni utilizzati sono:

```bash
stat -c '%U:%G %a %n' /root /root/flag.txt /etc/sudoers.d/j4-ctf
sudo -l -U ctf
```

Permessi attesi:

```text
root:root 700 /root
root:root 600 /root/flag.txt
root:root 440 /etc/sudoers.d/j4-ctf
```

Una copia privata della flag viene conservata fuori dalla VM e
confrontata mediante checksum con quella del guest. Il checksum
identifica i byte del file; il valore inserito in CTFd è il testo
della flag, senza il carattere finale di nuova riga.

### Preparazione dell'esportazione

Dopo la verifica del percorso di soluzione si rimuovono dal guest
le copie dello script di configurazione, il backup temporaneo della
configurazione di rete e i comandi di soluzione dalle cronologie
delle shell. Lo script originale rimane nel repository.

La VM viene spenta ordinatamente e l'ISO viene scollegata dal lettore
ottico virtuale prima dell'esportazione.

## Artefatti locali

L'organizzazione prevista, con percorsi relativi alla radice del
repository, è:

- `artifacts/j4/iso/`: ISO Debian e materiali per verificarne il checksum.
- `artifacts/j4/vm/`: file della VM di costruzione.
- `artifacts/j4/private/`: copia canonica della flag e materiali riservati.
- `artifacts/j4/validation/`: file della VM importata per il collaudo.
- `artifacts/j4/release/`: `j4-privilegi-linux.ova`, `SHA256SUMS` e `README.txt`.
- `artifacts/j4/download-check/`: OVA, `README.txt` e `SHA256SUMS` scaricati da CTFd di sviluppo per il confronto.

La directory `artifacts/` rimane esclusa dal versionamento Git.
Il controllo effettuato con `git ls-files -- artifacts` non ha
restituito file tracciati.

Durante la costruzione e la prima esportazione i materiali sono stati
collocati nelle corrispondenti directory sotto `D:\Girello\j4`.
La repository è stata successivamente trasferita in:

```text
D:\Users\Filippo\IdeaProjects\girello-implementazione
```

Il controllo del download è stato eseguito in `artifacts/j4/download-check/`
nella nuova posizione. La posizione degli altri materiali va verificata nella postazione
effettiva: non è documentato qui il trasferimento completo delle VM.
Lo spostamento della repository non trasferisce automaticamente
le VM registrate in VirtualBox né i volumi Docker del CTFd di sviluppo.

## Esito della verifica nell'ambiente di sviluppo

La challenge è stata verificata nella VM di costruzione e poi in una
nuova VM importata dall'OVA, denominata `Girello-J4-validation`.

Le prove hanno confermato:

- avvio della VM importata e accesso SSH come `ctf`;
- indirizzo statico previsto e assenza di rotte predefinite;
- presenza della delega sudo prevista dalla challenge;
- rifiuto della lettura diretta della flag con l'account ordinario;
- ottenimento dei privilegi root tramite il percorso previsto;
- corrispondenza della flag con la copia canonica;
- ripristino dello stato iniziale mediante snapshot.

Per verificare il ripristino è stato creato il file
`/home/ctf/j4-reset-test.txt` dopo lo snapshot. Dopo lo spegnimento,
il ripristino e il nuovo avvio, il file risultava assente e il checksum
della flag era invariato.

Le prove nella VM importata non modificano l'OVA originale.
Il file successivamente scaricato da CTFd presenta lo stesso SHA-256
dell'appliance collaudata. L'importazione non è stata ripetuta sul
download, poiché il confronto ha confermato l'identità del file.

Questi esiti verificano il funzionamento nell'ambiente locale provato.
La compatibilità con le altre postazioni BYOD e la difficoltà didattica
restano da valutare.

## Pacchetto di distribuzione

Il rilascio contiene tre file separati:

| File | Funzione |
| --- | --- |
| `j4-privilegi-linux.ova` | Guest configurato, con descrittore OVF 2.0 e manifest. |
| `README.txt` | Istruzioni di preparazione, accesso e ripristino per il partecipante. |
| `SHA256SUMS` | Impronta SHA-256 dell'OVA collaudata. |

L'OVA non viene racchiusa in un ulteriore archivio ZIP. Il README
accompagna l'appliance come file separato; non viene inserito nel disco
virtuale e non richiede di modificare la VM.

Per aggiornare la copia delle istruzioni, dalla radice del repository:

```powershell
Copy-Item .\jeopardy\challenges\j4-privilegi-linux\player\README.txt .\artifacts\j4\release\README.txt
```

Caricare su CTFd la copia in `release/`. Dopo eventuali modifiche alle
istruzioni, aggiornare anche la copia distribuita e controllare che
il partecipante possa scaricare e leggere il nuovo file.

L'esportazione dell'appliance collaudata è stata eseguita con la VM
spenta, utilizzando il percorso originario dei materiali:

```powershell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" export "Girello-J4-build" --output="D:\Girello\j4\release\j4-privilegi-linux.ova" --ovf20 --manifest
```

Per esportazioni successive il percorso di destinazione deve
corrispondere all'organizzazione effettiva degli artefatti.

L'OVA verificata ha una dimensione di 1 149 221 376 byte, circa 1,07 GiB.

SHA-256 dell'appliance verificata:

```text
c541e0d2ced8c505cadc4a437d9caa452bca6e76322b785847a2f5ac7deaea1f
```

Il file `SHA256SUMS`, distribuito separatamente, contiene:

```text
c541e0d2ced8c505cadc4a437d9caa452bca6e76322b785847a2f5ac7deaea1f  j4-privilegi-linux.ova
```

Il checksum si riferisce all'OVA. L'aggiunta o la modifica
di `README.txt` come file separato non modifica l'appliance né il suo hash
e non richiede di aggiornare questo `SHA256SUMS`.
Il confronto del README con la copia scaricata rimane separato.
Il manifest incluso nell'OVA è distinto dal file `SHA256SUMS`
distribuito come allegato.

Prima dell'esercitazione il partecipante verifica il checksum, importa
l'OVA e collega la sola scheda di rete alla rete host-only dedicata.
L'interfaccia host utilizza `192.168.56.1/24`, il guest mantiene
`192.168.56.10/24` e il DHCP VirtualBox viene disabilitato.
La sottorete deve essere verificata rispetto alle altre reti del PC.

Il nome dell'adattatore dipende dalla postazione. Nel collaudo Windows
è stato utilizzato `VirtualBox Host-Only Ethernet Adapter`.
Non si avviano contemporaneamente più copie con lo stesso indirizzo
sulla stessa rete host-only.

Dopo l'importazione e la configurazione della rete si crea lo snapshot
`iniziale` a VM spenta, prima dell'avvio della prova. Gli snapshot della VM
di costruzione non vengono distribuiti come albero di snapshot nell'OVA.
Per ricominciare si spegne la VM e si ripristina lo snapshot `iniziale`.

La password di `ctf` viene comunicata insieme alle istruzioni di accesso.
È distinta dalle credenziali CTFd e dalla password amministrativa del guest.

La distribuzione prevista sul Master avviene tramite CTFd; l'esecuzione
della challenge avviene sulla postazione del partecipante e non richiede
Internet. La rete host-only permette la comunicazione tra host e VM,
ma non isola il guest dai servizi esposti sull'interfaccia host-only
del PC.

Il percorso previsto utilizza l'account `ctf` all'interno del guest.
L'accesso offline al disco virtuale è escluso dalle regole dell'esercitazione;
non è tecnicamente impedito a chi amministra il proprio PC BYOD.

### Controllo dei file distribuiti

Per confrontare l'OVA conservata nel rilascio con l'impronta già
collaudata, dalla radice del repository:

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j4Ova = ".\artifacts\j4\release\j4-privilegi-linux.ova"
    $j4Expected = "c541e0d2ced8c505cadc4a437d9caa452bca6e76322b785847a2f5ac7deaea1f"
    $j4Actual = (Get-FileHash -LiteralPath $j4Ova -Algorithm SHA256).Hash
    if ($j4Actual -ne $j4Expected) { throw "OVA diversa dal rilascio collaudato." }
    Write-Output "OVA J4: OK"
}
```

L'impronta nel blocco identifica il rilascio descritto in questo README;
una nuova esportazione richiede un proprio checksum e un nuovo collaudo.
Il controllo dell'OVA scaricata è già stato completato. Per la sola
aggiunta del README è sufficiente caricare la copia in `release/`
su CTFd, scaricarla con l'account studente e controllarne la leggibilità.

Per un confronto puntuale, salvare il nuovo download come
`artifacts/j4/download-check/README.txt` e utilizzare:

```powershell
& {
    $ErrorActionPreference = "Stop"
    $j4Original = ".\artifacts\j4\release\README.txt"
    $j4Downloaded = ".\artifacts\j4\download-check\README.txt"
    foreach ($j4Path in @($j4Original, $j4Downloaded)) {
        if (-not (Test-Path -LiteralPath $j4Path -PathType Leaf)) {
            throw "File mancante: $j4Path"
        }
    }
    $j4OriginalHash = (Get-FileHash -LiteralPath $j4Original -Algorithm SHA256).Hash
    $j4DownloadHash = (Get-FileHash -LiteralPath $j4Downloaded -Algorithm SHA256).Hash
    if ($j4OriginalHash -ne $j4DownloadHash) { throw "README scaricato differente." }
    Write-Output "README J4: OK"
}
```

Il confronto del `README.txt` scaricato è stato completato
con esito coincidente, insieme a quello degli altri due allegati.
Il blocco permette di ripetere il controllo dopo una nuova distribuzione.
Il file `SHA256SUMS` contiene il solo hash dell'OVA: il confronto
separato delle istruzioni non richiede di modificarlo.

## Riproducibilità

La procedura di installazione e lo script consentono di ricostruire
lo scenario. La costruzione comprende passaggi manuali e non prevede
una pipeline completamente automatica.

Installazioni, aggiornamenti ed esportazioni successive possono produrre
byte differenti. Non viene dichiarata la generazione di OVA identiche
byte per byte.

Per ripetere l'esercitazione con gli stessi materiali si conserva
e distribuisce l'appliance validata, identificata dal suo SHA-256.
Lo spostamento del file tra cartelle non richiede una nuova esportazione.

Ogni nuova esportazione deve avere un checksum aggiornato e una verifica
prima della distribuzione. Se viene generata una nuova flag, occorre
allineare l'appliance, la copia canonica e il valore atteso in CTFd.

L'aggiornamento di questo README tecnico non modifica la VM,
l'OVA, le istruzioni distribuite o i relativi checksum.
Non richiede una nuova esportazione né la modifica dei rapporti
di collaudo già conservati.

## Configurazione CTFd

### Parametri della challenge

| Campo | Valore |
| --- | --- |
| Nome | J4 - Privilegi Linux |
| Categoria | Sicurezza Linux |
| Tipo | `standard` |
| Punteggio | 250 punti, fisso |
| Tipo di flag | `static` |
| Confronto della flag | Case Sensitive |

Punteggi e suggerimenti seguono le [regole comuni Jeopardy](../../README.md#challenge).

Durante la configurazione si mantiene lo stato `Hidden`.
Per la verifica in CTFd di sviluppo con l'account studente
è stato impostato `Visible`.

La distribuzione nel laboratorio segue la distinzione tra
[preparazione e avvio della prova](../../README.md#preparazione-e-avvio-della-prova):
materiali e istruzioni devono essere accessibili prima del tempo
di risoluzione. Il passaggio a `Visible` non basta se gli orari
configurati impediscono il download anticipato.

Il valore effettivo della flag si legge dalla copia privata di
`flag.txt` relativa all'appliance validata. Il file rimane escluso
dal versionamento Git e dagli allegati pubblici.

### Descrizione per i partecipanti

Hai accesso a un account ordinario su una macchina Linux predisposta
per il laboratorio. Analizza i privilegi disponibili e individua
una configurazione che consenta di leggere il file `/root/flag.txt`.

Utilizza la VM J4 preparata sulla tua postazione e collegati tramite SSH:

```bash
ssh ctf@192.168.56.10
```

Usa la password dell'account `ctf` fornita nelle istruzioni di preparazione.

Il percorso previsto si svolge all'interno del guest tramite questo
account. L'accesso offline al disco virtuale è escluso dall'esercitazione.

Inserisci la flag completa nel formato `CRCTF{...}`, rispettando
maiuscole, minuscole e simboli.

### Allegati

La scheda deve distribuire i tre file della cartella `release/`:

- `j4-privilegi-linux.ova`;
- `README.txt`;
- `SHA256SUMS`.

I tre allegati sono stati caricati in CTFd di sviluppo e scaricati
con l'account studente. Il confronto SHA-256 con i file di rilascio
ha confermato l'identità di tutti gli allegati.
L'hash dell'OVA è riportato nella sezione Pacchetto di distribuzione.

Il file `README.txt` completa i materiali destinati al partecipante.
Per ogni successiva modifica alle istruzioni occorre aggiornare
la copia distribuita e controllarne il download e la leggibilità.
L'importazione e la soluzione della VM già collaudata non devono
essere ripetute per una modifica al solo README.
Le istruzioni e le credenziali del guest devono essere disponibili
prima dell'inizio del tempo di risoluzione.

La copia privata di `flag.txt`, lo script di configurazione e questo
README tecnico non vengono allegati alla challenge.

### Suggerimenti

#### Orientamento

- Costo: 0 punti.
- Prerequisiti: nessuno.

Un account ordinario può avere autorizzazioni specifiche per eseguire
alcuni programmi con privilegi maggiori. Controlla le autorizzazioni
assegnate al tuo utente.

#### Procedura operativa

- Costo: 25 punti.
- Prerequisito: Orientamento.

Usa `sudo -l` per elencare i comandi consentiti. Esamina le opzioni
del programma autorizzato: oltre alla sua funzione principale,
può eseguire altri comandi?

Il costo corrisponde al 10% del punteggio della challenge.
CTFd richiede un saldo sufficiente per acquistare il suggerimento
a pagamento e sottrae il costo al momento dello sblocco.
Questo comportamento generale è stato verificato con J1.

### Verifica funzionale in CTFd di sviluppo

Ambiente: CTFd 3.8.7 sul PC di sviluppo, raggiungibile all'indirizzo
[http://127.0.0.1:18080](http://127.0.0.1:18080).

Le prove hanno confermato:

- caricamento dell'OVA, di `README.txt` e di `SHA256SUMS`;
- corrispondenza SHA-256 di tutti e tre gli allegati scaricati dal portale;
- rifiuto di una flag errata inviata da un account studente;
- accettazione della flag corretta dallo stesso account.

I controlli generali sul funzionamento dei suggerimenti, già eseguiti
con J1, non sono stati ripetuti.

Il Compose di sviluppo espone CTFd direttamente sulla porta 18080, senza
Nginx. Gli upload sono conservati nel volume Docker `ctfd_uploads`,
montato in `/var/uploads`; non sono contenuti in `artifacts/ctfd-dev`.

Il controllo della configurazione ha restituito `MAX_CONTENT_LENGTH: None`.
Il caricamento dell'OVA è riuscito senza modificare il Compose per
aumentare questo limite.

Il caricamento sul Master, che utilizza Nginx, e la verifica dalla
rete del laboratorio restano attività successive.
