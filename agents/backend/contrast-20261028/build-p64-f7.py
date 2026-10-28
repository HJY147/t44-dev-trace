"""Offline, deterministic scope bridge manifest and small public installation commands."""

import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tmp/790_backend_contrast_20261028/p64-f7-window1600"
DEST = "/root/t44-r9/p790-f7-1600-01"
FILES = (
    "790_bootstrap.py",
    "790_host.py",
    "790_load.py",
    "790_budget.py",
    "790_producer.py",
    "790_consumer.py",
    "790_receive.py",
    "data/790_select.py",
    "data/790_stage1.py",
    "edge/790_http.py",
    "edge/790_stage2.py",
    "edge/790_authority.py",
    "transport/790_transfer.py",
)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def command(entries, manifest_sha, first, final):
    packed = base64.b64encode(gzip.compress(canonical(entries), mtime=0)).decode()
    return f"""python3 - <<'PY'
import base64,gzip,hashlib,json,os,pathlib,stat
root=pathlib.Path({DEST!r})
bundle={manifest_sha!r}
first={first!r}
final={final!r}
data=json.loads(gzip.decompress(base64.b64decode({packed!r},validate=True)))
def sha(raw): return hashlib.sha256(raw).hexdigest()
def write(path,raw,mode):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    os.fchmod(fd,mode)
    try:
        with os.fdopen(fd,'wb',closefd=False) as out:
            out.write(raw);out.flush();os.fsync(fd)
    finally: os.close(fd)
if first:
    root.mkdir(mode=0o755)
    root.chmod(0o755)
    write(root/'install-bundle.PUBLIC.json',(json.dumps({{'bundle_sha256':bundle}},sort_keys=True)+'\\n').encode(),0o444)
assert root.is_dir() and not root.is_symlink() and root.resolve()==root
assert json.loads((root/'install-bundle.PUBLIC.json').read_text())=={{'bundle_sha256':bundle}}
installed=[]
for name,item in data.items():
    assert not pathlib.PurePosixPath(name).is_absolute() and '..' not in pathlib.PurePosixPath(name).parts and name in {list(FILES) + ["manifest.json"]!r}
    target=root/name
    target.parent.mkdir(parents=True,exist_ok=True)
    assert target.parent.resolve()==target.parent
    target.parent.chmod(0o755)
    raw=item['text'].encode('utf-8')
    assert sha(raw)==item['sha256']
    write(root/name,raw,0o444)
    installed.append({{'name':name,'sha256':sha(raw),'bytes':len(raw)}})
if final:
    raw=(root/'manifest.json').read_bytes();assert sha(raw)==bundle
    for name,item in json.loads(raw)['files'].items():
        path=root/name;assert path.is_file() and not path.is_symlink()
        assert sha(path.read_bytes())==item['sha256'] and path.stat().st_size==item['bytes']
        assert stat.S_IMODE(path.stat().st_mode)==0o444
print(json.dumps({{'kind':'PUBLIC_SCOPE_BRIDGE_INSTALL','bundle_sha256':bundle,'installed':installed,'all_thirteen_verified':final,'no_SUT_or_cloud_action':True}},sort_keys=True))
PY
"""


