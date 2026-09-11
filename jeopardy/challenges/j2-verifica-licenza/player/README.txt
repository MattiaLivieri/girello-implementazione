J2 - Verifica licenza

Scenario
Un programma verifica un codice di licenza prima di consentire l'accesso.
Il controllo e i dati necessari alla verifica sono contenuti nel JAR.

Obiettivo
Analizza verifica-licenza.jar e ricostruisci il codice accettato.
Il codice ha formato XXXX-XXXX-XXXX: ogni X rappresenta una lettera
ASCII (A-Z, a-z) o una cifra (0-9). I trattini sono obbligatori;
spazi e altri caratteri non sono ammessi.

Per formare la flag, converti le lettere in maiuscolo e rimuovi
i trattini dal codice ricostruito. Inserisci su CTFd la risposta
CRCTF{CODICE_NORMALIZZATO}, sostituendo CODICE_NORMALIZZATO con
i dodici caratteri ottenuti. Rispetta maiuscole, minuscole e simboli.

Strumenti
Un decompilatore Java da utilizzare offline, come Vineflower.
Il JAR è compilato per Java 17 e non ha dipendenze applicative esterne.
L'analisi statica è sufficiente a ricostruire la soluzione.
L'esecuzione del verificatore è facoltativa, con Java 17 o successivo:

java -jar verifica-licenza.jar

Il programma legge il codice dal terminale e indica se è valido.
Non richiede accesso alla rete. Modificarlo per accettare qualsiasi
input non fornisce il codice da utilizzare nella flag.

Materiali
- verifica-licenza.jar: programma da analizzare.
- README.txt: istruzioni della challenge.
- SHA256SUMS: hash SHA-256 dei due file precedenti.

Lo ZIP di distribuzione si estrae senza password.