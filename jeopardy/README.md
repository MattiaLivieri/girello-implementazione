# Modalità Jeopardy di Girello

Questa directory raccoglie il lavoro sulle quattro challenge del laboratorio
Jeopardy. Il Master ospita il portale CTFd e distribuisce i materiali;
ciascuno studente analizza o esegue la propria copia sul PC personale.

## Stato del lavoro

È predisposta la struttura delle challenge con le rispettive specifiche
iniziali. Generatori, applicazioni, pacchetti e verifiche di esecuzione devono
ancora essere realizzati. La presenza delle directory non costituisce una
validazione degli esercizi.

## Organizzazione

| Directory | Contenuto previsto | Distribuzione |
| --- | --- | --- |
| [challenges/j1-traffico-in-chiaro/](challenges/j1-traffico-in-chiaro/README.md) | Analisi di una cattura di rete | ZIP con PCAP e istruzioni |
| [challenges/j2-verifica-licenza/](challenges/j2-verifica-licenza/README.md) | Analisi di un verificatore Java | ZIP con JAR e istruzioni |
| [challenges/j3-portale-universitario/](challenges/j3-portale-universitario/README.md) | Applicazione web locale e autorizzazione dei documenti | Immagine Docker in TAR |
| [challenges/j4-privilegi-linux/](challenges/j4-privilegi-linux/README.md) | Gestione dei privilegi in un guest Linux | Appliance Debian in OVA |

I file necessari a build, esecuzione e verifica verranno aggiunti alla
directory della challenge corrispondente quando saranno implementati.
I pacchetti generati appartengono a `/artifacts/`, già esclusa da Git nella
radice del repository. Credenziali effettive, flag canoniche, soluzioni,
copie corrette e risultati grezzi delle sessioni sono conservati fuori dal
repository pubblico. Prima della pubblicazione va valutato anche se i
sorgenti anticipano il percorso risolutivo della sessione valutata.

## Impostazione del laboratorio

- Partecipazione individuale con account CTFd precreati in User Mode.
- Quattro challenge indipendenti, disponibili in ordine libero durante la prova.
- Preparazione e importazione degli ambienti prima del tempo di soluzione.
- Accesso Wi-Fi al portale e funzionamento offline durante la sessione.
- Punteggi statici, un hint gratuito per challenge e un secondo opzionale a costo.
- Classifica per account; un invio duplicato non assegna ulteriori punti.
- Reset della copia locale senza cancellare i risultati registrati sul portale.

La configurazione del portale e la procedura di preparazione devono essere
collaudate separatamente. Il cambio del profilo di rete non imposta account,
challenge, hint o orari in CTFd.

### Configurazione rinviata alla preparazione della sessione

La predisposizione degli account e la chiusura della registrazione autonoma
sul portale del Master sono rinviate alla preparazione della sessione.
Non sono prerequisiti per creare questa struttura o sviluppare le challenge.
Prima dell'accesso dei partecipanti andranno verificati gli account
individuali precreati, la separazione degli amministratori, il login e
il blocco delle nuove registrazioni autonome.

La visibilità della registrazione è un'impostazione globale dell'istanza
CTFd condivisa con Attack & Defense. Il cambio del profilo di rete non la
modifica e non conserva configurazioni CTFd distinte per le due modalità.
Questo punto resta da completare; non documenta una modifica già eseguita.
Rimane valido il vincolo di sola lettura sul Master.

## Ordine di implementazione

1. Rilevare in sola lettura lo stato del Master e la configurazione del portale.
2. Verificare in un ambiente di sviluppo distinto il flusso CTFd: accesso,
   preparazione prima del via, invio flag, punteggio, hint e classifica.
3. Realizzare J1 con generatore, pacchetto finale, istruzioni e controlli.
4. Realizzare J3 per verificare anche distribuzione, esecuzione e reset
   di un ambiente interattivo locale.
5. Completare J2 e J4 con i rispettivi percorsi di build e collaudo.
6. Validare la sessione completa, raccogliere le evidenze e tarare i parametri.

Per ogni blocco si registrano requisito, modifica, verifica eseguita, esito
osservato e limiti. Dopo il consolidamento si prepara il testo della tesi
coerente con lo stile e l'indice correnti, distinguendo implementazione e
risultati misurati.

## Confini del lavoro

Lo sviluppo avviene in una copia di lavoro distinta dal Master. Sul Master,
anche tramite SSH, sono consentiti esclusivamente comandi di lettura: questo
documento non autorizza modifiche a file, configurazioni, repository,
servizi o dati della competizione. Commit e pubblicazione vengono eseguiti
dall'utente nella propria copia di sviluppo, dopo la spiegazione delle
modifiche, delle motivazioni e delle verifiche svolte.

La configurazione comune è descritta in
[Preparazione e utilizzo del Master](../common/README.md).