"""Offline, deterministic scope bridge manifest and small public installation commands."""

import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tmp/790_backend_contrast_20261028/scope-callback-bridge-v1"
DEST = "/root/t44-r9/scope-bridge-v1-01"
FILES = (
    "bridge_common.py",
    "bridge_protocol.py",
    "bridge_load.py",
    "bridge_app.py",
    "bridge_backend.py",
    "bridge_data.py",
    "bridge_cli.py",
    "bridge_owner_probe.py",
    "scope_crypto.py",
)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def command(entries, manifest_sha, first, final):
    packed = base64.b64encode(gzip.compress(canonical(entries), mtime=0)).decode()
    return f'''python3 - <<'PY'
import base64,gzip,hashlib,json,os,pathlib,stat
root=pathlib.Path({DEST!r})
bundle={manifest_sha!r}
first={first!r}
final={final!r}
data=json.loads(gzip.decompress(base64.b64decode({packed!r},validate=True)))
def sha(raw): return hashlib.sha256(raw).hexdigest()
def write(path,raw,mode):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    try:
        with os.fdopen(fd,'wb',closefd=False) as out:
            out.write(raw);out.flush();os.fsync(fd)
    finally: os.close(fd)
if first:
    root.mkdir(mode=0o755)
    write(root/'install-bundle.PUBLIC.json',(json.dumps({{'bundle_sha256':bundle}},sort_keys=True)+'\\n').encode(),0o444)
assert root.is_dir() and not root.is_symlink() and root.resolve()==root
assert json.loads((root/'install-bundle.PUBLIC.json').read_text())=={{'bundle_sha256':bundle}}
installed=[]
for name,item in data.items():
    assert name==pathlib.Path(name).name and name in {list(FILES) + ['manifest.PUBLIC.json']!r}
    raw=base64.b64decode(item['base64'],validate=True)
    assert sha(raw)==item['sha256']
    write(root/name,raw,0o444)
    installed.append({{'name':name,'sha256':sha(raw),'bytes':len(raw)}})
if final:
    raw=(root/'manifest.PUBLIC.json').read_bytes();assert sha(raw)==bundle
    for name,item in json.loads(raw)['files'].items():
        path=root/name;assert path.is_file() and not path.is_symlink()
        assert sha(path.read_bytes())==item['sha256'] and path.stat().st_size==item['bytes']
        assert stat.S_IMODE(path.stat().st_mode)==0o444
print(json.dumps({{'kind':'PUBLIC_SCOPE_BRIDGE_INSTALL','bundle_sha256':bundle,'installed':installed,'all_nine_verified':final,'no_SUT_or_cloud_action':True}},sort_keys=True))
PY
'''


def main():
    manifest = {
        "kind": "PUBLIC_SCOPE_CALLBACK_BRIDGE_MANIFEST_V1",
        "version": 1,
        "tool_freeze_sha256": "33dd522d7b1c498e74848b571537a68a21ea2c815013725ad4a907500eb5309e",
        "tool_execution_build_sha256": "e8ac37bb681661509873ab53bfa35a6c94f93608774b6f87c172cab5b457e16ae",
        "files": {
            name: {"bytes": (TOOLS / name).stat().st_size, "sha256": digest((TOOLS / name).read_bytes())}
            for name in FILES
        },
        "policy_seconds": {
            "original_callback": 120,
            "authority_lease_maximum": 80,
            "APP_snapshot_maximum_age": 30,
            "LOAD_return_margin": 10,
            "APP_minimum_before_provision": 45,
            "APP_maximum_execution": 60,
            "original_GEN_minimum_window": 600,
        },
        "automatic_retry": False,
        "revocation_ACK_implemented": False,
        "wire_encoder_sha256": "c89d03005725cdc5eb36e1969f26d7c2bdc4b067fbcf67c1329133809802ad06",
        "actual_VM_MySQL_SUT_run": False,
        "root_supplies_new_actual_authority_only": True,
    }
    (TOOLS / "manifest.PUBLIC.json").write_bytes(canonical(manifest))
    bundle_sha = digest((TOOLS / "manifest.PUBLIC.json").read_bytes())
    entries = {
        name: {"base64": base64.b64encode((TOOLS / name).read_bytes()).decode(),
               "sha256": digest((TOOLS / name).read_bytes())}
        for name in (*FILES, "manifest.PUBLIC.json")
    }
    groups = []
    pending = {}
    for name, item in entries.items():
        candidate = {**pending, name: item}
        if pending and len(command(candidate, bundle_sha, not groups, False).encode()) > 16500:
            groups.append(pending)
            pending = {name: item}
        else:
            pending = candidate
    groups.append(pending)
    pieces = []
    for index, group in enumerate(groups):
        text = command(group, bundle_sha, index == 0, index == len(groups) - 1)
        assert len(text.encode()) + 300 < 18000
        filename = f"install-part{index + 1:02}.PUBLIC.txt"
        (TOOLS / filename).write_text(text)
        pieces.append({"file": filename, "sha256": digest(text.encode()), "bytes": len(text.encode()),
                       "description_allowance": 300, "files": list(group)})
    template = {
        "kind": "PUBLIC_SCOPE_BRIDGE_CONFIGURATION_V1",
        "bridge_bundle_sha256": bundle_sha,
        "originals": {name: {"path": None, "sha256": None}
                      for name in ("grant", "launch", "supervisor", "binding", "neutral", "admission")},
        "app_phase_dir": None,
        "owner": None,
        "forbidden_key_shas": [None, None],
        "status_path": None,
    }
    (TOOLS / "configuration.template.PUBLIC.json").write_bytes(canonical(template))
    (TOOLS / "delivery.PUBLIC.json").write_bytes(canonical({
        "kind": "PUBLIC_SCOPE_BRIDGE_INSTALL_DELIVERY_V1", "destination": DEST,
        "manifest_sha256": bundle_sha, "parts": pieces,
        "template_is_not_runnable_authority": True, "cloud_actions_executed": False,
    }))
    print(json.dumps({"manifest_sha256": bundle_sha, "parts": pieces}, sort_keys=True))


if __name__ == "__main__":
    main()
