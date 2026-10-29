#!/bin/sh
# New 0b/v2.4 entry. No inherited path/IP/key/cost stop; no old V1 edit.
set -eu
umask 077
mode=${1:-}
[ "$#" -gt 0 ] || exit 2
shift
workspace=
packet=
run_id=
grant_file=
authorize_once=
while [ "$#" -gt 0 ]; do
  [ "$#" -ge 2 ] || exit 2
  case "$1" in
    --workspace) workspace=$2 ;;
    --neutral-opened-dir) packet=$2 ;;
    --run-id) run_id=$2 ;;
    --grant-file) grant_file=$2 ;;
    --authorize-once) authorize_once=$2 ;;
    *) exit 2 ;;
  esac
  shift 2
done
case "$workspace" in /*) ;; *) exit 2 ;; esac
case "$run_id" in ''|*[!A-Za-z0-9_-]*) exit 2 ;; esac
[ -d "$workspace" ] && [ -f "$workspace/public/ADAPTER_0B_V24.py" ] && [ -f "$workspace/runtime/runtime.py" ] || exit 2
image=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
actual_image=$(docker image inspect --format '{{.Id}}' "$image")
[ "$actual_image" = "$image" ] || exit 2
case "$mode" in
  prepare)
    case "$packet" in /*) ;; *) exit 2 ;; esac
    [ -d "$packet/inputs" ] && [ -z "$grant_file" ] && [ -z "$authorize_once" ] || exit 2
    exec docker run --rm --restart=no --pull=never --network none \
      --name "qa772-v24-prepare-$run_id" --cpus 8 --memory 8g --memory-swap 8g --pids-limit 2048 \
      --ulimit nofile=4096:4096 --read-only --cap-drop ALL --security-opt no-new-privileges \
      --tmpfs /tmp:rw,nosuid,nodev,size=64m \
      --mount "type=bind,src=$workspace,dst=/private" --mount "type=bind,src=$packet,dst=/packet,readonly" \
      --entrypoint python3 "$image" /private/public/ADAPTER_0B_V24.py prepare \
      --workspace /private --runtime-file /private/runtime/runtime.py --neutral-opened-dir /packet --run-id "$run_id"
    ;;
  execute)
    case "$grant_file" in /*) ;; *) exit 2 ;; esac
    [ -f "$grant_file" ] && [ -z "$packet" ] && [ "$authorize_once" = "$run_id" ] || exit 2
    exec docker run --rm --restart=no --pull=never --network host \
      --name "qa772-v24-execute-$run_id" --stop-timeout 3 \
      --cpus 8 --memory 8g --memory-swap 8g --pids-limit 2048 --ulimit nofile=4096:4096 \
      --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m \
      --mount "type=bind,src=$workspace,dst=/private" --mount "type=bind,src=$grant_file,dst=/authorized-grant.json,readonly" \
      --entrypoint python3 "$image" /private/public/ADAPTER_0B_V24.py execute \
      --workspace /private --runtime-file /private/runtime/runtime.py --run-id "$run_id" \
      --grant-file /authorized-grant.json --authorize-once "$authorize_once"
    ;;
  *) exit 2 ;;
esac
