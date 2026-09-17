#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Uso: bash $0 /percorso/nuovo-pacchetto" >&2
    exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
output_dir=$(realpath -m -- "$1")
runtime_image="girello/ad-runtime:1"

# Il pacchetto resta fuori dalla repository e non sovrascrive altri file.
case "$output_dir" in
    "$repo_root"|"$repo_root"/*)
        echo "Scegli una destinazione esterna alla repository." >&2
        exit 1
        ;;
esac

if [[ -e "$output_dir" || -L "$output_dir" ]]; then
    echo "La destinazione esiste gia': $output_dir" >&2
    exit 1
fi

# I sorgenti vengono esportati da HEAD: richiede modifiche gia' committate.
if ! git -C "$repo_root" diff --quiet HEAD -- attack_defense/services; then
    echo "Completa prima il commit delle modifiche ai sorgenti dei servizi." >&2
    exit 1
fi

runtime_id=$(sudo docker image inspect --format '{{.Id}}' "$runtime_image")
source_commit=$(git -C "$repo_root" rev-parse HEAD)

mkdir -p -- "$output_dir"

# Esporta soltanto i file tracciati necessari alle applicazioni.
for service in document-vault helpdesk; do
    git -C "$repo_root" archive --format=tar HEAD \
        "attack_defense/services/$service/app.py" \
        "attack_defense/services/$service/requirements.txt" \
        "attack_defense/services/$service/.dockerignore" \
        "attack_defense/services/$service/static" |
        tar -xf - -C "$output_dir" --strip-components=1

    cp -- "$script_dir/Dockerfile.$service" \
        "$output_dir/services/$service/Dockerfile"
done

cp -- "$script_dir/compose.team.yaml" "$output_dir/compose.yaml"
cp -- "$script_dir/README.team.md" "$output_dir/README.md"

# Salva l'immagine, senza container o volumi. La redirezione resta dell'utente.
sudo docker image save "$runtime_image" > "$output_dir/runtime.tar"

printf 'SERVICE_SOURCE_COMMIT=%s\nRUNTIME_IMAGE=%s\nRUNTIME_IMAGE_ID=%s\n' \
    "$source_commit" "$runtime_image" "$runtime_id" \
    > "$output_dir/build-info.txt"

printf 'Pacchetto preparato in: %s\n' "$output_dir"
