"""Synthetic resource/TLS/append integrity checks, no Docker, SUT, accounts or cloud."""

import hashlib
import http.client
import importlib.util
import os
import ssl
import subprocess
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "resource_stream", ROOT / "deployment/cloud-reuse/resource-stream.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_cpu_interval_units_and_first_or_reset_are_real_null():
    m = module()
    assert m.cpu_delta(None, 1000000, 1000000000) == (None, "first_sample_no_delta")
    assert m.cpu_delta((1000000, 1000000000), 3000000, 2000000000) == (200.0, None)
    assert m.cpu_delta((3000000, 2000000000), 1, 3000000000)[0] is None
    assert m.cpu_delta((1, 100), 2, 100)[0] is None


def test_proc_rss_pages_and_start_ticks_handle_parentheses_and_spaces(tmp_path):
    m = module()
    parts = ["0"] * 22
    parts[0] = "S"
    parts[19] = "1234"
    parts[21] = "3"
    p = tmp_path / "stat"
    p.write_text("12 (some) name) " + " ".join(parts))
    assert m.proc_stat(p) == {
        "start_ticks": 1234,
        "rss_bytes": 3 * os.sysconf("SC_PAGE_SIZE"),
    }
    parts[21] = "-1"
    p.write_text("12 (name) " + " ".join(parts))
    with pytest.raises(ValueError):
        m.proc_stat(p)


def test_cgroup_keys_are_not_position_dependent_and_memory_not_rss(tmp_path):
    m = module()
    (tmp_path / "cpu.stat").write_text("system_usec 5\nusage_usec 123\nuser_usec 118\n")
    (tmp_path / "memory.current").write_text("9000\n")
    (tmp_path / "memory.stat").write_text("file 7000\nunknown 12\nanon 2000\n")
    assert m.counters(tmp_path) == {
        "cpu_usage_usec": 123,
        "cgroup_memory_bytes": 9000,
        "cgroup_anon_bytes": 2000,
    }


def populated(m, tmp_path):
    sink = m.Sink(tmp_path / "raw.jsonl", 1024 * 1024)
    sink.append(
        {"kind": "resource_header", "source_sha": m.SOURCE, "stream_id": "fixture1"}
    )
    for i in range(2):
        sink.append(
            {
                "kind": "resource_sample",
                "role": "mysql",
                "utc": f"2026-10-25T16:00:0{i * 2}Z",
                "monotonic_ns": 1000000000 + i * 2000000000,
                "cpu_percent": None if i == 0 else 12.5,
                "rss_bytes": 4096,
            }
        )
    sink.append(
        {
            "kind": "resource_final",
            "prefix_sha256": sink.hash.hexdigest(),
            "prefix_bytes": sink.size,
        },
        final=True,
    )
    return sink


def test_full_prefix_tail_hash_and_actual_coverage_do_not_claim_after_only_pass(
    tmp_path,
):
    m = module()
    s = populated(m, tmp_path)
    try:
        assert m.sha(tmp_path / "raw.jsonl") == s.whole_sha
        row = m.summarize(
            tmp_path / "raw.jsonl",
            {
                "stream_id": "fixture1",
                "required_start_utc": "2026-10-25T15:59:59Z",
                "required_end_utc": "2026-10-25T16:00:03Z",
            },
        )
        assert row["received_final_tail"] and row["resource_rows"] == 2
        assert (
            row["at_or_before_required_start"] is False
            and row["at_or_after_required_end"] is False
        )
        assert row["maximum_mysql_sample_start_gap_seconds"] == 2.0
        assert (
            row["rows_with_null_CPU_or_RSS"] == 1
            and row["independent_acceptance_verdict"] is None
        )
        with pytest.raises(ValueError):
            s.append({"later": "forbidden"})
    finally:
        os.close(s.fd)


def test_existing_raw_never_overwritten(tmp_path):
    m = module()
    p = tmp_path / "raw"
    p.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        m.Sink(p, 1024 * 1024)
    assert p.read_bytes() == b"original"


def test_replaced_raw_path_refuses_read_and_original_fd_is_preserved(tmp_path):
    m = module()
    p = tmp_path / "raw"
    s = m.Sink(p, 1024 * 1024)
    try:
        s.append({"x": 1})
        p.rename(tmp_path / "original")
        p.write_bytes(b"other")
        with pytest.raises(ValueError, match="DESCRIPTOR_IDENTITY"):
            s.chunk(0)
        assert (tmp_path / "original").read_bytes() == b'{"x":1}\n'
    finally:
        os.close(s.fd)


