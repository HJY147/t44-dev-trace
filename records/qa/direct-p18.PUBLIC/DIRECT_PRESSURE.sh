#!/bin/sh
set -eu
umask 077
[ "$#" -eq 2 ] || exit 2
W=$1
INPUT_FILE=$2
[ -f "$INPUT_FILE" ] && [ "$(basename "$INPUT_FILE")" = session.private.json ] || exit 2
INPUTS=$(dirname "$INPUT_FILE")
case "$W:$INPUTS" in /*:/*) ;; *) exit 2 ;; esac
[ ! -e "$W/runs/r30posttools18" ] && [ ! -e "$W/results/r30posttools18" ] || exit 2
mkdir -p "$W/operator-channel/r30posttools18"
IMAGE=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
set +e
docker run --rm --restart=no --pull=never --network host --name qa753-p-r30posttools18 --stop-timeout 3 --cpus 8 --memory 8g --memory-swap 8g --pids-limit 2048 --ulimit nofile=4096:4096 --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,src=$W,dst=/private" --mount "type=bind,src=$INPUTS,dst=/direct-inputs,readonly" --entrypoint python3 "$IMAGE" /private/private_tools/direct_boot.py --workspace /private --inputs /direct-inputs/session.private.json > "$W/operator-channel/r30posttools18/entry.stdout.private" 2> "$W/operator-channel/r30posttools18/entry.stderr.private"
code=$?
set -e
# No measurements run after docker exits. Preserve failure then seal available evidence.
printf '{"run_id":"r30posttools18","classification":"DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE","process_exit":%s}
' "$code" > "$W/operator-channel/r30posttools18/exit.PUBLIC.json"
D=/root/t44-sealed-directp18-tmpfs
if ! mountpoint -q "$D"; then
 if [ -d "$D" ]; then [ -z "$(find "$D" -mindepth 1 -maxdepth 1 -print -quit)" ] || exit 2; else mkdir -m 700 "$D"; fi
 mount -t tmpfs -o size=14G,mode=0700,nosuid,nodev,noexec tmpfs "$D"
fi
sh "$W/public/SEAL_DIRECT.sh" "$W" r30posttools18 "$D/r30posttools18.753backup" EXITED_ALL_PRODUCERS_AND_WRITERS_STOPPED
exit "$code"
