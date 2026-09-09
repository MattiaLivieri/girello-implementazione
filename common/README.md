# Infrastruttura comune di Girello

Questa directory contiene i servizi del portale e le configurazioni con cui il
Master gestisce le reti Jeopardy e Attack & Defense. Gli ambienti delle
esercitazioni vengono eseguiti sulle postazioni dei partecipanti.

## File e responsabilità

I collegamenti seguenti sono relativi a questa directory del repository.

| File o directory | Funzione |
| --- | --- |
| [compose.yaml](compose.yaml) | Esegue CTFd, MariaDB e Redis, definendo reti, dati persistenti e controlli di disponibilità. |
| [config/](config/) | Contiene i modelli dei file con le credenziali del portale e la configurazione Redis. |
| [network/](network/) | Contiene i profili statici delle due Ethernet per `default`, `jeopardy` e `ad`. |
| [nginx/ctfd-local.conf](nginx/ctfd-local.conf) | Rende CTFd accessibile dal Master attraverso `127.0.0.1:80`. |
| [nginx/jeopardy.http.conf](nginx/jeopardy.http.conf) | Apre l'accesso al portale sulla rete Jeopardy. |
| [nginx/ad.http.conf](nginx/ad.http.conf) e [nginx/ad.stream.conf](nginx/ad.stream.conf) | Definiscono gli ingressi HTTP e i proxy TCP della modalità A&D. |
| [scripts/girello-mode.sh](scripts/girello-mode.sh) | Coordina cambio di rete, applicazione del firewall e selezione degli ingressi Nginx. |
| [scripts/jeopardy-firewall.sh](scripts/jeopardy-firewall.sh) | Applica o rimuove il filtro del Master per Jeopardy. |
| [scripts/ad-firewall.sh](scripts/ad-firewall.sh) | Applica o rimuove il filtro del Master per A&D. |

## Ambiente di riferimento

La configurazione riguarda un ODROID H4+ con Debian 13, architettura amd64 e due
porte Ethernet. Il repository è collocato in:

```text
/home/debian/girello-implementazione
```

Sono necessari Docker Engine con Compose, Nginx con il modulo `stream`,
NetworkManager, systemd-networkd, iptables-nft, ip6tables-nft, curl e OpenSSL.
Lo script utilizza anche `ip`, `sysctl` e `flock`, forniti rispettivamente da
iproute2, procps e util-linux.

La prima Ethernet deve avere una connessione ordinaria già configurata in
NetworkManager. I riferimenti adottati nei file sono:

| Parametro | Valore |
| --- | --- |
| Prima Ethernet | `enp1s0`, MAC `00:1e:06:45:a4:84` |
| Seconda Ethernet | `enp2s0`, MAC `00:1e:06:45:a4:85` |
| UUID della connessione ordinaria | `7303acd9-c1e2-4d71-a9ba-31fdc0f8bfd9` |

Su un altro Master occorre adattare nomi e MAC nei profili di rete, i riferimenti
alle interfacce negli script e `connessione_default` in `girello-mode.sh`.
Un cambio degli indirizzi richiede di aggiornare coerentemente profili di rete,
firewall, Nginx e configurazione delle postazioni. Le reti Docker definite nel
Compose devono rimanere distinte dalle reti del laboratorio.

## Preparazione iniziale del Master

Questa procedura serve per predisporre un Master nuovo, dalla sua console locale,
con accesso alla rete ordinaria. Sul Master già configurato si passa direttamente
alla sezione «Uso dei profili». Le credenziali esistenti vanno conservate quando
si riutilizzano i dati del portale.

I comandi con percorsi relativi si eseguono dalla radice del repository:

```bash
cd /home/debian/girello-implementazione
```

### 1. Dipendenze