def test_same_inode_overwrite_detected_before_sealing(tmp_path):
    m = module()
    p = tmp_path / "raw"
    s = m.Sink(p, 1024 * 1024)
    try:
        s.append({"x": 1})
        with p.open("r+b") as f:
            f.write(b"[")
        with pytest.raises(ValueError, match="PREFIX_BYTES_CHANGED"):
            s.append({"kind": "resource_final"}, final=True)
    finally:
        os.close(s.fd)


def chunk_fields(m):
    body = b"raw original bytes"
    h = {
        "stream_id": "fixture1",
        "app_binding_sha256": "a" * 64,
        "byte_cap": 1024 * 1024,
    }
    headers = {
        "X-Stream-ID": "fixture1",
        "X-Binding-Sha256": "a" * 64,
        "X-Offset": "0",
        "X-Next-Offset": str(len(body)),
        "X-Chunk-Sha256": hashlib.sha256(body).hexdigest(),
        "X-Stream-Bytes": str(len(body)),
        "X-Stream-Sealed": "true",
        "X-Stream-Sha256": "b" * 64,
    }
    return h, headers, body


@pytest.mark.parametrize(
    "field",
    [
        "X-Stream-ID",
        "X-Binding-Sha256",
        "X-Offset",
        "X-Next-Offset",
        "X-Chunk-Sha256",
        "X-Stream-Bytes",
        "X-Stream-Sealed",
        "X-Stream-Sha256",
    ],
)
def test_wrong_identity_offset_hash_or_sealed_state_cannot_append(field):
    m = module()
    h, headers, body = chunk_fields(m)
    headers[field] = "bad"
    with pytest.raises(ValueError):
        m.verify_chunk(h, 0, headers, body)


def test_duplicate_owned_role_does_not_choose_arbitrary_container_or_read_proc(
    monkeypatch,
):
    m = module()
    cid = "a" * 64
    monkeypatch.setattr(
        m,
        "identities",
        lambda v: [[cid, "x", "project1", "mysql", 1, True, False, 0]] * 2,
    )
    monkeypatch.setattr(
        m, "proc_stat", lambda p: pytest.fail("ambiguous resource reached proc")
    )
    rows, _ = m.sample({"project": "project1"}, 1, 0, {})
    mysql = rows[0]
    assert (
        "multiple_role_containers" in mysql["missing_reason"]
        and mysql["cpu_percent"] is None
    )
    assert all(r["rss_bytes"] is None for r in rows)


def test_real_loopback_tls_stream_requires_ca_nonce_single_path_and_exact_bytes(
    tmp_path,
):
    m = module()
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    config = tmp_path / "openssl.cnf"
    config.write_text(
        "[req]\nprompt=no\ndistinguished_name=dn\nx509_extensions=v3\n[dn]\nCN=synthetic resource TLS\n[v3]\nsubjectAltName=IP:127.0.0.1\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,digitalSignature,keyEncipherment,keyCertSign,cRLSign\nextendedKeyUsage=serverAuth\nsubjectKeyIdentifier=hash\n"
    )
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-config",
            str(config),
        ],
        capture_output=True,
        check=True,
        timeout=15,
    )
    (tmp_path / "nonce").write_text("1" * 64)
    sink = populated(m, tmp_path)
    v = {
        "stream_id": "fixture1",
        "app_ip": "127.0.0.1",
        "load_ip": "127.0.0.1",
        "port": 0,
        "certificate": str(cert),
        "key": str(key),
    }
    server = m.server_for(v, tmp_path, sink, "a" * 64)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        ctx = ssl.create_default_context(cafile=str(cert))
        port = server.server_address[1]
        c = http.client.HTTPSConnection("127.0.0.1", port, context=ctx, timeout=3)
        c.request(
            "GET", "/raw", headers={"X-T44-Telemetry-Nonce": "1" * 64, "X-Offset": "0"}
        )
        r = c.getresponse()
        body = r.read()
        assert r.status == 200 and body == (tmp_path / "raw.jsonl").read_bytes()
        h = {
            "stream_id": "fixture1",
            "app_binding_sha256": "a" * 64,
            "byte_cap": 1024 * 1024,
        }
        assert m.verify_chunk(h, 0, dict(r.getheaders()), body) == (len(body), True)
        c.close()
        for path, nonce, status in [
            ("/raw", "wrong", 403),
            ("/raw?other", "1" * 64, 400),
        ]:
            c = http.client.HTTPSConnection("127.0.0.1", port, context=ctx, timeout=3)
            c.request(
                "GET", path, headers={"X-T44-Telemetry-Nonce": nonce, "X-Offset": "0"}
            )
            r = c.getresponse()
            assert r.status == status
            r.read()
            c.close()
        c = http.client.HTTPSConnection(
            "127.0.0.1", port, context=ssl.create_default_context(), timeout=3
        )
        with pytest.raises(ssl.SSLCertVerificationError):
            c.request("GET", "/raw")
        c.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        os.close(sink.fd)
