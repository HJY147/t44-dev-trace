#!/usr/bin/env bash
# Neutral delivery checks only; no application, account or independent test calls.
set -euo pipefail
umask 077
test "$(id -u)" = 0
test "$(date -u +%s)" -lt "$(date -u -d 2026-10-24T08:55:00Z +%s)"
python3.12 - <<'PY'
import json
import time
import urllib.request

url = 'https://mirrors.aliyun.com/pypi/simple/cryptography/'
started = time.monotonic()
with urllib.request.urlopen(url, timeout=10) as response:
    response.read(128)
    assert response.status == 200
    print(json.dumps({'official_mirror_https_status': response.status,
                      'elapsed_s': round(time.monotonic() - started, 3)}))
PY
openssl version
guard_dir=/run/t44-delivery/tls-san-guard
mkdir -m 0700 "$guard_dir"
openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 1 \
    -subj '/CN=T44 synthetic guard CA' \
    -addext 'basicConstraints=critical,CA:TRUE,pathlen:0' \
    -addext 'keyUsage=critical,keyCertSign,cRLSign' \
    -keyout "$guard_dir/ca.key" -out "$guard_dir/ca.crt" \
    2>> "$guard_dir/setup.stderr"
openssl req -new -newkey rsa:2048 -nodes -sha256 \
    -subj '/CN=T44 synthetic guard leaf' \
    -keyout "$guard_dir/server.key" -out "$guard_dir/server.csr" \
    2>> "$guard_dir/setup.stderr"
cat > "$guard_dir/server.ext" <<'EXT'
subjectAltName=IP:127.0.0.1
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
EXT
openssl x509 -req -in "$guard_dir/server.csr" -CA "$guard_dir/ca.crt" \
    -CAkey "$guard_dir/ca.key" -CAcreateserial -days 1 -sha256 \
    -extfile "$guard_dir/server.ext" -out "$guard_dir/server.crt" \
    2>> "$guard_dir/setup.stderr"
openssl verify -CAfile "$guard_dir/ca.crt" -verify_ip 127.0.0.1 \
    -purpose sslserver "$guard_dir/server.crt" \
    > "$guard_dir/correct-san.stdout" 2> "$guard_dir/correct-san.stderr"
printf 'correct_san_verification_exit=0\n'
if openssl verify -CAfile "$guard_dir/ca.crt" -verify_ip 127.0.0.2 \
    -purpose sslserver "$guard_dir/server.crt" \
    > "$guard_dir/wrong-san.stdout" 2> "$guard_dir/wrong-san.stderr"; then
    printf 'ERROR: wrong SAN was accepted\n'
    exit 1
else
    mismatch_status=$?
    test "$mismatch_status" = 2
    printf 'wrong_san_verification_exit=%s\n' "$mismatch_status"
fi
printf 'T44_DELIVERY_GUARDS_OK\n'
