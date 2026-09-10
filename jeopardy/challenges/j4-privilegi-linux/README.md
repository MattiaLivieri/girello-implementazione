# J4 Privilegi Linux

La challenge riguarda l'analisi dei privilegi di un account ordinario
all'interno di un sistema Linux predisposto per l'esercitazione.

## Stato

Specifica iniziale. Appliance, script di configurazione e collaudo non ancora realizzati.

## Materiali previsti

- Procedura di installazione da ISO Debian amd64 identificata.
- Script di configurazione della challenge destinato al solo guest di sviluppo.
- OVA VirtualBox con versione, checksum e istruzioni per importazione e rete.
- Controlli su una nuova importazione e sul ripristino dello stato iniziale.

La VM viene eseguita sul PC dello studente, con rete host-only dedicata e
senza NAT, bridge o condivisioni dell'host. Lo snapshot iniziale viene creato
a VM spenta dopo importazione e configurazione della rete. Non è richiesta
una pipeline completamente automatica per la produzione dell'OVA.

La soluzione e i valori canonici rimangono nei materiali riservati degli autori.