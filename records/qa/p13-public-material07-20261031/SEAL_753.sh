#!/bin/sh
# Public wrapper: after runtime exit and all writers stopped, operator explicitly attests.
set -eu
umask 077
[ "$#" -eq 3 ] || exit 2
W=$1
OUT=$2
[ "$3" = EXITED_ALL_WRITERS_STOPPED ] || exit 2
case "$W:$OUT" in /*:/*) ;; *) exit 2 ;; esac
[ ! -e "$OUT" ] && [ ! -e "$OUT.receipt.json" ] || exit 2
[ "$(docker inspect --format '{{.State.Running}}' qa753-p-r30manualp13 2>/dev/null || true)" != true ] || exit 2
IMAGE=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
# Output is outside evidence folders to avoid backing up the growing ciphertext itself.
case "$OUT" in "$W"/*) exit 2 ;; esac
D=$(dirname "$OUT")
N=$(basename "$OUT")
[ -d "$D" ] || exit 2
exec docker run --rm --restart=no --pull=never --network none --cpus 2 --memory 2g --memory-swap 2g --pids-limit 64 --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,src=$W,dst=/private,readonly" --mount "type=bind,src=$D,dst=/sealed" --entrypoint python3 "$IMAGE" /private/private_tools/backup.py /private "/sealed/$N"
