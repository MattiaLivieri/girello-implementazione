#!/usr/bin/env bash
# Filtro del Master per Jeopardy. Non configura indirizzi o servizi.
# Applicare e rimuovere fuori sessione, con entrambe le Ethernet scollegate.
set -Eeuo pipefail
trap 'printf "Errore alla riga %s: operazione interrotta; il filtro potrebbe essere incompleto.\n" "$LINENO" >&2' ERR

if (( EUID != 0 || $# != 1 )) || [[ $1 != apply && $1 != remove ]]; then
    printf 'Uso: sudo %s apply|remove\n' "$0" >&2
    exit 2
fi
azione=$1

# Valori del profilo statico Jeopardy.
interfaccia_lab=enp1s0
interfaccia_inattiva=enp2s0
rete_lab=10.77.10.0/24
ip_master=10.77.10.2

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

# Aggiunge lo stesso tipo di messaggio ICMP nei due versi, solo nella rete lab.
consenti_icmp() {
    local tipo=$1 stati=$2

    iptables-nft -w 5 -A GIRELLO-IN -i "$interfaccia_lab" \
        -s "$rete_lab" -d "$ip_master" -p icmp --icmp-type "$tipo" \
        -m conntrack --ctstate "$stati" -j RETURN
    iptables-nft -w 5 -A GIRELLO-OUT -o "$interfaccia_lab" \
        -s "$ip_master" -d "$rete_lab" -p icmp --icmp-type "$tipo" \
        -m conntrack --ctstate "$stati" -j RETURN
}

# Prima di modificare le regole, verifica l'accesso a entrambi i filtri.
# I comandi espliciti *-nft selezionano il backend adottato sul Master.
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
    rimuovi_catena "$comando" INPUT GIRELLO-IN
    rimuovi_catena "$comando" OUTPUT GIRELLO-OUT
    rimuovi_catena "$comando" DOCKER-USER GIRELLO-FWD
done

if [[ $azione == remove ]]; then
    printf 'Filtro Jeopardy rimosso.\n'
    exit 0
fi

# Prepara le catene prima di collegarle al traffico dell'host e di Docker.
for comando in iptables-nft ip6tables-nft; do
    "$comando" -w 5 -N GIRELLO-IN
    "$comando" -w 5 -N GIRELLO-OUT
    "$comando" -w 5 -N GIRELLO-FWD
done

# Richieste HTTP dei partecipanti verso Nginx sul Master.
# RETURN prosegue nelle regole dell'host: non le scavalca con un ACCEPT.
iptables-nft -w 5 -A GIRELLO-IN -i "$interfaccia_lab" \
    -s "$rete_lab" -d "$ip_master" -p tcp --dport 80 \
    -m conntrack --ctstate NEW,ESTABLISHED -j RETURN

# Risposte HTTP. REPLY esclude connessioni iniziate dal Master usando porta 80.
iptables-nft -w 5 -A GIRELLO-OUT -o "$interfaccia_lab" \
    -s "$ip_master" -d "$rete_lab" -p tcp --sport 80 \
    -m conntrack --ctstate ESTABLISHED --ctdir REPLY -j RETURN

# Ping e messaggi di errore relativi a comunicazioni tracciate.
consenti_icmp echo-request NEW,ESTABLISHED
consenti_icmp echo-reply ESTABLISHED
consenti_icmp destination-unreachable RELATED
consenti_icmp time-exceeded RELATED
consenti_icmp parameter-problem RELATED

# Blocca il resto del traffico sulle due Ethernet, incluso l'inoltro ai container.
# Per IPv6 non sono previste eccezioni: il laboratorio utilizza IPv4.
for comando in iptables-nft ip6tables-nft; do
    for interfaccia in "$interfaccia_lab" "$interfaccia_inattiva"; do
        "$comando" -w 5 -A GIRELLO-IN -i "$interfaccia" -j DROP
        "$comando" -w 5 -A GIRELLO-OUT -o "$interfaccia" -j DROP
        "$comando" -w 5 -A GIRELLO-FWD -i "$interfaccia" -j DROP
        "$comando" -w 5 -A GIRELLO-FWD -o "$interfaccia" -j DROP
    done

    # Le altre interfacce proseguono nelle regole esistenti.
    # Restano quindi disponibili loopback e comunicazioni interne dei container.
    "$comando" -w 5 -A GIRELLO-IN -j RETURN
    "$comando" -w 5 -A GIRELLO-OUT -j RETURN
    "$comando" -w 5 -A GIRELLO-FWD -j RETURN
done

# Inserisce i collegamenti in testa, prima di eventuali regole gia' permissive.
for comando in iptables-nft ip6tables-nft; do
    "$comando" -w 5 -I INPUT 1 -j GIRELLO-IN
    "$comando" -w 5 -I OUTPUT 1 -j GIRELLO-OUT
    "$comando" -w 5 -I DOCKER-USER 1 -j GIRELLO-FWD
done

printf 'Filtro Jeopardy applicato a IPv4 e IPv6.\n'
