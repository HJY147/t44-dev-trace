"""Offline exact-source date derivation; never executes a cloud or SUT action."""

import gzip
import hashlib
import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD_PROFILE = ROOT / "agents/deployment/v4-f7-20z-20261028/profile-f7-2000"
OLD_P64 = ROOT / "tmp/790_backend_contrast_20261028/p64-f7-window2000"
PROFILE = HERE / "profile"
P64 = HERE / "p64"
STOP = "2026-10-29T12:00:00Z"
OLD_STOP = "2026-10-28T20:00:00Z"
OLD_MANIFEST_SHA = "2af6444892171c1004474379dff699f3ede876c6e7d55e85b72125cbce4626de"
PROFILE_DEST = "/root/t44-r9/r29-code-01/profile"
P64_DEST = "/root/t44-r9/p790-r29-01"
DATE_CHANGES = {
    "790_bootstrap.py": [
        ("datetime(2026, 10, 28, 20, 0, tzinfo=UTC)", "datetime(2026, 10, 29, 12, 0, tzinfo=UTC)")
    ],
    "edge/790_http.py": [
        ("datetime(2026, 10, 28, 20, 0, tzinfo=UTC)", "datetime(2026, 10, 29, 12, 0, tzinfo=UTC)")
    ],
    "transport/790_transfer.py": [
        ("datetime(2026, 10, 28, 20, 0, tzinfo=UTC)", "datetime(2026, 10, 29, 12, 0, tzinfo=UTC)")
    ],
    "edge/790_authority.py": [(OLD_STOP, STOP), ("EXACT_20Z_WINDOW", "EXACT_R29_12Z_WINDOW")],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def replace_once(raw, replacements):
    text = raw.decode()
    for before, after in replacements:
        assert text.count(before) == 1, before
        text = text.replace(before, after)
    return text.encode()


def main():
    old_profile = json.loads((OLD_PROFILE / "profile.json").read_bytes())
    old_manifest_raw = (OLD_P64 / "manifest.json").read_bytes()
    assert sha(old_manifest_raw) == OLD_MANIFEST_SHA
    old_manifest = json.loads(old_manifest_raw)
    proofs = {"profile": [], "p64": []}
    generator = replace_once((OLD_PROFILE / "generation.py").read_bytes(), [(OLD_STOP, STOP)])
    for name, row in old_profile["derived_files"].items():
        old = (OLD_PROFILE / name).read_bytes()
        assert sha(old) == row["sha256"]
        if name == "generation.py":
            new = generator
        elif name == "resource-stream.py":
            new = replace_once(old, [(OLD_STOP, STOP), (old_profile["derived_files"]["generation.py"]["sha256"], sha(generator))])
        else:
            new = old
        write(PROFILE / name, new)
        proofs["profile"].append({"file": name, "parent_sha256": sha(old), "new_sha256": sha(new), "unchanged": old == new})
    p = dict(old_profile)
    p.update(stop_utc=STOP, created_utc=datetime.now(timezone.utc).isoformat(), parent_profile_sha256=sha((OLD_PROFILE / "profile.json").read_bytes()), local_deriver="agents/backend/window-20261029/build.py")
    p["derived_files"] = {name: {"bytes": (PROFILE / name).stat().st_size, "sha256": sha((PROFILE / name).read_bytes())} for name in old_profile["derived_files"]}
    write(PROFILE / "profile.json", canonical(p))
    m = dict(old_manifest)
    for name, row in old_manifest["files"].items():
        old = (OLD_P64 / name).read_bytes()
        assert sha(old) == row["sha256"]
        new = replace_once(old, DATE_CHANGES.get(name, []))
        write(P64 / name, new)
        proofs["p64"].append({"file": name, "parent_sha256": sha(old), "new_sha256": sha(new), "unchanged": old == new, "literal_allowlist": DATE_CHANGES.get(name, [])})
    m.update(window_utc=STOP, supersedes_manifest_sha256=OLD_MANIFEST_SHA, phase_GEN_sha256=sha(generator))
    m["files"] = {name: {"bytes": (P64 / name).stat().st_size, "sha256": sha((P64 / name).read_bytes())} for name in old_manifest["files"]}
    write(P64 / "manifest.json", canonical(m))
    for side in ("APP", "LOAD"):
        template = json.loads((OLD_P64 / f"{side}-configuration.template.PUBLIC.json").read_bytes())
        assert template["transfer_sha256"] == old_manifest["files"]["transport/790_transfer.py"]["sha256"]
        template.update(tools_dir=P64_DEST, manifest_sha256=sha(canonical(m)), transfer_sha256=m["files"]["transport/790_transfer.py"]["sha256"])
        write(HERE / "templates" / f"{side}-configuration.template.PUBLIC.json", canonical(template))
    for mode in ("prep", "pressure"):
        template = json.loads((OLD_P64 / f"{mode}-grant.template.PUBLIC.json").read_bytes())
        template.update(stop_utc=STOP, expires_at=STOP)
        write(HERE / "templates" / f"{mode}-grant.template.PUBLIC.json", canonical(template))
    payload = {}
    for group, source in (("profile", PROFILE), ("p64", P64)):
        for path in sorted(source.rglob("*")):
            if path.is_file():
                payload[group + "/" + path.relative_to(source).as_posix()] = path.read_bytes()
    bundle_manifest = {"kind": "R29_EXACT_PUBLIC_CODE_ONLY_INSTALL", "source_sha": m["product"], "stop_utc": STOP, "targets": {"profile": PROFILE_DEST, "p64": P64_DEST}, "files": {name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in payload.items()}, "no_SUT_or_sessions_or_keys": True, "services_started": False}
    manifest_raw = canonical(bundle_manifest)
    payload["install-manifest.PUBLIC.json"] = manifest_raw
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, raw in sorted(payload.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(raw), 0o444, 0
            info.uid = info.gid = 0
            archive.addfile(info, io.BytesIO(raw))
    packed = gzip.compress(tar_buffer.getvalue(), mtime=0)
    write(HERE / "runtime-bundle.PUBLIC.tar.gz", packed)
    write(HERE / "install-manifest.PUBLIC.json", manifest_raw)
    proofs.update(source_sha=m["product"], stop_utc=STOP, profile_sha256=sha(canonical(p)), p64_manifest_sha256=sha(canonical(m)), generator_sha256=sha(generator), resource_sha256=p["derived_files"]["resource-stream.py"]["sha256"], transfer_sha256=m["files"]["transport/790_transfer.py"]["sha256"], runtime_code_file_count=18, delivered_file_count=20, bundle_members=len(payload), bundle_bytes=len(packed), bundle_sha256=sha(packed), parent_p64_manifest_sha256=OLD_MANIFEST_SHA, legacy_run_id="r28p64gen04", run_id_grammar_unchanged=True, inherited_anchor_unchanged=m["anchor_at"], cloud_or_SUT_actions=False)
    write(HERE / "derivation.PUBLIC.json", canonical(proofs))
    print(json.dumps({key: value for key, value in proofs.items() if key not in ("profile", "p64")}, sort_keys=True))


if __name__ == "__main__":
    main()
