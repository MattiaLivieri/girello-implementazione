J1 - Traffico in chiaro

Scenario
Una postazione ha consultato un archivio documentale interno.
La cattura contiene il traffico di questa attività, comprese le richieste
alle risorse pubbliche e il trasferimento di un documento riservato.
L'utente riutilizza la stessa password per l'accesso al servizio e per
proteggere l'archivio trasferito.

Obiettivo
Analizza traffico.pcap, ricostruisci il documento trasferito e recupera
la flag contenuta al suo interno. Inserisci la flag nella pagina di J1
su CTFd, rispettando maiuscole, minuscole e simboli.

Strumenti
Wireshark e un programma compatibile con archivi ZIP AES-256, come 7-Zip.
L'analisi si svolge offline sul proprio PC. Gli indirizzi nella cattura
appartengono allo scenario registrato: non occorre contattarli.

Materiali
- traffico.pcap: cattura da analizzare.
- README.txt: istruzioni della challenge.
- SHA256SUMS: hash SHA-256 dei due file precedenti.

Lo ZIP di distribuzione si estrae senza password. L'archivio presente
nel traffico è invece protetto dalla password da recuperare.