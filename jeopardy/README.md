# Modalità Jeopardy di Girello

Questa directory contiene le quattro challenge del laboratorio Jeopardy.
Nell'architettura prevista, il Master ospita CTFd e distribuisce
i materiali; ciascuno studente analizza o esegue la propria copia
sul PC personale.

## Stato del lavoro

J1 è stata realizzata e verificata sul PC di sviluppo, comprendendo
generazione dei materiali, soluzione e integrazione nel CTFd locale.

Le intestazioni HTTP del server di costruzione sono state corrette.
La cattura aggiornata e il pacchetto di distribuzione sono stati
verificati, confermando il recupero dell'archivio e della flag.
Gli hash dei materiali validati sono riportati nel README di J1.

J2, J3 e J4 contengono le specifiche iniziali. I relativi ambienti,
artefatti e collaudi devono ancora essere realizzati.

Il caricamento sul Master e la verifica nella rete del laboratorio
restano attività successive.

## Organizzazione

| Directory | Contenuto | Distribuzione |
| --- | --- | --- |
| [J1](challenges/j1-traffico-in-chiaro/README.md) | Analisi di traffico HTTP | ZIP con PCAP e istruzioni |
| [J2](challenges/j2-verifica-licenza/README.md) | Analisi di un verificatore Java | ZIP con JAR e istruzioni |
| [J3](challenges/j3-portale-universitario/README.md) | Autorizzazione dei documenti in un'applicazione web | Immagine Docker in TAR |
| [J4](challenges/j4-privilegi-linux/README.md) | Privilegi di un account Linux | Appliance Debian in OVA |
| [Ambiente di sviluppo](dev/README.md) | Istanza CTFd locale per il collaudo | Servizi Docker sul PC degli autori |

## Documentazione delle challenge

Ogni challenge mantiene un unico README contenente:

- obiettivo e scenario;
- stato di avanzamento;
- sorgenti e costruzione dei materiali;
- materiali distribuiti e istruzioni d'uso;
- configurazione CTFd;
- verifiche effettuate ed esiti;
- riproducibilità e ripristino, dove applicabile.

Le schede iniziali vengono completate durante l'implementazione.
La presenza di una directory non indica che la challenge sia già pronta.

## Impostazione del laboratorio

- Partecipazione individuale con account CTFd precreati in User Mode.
- Quattro challenge indipendenti, affrontabili in ordine libero.
- Preparazione e importazione degli ambienti prima del tempo di soluzione.
- Accesso Wi-Fi al portale locale, senza necessità di Internet durante la sessione.
- Punteggi statici, un suggerimento gratuito e un secondo opzionale a pagamento.
- Classifica per account; gli invii duplicati non assegnano ulteriori punti.
- Ripristino degli ambienti locali senza cancellare i risultati sul portale.

Il cambio del profilo di rete non configura account, challenge,
suggerimenti o orari in CTFd.

## Materiali locali

La directory `artifacts/`, nella radice del repository, contiene
i materiali generati e le evidenze delle verifiche ed è esclusa da Git.

Le credenziali dell'istanza di sviluppo appartengono a `dev/.env`,
anch'esso escluso dal versionamento. Il modello pubblico è
`dev/.env.example`.

I valori effettivi delle flag, le credenziali e le configurazioni
riservate non vengono pubblicati nei sorgenti o nella documentazione.
Le flag sono inserite nei materiali della challenge secondo
il meccanismo previsto per il loro recupero.

Ai partecipanti vengono forniti soltanto gli allegati indicati
nel README della rispettiva challenge. Configurazioni degli autori,
soluzioni estratte e rapporti di verifica rimangono separati
dai pacchetti distribuiti.

## Attività successive

1. Realizzare J4, dall'installazione della VM al collaudo dell'OVA.
2. Completare J2 e J3.
3. Predisporre sul Master la sessione con account e materiali definitivi.
4. Verificare accesso, distribuzione, isolamento e funzionamento complessivo
   nella rete del laboratorio.

Prima del caricamento dei materiali sul Master devono essere verificati
anche i limiti di upload del portale e del reverse proxy, dimensionandoli
sui pacchetti effettivi, in particolare TAR e OVA.

## Integrazione con il Master

Durante lo sviluppo, sul Master sono previste esclusivamente operazioni
di lettura. L'applicazione delle configurazioni e il caricamento dei
materiali appartengono alla successiva fase di integrazione.

La registrazione autonoma, la predisposizione degli account e le altre
impostazioni globali di CTFd devono essere coordinate con l'utilizzo
dell'istanza comune da parte di Attack & Defense.

La configurazione comune è descritta in
[Preparazione e utilizzo del Master](../common/README.md).

Le prove nell'ambiente locale non sostituiscono quelle sul reverse proxy,
sulla rete Wi-Fi e sulle postazioni effettivamente utilizzate.