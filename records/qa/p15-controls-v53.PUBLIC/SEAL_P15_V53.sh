#!/bin/sh
# Public sealing only. Attestation must cover all producers/operator writers too.
set -eu
umask 077
[ "$#" -eq 4 ] || exit 2
W=$1
RUN=$2
OUT=$3
[ "$RUN" = r30manualp15 ] && [ "$4" = EXITED_ALL_PRODUCERS_AND_WRITERS_STOPPED ] || exit 2
case "$W:$OUT" in /*:/*) ;; *) exit 2 ;; esac
W=$(realpath "$W")
OUT=$(realpath -m "$OUT")
case "$OUT" in "$W"|"$W"/*) exit 2 ;; esac
[ ! -e "$OUT" ] && [ ! -e "$OUT.receipt.json" ] || exit 2
D=$(dirname "$OUT")
N=$(basename "$OUT")
[ -d "$D" ] || exit 2
# Fail if docker cannot enumerate; absent --rm execution container is allowed.
STATES=$(docker ps -a --format '{{.Names}} {{.State}}')
[ "$(printf '%s\n' "$STATES" | awk '$1=="qa753-p-r30manualp15" && $2!="exited" && $2!="dead" {print "UNSAFE"}')" != UNSAFE ] || exit 2
IMAGE=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
[ "$(docker image inspect --format '{{.Id}}' "$IMAGE")" = "$IMAGE" ] || exit 2
# Container alone reads installed PRIVATE bytes/key. No secret/tool content is printed.
CODE='import pathlib,json,hashlib,os,sys;w=pathlib.Path("/private");b=(w/"public/tool-manifest.json").read_bytes();assert hashlib.sha256(b).hexdigest()=="fd8c8fb6ec7b655c5e4699774cdc4e1fbac151eb77fe41bf5f74add0d059b882";m=json.loads(b);assert all(hashlib.sha256((w/"private_tools"/n).read_bytes()).hexdigest()==h for n,h in m["files"].items());r=json.loads((w/"results/r30manualp15/result.json").read_bytes());assert r.get("writer_finalized") is True;os.execv(sys.executable,[sys.executable,"/private/private_tools/backup.py","/private",sys.argv[1]])'
exec docker run --rm --restart=no --pull=never --network none --cpus 2 --memory 2g --memory-swap 2g --pids-limit 64 --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,src=$W,dst=/private,readonly" --mount "type=bind,src=$D,dst=/sealed" --entrypoint python3 "$IMAGE" -c "$CODE" "/sealed/$N"
