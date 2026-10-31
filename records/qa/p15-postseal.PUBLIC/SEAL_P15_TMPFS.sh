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
[ "$(dirname "$OUT")" = /root/t44-sealed-p15-tmpfs ] || exit 2
[ "$(findmnt -n -o FSTYPE --target /root/t44-sealed-p15-tmpfs)" = tmpfs ] || exit 2
[ "$(awk '/MemAvailable/{print $2}' /proc/meminfo)" -ge 30408704 ] || exit 2
[ -z "$(docker ps -q)" ] || exit 2
D=$(dirname "$OUT")
N=$(basename "$OUT")
[ -d "$D" ] || exit 2
# Fail if docker cannot enumerate; absent --rm execution container is allowed.
STATES=$(docker ps -a --format '{{.Names}} {{.State}}')
[ "$(printf '%s\n' "$STATES" | awk '$1=="qa753-p-r30manualp15" && $2!="exited" && $2!="dead" {print "UNSAFE"}')" != UNSAFE ] || exit 2
IMAGE=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1
[ "$(docker image inspect --format '{{.Id}}' "$IMAGE")" = "$IMAGE" ] || exit 2
# Container alone reads installed PRIVATE bytes/key. No secret/tool content is printed.
CODE='import pathlib,json,hashlib,os,sys;w=pathlib.Path("/private");b=(w/"public/tool-manifest.json").read_bytes();assert hashlib.sha256(b).hexdigest()=="fd8c8fb6ec7b655c5e4699774cdc4e1fbac151eb77fe41bf5f74add0d059b882";m=json.loads(b);assert all(hashlib.sha256((w/"private_tools"/n).read_bytes()).hexdigest()==h for n,h in m["files"].items());r=json.loads((w/"results/r30manualp15/result.json").read_bytes());assert r.get("writer_finalized") is True;folders=["functional-input","functional-results","runs","results","operator-channel","evidence-neutral"];paths=[p for f in folders for p in (w/f).rglob("*") if p.is_file() and not p.is_symlink()];assert len(paths)<=8192,"FILE_COUNT_RESOURCE_BOUND";assert all(len(str(p.relative_to(w)).encode())<=4096 for p in paths),"PATH_RESOURCE_BOUND";tar_bound=sum(((p.stat().st_size+511)//512)*512+65536 for p in paths)+1048576;assert tar_bound<=int(12.75*1024**3),"SEALED_TREE_RESOURCE_BOUND";cipher_bound=(tar_bound*102+99)//100+16*1024**2;assert cipher_bound<=int(13.1*1024**3),"CIPHER_RESOURCE_BOUND";assert os.statvfs("/sealed").f_bavail*os.statvfs("/sealed").f_frsize>=cipher_bound+128*1024**2,"TMPFS_FREE_BOUND";print(json.dumps({"status":"POSTSEAL_RESOURCE_GUARD_OK","files":len(paths),"tar_bound":tar_bound,"cipher_bound":cipher_bound,"memory_limit_bytes":28*1024**3}),flush=True);os.execv(sys.executable,[sys.executable,"/private/private_tools/backup.py","/private",sys.argv[1]])'
exec docker run --rm --restart=no --pull=never --network none --cpus 2 --memory 28g --memory-swap 28g --pids-limit 64 --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,src=$W,dst=/private,readonly" --mount "type=bind,src=$D,dst=/sealed" --entrypoint python3 "$IMAGE" -c "$CODE" "/sealed/$N"