Installare Docker Engine e il plugin Compose seguendo le
[istruzioni ufficiali per Debian](https://docs.docker.com/engine/install/debian/).
Installare inoltre i componenti mancanti:

```bash
sudo apt update
sudo apt install nginx libnginx-mod-stream iptables curl openssl
sudo systemctl enable --now docker.service
```

Docker deve usare il backend iptables, compatibile con i comandi `*-nft` adottati
dagli script. Dopo l'avvio di Docker, controllare entrambe le famiglie:

```bash
sudo iptables-nft -S FORWARD
sudo ip6tables-nft -S FORWARD
```

In entrambi gli output, la prima regola dopo la politica della catena deve essere
`-A FORWARD -j DOCKER-USER`. Gli script richiedono questa disposizione per
filtrare il traffico prima delle autorizzazioni di Docker. Se manca, occorre
verificare la configurazione di Docker prima di attivare i profili.
Il ruolo della catena è descritto nella
[documentazione Docker](https://docs.docker.com/engine/network/firewall-iptables/).

### 2. Dati, credenziali e container

Creare le directory persistenti. Per l'immagine CTFd fissata nel Compose,
le directory degli allegati e dei log appartengono all'utente `1001:1001`.

```bash
sudo install -d -m 0700 /srv/girello/secrets
sudo install -d -m 0750 /srv/girello/ctfd
sudo mkdir -p /srv/girello/ctfd/db /srv/girello/ctfd/redis
sudo install -d -o 1001 -g 1001 -m 0750 \
  /srv/girello/ctfd/uploads \
  /srv/girello/ctfd/logs
```

Soltanto per la prima installazione, generare quattro valori distinti eseguendo
quattro volte:

```bash
openssl rand -hex 32
```

Copiare e compilare i modelli:

```bash
sudo install -m 0600 common/config/ctfd.env.example /srv/girello/secrets/ctfd.env
sudo install -m 0600 common/config/redis.conf.example /srv/girello/secrets/redis.conf

sudo nano /srv/girello/secrets/ctfd.env
sudo nano /srv/girello/secrets/redis.conf
```

Inserire i valori nelle quattro variabili di `ctfd.env`. In `redis.conf`,
sostituire `INSERIRE_LA_PASSWORD_REDIS` con lo stesso valore assegnato a
`CTFD_REDIS_PASSWORD`. Redis legge una password letterale e non espande
variabili di ambiente nel proprio file di configurazione.

Rendere il file Redis leggibile dal processo nel container. La directory
`secrets`, con permessi `0700`, ne limita l'accesso dal filesystem del Master.

```bash
sudo chmod 0444 /srv/girello/secrets/redis.conf
```

Verificare il Compose senza stampare le credenziali, scaricare le immagini
durante la preparazione online e avviare i servizi:

```bash
sudo docker compose \
  --env-file /srv/girello/secrets/ctfd.env \
  -f common/compose.yaml config --quiet

sudo docker compose \
  --env-file /srv/girello/secrets/ctfd.env \
  -f common/compose.yaml pull --policy always

sudo docker compose \
  --env-file /srv/girello/secrets/ctfd.env \
  -f common/compose.yaml up --wait --wait-timeout 180
```

Il download esplicito prepara le immagini fissate nel Compose. Nei successivi
avvii, `pull_policy: never` richiede che siano già disponibili sul Master.
CTFd attende che MariaDB e Redis superino i rispettivi controlli di disponibilità.

### 3. Collegamenti per la gestione della rete

Installare i profili permanenti che lasciano le Ethernet a NetworkManager:

```bash
sudo install -d -m 0755 \
  /etc/systemd/network \
  /etc/systemd/networkd.conf.d

sudo install -m 0644 \
  common/network/default/10-girello-enp1s0.network \
  common/network/default/10-girello-enp2s0.network \
  /etc/systemd/network/
```

Aggiungere una regola generale affinché networkd lasci non gestite le altre
interfacce, comprese quelle create da Docker:

```bash
sudo tee /etc/systemd/network/20-girello-unmanaged.network >/dev/null <<'EOF'
# Lascia non gestite le interfacce senza un profilo precedente applicabile.
[Match]
Name=*

[Link]
Unmanaged=yes
EOF
```

Impedire a networkd di rimuovere le impostazioni di instradamento create dagli
altri componenti:

```bash
sudo tee /etc/systemd/networkd.conf.d/90-girello.conf >/dev/null <<'EOF'
# Conserva le impostazioni di instradamento create dagli altri componenti.
[Network]
ManageForeignRoutes=no
ManageForeignRoutingPolicyRules=no
ManageForeignNextHops=no
EOF
```

Durante il cambio di profilo, `girello-mode.sh` copia i file dell'esercitazione
in `/run/systemd/network/` con prefisso `05`, così precedono quelli permanenti
con prefisso `10`. Lo script gestisce anche il file
`/etc/NetworkManager/conf.d/90-girello-lab.conf`, che esclude temporaneamente le
due Ethernet dalla gestione di NetworkManager. Questi file vengono gestiti
dal comando di cambio profilo.

### 4. Collegamenti Nginx

Installare l'accesso locale a CTFd:

```bash
sudo install -m 0644 \
  common/nginx/ctfd-local.conf \
  /etc/nginx/sites-available/girello-ctfd-local.conf

sudo ln -sfn \
  /etc/nginx/sites-available/girello-ctfd-local.conf \
  /etc/nginx/sites-enabled/girello-ctfd-local.conf

sudo rm -f /etc/nginx/sites-enabled/default
sudo install -d -m 0755 /run/girello/nginx
```

La rimozione del collegamento `default` disattiva il sito predefinito di Debian,
che ascolterebbe anche sugli indirizzi esterni. Nella configurazione dedicata a
Girello, gli accessi dei partecipanti sono definiti dai profili.

Aggiungere l'inclusione dei profili HTTP nel percorso letto dal blocco `http`
della configurazione Debian:

```bash
printf '%s\n' 'include /run/girello/nginx/*.http.conf;' |
  sudo tee /etc/nginx/conf.d/90-girello-mode.conf >/dev/null
```

Aprire `/etc/nginx/nginx.conf` e aggiungere una sola volta la seguente riga
nel contesto principale, fuori dal blocco `http`:

```nginx
include /run/girello/nginx/*.main.conf;
```

Questa seconda inclusione serve al blocco `stream` della modalità A&D.
Conservare le inclusioni standard di `conf.d` e `sites-enabled` nel blocco `http`.
Mantenere anche l'utente Nginx `www-data`, utilizzato dal filtro A&D per
autorizzare le connessioni dei proxy verso le VM.
Quindi verificare e attivare Nginx:

```bash
sudo systemctl enable nginx.service
sudo nginx -t && sudo systemctl restart nginx.service
```

Dal browser del Master, aprire `http://127.0.0.1/` e completare la configurazione
iniziale di CTFd con l'account amministrativo. Il backend del portale rimane
pubblicato su `127.0.0.1:18000`; database e cache non pubblicano porte sull'host.

### 5. Comando di cambio profilo e servizio al riavvio

Rendere eseguibili i tre script e predisporre il comando `girello-mode`:

```bash
chmod +x common/scripts/girello-mode.sh \
  common/scripts/jeopardy-firewall.sh \
  common/scripts/ad-firewall.sh

sudo tee /usr/local/sbin/girello-mode >/dev/null <<'EOF'
#!/usr/bin/env bash
exec /home/debian/girello-implementazione/common/scripts/girello-mode.sh "$@"
EOF

sudo chmod 0755 /usr/local/sbin/girello-mode
```

Il comando richiama direttamente lo script nel repository. Se cambia il percorso
del checkout, occorre aggiornare questo collegamento.

Creare il servizio che sospende la rete del laboratorio al riavvio:

```bash
sudo tee /etc/systemd/system/girello-network-boot.service >/dev/null <<'EOF'
[Unit]
Description=Girello - sospensione della rete di gara al riavvio
DefaultDependencies=no
After=local-fs.target systemd-udev-trigger.service
Before=network-pre.target NetworkManager.service systemd-networkd.service nginx.service docker.service
ConditionPathExists=/etc/NetworkManager/conf.d/90-girello-lab.conf

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/girello-mode boot
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable girello-network-boot.service
```

Il servizio viene abilitato per i successivi avvii. Il parametro `boot` è
riservato al servizio e non fa parte dei comandi ordinari dell'organizzatore.

## Uso dei profili

Eseguire il cambio fuori sessione, dalla console locale del Master. Lo script
chiede di scollegare entrambe le Ethernet prima di proseguire e indica quando
ricollegarle. Durante l'operazione chiude gli accessi Nginx; i container del
portale rimangono in esecuzione.

| Comando | Collegamenti da predisporre quando richiesto |
| --- | --- |
| `sudo girello-mode default` | Prima Ethernet alla rete ordinaria; seconda libera. |
| `sudo girello-mode jeopardy` | Prima Ethernet a una porta LAN del router Jeopardy, con WAN scollegata; seconda libera. |
| `sudo girello-mode ad` | Prima Ethernet al segmento del Team 1; seconda al segmento del Team 2. Router Jeopardy scollegato dal Master. |

Nel profilo `default`, NetworkManager ripristina la connessione ordinaria e
CTFd è accessibile soltanto dal Master. Nei profili di esercitazione, le
Ethernet usano indirizzi statici, senza una route predefinita né IPv6.

### Jeopardy

Il Master usa `10.77.10.2/24` sulla prima Ethernet. I partecipanti raggiungono
il portale all'indirizzo `http://10.77.10.2/` dalla rete Wi-Fi del laboratorio.

Il router TP-Link Archer AX72 Pro va configurato con:

- LAN `10.77.10.1/24` e DHCP per i client, escludendo l'indirizzo del Master;
- rete ospiti protetta da password;
- comunicazione tra client ospiti disabilitata;
- accesso dei client ospiti alla LAN abilitato, per raggiungere il Master;
- WAN fisicamente scollegata durante l'esercitazione.

La rete cablata è dedicata al Master e agli eventuali dispositivi amministrativi
autorizzati. L'isolamento fra partecipanti dipende dalle impostazioni del router;
il firewall del Master controlla il traffico che attraversa il Master stesso.

### Attack & Defense

Il Master usa `10.77.1.1`, `10.77.1.2` e `10.77.1.3` sulla prima Ethernet, e
`10.77.2.1`, `10.77.2.2` e `10.77.2.3` sulla seconda, tutti con prefisso `/24`.

| Postazione | Indirizzo | Gateway | Portale CTFd |
| --- | --- | --- | --- |
| Team 1 | `10.77.1.20/24` | `10.77.1.1` | `http://10.77.1.1/` |
| Team 2 | `10.77.2.20/24` | `10.77.2.1` | `http://10.77.2.1/` |

Gli indirizzi `.2:8080` inoltrano le richieste all'applicazione A&D attesa su
`127.0.0.1:18080`. L'accesso ai servizi avversari passa invece attraverso i proxy:

| Ingresso utilizzato | Destinazione sulle stesse porte |
| --- | --- |
| Team 1: `10.77.1.3:8081` e `10.77.1.3:8082` | VM del Team 2: `10.77.2.10` |
| Team 2: `10.77.2.3:8081` e `10.77.2.3:8082` | VM del Team 1: `10.77.1.10` |

Questi ingressi richiedono che i rispettivi servizi siano in esecuzione;
il loro avvio è gestito dalla componente A&D.

Il cambio profilo coordina rete, filtro e ingressi Nginx. Account, challenge e
regole della sessione vengono configurati separatamente nel portale e nelle
componenti delle esercitazioni.

### Riavvio e cambio interrotto

Se il Master viene riavviato da un profilo di laboratorio, il servizio di avvio
lascia entrambe le Ethernet disattivate e registra `sospeso` in
`/run/girello/mode`. Nginx mantiene soltanto l'accesso locale. Per riprendere,
selezionare esplicitamente un profilo dalla console con `girello-mode`.

Se un cambio si interrompe, lo script segnala il punto dell'errore. Correggere
il problema dalla console e ripetere il comando, seguendo le indicazioni sui
cavi. Il ritorno al profilo precedente richiede un comando esplicito.

## Dati e configurazioni sul Master

| Percorso | Contenuto |
| --- | --- |
| `/srv/girello/secrets/` | Credenziali effettive e configurazione Redis; rimangono fuori dal repository. |
| `/srv/girello/ctfd/` | Database, dati Redis, allegati e log persistenti del portale. |
| `/var/lib/girello/network/sysctl.conf` | Parametri delle Ethernet conservati dallo script per ripristinare la connessione ordinaria. |
| `/run/girello/` e `/run/systemd/network/05-girello-*.network` | Stato e configurazioni temporanee del profilo; scompaiono al riavvio. |

I file statici del profilo vengono copiati dal repository a ogni cambio di
modalità. L'accesso locale `ctfd-local.conf` è invece installato in `/etc/nginx`:
dopo averlo modificato, ripetere la relativa copia e verificare Nginx prima del
riavvio del servizio.

## Controlli essenziali

Dopo un cambio completato, verificare sul Master:

```bash
cat /run/girello/mode
ip -br address show dev enp1s0
ip -br address show dev enp2s0
ip -4 route show default
sudo ss -ltnp | grep nginx

curl --noproxy '*' --fail --silent --show-error \
  --max-time 10 --output /dev/null \
  --write-out 'HTTP %{http_code}\n' http://127.0.0.1/
```

Il profilo registrato deve corrispondere alla scelta effettuata. Gli indirizzi
devono corrispondere alla modalità e i listener Nginx agli ingressi previsti.
In Jeopardy e A&D il comando sulle route predefinite non deve mostrare risultati.
Le porte Ethernet possono risultare `DOWN` finché i cavi non sono collegati.

Dalle postazioni, aprire il portale previsto per la modalità. Per controllare
un accesso che deve rimanere bloccato, provare la porta `18000` sull'indirizzo
del Master: la richiesta non deve raggiungere il backend. Ad esempio, da un
partecipante Jeopardy:

```bash
curl --noproxy '*' --connect-timeout 3 --max-time 5 http://10.77.10.2:18000/
```

La raggiungibilità dei proxy A&D va verificata con i servizi delle VM attivi.
L'ascolto di Nginx sulla porta del proxy, da solo, non conferma il collegamento
al servizio di destinazione.

Per controllare la sospensione al riavvio, riavviare il Master fuori sessione
partendo da `jeopardy` o `ad`, poi verificare dalla console:

```bash
cat /run/girello/mode
ip -br address show dev enp1s0
ip -br address show dev enp2s0
sudo ss -ltnp | grep nginx
systemctl show girello-network-boot.service -p Result -p ExecMainStatus
```

Sono attesi `sospeso`, entrambe le Ethernet senza indirizzi, il solo ingresso
Nginx `127.0.0.1:80`, `Result=success` ed `ExecMainStatus=0`.
Infine, `sudo girello-mode default` deve ripristinare la connessione ordinaria.
Un avvio effettuato già in modalità ordinaria può lasciare assente
`/run/girello/mode`, perché il servizio di sospensione non deve intervenire.
