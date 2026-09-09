#!/usr/bin/env bash
# Cambia rete, firewall e ingressi Nginx dalla console locale del Master.
# Usare fuori sessione, scollegando le Ethernet quando richiesto.
# I container del portale restano in esecuzione durante il cambio.
set -Eeuo pipefail
umask 022
trap 'printf "Cambio interrotto alla riga %s. Correggere dalla console e ripetere il comando.\n" "$LINENO" >&2' ERR
trap 'exit 130' INT
trap 'exit 143' TERM

if (( EUID != 0 || $# != 1 )); then
    printf 'Uso: sudo %s default|jeopardy|ad\n' "$0" >&2
    exit 2
fi
profilo=$1
case "$profilo" in
    default|jeopardy|ad|boot) ;;
    *) printf 'Profilo sconosciuto: %s\n' "$profilo" >&2; exit 2 ;;
esac

# Percorsi comuni e connessione ordinaria gia' configurata in NetworkManager.
cartella_common=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
script_dir=$cartella_common/scripts
rete_dir=/run/systemd/network
nginx_dir=/run/girello/nginx
nm_config=/etc/NetworkManager/conf.d/90-girello-lab.conf
parametri_default=/var/lib/girello/network/sysctl.conf
connessione_default=7303acd9-c1e2-4d71-a9ba-31fdc0f8bfd9

# 1. Conserva i parametri che networkd puo' modificare sulle due Ethernet.
# La copia viene aggiornata solo partendo dalla gestione ordinaria.
salva_parametri_default() {
    local interfaccia parametro
    local chiavi=()

    for interfaccia in enp1s0 enp2s0; do
        for parametro in forwarding promote_secondaries; do
            chiavi+=("net.ipv4.conf.$interfaccia.$parametro")
        done
        for parametro in forwarding accept_ra autoconf use_tempaddr \
                         accept_redirects dad_transmits hop_limit \
                         addr_gen_mode disable_ipv6; do
            chiavi+=("net.ipv6.conf.$interfaccia.$parametro")
        done
    done

    install -d -m 0700 /var/lib/girello/network
    sysctl "${chiavi[@]}" > "$parametri_default.new"
    mv "$parametri_default.new" "$parametri_default"
}

# 2. Chiude gli accessi e libera le Ethernet dalla configurazione precedente.
sospendi_rete() {
    local interfaccia

    # TERM chiude anche le connessioni persistenti, come gli eventi di CTFd.
    if systemctl is-active --quiet nginx.service; then
        systemctl kill --kill-whom=all --signal=TERM nginx.service
    fi
    systemctl stop nginx.service

    # NetworkManager deve ignorare le porte prima della pulizia degli indirizzi.
    install -d -m 0755 /etc/NetworkManager/conf.d
    cat > "$nm_config" <<'CONFIG'
[keyfile]
unmanaged-devices+=interface-name:enp1s0;interface-name:enp2s0
CONFIG
    nmcli general reload conf

    # Il socket va fermato insieme al servizio per impedirne la riattivazione.
    systemctl stop systemd-networkd.service systemd-networkd.socket

    # La pulizia riguarda soltanto le due Ethernet del Master.
    for interfaccia in enp1s0 enp2s0; do
        ip link set dev "$interfaccia" down
        rm -f "$rete_dir/05-girello-$interfaccia.network"
        ip -4 address flush dev "$interfaccia"
        ip -6 address flush dev "$interfaccia"
        ip -4 route flush table all dev "$interfaccia"
        ip -6 route flush table all dev "$interfaccia"
    done

    # Ogni firewall elimina soltanto le proprie catene.
    "$script_dir/jeopardy-firewall.sh" remove
    "$script_dir/ad-firewall.sh" remove
}

# 3a. Affida le Ethernet a networkd e applica il filtro dell'esercitazione.
attiva_laboratorio() {
    local interfaccia

    for interfaccia in enp1s0 enp2s0; do
        sysctl -q -w "net.ipv6.conf.$interfaccia.disable_ipv6=1"

        # Copia il file statico senza modificarne il contenuto.
        # 05 precede i file default 10 gia' installati in /etc/systemd/network.
        install -m 0644 \
            "$cartella_common/network/$profilo/10-girello-$interfaccia.network" \
            "$rete_dir/05-girello-$interfaccia.network"
    done

    systemctl start systemd-networkd.service

    # Attende la configurazione delle porte, anche senza cavi collegati.
    # :off indica lo stato operativo minimo accettato, non spegne le porte.
    /usr/lib/systemd/systemd-networkd-wait-online \
        --interface=enp1s0:off --interface=enp2s0:off --timeout=15

    "$script_dir/$profilo-firewall.sh" apply
}

