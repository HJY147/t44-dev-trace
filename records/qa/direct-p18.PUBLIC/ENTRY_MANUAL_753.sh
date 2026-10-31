#!/bin/sh
set -eu
umask 077
[ "$#" -ge 3 ] || exit 2
mode=$1
workspace=$2
run_id=$3
shift 3
case "$workspace" in /*) ;; *) exit 2 ;; esac
case "$run_id" in ''|*[!A-Za-z0-9_-]*) exit 2 ;; esac
image=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
[ "$(docker image inspect --format '{{.Id}}' "$image")" = "$image" ] || exit 2
case "$mode" in
 prepare)
  [ "$#" -eq 1 ] || exit 2
  packet=$1
  case "$packet" in /*) ;; *) exit 2 ;; esac
  exec docker run --rm --restart=no --pull=never --network none --cpus 8 --memory 8g --memory-swap 8g --pids-limit 2048 --ulimit nofile=4096:4096 --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,src=$workspace,dst=/private" --mount "type=bind,src=$packet,dst=/packet,readonly" --entrypoint python3 "$image" /private/public/ADAPTER_MANUAL_753.py prepare --workspace /private --run-id "$run_id" --neutral-opened-dir /packet
 ;;
 execute)
  [ "$#" -eq 1 ] || exit 2
  grant=$1
  case "$grant" in /*) ;; *) exit 2 ;; esac
  exec docker run --rm --restart=no --pull=never --network host --name "qa753-p-$run_id" --stop-timeout 3 --cpus 8 --memory 8g --memory-swap 8g --pids-limit 2048 --ulimit nofile=4096:4096 --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,src=$workspace,dst=/private" --mount "type=bind,src=$grant,dst=/authorized-grant.json,readonly" --entrypoint python3 "$image" /private/public/ADAPTER_MANUAL_753.py execute --workspace /private --run-id "$run_id" --grant-file /authorized-grant.json --authorize-once "$run_id"
 ;;
 *) exit 2 ;;
esac
