#!/bin/sh
set -eu
umask 077
[ "$#" -eq 2 ] || exit 2
workspace=$1
rsa_private=$2
case "$workspace" in /*) ;; *) exit 2 ;; esac
case "$rsa_private" in /*) ;; *) exit 2 ;; esac
[ -d "$workspace/public" ] && [ ! -e "$workspace/private_tools" ] && [ ! -e "$workspace/.transport.key" ] || exit 2
[ "$(sha256sum "$workspace/public/tool-manifest.json" | cut -d " " -f 1)" = b74a36dc706fca25f78bfca12a9025b158457e851a3e1dd17c1f29639bc59026 ] || exit 2
[ "$(sha256sum "$workspace/public/capsule_tool.py" | cut -d " " -f 1)" = 3bef32da32b006d30b50f610e294d51536a227fd741207e15ea860f5a051a118 ] || exit 2
[ "$(sha256sum "$workspace/public/ADAPTER_MANUAL_753.py" | cut -d " " -f 1)" = 44451456d63d94b612924d215ece822dfce127f4cc67926294f33b643fd14cf3 ] || exit 2
[ "$(sha256sum "$workspace/public/ENTRY_MANUAL_753.sh" | cut -d " " -f 1)" = d15874c477fef0d92bc68ab77802a5354d15be237c853621b56467005c20d43e ] || exit 2
[ "$(sha256sum "$workspace/public/tools.753capsule" | cut -d " " -f 1)" = f4ac699408a3c00d8cd547cde90be547279c009dda4a94360f8fb0ef3e5d7939 ] || exit 2
[ "$(sha256sum "$workspace/public/transport-key.rsa-oaep-sha256" | cut -d " " -f 1)" = 2bef07a39efdda1f1a94768efe83c898b4381c02080f062361eb05013c61f925 ] || exit 2
image=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
[ "$(docker image inspect --format '{{.Id}}' "$image")" = "$image" ] || exit 2
[ "$(openssl pkey -in "$rsa_private" -pubout -outform DER 2>/dev/null | openssl dgst -sha256 | awk '{print $NF}')" = 385f2632f9c82260639db1c0994ebf951a9c1e9efa97a2cd5249b190220f5e66 ] || exit 2
(set -C; openssl pkeyutl -decrypt -passin pass: -inkey "$rsa_private" -in "$workspace/public/transport-key.rsa-oaep-sha256" -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256 > "$workspace/.transport.key" 2>/dev/null)
[ "$(wc -c < "$workspace/.transport.key")" -eq 32 ] || exit 2
chmod 600 "$workspace/.transport.key"
exec docker run --rm --restart=no --pull=never --network none --cpus 1 --memory 256m --memory-swap 256m --pids-limit 32 --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=16m --mount "type=bind,src=$workspace,dst=/private" --entrypoint python3 "$image" /private/public/capsule_tool.py open --capsule /private/public/tools.753capsule --key-file /private/.transport.key --manifest /private/public/tool-manifest.json --dest /private/private_tools
