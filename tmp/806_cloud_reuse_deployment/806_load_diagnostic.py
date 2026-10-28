"""Mocked Docker lease guards; no real container, port, app environment or diagnostic script execution."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "load_diagnostic", ROOT / "deployment/cloud-reuse/load-diagnostic.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def fixture(tmp_path, m):
    tmp_path.chmod(0o700)
    (tmp_path / "receipts").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "controller.py").write_text("synthetic controller")
    (tmp_path / "controller.py").chmod(0o600)
    v = {
        "kind": "pure-synthetic-linux-calibration",
        "name": "t44-cal-example1",
        "run_id": "example1",
        "data_dir": str(tmp_path / "data"),
        "port": 18205,
        "max_seconds": 900,
        "controller_sha256": m.sha(tmp_path / "controller.py"),
        "actual_image_id": "sha256:" + "1" * 64,
        "original_config_id": "sha256:" + "2" * 64,
        "image_alias": "t44-official-python:checked",
        "proof_raw_sha256": "3" * 64,
    }
    m.save(tmp_path / "binding.json", v)
    return v


def inspector(v, extra=False):
    mounts = [
        {"Type": "bind", "Source": v["data_dir"], "Destination": "/diagnostic"},
        {"Type": "tmpfs", "Destination": "/tmp"},
    ]
    if extra:
        mounts.append(
            {"Type": "bind", "Source": "/synthetic/app.env", "Destination": "/bad"}
        )
    return (
        "\t".join(
            json.dumps(x)
            for x in [
                "a" * 64,
                v["actual_image_id"],
                {
                    "io.t44.calibration.run": v["run_id"],
                    "io.t44.calibration.proof": v["proof_raw_sha256"],
                },
                True,
                mounts,
                {"18205/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18205"}]},
            ]
        )
        + "\n"
    ).encode()


class Socket:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def bind(self, address):
        assert address == ("127.0.0.1", 18205)


def test_actual_run_argv_has_labels_one_data_mount_and_bounded_lifespan(
    tmp_path, monkeypatch
):
    m = module()
    v = fixture(tmp_path, m)
    calls = []

    def command(argv, **kwargs):
        argv = list(map(str, argv))
        calls.append(argv)
        if "run" in argv:
            return ("a" * 64 + "\n").encode()
        if "inspect" in argv:
            return inspector(v)
        return b"Python 3.12.synthetic\n"

    monkeypatch.setattr(m, "command", command)
    monkeypatch.setattr(m.socket, "socket", Socket)
    result = m.operate(SimpleNamespace(action="start", directory=tmp_path))
    assert result["success"]
    run = calls[0]
    assert (
        "io.t44.calibration.run=example1" in run
        and "io.t44.calibration.proof=" + "3" * 64 in run
    )
    assert run.count("--mount") == 1 and "127.0.0.1:18205:18205" in run
    assert not any(
        ".env" in part or "MYSQL" in part or "docker.sock" in part for part in run
    )
    compile(run[-1], "lifespan.py", "exec")
    assert "wall=" in run[-1] and "time.monotonic" in run[-1]


def test_any_extra_host_mount_rejects_before_stop_or_exec(tmp_path, monkeypatch):
    m = module()
    v = fixture(tmp_path, m)
    m.save(tmp_path / "container.json", {"container_id": "a" * 64})
    monkeypatch.setattr(m, "command", lambda *a, **k: inspector(v, True))
    with pytest.raises(ValueError, match="MOUNT_OR_LOOPBACK"):
        m.container(tmp_path, v)


def test_unapproved_script_bytes_reject_before_chown_or_Docker_exec(
    tmp_path, monkeypatch
):
    m = module()
    v = fixture(tmp_path, m)
    m.save(
        tmp_path / "container.json",
        {"container_id": "a" * 64, "stop_epoch": m.time.time() + 900},
    )
    (tmp_path / "data/tool.py").write_text("synthetic")
    calls = []
    monkeypatch.setattr(
        m, "command", lambda argv, **k: calls.append(argv) or inspector(v)
    )
    monkeypatch.setattr(m.os, "chown", lambda *a: pytest.fail("bad script adopted"))
    with pytest.raises(ValueError, match="SCRIPT_BYTES"):
        m.operate(
            SimpleNamespace(
                action="exec",
                directory=tmp_path,
                script="tool.py",
                script_sha256="0" * 64,
                detach=False,
            )
        )
    assert len(calls) == 1
