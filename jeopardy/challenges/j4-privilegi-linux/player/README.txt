J4 - Privilegi Linux

Scenario
Hai accesso a un account ordinario su una macchina Linux predisposta
per il laboratorio. Il sistema contiene un documento riservato,
normalmente accessibile soltanto all'amministratore.
Una configurazione dei privilegi permette di superare questa limitazione.

Obiettivo
Analizza i privilegi disponibili per l'utente ctf e individua un modo
per leggere il file /root/flag.txt. Inserisci la flag nella pagina di J4
su CTFd, rispettando maiuscole, minuscole e simboli.
Il percorso previsto si svolge all'interno della VM tramite l'account
assegnato. L'accesso offline al disco virtuale è escluso dall'esercitazione.

Strumenti
VirtualBox e un terminale con client SSH sul proprio PC.
Prima dell'inizio dell'esercitazione, verifica il checksum dell'OVA,
importa la VM e configura la rete host-only seguendo le istruzioni
di preparazione. Crea lo snapshot iniziale a VM spenta.

Avvia la VM e collegati dal terminale del PC:

ssh ctf@192.168.56.10

Usa la password dell'account ctf fornita dagli organizzatori.
Queste credenziali sono distinte da quelle utilizzate per CTFd.
La challenge si svolge nella VM locale e non richiede accesso a Internet.
Per ricominciare, spegni la VM e ripristina lo snapshot iniziale.

Materiali
- j4-privilegi-linux.ova: macchina virtuale della challenge.
- README.txt: istruzioni della challenge.
- SHA256SUMS: hash SHA-256 del file OVA.

L'appliance si importa senza password. Le credenziali dell'account ctf
servono per accedere al sistema dopo l'avvio.