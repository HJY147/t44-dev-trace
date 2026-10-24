"""Synthetic counter and own-output guards; no collector/proc/Docker/cloud execution."""

import ast
import io
import json
import os
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOST = runpy.run_path(str(ROOT / "deployment/host-resource-sampler.py"))
APP = runpy.run_path(str(ROOT / "deployment/seven-resource-sampler-v3.py"))
EXPECTED = ("/proc/stat", "/proc/meminfo", "/proc/diskstats", "/proc/net/dev", "/proc/net/snmp")


def test_fixed_sources_and_cpu_count_context():
    assert HOST["PROC_FILES"] == APP["PROC_FILES"] == EXPECTED
    assert str(HOST["OUTPUT_PARENT"]) == "/run/t44-relay852"
    tree = ast.parse((ROOT / "deployment/host-resource-sampler.py").read_text())
    modules = {n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)}
    assert not modules.intersection({"subprocess", "socket", "urllib", "requests", "pymysql"})
    assert not any(isinstance(n, ast.Attribute) and n.attr in {"iterdir", "glob", "rglob", "walk"}
                   for n in ast.walk(tree))
    app = (ROOT / "deployment/seven-resource-sampler-v3.py").read_text()
    assert '"cpu_count": os.cpu_count()' in app


def test_complete_synthetic_proc_snapshot(monkeypatch):
    opened = []
    def fake(name, mode):
        opened.append((name, mode))
        return io.BytesIO(b"synthetic cumulative counters\n")
    monkeypatch.setitem(HOST["read_counters"].__globals__, "open", fake)
    result, errors = HOST["read_counters"]()
    assert tuple(result) == EXPECTED and not errors
    assert opened == [(name, "rb") for name in EXPECTED]


def test_missing_tcp_source_is_null_not_proven(monkeypatch):
    def fake(name, mode):
        if name == "/proc/net/snmp":
            raise PermissionError("synthetic-private-marker-must-not-escape")
        return io.BytesIO(b"synthetic\n")
    monkeypatch.setitem(HOST["read_counters"].__globals__, "open", fake)
    values, errors = HOST["read_counters"]()
    assert values["/proc/net/snmp"] is None
    assert errors == [{"source": "/proc/net/snmp", "status": "NOT_PROVEN"}]
    assert "private-marker" not in json.dumps(errors)


def test_oversized_source_not_proven(monkeypatch):
    monkeypatch.setitem(HOST["read_counters"].__globals__, "open",
                        lambda *args: io.BytesIO(b"x" * 262145))
    values, errors = HOST["read_counters"]()
    assert all(value is None for value in values.values())
    assert len(errors) == 5


def test_hash_only_created_inode_and_private_mode(tmp_path, monkeypatch):
    path = tmp_path / "owned-output"
    path.write_bytes(b"synthetic-only")
    path.chmod(0o600)
    meta = path.stat()
    identity = (meta.st_dev, meta.st_ino)
    real_fstat = os.fstat
    def root_fstat(descriptor):
        result = list(real_fstat(descriptor))
        result[4] = 0
        return os.stat_result(result)
    monkeypatch.setattr(HOST["owned_hash"].__globals__["os"], "fstat", root_fstat)
    digest, size = HOST["owned_hash"](path, identity)
    assert len(digest) == 64 and size == len(b"synthetic-only")
    with pytest.raises(ValueError, match="IDENTITY"):
        HOST["owned_hash"](path, (meta.st_dev, meta.st_ino + 1))
    path.chmod(0o644)
    with pytest.raises(ValueError, match="IDENTITY"):
        HOST["owned_hash"](path, identity)