def main():
    manifest = {
        "kind": "p790-exact-f7-short-diagnostic-bundle-v4",
        "tool_version": 4,
        "product": "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f",
        "supersedes_manifest_sha256": "0ef08aab3e14887b703c9a2fa5e5265d60fbbcb4172d1d6deb20b5f746df048a",
        "window_utc": "2026-10-28T16:00:00Z",
        "files": {
            name: {
                "bytes": (TOOLS / name).stat().st_size,
                "sha256": digest((TOOLS / name).read_bytes()),
            }
            for name in FILES
        },
        "approved_scope_bridge_dependency": "e5512dd264a2199bb599742ea72f671d184ab5e41a3d102bed498d49b244d5f7",
        "phase_budget_helper_sha256": "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d",
        "phase_GEN_sha256": "6b2da1de7d494527447078ba5ec427edf5a23f203129d5149f20d66a0b2410fd",
        "seed": 44,
        "anchor_at": "2026-10-28T04:00:00Z",
        "session_ttl_seconds": 600,
        "cohorts": [["baseline1", 1, 20, 0], ["warmup40", 40, 5, 1], ["measure400", 400, 5, 41]],
        "request_totals": [80, 800, 8000],
        "think_time": 0,
        "default_without_root_grant": "REFUSE",
        "automatic_retry": False,
        "formal600s_authorization": False,
        "actual_cloud_SUT_run": False,
    }
    (TOOLS / "manifest.json").write_bytes(canonical(manifest))
    bundle_sha = digest((TOOLS / "manifest.json").read_bytes())
    entries = {
        name: {
            "text": (TOOLS / name).read_text(),
            "sha256": digest((TOOLS / name).read_bytes()),
        }
        for name in (*FILES, "manifest.json")
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
        pieces.append(
            {
                "file": filename,
                "sha256": digest(text.encode()),
                "bytes": len(text.encode()),
                "description_allowance": 300,
                "files": list(group),
            }
        )
    for old in TOOLS.glob("install-part*.PUBLIC.txt"):
        if old.name not in {item["file"] for item in pieces}:
            old.unlink()
    common = {
        "source_sha": manifest["product"],
        "binding_sha256": None,
        "tools_dir": DEST,
        "manifest_sha256": bundle_sha,
        "namespace": None,
        "root_grant_sha256": None,
        "key_sha256": None,
        "transfer_sha256": manifest["files"]["transport/790_transfer.py"]["sha256"],
        "ca_sha256": None,
    }
    app = {
        **common,
        "kind": "P790_F7_APP_CONFIGURATION_V4",
        "phase_dir": None,
        "output_dir": None,
        "public_key_file": None,
        "fixture_name": None,
        "split_name": None,
        "budget_receipt": None,
        "budget_receipt_sha256": None,
        "root_grant": None,
        "scope_bridge_dir": "/root/t44-r9/scope-bridge-v3-01",
        "mirror_path": None,
        "mirror_sha256": None,
        "python_image_id": None,
    }
    load = {
        **common,
        "kind": "P790_F7_LOAD_CONFIGURATION_V4",
        "work_dir": None,
        "mirror_dir": None,
        "mirror_binding_sha256": None,
        "control_sha256": None,
        "private_key": None,
        "expected_host": None,
        "python_image": None,
        "python_image_id": None,
    }
    for side, value in (("APP", app), ("LOAD", load)):
        (TOOLS / (side + "-configuration.template.PUBLIC.json")).write_bytes(canonical(value))
    for mode in ("prep", "pressure"):
        grant = {
            key: None
            for key in (
                "run_id",
                "binding_sha256",
                "namespace",
                "database",
                "api_workers",
                "backend_image_id",
                "source_proof_sha256",
                "issued_at",
                "session_nonce",
                "roles",
            )
        }
        grant.update(
            {
                "kind": "ROOT_P_" + mode.upper() + "_GRANT_V4",
                "admitted": False,
                "source_sha": manifest["product"],
                "source_file_count": 53,
                "seed": 44,
                "anchor_at": manifest["anchor_at"],
                "stop_utc": manifest["window_utc"],
                "expires_at": manifest["window_utc"],
                "no_automatic_retry": True,
                "HTTP_authorized": mode == "pressure",
                "cohorts": manifest["cohorts"],
                "session_ttl_seconds": 600,
                "formal_performance_authorized": False,
            }
        )
        (TOOLS / (mode + "-grant.template.PUBLIC.json")).write_bytes(canonical(grant))
    (TOOLS / "delivery.PUBLIC.json").write_bytes(
        canonical(
            {
                "kind": "P790_F7_INSTALL_DELIVERY_V4",
                "destination": DEST,
                "manifest_sha256": bundle_sha,
                "parts": pieces,
                "template_is_not_runnable_authority": True,
                "cloud_actions_executed": False,
            }
        )
    )
    print(json.dumps({"manifest_sha256": bundle_sha, "parts": pieces}, sort_keys=True))


if __name__ == "__main__":
    main()
