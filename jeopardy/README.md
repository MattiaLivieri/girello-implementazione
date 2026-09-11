# Girello — Modalità Jeopardy

Questa directory raccoglie le quattro challenge Jeopardy, le istruzioni
dei partecipanti e la configurazione del CTFd locale di sviluppo.
Per l'architettura complessiva consultare il [README generale](../README.md);
per rete, servizi e profili del Master consultare il
[README comune](../common/README.md).

## Organizzazione del laboratorio

La modalità Jeopardy prevede account individuali in CTFd e challenge
indipendenti, risolvibili nell'ordine scelto dal partecipante.
CTFd presenta consegne e suggerimenti, distribuisce i materiali,
verifica le flag e aggiorna la classifica.

L'analisi di J1 e J2 avviene con strumenti locali. J3 viene eseguita
in un container Docker e J4 in una VM VirtualBox sulla postazione
del partecipante. CTFd non avvia né ripristina questi ambienti.
Strumenti e materiali vengono predisposti prima del tempo di soluzione,
così da consentire lo svolgimento senza accesso a Internet.

## Challenge

| Challenge | Categoria | Obiettivo didattico | Punti |
| --- | --- | --- | --- |
| [J1 - Traffico in chiaro](challenges/j1-traffico-in-chiaro/README.md) | Analisi di rete | Interpretare HTTP Basic e ricostruire un documento dal traffico. | 100 |
| [J2 - Verifica licenza](challenges/j2-verifica-licenza/README.md) | Reverse engineering | Ricostruire una licenza analizzando le trasformazioni nel JAR. | 200 |
| [J3 - Portale universitario](challenges/j3-portale-universitario/README.md) | Web | Comprendere la distinzione fra autenticazione e autorizzazione. | 150 |
| [J4 - Privilegi Linux](challenges/j4-privilegi-linux/README.md) | Sicurezza Linux | Riconoscere una delega sudo eccessiva. | 250 |

Le schede locali utilizzano il tipo `standard`, punteggi fissi e flag
statiche con confronto case sensitive. Ogni challenge prevede
`Orientamento`, gratuito, e `Procedura operativa`, con costo pari
al 10% del punteggio e il primo suggerimento come prerequisito.
I punteggi restano valori iniziali da confrontare con la difficoltà
osservata durante la valutazione didattica.

## Sorgenti e istruzioni

| Percorso relativo a questa directory | Contenuto |
| --- | --- |
| `challenges/` | Sorgenti e documentazione delle quattro challenge. |
| `challenges/*/author/` | Strumenti di costruzione, configurazione e controllo degli autori. |
| `challenges/*/player/` | Istruzioni e configurazioni destinate ai partecipanti. |
| `dev/` | Configurazione dell'istanza CTFd locale di sviluppo. |

L'organizzazione dei sorgenti applicativi dipende dalla challenge:
per esempio J3 mantiene `app/`, `Dockerfile` e `requirements.txt`
nella propria directory principale. I README tecnici collegati sopra
documentano le procedure e i comandi disponibili, i risultati delle prove
e le eventuali lacune ancora da completare.

I README tecnici degli autori contengono dettagli delle soluzioni.
Agli studenti viene distribuito il `README.txt` della cartella `player/`.

## Materiali di distribuzione

| Challenge | Allegati della scheda CTFd |
| --- | --- |
| J1 | `j1-traffico-in-chiaro.zip`, contenente PCAP, `README.txt` e `SHA256SUMS`. |
| J2 | `j2-verifica-licenza.zip`, contenente JAR, `README.txt` e `SHA256SUMS`. |
| J3 | `j3-portale-universitario.tar`, `compose.yaml`, `README.txt` e `SHA256SUMS`, separati. |
| J4 | `j4-privilegi-linux.ova`, `README.txt` e `SHA256SUMS`, separati. |

Per J1 e J2 il checksum esterno dello ZIP rimane nei materiali degli
autori; il manifest interno verifica i contenuti estratti. Per J3
`SHA256SUMS` elenca TAR, Compose e README; per J4 il manifest attuale
contiene il solo checksum dell'OVA. I checksum servono a confrontare
i materiali distribuiti con il rilascio collaudato.

I rilasci sono conservati in `artifacts/j1/release/` fino a
`artifacts/j4/release/`, con percorsi relativi alla radice del repository.
La directory `artifacts/` è esclusa da Git. Le sottocartelle `private/`
conservano i valori canonici e i materiali riservati; `validation/`
e le eventuali `download-check/` raccolgono le verifiche degli autori.
Non è necessario che tutte le challenge abbiano le stesse sottocartelle.

Per J4 il README viene copiato da `player/README.txt` in `release/`
e allegato alla scheda, senza modificare l'OVA. Non appartiene ai
materiali privati. Per riutilizzare gli stessi rilasci su un altro PC
o sul Master occorre trasferire anche gli artefatti: il solo clone
del repository non recupera i pacchetti né i valori canonici delle flag.

## Stato delle verifiche locali

Le quattro challenge sono implementate e configurate nel CTFd locale
di sviluppo, raggiungibile su `http://127.0.0.1:18080`.

| Challenge | Verifiche concluse e attività residue |
| --- | --- |
| J1 | Cattura aggiornata, soluzione e confezionamento verificati. Le prove degli invii e dei suggerimenti precedono la revisione HTTP; il download dello ZIP aggiornato da CTFd resta da confermare. |
| J2 | 439 controlli automatici, ricostruzione con Vineflower, rilascio, confronto del download e invii della flag verificati. |
| J3 | 18 test automatici, login e IDOR, esportazione e caricamento del TAR, prova offline, confronto dei quattro allegati e invii con assegnazione di 150 punti verificati. |
| J4 | OVA importata, accesso SSH, soluzione, ripristino, confronto del download e invii verificati. Il download del nuovo README del partecipante resta da confermare. |

Questi risultati riguardano la postazione di sviluppo. Non costituiscono
una verifica su tutte le postazioni BYOD né una misura della difficoltà
per studenti che non conoscono già le soluzioni.

## Passaggio al Master

Il caricamento delle challenge sul Master e il collaudo nella rete
del laboratorio sono previsti dopo il completamento della redazione.
Occorrerà trasferire i rilasci verificati, configurare schede, flag,
suggerimenti e account e verificare i download e gli invii dalle postazioni
attraverso Nginx e la rete Wi-Fi dedicata.

Le procedure comuni gestiscono rete e servizi; il cambio del profilo
del Master non importa automaticamente le challenge o i dati CTFd.
Un push su GitHub pubblica sorgenti e documentazione, ma non trasferisce
gli artefatti esclusi da Git e non aggiorna da solo il portale del Master.