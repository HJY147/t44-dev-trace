#!/bin/sh
# Public adapter entry; only execute with the later explicit single-run authorization.
set -eu
umask 077
base=/root/t44-r9/independent772
image=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
mode=${1:-}
case "$mode" in
  capabilities)
    [ "$#" -eq 1 ] || exit 2
    set -- capabilities
    network=none
    ;;
  prepare)
    shift
    packet=
    run_id=
    origin=
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --neutral-opened-dir) [ "$#" -ge 2 ] || exit 2; packet=$2; shift 2 ;;
        --run-id) [ "$#" -ge 2 ] || exit 2; run_id=$2; shift 2 ;;
        --origin) [ "$#" -ge 2 ] || exit 2; origin=$2; shift 2 ;;
        *) exit 2 ;;
      esac
    done
    case "$packet" in /*) ;; *) exit 2 ;; esac
    [ -d "$packet" ] && [ -n "$run_id" ] || exit 2
    network=none
    set -- prepare --neutral-opened-dir /packet --run-id "$run_id"
    if [ -n "$origin" ]; then set -- "$@" --origin "$origin"; fi
    ;;
  execute)
    [ "$#" -eq 4 ] || exit 2
    run_id=$2
    [ "$3" = --authorize-once ] && [ "$4" = "$run_id" ] || exit 2
    network=host
    set -- execute --run-id "$run_id" --authorize-once "$run_id"
    ;;
  *) printf '%s\n' 'usage: capabilities | prepare --neutral-opened-dir /absolute/opened-neutral --run-id RUN_ID [--origin https://ACTUAL_HOST] | execute RUN_ID --authorize-once RUN_ID' >&2; exit 2 ;;
esac
actual_image=$(docker image inspect --format '{{.Id}}' "$image")
[ "$actual_image" = "$image" ] || exit 2
if [ "$mode" = prepare ]; then
  exec docker run --rm --restart=no --pull=never --network "$network" \
    --cpus 8 --memory 8g --memory-swap 8g --pids-limit 2048 \
    --ulimit nofile=4096:4096 --read-only --cap-drop ALL \
    --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m \
    --mount "type=bind,src=$base,dst=/private" \
    --mount "type=bind,src=$packet,dst=/packet,readonly" \
    --entrypoint python3 "$image" /private/public/LOAD_NEUTRAL_ADAPTER.py "$@"
fi
exec docker run --rm --restart=no --pull=never --network "$network" \
  --cpus 8 --memory 8g --memory-swap 8g --pids-limit 2048 \
  --ulimit nofile=4096:4096 --read-only --cap-drop ALL \
  --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --mount "type=bind,src=$base,dst=/private" \
  --entrypoint python3 "$image" /private/public/LOAD_NEUTRAL_ADAPTER.py "$@"
