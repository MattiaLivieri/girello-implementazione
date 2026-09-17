# Distribuzione delle VM A&D con CTFd

CTFd autentica gli utenti e mostra a ciascuno la VM assegnata.
Nginx trasferisce la OVA dal filesystem del Master dopo l'autorizzazione
del plugin, attraverso un percorso interno.

Il download è disponibile dal portale locale e dai due ingressi CTFd
della modalità A&D. ForcAD gestisce separatamente round, flag e punteggi.

## Artefatti v1

Le OVA rimangono fuori dalla repository:

- `/srv/girello/distribution/ad/v1/girello-team1.ova`
- `/srv/girello/distribution/ad/v1/girello-team2.ova`

SHA-256 delle esportazioni del 17 settembre 2026:

```text
29a76ae656c9e718412c3a5c95ddb5714c8d82063486a8c97562ade5ffe12442  girello-team1.ova
2a5de0f6be4a6aed54d9d201d566c3cf2fdba94dd987ccb9eed7d6771d3886c9  girello-team2.ova
```

Una nuova esportazione richiede una nuova directory di versione e
l'aggiornamento di VERSION, nomi e hash nel plugin. Il checksum scaricabile
viene generato dai metadati del plugin.

## Assegnazione degli account

Creare due utenti normali CTFd, per esempio team1 e team2.
Annotare gli ID numerici dalle rispettive pagine amministrative.

Nel file locale `/srv/girello/secrets/ctfd.env` impostare:

```dotenv
GIRELLO_VM_TEAM1_USER_ID=ID_UTENTE_TEAM1
GIRELLO_VM_TEAM2_USER_ID=ID_UTENTE_TEAM2
```

Sostituire i segnaposto con ID numerici distinti. Il valore 0 disabilita
la relativa assegnazione. Conservare le altre variabili già presenti.

Non occorre cambiare la modalità utenti di CTFd. Gli account del portale
sono distinti dagli accessi Linux delle VM e dagli account ForcAD.

## Installazione sul Master

Dalla radice della repository:

1. Rendere le OVA leggibili dall'utente www-data e verificare i permessi
   di attraversamento delle directory superiori.
2. Installare `common/nginx/vm-downloads.conf` come
   `/etc/nginx/snippets/girello-vm-downloads.conf`.
3. Installare `common/nginx/ctfd-local.conf` come
   `/etc/nginx/sites-available/girello-ctfd-local.conf`.
4. Eseguire `sudo nginx -t` e ricaricare Nginx.
5. Verificare e applicare il Compose:

```bash
sudo docker compose --env-file /srv/girello/secrets/ctfd.env \
  -f common/compose.yaml config --quiet

sudo docker compose --env-file /srv/girello/secrets/ctfd.env \
  -f common/compose.yaml up -d --no-deps --no-build --pull never \
  --wait --wait-timeout 120 ctfd
```

Database e Redis devono essere già attivi.
Il cambio alla modalità A&D installerà il relativo profilo Nginx aggiornato.

## Accesso e verifiche

La pagina è `/girello/vm`; gli endpoint sono `/girello/vm/download`
e `/girello/vm/checksum`.

- Senza autenticazione viene richiesto il login.
- Ogni account assegnato vede e scarica la propria VM.
- Account non assegnati, bannati o amministrativi non ricevono una VM.
- Gli accessi HTTP diretti a `/_girello_vm/` sono negati.
- Nginx trasferisce i file statici e supporta le richieste Range.

Durante la prova generale, ciascun PC scarica OVA e checksum dal portale,
verifica il checksum e importa la VM. La scheda in bridge va associata
alla Ethernet collegata al segmento della propria squadra.
Le VM originali sul Master rimangono spente.

## Identificativi pubblici di gara

La pagina delle VM include il collegamento al feed ForcAD
`/api/client/attack_data/`, accessibile durante l'esercitazione.

| Squadra | Ingresso ForcAD | Bersaglio avversario nel feed |
| --- | --- | --- |
| Team 1 | http://10.77.1.2:8080 | 10.77.1.3 |
| Team 2 | http://10.77.2.2:8080 | 10.77.2.3 |

Document Vault pubblica owner_id e document_id.
HelpDesk pubblica owner_id e ticket_id.
Gli identificativi appartengono ai rispettivi servizi.
Il feed contiene tutte le squadre e conserva ciascuna coppia
di identificativi come stringa JSON nell'elenco del bersaglio.

Gli identificativi diventano disponibili dopo il deposito riuscito
del checker. Aggiorna la pagina per consultarli. Il feed contiene
i depositi del round corrente e dei due precedenti; una flag può
scadere se cambia il round tra la consultazione e l'invio.

Consultando CTFd sul Master tramite `127.0.0.1` o `localhost`,
il pulsante degli identificativi apre il feed locale su
`http://127.0.0.1:18080/api/client/attack_data/`.
Dai portali dei segmenti A&D usa l'ingresso ForcAD della squadra.
ForcAD deve essere avviato; le VM delle squadre possono restare spente
per consultare i depositi già conservati nel database.