# 3b. Ripristina la connessione ordinaria sulla prima Ethernet.
ripristina_default() {
    local interfaccia

    sysctl -q -p "$parametri_default"

    # Evita attivazioni automatiche mentre restituiamo le porte a NetworkManager.
    for interfaccia in enp1s0 enp2s0; do
        nmcli device set "$interfaccia" autoconnect no
    done
    rm -f "$nm_config"
    nmcli general reload conf
    for interfaccia in enp1s0 enp2s0; do
        nmcli device set "$interfaccia" managed yes
    done

    printf 'Collega la prima Ethernet alla rete ordinaria; lascia libera la seconda.\n'
    read -r -p 'Premi Invio dopo aver collegato il cavo: ' </dev/tty
    nmcli --wait 30 connection up uuid "$connessione_default" ifname enp1s0
    nmcli device set enp1s0 autoconnect yes
    ip link set dev enp2s0 down
}

# 4. Seleziona gli ingressi Nginx e riapre il portale.
attiva_portale() {
    # Questi sono i soli file di profilo gestiti dallo switch.
    rm -f "$nginx_dir/profile.http.conf" "$nginx_dir/profile.main.conf"
    case "$profilo" in
        jeopardy)
            install -m 0644 "$cartella_common/nginx/jeopardy.http.conf" \
                "$nginx_dir/profile.http.conf"
            ;;
        ad)
            install -m 0644 "$cartella_common/nginx/ad.http.conf" \
                "$nginx_dir/profile.http.conf"
            install -m 0644 "$cartella_common/nginx/ad.stream.conf" \
                "$nginx_dir/profile.main.conf"
            ;;
    esac

    # In default resta soltanto ctfd-local.conf, installato permanentemente.
    nginx -t
    systemctl start nginx.service

    # Controllo locale del portale; la prova dalle postazioni resta distinta.
    curl --noproxy '*' --fail --silent --show-error --max-time 10 \
        --output /dev/null http://127.0.0.1/
}

# Riavvio: ramo riservato a girello-network-boot.service.
# I file di esercitazione in /run scompaiono al reboot; il file persistente
# di NetworkManager impedisce di riattivare automaticamente la rete ordinaria.
if [[ $profilo == boot ]]; then
    if [[ -e $nm_config ]]; then
        for interfaccia in enp1s0 enp2s0; do
            [[ -e /sys/class/net/$interfaccia ]] || continue
            ip link set dev "$interfaccia" down
            ip -4 address flush dev "$interfaccia"
            ip -6 address flush dev "$interfaccia"
            sysctl -q -w "net.ipv6.conf.$interfaccia.disable_ipv6=1"
        done
        install -d -m 0755 /run/girello
        printf 'sospeso\n' > /run/girello/mode
    fi
    exit 0
fi

# Sequenza principale: un solo cambio alla volta, dalla console locale.
exec 8>/run/girello-network.lock
flock -n 8 || {
    printf 'Un altro cambio di profilo sta usando la rete.\n' >&2
    exit 1
}

printf 'Operare fuori sessione dalla console locale del Master.\n'
printf 'Scollega entrambe le Ethernet prima di proseguire.\n'
read -r -p 'Premi Invio dopo aver scollegato i cavi: ' </dev/tty

if [[ ! -e $nm_config ]]; then
    salva_parametri_default
fi
if [[ ! -s $parametri_default ]]; then
    printf 'Mancano i parametri per il ritorno alla rete ordinaria.\n' >&2
    exit 1
fi

install -d -m 0755 "$rete_dir" "$nginx_dir"
printf 'incompleto\n' > /run/girello/mode

sospendi_rete
if [[ $profilo == default ]]; then
    ripristina_default
else
    attiva_laboratorio
fi
attiva_portale

ip -br address show dev enp1s0
ip -br address show dev enp2s0
printf '%s\n' "$profilo" > /run/girello/mode
printf 'Configurazione del profilo %s completata.\n' "$profilo"

case "$profilo" in
    jeopardy)
        printf 'Ora collega la prima Ethernet al router Jeopardy, con WAN scollegata. Lascia libera la seconda.\n'
        ;;
    ad)
        printf 'Ora collega la prima Ethernet al Team 1 e la seconda al Team 2. Il router Jeopardy resta scollegato dal Master.\n'
        ;;
esac
