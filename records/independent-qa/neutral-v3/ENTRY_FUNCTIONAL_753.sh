#!/bin/sh
set -eu
umask 077
[ "$#" -eq 3 ] || exit 2
workspace=$1
environment=$2
run_id=$3
case "$workspace" in /*) ;; *) exit 2 ;; esac
case "$environment" in /*) ;; *) exit 2 ;; esac
case "$run_id" in ''|*[!A-Za-z0-9_-]*) exit 2 ;; esac
[ -f "$environment" ] && [ -d "$workspace/private_tools" ] || exit 2
image=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
[ "$(docker image inspect --format '{{.Id}}' "$image")" = "$image" ] || exit 2
mkdir -p "$workspace/functional-input" "$workspace/functional-results" "$workspace/operator-channel"
cp "$environment" "$workspace/functional-input/environment.json"
chmod 600 "$workspace/functional-input/environment.json"
exec docker run --rm --restart=no --pull=never --network host --name "qa753-f-$run_id" --stop-timeout 3 --cpus 8 --memory 8g --memory-swap 8g --pids-limit 2048 --ulimit nofile=4096:4096 --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,src=$workspace,dst=/private" --entrypoint python3 "$image" /private/private_tools/functional.py /private/functional-input/environment.json --allow-run "$run_id"
