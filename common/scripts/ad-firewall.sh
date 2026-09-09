#!/usr/bin/env bash
# Filtro del Master per Attack & Defense. Non configura indirizzi o servizi.
# Applicare e rimuovere fuori sessione, con entrambe le Ethernet scollegate.
set -Eeuo pipefail
trap 'printf "Errore alla riga %s: operazione interrotta; il filtro potrebbe essere incompleto.\n" "$LINENO" >&2' ERR

if (( EUID != 0 || $# != 1 )) || [[ $1 != apply && $1 != remove ]]; then
    printf 'Uso: sudo %s apply|remove\n' "$0" >&2
    exit 2
fi
azione=$1

# Porte dei servizi vulnerabili e accesso del worker che esegue i checker.
porte_servizi=8081,8082
bridge_ad=br-girello-ad
ip_checker=172.30.20.3

# Scollega e cancella una sola catena di Girello, se presente.
# Non svuota le catene dell'host o di Docker e non cambia le loro politiche.
rimuovi_catena() {
    local comando=$1 catena_base=$2 catena_girello=$3

    while "$comando" -w 5 -C "$catena_base" -j "$catena_girello" 2>/dev/null; do
        "$comando" -w 5 -D "$catena_base" -j "$catena_girello"
    done
    if "$comando" -w 5 -S "$catena_girello" >/dev/null 2>&1; then
        "$comando" -w 5 -F "$catena_girello"
        "$comando" -w 5 -X "$catena_girello"
    fi
}

# Consente le richieste del team a un ingresso del Master e le relative risposte.
# RETURN prosegue nelle regole dell'host: non le scavalca con un ACCEPT.
consenti_accesso() {
    local interfaccia=$1 rete=$2 ip_servizio=$3 porte=$4

    iptables-nft -w 5 -A GIRELLO-AD-IN -i "$interfaccia" \
        -s "$rete" -d "$ip_servizio" -p tcp -m multiport --dports "$porte" \
        -m conntrack --ctstate NEW,ESTABLISHED --ctdir ORIGINAL -j RETURN
    iptables-nft -w 5 -A GIRELLO-AD-OUT -o "$interfaccia" \
        -s "$ip_servizio" -d "$rete" -p tcp -m multiport --sports "$porte" \
        -m conntrack --ctstate ESTABLISHED --ctdir REPLY -j RETURN
}

# Applica le stesse regole ai due segmenti, usando i rispettivi indirizzi.
configura_segmento() {
    local interfaccia=$1 rete=$2 ip_ctfd=$3
    local ip_gara=$4 ip_proxy=$5 ip_vm=$6

    # Ingressi del team: portale, applicazione A&D e servizi avversari via proxy.
    consenti_accesso "$interfaccia" "$rete" "$ip_ctfd" 80
    consenti_accesso "$interfaccia" "$rete" "$ip_gara" 8080
    consenti_accesso "$interfaccia" "$rete" "$ip_proxy" "$porte_servizi"

    # Nginx apre verso questa VM la connessione proveniente dal proxy opposto.
    # L'utente www-data e l'IP sorgente corrispondono ai worker e a proxy_bind.
    iptables-nft -w 5 -A GIRELLO-AD-OUT -o "$interfaccia" \
        -s "$ip_ctfd" -d "$ip_vm" -p tcp -m multiport --dports "$porte_servizi" \
        -m owner --uid-owner "$uid_nginx" \
        -m conntrack --ctstate NEW,ESTABLISHED --ctdir ORIGINAL -j RETURN

    # La VM puo' rispondere alle connessioni aperte dal Master su quelle porte.
    iptables-nft -w 5 -A GIRELLO-AD-IN -i "$interfaccia" \
        -s "$ip_vm" -d "$ip_ctfd" -p tcp -m multiport --sports "$porte_servizi" \
        -m conntrack --ctstate ESTABLISHED --ctdir REPLY -j RETURN

    # Il worker raggiunge i proxy dal bridge Docker di A&D.
    iptables-nft -w 5 -A GIRELLO-AD-IN -i "$bridge_ad" \
        -s "$ip_checker" -d "$ip_proxy" -p tcp -m multiport --dports "$porte_servizi" \
        -m conntrack --ctstate NEW,ESTABLISHED --ctdir ORIGINAL -j RETURN

    # ICMP solo per errori relativi a comunicazioni tracciate; non abilita il ping.
    iptables-nft -w 5 -A GIRELLO-AD-IN -i "$interfaccia" \
        -d "$ip_ctfd" -p icmp -m conntrack --ctstate RELATED -j RETURN
    iptables-nft -w 5 -A GIRELLO-AD-OUT -o "$interfaccia" \
        -d "$rete" -p icmp -m conntrack --ctstate RELATED -j RETURN
}

# Serve per il controllo dell'utente che apre le connessioni verso le VM.
# La rimozione del filtro non dipende dalla presenza dell'utente Nginx.
if [[ $azione == apply ]]; then
    uid_nginx=$(id -u www-data)
fi

# Prima di modificare le regole, verifica l'accesso a entrambi i filtri.
for comando in iptables-nft ip6tables-nft; do
    "$comando" -w 5 -S >/dev/null

    if [[ $azione == apply ]]; then
        # In -S FORWARD la prima riga e' la politica, la seconda la prima regola.
        # DOCKER-USER deve essere attraversata prima delle autorizzazioni Docker.
        if [[ $("$comando" -w 5 -S FORWARD | sed -n '2p') != '-A FORWARD -j DOCKER-USER' ]]; then
            printf '%s: DOCKER-USER deve essere la prima regola di FORWARD.\n' "$comando" >&2
            exit 1
        fi
    fi
done

# Rimuove una precedente applicazione, senza lasciare collegamenti duplicati.
for comando in iptables-nft ip6tables-nft; do
    rimuovi_catena "$comando" INPUT GIRELLO-AD-IN
    rimuovi_catena "$comando" OUTPUT GIRELLO-AD-OUT
    rimuovi_catena "$comando" DOCKER-USER GIRELLO-AD-FWD
done

if [[ $azione == remove ]]; then
    printf 'Filtro A&D rimosso.\n'
    exit 0
fi

# Prepara le catene prima di collegarle al traffico dell'host e di Docker.
for comando in iptables-nft ip6tables-nft; do
    "$comando" -w 5 -N GIRELLO-AD-IN
    "$comando" -w 5 -N GIRELLO-AD-OUT
    "$comando" -w 5 -N GIRELLO-AD-FWD
done

# Parametri: interfaccia, rete, IP CTFd, IP applicazione, IP proxy, IP VM.
configura_segmento enp1s0 10.77.1.0/24 10.77.1.1 10.77.1.2 10.77.1.3 10.77.1.10
configura_segmento enp2s0 10.77.2.0/24 10.77.2.1 10.77.2.2 10.77.2.3 10.77.2.10

# Blocca gli altri accessi sulle Ethernet e l'inoltro che le attraversa.
# Il proxy funziona tramite INPUT e OUTPUT, senza richiedere un'apertura FORWARD.
# Per IPv6 non sono previste eccezioni: il laboratorio utilizza IPv4.
for comando in iptables-nft ip6tables-nft; do
    for interfaccia in enp1s0 enp2s0; do
        "$comando" -w 5 -A GIRELLO-AD-IN -i "$interfaccia" -j DROP
        "$comando" -w 5 -A GIRELLO-AD-OUT -o "$interfaccia" -j DROP
        "$comando" -w 5 -A GIRELLO-AD-FWD -i "$interfaccia" -j DROP
        "$comando" -w 5 -A GIRELLO-AD-FWD -o "$interfaccia" -j DROP
    done
done

# Conserva gli accessi locali del Master. Dagli altri percorsi, inclusi i bridge
# Docker, gli IP di gara restano chiusi salvo le eccezioni dei checker gia' inserite.
iptables-nft -w 5 -A GIRELLO-AD-IN -i lo -j RETURN
for ip in 10.77.1.1 10.77.2.1 \
          10.77.1.2 10.77.2.2 \
          10.77.1.3 10.77.2.3; do
    iptables-nft -w 5 -A GIRELLO-AD-IN -d "$ip" -j DROP
done

# Il traffico non interessato dai blocchi prosegue nelle regole esistenti.
for comando in iptables-nft ip6tables-nft; do
    "$comando" -w 5 -A GIRELLO-AD-IN -j RETURN
    "$comando" -w 5 -A GIRELLO-AD-OUT -j RETURN
    "$comando" -w 5 -A GIRELLO-AD-FWD -j RETURN
done

# Inserisce i collegamenti in testa, prima di eventuali regole gia' permissive.
for comando in iptables-nft ip6tables-nft; do
    "$comando" -w 5 -I INPUT 1 -j GIRELLO-AD-IN
    "$comando" -w 5 -I OUTPUT 1 -j GIRELLO-AD-OUT
    "$comando" -w 5 -I DOCKER-USER 1 -j GIRELLO-AD-FWD
done

printf 'Filtro A&D applicato a IPv4 e IPv6.\n'
