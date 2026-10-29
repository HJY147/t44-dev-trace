"""Actual loopback TLS and original receiver CLI; synthetic opaque bytes only."""
import argparse
import base64
import datetime as dt
import gzip
import hashlib
import http.client
import importlib.util
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "agents/deployment/opaque-relay-20261029/relay.py"
spec = importlib.util.spec_from_file_location("opaque_relay", CODE)
relay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relay)
SOURCE = None


class Relay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        generated = Path(__file__).parent / "generated-private"
        generated.mkdir(mode=0o700, exist_ok=True)
        cls.root = Path(tempfile.mkdtemp(prefix="tls-", dir=generated))
        cls.cert, cls.key = cls.root / "cert.pem", cls.root / "key.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-subj", "/CN=127.0.0.1", "-addext", "subjectAltName=IP:127.0.0.1",
                        "-days", "1", "-keyout", str(cls.key), "-out", str(cls.cert)],
                       capture_output=True, check=True)
        cls.tools = cls.root / "tools"
        cls.tools.mkdir()
        manifest = json.loads((SOURCE / "manifest.json").read_bytes())
        for name, record in manifest["files"].items():
            value = (SOURCE / name).read_bytes()
            assert relay.digest(value) == record["sha256"] and len(value) == record["bytes"]
            dest = cls.tools / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(value)
        (cls.tools / "manifest.json").write_bytes((SOURCE / "manifest.json").read_bytes())

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="case-", dir=self.root))
        self.export = self.dir / "export"
        self.export.mkdir()
        self.base = {"kind": "T44_OPAQUE_RELAY_APP_V1", "source_sha":
                     "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f",
                     "binding_sha256": "b" * 64, "root_grant_sha256": "c" * 64,
                     "key_sha256": "d" * 64, "nonce": "local-nonce-" + "a" * 32,
                     "app_ip": "127.0.0.1", "load_ip": "127.0.0.1", "port": 0,
                     "producer_unit": "t44-local-producer", "export_dir": str(self.export),
                     "expires_at": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15)).isoformat(),
                     "cost_stop_utc": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15)).isoformat(),
                     "tls_certificate": str(self.cert), "tls_key": str(self.key),
                     "tls_certificate_sha256": relay.digest(self.cert.read_bytes()),
                     "deadline": time.monotonic() + 900, "expires_epoch": time.time() + 900}
        self.ready = True
        self.store = relay.Store(self.base, lambda _: self.ready)
        self.server = relay.private_server(self.base, self.store)
        self.base["port"] = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = dict(self.base, ca_file=str(self.cert),
                           ca_sha256=relay.digest(self.cert.read_bytes()))
        self.raw = os.urandom(37000)
        packed = gzip.compress(self.raw, mtime=0)
        fragments = [packed[i:i + 11800] for i in range(0, len(packed), 11800)]
        self.parts = []
        for i, value in enumerate(fragments):
            record = {"index": i, "parts": len(fragments), "bytes": len(value),
                      "sha256": relay.digest(value), "data": base64.b64encode(value).decode()}
            part = json.dumps(record).encode()
            self.parts.append(part)
            (self.export / ("part-" + str(i) + ".OPAQUE.json")).write_bytes(part)
        self.metadata = {"source_sha": self.base["source_sha"],
                         "phase_binding_sha256": self.base["binding_sha256"],
                         "root_grant_sha256": self.base["root_grant_sha256"],
                         "part_count": len(self.parts), "compressed_bytes": len(packed),
                         "compressed_sha256": relay.digest(packed), "raw_bytes": len(self.raw),
                         "raw_sha256": relay.digest(self.raw),
                         "original_public_meta": {"key_sha256": self.base["key_sha256"]}}
        self.meta_bytes = json.dumps(self.metadata).encode()
        (self.export / "metadata.PUBLIC.json").write_bytes(self.meta_bytes)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)
        self.assertFalse(self.thread.is_alive())

    def test_tls_original_receiver_and_once_consumer_capture(self):
        manifest_raw = (self.tools / "manifest.json").read_bytes()
        manifest = json.loads(manifest_raw)
        config = {"kind": "P790_F7_LOAD_CONFIGURATION_V4", "source_sha": self.base["source_sha"],
                  "binding_sha256": self.base["binding_sha256"],
                  "root_grant_sha256": self.base["root_grant_sha256"],
                  "key_sha256": self.base["key_sha256"], "ca_sha256": self.client["ca_sha256"],
                  "tools_dir": str(self.tools), "manifest_sha256": relay.digest(manifest_raw),
                  "transfer_sha256": manifest["files"]["transport/790_transfer.py"]["sha256"],
                  "work_dir": str(self.dir / "original-work")}
        original = self.dir / "original-load.PUBLIC.json"
        original.write_text(json.dumps(config))
        load_config = dict(self.client, kind="T44_OPAQUE_RELAY_LOAD_V1",
                           max_wait_seconds=20, load_configuration=str(original),
                           load_configuration_sha256=relay.digest(original.read_bytes()),
                           receiver_sha256=manifest["files"]["790_receive.py"]["sha256"],
                           consumer_sha256=manifest["files"]["790_consumer.py"]["sha256"],
                           output_dir=str(self.dir / "relay-output"))
        path = self.dir / "relay-load.PUBLIC.json"
        path.write_text(json.dumps(load_config))
        checked = relay.configure(path, relay.digest(path.read_bytes()), "LOAD")
        invoked = []

        def invoke(c, output, argv, name, cap):
            invoked.append(name)
            if name == "consumer-once":
                return  # Captured explicitly; no SUT, decryption or matrix is executed.
            relay.run_original(c, output, argv, name, cap)

        result = relay.load(checked, invoke)
        self.assertTrue(result["consumer_started_once"])
        self.assertEqual(invoked.count("consumer-once"), 1)
        imported = Path(config["work_dir"])
        self.assertEqual(json.loads((imported / "metadata.PUBLIC.json").read_bytes()), self.metadata)
        actual = b"".join((imported / ("part-" + str(i) + ".OPAQUE")).read_bytes()
                          for i in range(len(self.parts)))
        self.assertEqual(gzip.decompress(actual), self.raw)
        with self.assertRaises(FileExistsError):
            relay.load(checked, invoke)
        self.assertEqual(invoked.count("consumer-once"), 1)

    def test_unready_does_not_read_half_metadata(self):
        self.ready = False
        (self.export / "metadata.PUBLIC.json").write_bytes(b'{"incomplete"')
        self.assertIsNone(relay.fetch(self.client, "metadata", relay.META_CAP))
        (self.export / "metadata.PUBLIC.json").write_bytes(self.meta_bytes)
        self.ready = True
        self.assertEqual(relay.fetch(self.client, "metadata", relay.META_CAP), self.meta_bytes)

    def test_success_unit_with_half_file_refuses_not_retryable(self):
        (self.export / "part-1.OPAQUE.json").write_bytes(b'{"half"')
        with self.assertRaisesRegex(ValueError, "OPAQUE_HTTP_NOT_READY_OR_SUCCESS"):
            relay.fetch(self.client, "metadata", relay.META_CAP)
        self.assertIsNone(self.store.snapshot)

    def test_changed_part_digest_refuses(self):
        item = json.loads(self.parts[0])
        item["sha256"] = "0" * 64
        (self.export / "part-0.OPAQUE.json").write_text(json.dumps(item))
        with self.assertRaises(ValueError):
            relay.fetch(self.client, "metadata", relay.META_CAP)

    def test_exact_source_and_scope_refusal(self):
        self.base["load_ip"] = "127.0.0.2"
        with self.assertRaises((OSError, ssl.SSLError)):
            relay.fetch(self.client, "metadata", relay.META_CAP)

    def test_wrong_CA_rejected(self):
        other = self.dir / "other.pem"
        other_key = self.dir / "other-key.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-subj", "/CN=other", "-days", "1", "-keyout", str(other_key),
                        "-out", str(other)], capture_output=True, check=True)
        with self.assertRaises(ssl.SSLCertVerificationError):
            relay.fetch(dict(self.client, ca_file=str(other)), "metadata", relay.META_CAP)

    def test_no_directory_or_arbitrary_file_route(self):
        with self.assertRaises(ValueError):
            relay.fetch(self.client, "../private/input.json", relay.META_CAP)

    def test_symlink_and_oversized_source_rejected(self):
        p = self.export / "part-0.OPAQUE.json"
        p.unlink()
        p.symlink_to(self.export / "part-1.OPAQUE.json")
        with self.assertRaises(ValueError):
            relay.fetch(self.client, "metadata", relay.META_CAP)

    def test_atomic_publication_no_overwrite(self):
        path = self.dir / "published"
        relay.publish(path, b"original")
        with self.assertRaises(FileExistsError):
            relay.publish(path, b"replacement")
        self.assertEqual(path.read_bytes(), b"original")
        self.assertTrue(list(self.dir.glob(".unpublished-*")))

    def test_mid_body_disconnect_is_not_complete_metadata(self):
        class Cut(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", "9")
                self.send_header("X-T44-SHA256", relay.digest(b"123456789"))
                self.end_headers()
                self.wfile.write(b"123")
                self.close_connection = True

        self.server.RequestHandlerClass = Cut
        with self.assertRaises((ValueError, http.client.IncompleteRead)):
            relay.fetch(self.client, "metadata", relay.META_CAP)

    def test_cost_stop_is_distinct_and_expired_cost_refuses(self):
        config = dict(self.base, port=self.server.server_port,
                      cost_stop_utc="2000-01-01T00:00:00+00:00")
        path = self.dir / "expired-cost.json"
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "RELAY_AND_COST_WINDOW"):
            relay.configure(path, relay.digest(path.read_bytes()), "APP")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", required=True, type=Path)
    args, rest = parser.parse_known_args()
    SOURCE = args.tools.resolve()
    unittest.main(argv=[sys.argv[0], *rest], verbosity=2)
