"""PUBLIC11 immutable file scope and two-mount guards; synthetic bytes only, no805private or Docker."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "load805v2", ROOT / "deployment/cloud-reuse/load-diagnostic-v2.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def package(tmp_path):
    p = tmp_path / "public"
    p.mkdir()
    names = ["entry.py", *["file" + str(i) + ".txt" for i in range(10)]]
    lines = []
    for name in names:
        f = p / name
        f.write_bytes(b"synthetic approved PUBLIC only")
        f.chmod(0o444)
        lines.append(hashlib.sha256(f.read_bytes()).hexdigest() + "  " + name)
    manifest = p / "FILES.sha256"
    manifest.write_text("\n".join(lines) + "\n")
    manifest.chmod(0o444)
    p.chmod(0o555)
    yield p, hashlib.sha256(manifest.read_bytes()).hexdigest()
    p.chmod(0o700)


def test_exact_eleven_hashes_and_public_modes(package):
    p, sha = package
    value = module().public_package(p, "FILES.sha256", sha)
    assert len(value["file_hashes"]) == 11 and value["mount_read_only"]


@pytest.mark.parametrize(
    "change", ["extra", "changed_bytes", "writable", "manifest_hash"]
)
def test_public_package_changes_rejected(package, change):
    p, sha = package
    p.chmod(0o700)
    if change == "extra":
        f = p / "extra.py"
        f.write_text("synthetic not approved")
        f.chmod(0o444)
    elif change == "changed_bytes":
        f = p / "entry.py"
        f.chmod(0o600)
        f.write_text("changed")
        f.chmod(0o444)
    elif change == "writable":
        (p / "entry.py").chmod(0o644)
    else:
        sha = "0" * 64
    p.chmod(0o555)
    with pytest.raises(ValueError):
        module().public_package(p, "FILES.sha256", sha)


def inspect_row(value, wrong=False):
    mounts = [
        {
            "Type": "bind",
            "Source": value["data_dir"],
            "Destination": "/diagnostic",
            "RW": True,
        },
        {
            "Type": "bind",
            "Source": value["public_package"]["path"],
            "Destination": "/tool805",
            "RW": wrong,
        },
    ]
    row = [
        "a" * 64,
        value["actual_image_id"],
        {
            "io.t44.calibration.run": value["run_id"],
            "io.t44.calibration.proof": value["proof_raw_sha256"],
            "io.t44.calibration.runtime": value["runtime_binding_sha256"],
            "io.t44.calibration.public": value["public_package"]["manifest_sha256"],
        },
        True,
        mounts,
        {"18205/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18205"}]},
    ]
    return ("\t".join(json.dumps(x) for x in row) + "\n").encode()


@pytest.mark.parametrize("wrong", [False, True])
def test_exact_RW_data_RO_public_mount_roles(tmp_path, monkeypatch, wrong):
    m = module()
    value = {
        "data_dir": "/synthetic/new/data",
        "public_package": {
            "path": "/synthetic/approved/PUBLIC",
            "manifest_sha256": "4" * 64,
        },
        "actual_image_id": "sha256:" + "1" * 64,
        "runtime_config_id": "sha256:" + "2" * 64,
        "run_id": "r9test01",
        "proof_raw_sha256": "3" * 64,
        "runtime_binding_sha256": "5" * 64,
    }
    m.save(tmp_path / "container.json", {"container_id": "a" * 64})
    monkeypatch.setattr(m, "command", lambda *a: inspect_row(value, wrong))
    if wrong:
        with pytest.raises(ValueError, match="RW_DATA_RO_PUBLIC"):
            m.container(tmp_path, value)
    else:
        assert m.container(tmp_path, value)[1] is True


def test_original_82e4_is_preserved():
    assert (
        hashlib.sha256(
            (ROOT / "deployment/cloud-reuse/load-diagnostic.py").read_bytes()
        ).hexdigest()
        == "82e4acc28395bafc88b8917115dd22ee90135f2d6950ccc80920ac6d6e77e76d"
    )
