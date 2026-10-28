"""Generate bounded opaque public-code transport commands for a pinned v4 profile."""

import argparse
import base64
import gzip
import hashlib
import json
import os
import re
from pathlib import Path

ALLOWED = {
    "profile.json",
    "backend-upgrade.py",
    "generation.py",
    "resource-stream.py",
    "source-artifact-receive.py",
    "mysql-budget.py",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def exclusive(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


INSTALLER = """import hashlib,json,os,stat,zlib
from pathlib import Path
root=Path(REMOTE_ROOT)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def checked(path,expected,n):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  s=os.fstat(f.fileno())
  if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.geteuid() or stat.S_IMODE(s.st_mode)!=0o600 or s.st_nlink!=1: raise ValueError('EXACT_OWNED_PRIVATE_FILE_REQUIRED')
  raw=f.read(n+1)
 if len(raw)!=n or sha(raw)!=expected: raise ValueError('EXACT_BYTES_SHA_REQUIRED')
 return raw
def write(path,raw):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f: f.write(raw);f.flush();os.fsync(f.fileno())
if root.resolve()!=root or not root.is_dir(): raise ValueError('CANONICAL_NEW_ROOT_REQUIRED')
manifest=json.loads(checked(root/'manifest.PUBLIC.json',MANIFEST_SHA,MANIFEST_BYTES))
if manifest['source_sha']!=SOURCE or manifest['stop_utc']!=STOP: raise ValueError('SOURCE_WINDOW_REQUIRED')
rows=manifest['parts']
if set(p.name for p in (root/'parts').iterdir())!={r['path'] for r in rows}: raise ValueError('EXACT_PART_SET_REQUIRED')
joined=b''
for i,row in enumerate(rows):
 if row['path']!=f'{i:03}.bin' or not 0<row['bytes']<=7500: raise ValueError('EXACT_ORDER_BOUNDED_PART_REQUIRED')
 joined+=checked(root/'parts'/row['path'],row['sha256'],row['bytes'])
if len(joined)!=manifest['gzip_bytes'] or sha(joined)!=manifest['gzip_sha256']: raise ValueError('WHOLE_TRANSPORT_REQUIRED')
dec=zlib.decompressobj(31);raw=dec.decompress(joined,1048577)
if not dec.eof or dec.unused_data or dec.unconsumed_tail or len(raw)>1048576 or sha(raw)!=manifest['payload_sha256']: raise ValueError('BOUNDED_COMPLETE_GZIP_REQUIRED')
payload=json.loads(raw);files=payload['files']
allowed={'profile.json','backend-upgrade.py','generation.py','resource-stream.py','source-artifact-receive.py','mysql-budget.py'}
if payload['kind']!='v4-public-code-transport' or set(files)!=allowed or set(manifest['files'])!=allowed: raise ValueError('LITERAL_SIX_FILE_SET_REQUIRED')
for name,text in files.items():
 data=text.encode();item=manifest['files'][name]
 if len(data)!=item['bytes'] or sha(data)!=item['sha256']: raise ValueError('EXACT_PUBLIC_CODE_REQUIRED')
 if name.endswith('.py'): compile(text,name,'exec')
profile=json.loads(files['profile.json'])
if profile['kind']!='explicit-new-source-time-pool-profile-v4' or profile['source_sha']!=SOURCE or profile['stop_utc']!=STOP or profile['source_file_count']!=manifest['source_file_count']: raise ValueError('EXACT_V4_PROFILE_REQUIRED')
if set(profile['derived_files'])!=allowed-{'profile.json'}: raise ValueError('EXACT_V4_DERIVED_SET_REQUIRED')
for name,item in profile['derived_files'].items():
 if item!=manifest['files'][name]: raise ValueError('PROFILE_CODE_CHAIN_REQUIRED')
target=root/'profile';target.mkdir(mode=0o700)
for name,text in sorted(files.items()): write(target/name,text.encode())
print(json.dumps({'success':True,'profile_dir':str(target),'source_sha':SOURCE,'stop_utc':STOP,'files':manifest['files'],'SUT_or_services_started':False}))
"""


def make(args):
    if (
        args.profile.is_symlink()
        or sha(args.profile.read_bytes()) != args.profile_sha256
        or not re.fullmatch(r"/root/t44-r9/v4-[a-z0-9-]{6,50}", args.remote_root)
    ):
        raise ValueError("EXPLICIT_PINNED_PROFILE_AND_NEW_V4_REMOTE_ROOT_REQUIRED")
    profile = json.loads(args.profile.read_bytes())
    if profile["kind"] != "explicit-new-source-time-pool-profile-v4" or set(
        profile["derived_files"]
    ) != ALLOWED - {"profile.json"}:
        raise ValueError("EXACT_SIX_FILE_V4_PROFILE_REQUIRED")
    files, metadata = {}, {}
    for name in sorted(ALLOWED):
        path = args.profile.parent / name
        if path.is_symlink():
            raise ValueError("REGULAR_PROFILE_OBJECT_REQUIRED")
        raw = path.read_bytes()
        files[name] = raw.decode()
        metadata[name] = {"bytes": len(raw), "sha256": sha(raw)}
        if name != "profile.json" and metadata[name] != profile["derived_files"][name]:
            raise ValueError("PINNED_PROFILE_OBJECT_CHANGED")
    payload = json.dumps(
        {"kind": "v4-public-code-transport", "files": files},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    if len(payload) > 1024 * 1024:
        raise ValueError("PUBLIC_CODE_SIZE_BOUND")
    compressed = gzip.compress(payload, mtime=0)
    pieces = [compressed[:6000]]
    pieces.extend(compressed[n : n + 7500] for n in range(6000, len(compressed), 7500))
    manifest = {
        "kind": "v4-small-public-code-delivery",
        "source_sha": profile["source_sha"],
        "stop_utc": profile["stop_utc"],
        "source_file_count": profile["source_file_count"],
        "files": metadata,
        "gzip_bytes": len(compressed),
        "gzip_sha256": sha(compressed),
        "payload_sha256": sha(payload),
        "parts": [
            {"path": f"{i:03}.bin", "bytes": len(raw), "sha256": sha(raw)}
            for i, raw in enumerate(pieces)
        ],
    }
    manifest_raw = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    scripts = []
    for i, raw in enumerate(pieces):
        code = "import base64,hashlib,os\nfrom pathlib import Path\n"
        code += "root=Path(" + repr(args.remote_root) + ")\n"
        if i == 0:
            code += "if root.parent.resolve()!=root.parent: raise ValueError('CANONICAL_PARENT_REQUIRED')\n"
            code += "root.mkdir(mode=0o700)\n(root/'parts').mkdir(mode=0o700)\n"
        else:
            code += "if root.resolve()!=root or not root.is_dir(): raise ValueError('CANONICAL_ROOT_REQUIRED')\n"
        code += "def write(path,data):\n fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)\n with os.fdopen(fd,'wb') as f: f.write(data);f.flush();os.fsync(f.fileno())\n"
        if i == 0:
            code += (
                "write(root/'manifest.PUBLIC.json',base64.b64decode("
                + repr(base64.b64encode(manifest_raw).decode())
                + ",validate=True))\n"
            )
        code += (
            "raw=base64.b64decode("
            + repr(base64.b64encode(raw).decode())
            + ",validate=True)\n"
        )
        code += (
            "if hashlib.sha256(raw).hexdigest()!="
            + repr(sha(raw))
            + ": raise ValueError('PART_SHA_REQUIRED')\n"
        )
        code += (
            "write(root/'parts'/"
            + repr(f"{i:03}.bin")
            + ",raw)\nprint('PUBLIC_CODE_PART_SAVED',"
            + str(i)
            + ")\n"
        )
        scripts.append((f"{i + 1:02}-part-{i:03}.sh", code))
    constants = (
        "REMOTE_ROOT="
        + repr(args.remote_root)
        + "\nMANIFEST_SHA="
        + repr(sha(manifest_raw))
    )
    constants += (
        "\nMANIFEST_BYTES="
        + str(len(manifest_raw))
        + "\nSOURCE="
        + repr(profile["source_sha"])
    )
    constants += "\nSTOP=" + repr(profile["stop_utc"]) + "\n"
    scripts.append((f"{len(scripts) + 1:02}-verify-install.sh", constants + INSTALLER))
    final, sizes = {}, []
    for name, code in scripts:
        compile(code, name, "exec")
        raw = ("python3 - <<'PY'\n" + code + "PY\n").encode()
        encoded = len(base64.b64encode(raw)) + 256
        if len(raw) > 13000 or encoded >= 18000:
            raise ValueError("WHOLE_COMMAND_WITH_DESCRIPTION_EXCEEDS_REVIEWED_LIMIT")
        final[name] = raw
        sizes.append(
            {
                "name": name,
                "raw_bytes": len(raw),
                "base64_plus_description_256": encoded,
                "sha256": sha(raw),
            }
        )
    if (
        not args.output.is_absolute()
        or args.output.parent.resolve() != args.output.parent
    ):
        raise ValueError("NEW_CANONICAL_LOCAL_OUTPUT_REQUIRED")
    args.output.mkdir(mode=0o700)
    for name, raw in final.items():
        exclusive(args.output / name, raw)
    exclusive(args.output / "manifest.PUBLIC.json", manifest_raw)
    result = {
        "success": True,
        "remote_root": args.remote_root,
        "manifest_sha256": sha(manifest_raw),
        "source_sha": profile["source_sha"],
        "stop_utc": profile["stop_utc"],
        "commands": sizes,
        "cloud_or_SUT_executed": False,
    }
    exclusive(
        args.output / "delivery.PUBLIC.json",
        (json.dumps(result, indent=2) + "\n").encode(),
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--profile-sha256", required=True)
    parser.add_argument("--remote-root", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    os.umask(0o077)
    print(json.dumps(make(arguments)))
