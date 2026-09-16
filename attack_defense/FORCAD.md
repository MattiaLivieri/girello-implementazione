# ForcAD in Girello

ForcAD è il motore utilizzato per la modalità Attack & Defense di Girello.

La directory `forcad/` contiene i sorgenti importati dalla repository
https://github.com/pomo-mondreganto/ForcAD al commit:

`6ce3407be569b7f69f879501c5e2ca79231c1ff9`

Questa è la versione utilizzata nella valutazione iniziale del motore.
La licenza originale è conservata in `forcad/LICENSE`.

I sorgenti sono versionati direttamente nella repository Girello.
Gli adattamenti locali vengono quindi conservati nella stessa cronologia
del progetto.

I checker specifici dei servizi Girello si trovano nella directory
`checkers/`.

## Adattamenti per il laboratorio offline

Il frontend utilizza le risorse di Font Awesome distribuite localmente.
Sono stati rimossi i riferimenti a Google Fonts e al foglio di stile
remoto di Font Awesome, permettendo l'utilizzo dell'interfaccia senza
accesso a Internet.

È inoltre applicata una correzione alla gestione della cache delle flag.

L'adattamento del frontend riguarda la versione compilata in
`forcad/front/dist/`, utilizzata dal container Nginx.

## Configurazione sul Master

L'installazione Girello usa `compose.forcad.yaml`, con nome progetto
`girello-ad`. Le immagini sono costruite dai Dockerfile originali,
includendo gli adattamenti locali del motore.

`game.yml` contiene i parametri condivisi della gara: due team,
Document Vault, round da 300 secondi e durata delle flag pari al round
di deposito e ai due successivi. Gli indirizzi dei team nella
configurazione sono quelli dei rispettivi ingressi proxy.

Per il primo allestimento si costruisce l'immagine backend e si prepara
`forcad/config.yml` a partire da `game.yml`, aggiungendo in `game`
il campo `start_time` con la data e l'ora UTC di preparazione.
Il comando nativo `control.py setup`, eseguito nell'immagine backend,
completa la configurazione e genera credenziali e file di ambiente.
Questi file locali sono esclusi da Git dalle regole originali di ForcAD.

Una successiva modifica a `game.yml` non aggiorna automaticamente
la configurazione caricata nel database.

Il servizio `initializer`, nel profilo `setup`, inizializza il motore.
Il servizio `ticker`, nel profilo `gara`, avvia i round ed è escluso
dall'avvio iniziale dell'infrastruttura. I comandi di gestione usano
esplicitamente `compose.forcad.yaml`; il Compose generato da
`control.py setup` non viene usato per l'avvio Girello.

Il worker esegue due processi Celery e monta in sola lettura il checker
da `checkers/document-vault/`. Usa l'indirizzo `172.30.20.3`
sul bridge `br-girello-ad`, coerentemente con il firewall del Master.

Il frontend è pubblicato su `127.0.0.1:18080`, come previsto dal
proxy HTTP del Master. Il database PostgreSQL usa un volume del
progetto `girello-ad`, indipendente dai dati della prova iniziale.

La configurazione predispone il percorso verso i servizi dei team.
La verifica attraverso i proxy e l'avvio dei round appartengono
al successivo blocco di integrazione.
