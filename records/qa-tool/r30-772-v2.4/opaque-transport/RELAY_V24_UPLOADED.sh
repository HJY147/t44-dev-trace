#!/bin/sh
# Complete GUI relay after official file upload. No curl/SSH/SUT/run/grant.
set -eu
umask 077
[ "$#" -eq 4 ] && [ "$1" = --uploaded-bundle ] || exit 2
bundle=$2
workspace=$3
rsa_private=$4
for absolute in "$bundle" "$workspace" "$rsa_private"; do
  case "$absolute" in /*) ;; *) exit 2 ;; esac
done
[ -f "$bundle" ] && [ ! -L "$bundle" ] && [ ! -e "$workspace" ] && [ ! -L "$workspace" ] || exit 2
for tool in openssl docker sha256sum stat tar; do command -v "$tool" >/dev/null 2>&1 || exit 2; done
[ -f "$rsa_private" ] && [ ! -L "$rsa_private" ] || { printf '%s\n' '{"status":"BLOCKED","code":"RSA_PRIVATE_CANDIDATE_ABSENT"}'; exit 2; }
case "$(stat -c '%a' "$rsa_private")" in 400|600) ;; *) exit 2 ;; esac
public_der=$(openssl pkey -in "$rsa_private" -passin pass: -pubout -outform DER 2>/dev/null | sha256sum)
public_der=${public_der%% *}
[ "$public_der" = 385f2632f9c82260639db1c0994ebf951a9c1e9efa97a2cd5249b190220f5e66 ] || { printf '%s\n' '{"status":"BLOCKED","code":"RSA_PUBLIC_FINGERPRINT_MISMATCH"}'; exit 2; }
actual_bundle=$(sha256sum "$bundle")
actual_bundle=${actual_bundle%% *}
[ "$actual_bundle" = 82bef025877230b51b6d95eae18f3abc320442aa5b436b8524b12e946ff458c0 ] || exit 2
image=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
[ "$(docker image inspect --format '{{.Id}}' "$image" 2>/dev/null)" = "$image" ] || exit 2
# mkdir is exclusive; tar refuses to replace any existing member.
mkdir -m 700 "$workspace"
mkdir -m 700 "$workspace/public"
tar --extract --gzip --file "$bundle" --directory "$workspace/public" --keep-old-files --no-same-owner
exec sh "$workspace/public/INSTALL_V24_OPAQUE.sh" "$workspace" "$rsa_private"
