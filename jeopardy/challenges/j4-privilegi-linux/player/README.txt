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
VirtualBox su un PC x86-64 e un terminale con client SSH.
La VM utilizza 2048 MB di RAM e un processore virtuale.

Preparazione (prima del tempo di soluzione)
1. Confronta il checksum SHA-256 dell'OVA con quello in SHA256SUMS,
   poi importa j4-privilegi-linux.ova in VirtualBox.
2. Nel gestore di rete di VirtualBox prepara una rete host-only:
   indirizzo dell'adattatore del PC 192.168.56.1, maschera
   255.255.255.0 e server DHCP disabilitato.
3. A VM spenta, in Impostazioni > Rete collega soltanto la Scheda 1
   all'adattatore host-only preparato, con Cavo connesso attivo.
   Disabilita le altre schede; non utilizzare NAT o bridge.
   Mantieni disabilitati cartelle condivise, appunti condivisi
   e trascinamento fra host e guest.
4. L'indirizzo della VM è già impostato a 192.168.56.10, senza gateway:
   non occorre modificare la rete dentro Debian. Se la sottorete
   192.168.56.0/24 è già utilizzata sul PC, chiedi agli organizzatori.
5. Nella sezione Istantanee di VirtualBox crea lo snapshot iniziale
   a VM spenta, dopo la configurazione della rete e prima della soluzione.

Accesso
Avvia la VM e collegati dal terminale del PC:

ssh ctf@192.168.56.10

Utente: ctf
Password: JeoProvaaDeb1an.

Durante l'inserimento della password il terminale non mostra caratteri.
Queste credenziali sono distinte da quelle utilizzate per CTFd.
La challenge si svolge nella VM locale e non richiede accesso a Internet.
Avvia una sola copia di J4 sulla rete host-only.

Ripristino
Per ricominciare, spegni la VM e ripristina lo snapshot iniziale
nella sezione Istantanee di VirtualBox, poi riavviala.
Il ripristino annulla le modifiche nella VM, ma non le soluzioni
né i punti già registrati in CTFd.

Materiali
- j4-privilegi-linux.ova: macchina virtuale della challenge.
- README.txt: istruzioni della challenge.
- SHA256SUMS: hash SHA-256 del file OVA.

L'appliance si importa senza password. Le credenziali dell'account ctf
servono per accedere al sistema dopo l'avvio.