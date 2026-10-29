"""Provider -> original JSON receipt -> published pure adapter.validate, synthetic inputs only."""

import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import time
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = ROOT.parents[1]
ADAPTER_PATH = REPOSITORY / "tmp/772_independent_perf_20261029/PUBLIC/ADAPTER_0B_V24.py"
ADAPTER_SHA = "694fc3aa09aa6442a1763f3866a24ac274cc0b76f052cd98dd4cf82f346db938"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


W = load(ROOT / "deployment/cloud-reuse/r30-window.py", "r30_receipt_provider")


class NeutralReceiptContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if hashlib.sha256(ADAPTER_PATH.read_bytes()).hexdigest() != ADAPTER_SHA:
            raise ValueError("EXACT_PUBLISHED_PUBLIC_ADAPTER_REQUIRED")
        cls.qa = load(ADAPTER_PATH, "published_0b_adapter")
        cls.a = W.artifact()
        cls.package = ROOT / "tmp/761_deployment_preparation_r30/official-artifact-12880320744"
        cls.bundle_bytes = (cls.package / "backend-bundle-manifest.json").read_bytes()
        cls.source_bytes = (cls.package / "source-manifest.json").read_bytes()
        cls.bundle = json.loads(cls.bundle_bytes)
        cls.source = json.loads(cls.source_bytes)
        cls.observed = {"uid": 10001, "package_origin": "/app/backend/t44/__init__.py",
                        "python_version": "SYNTHETIC DEPLOYMENT FIXTURE; not a runtime observation",
                        "sys_executable": "/usr/local/bin/python", "business_env_absent": True,
                        "files": [r for r in cls.source["files"] if r["path"] not in cls.a.RUNTIME_EXCLUDED]}
        cls.scratch = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        cls.base = Path(cls.scratch.name).resolve()
        key, cert = cls.base / "synthetic-test-only.key", cls.base / "synthetic-test-only.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                        "-subj", "/CN=SYNTHETIC-DEPLOYMENT-RECEIPT-TEST-ONLY", "-keyout", str(key), "-out", str(cert)],
                       capture_output=True, check=True, timeout=15)
        cls.ca = cert.read_bytes()
        key.unlink()  # Only an ephemeral synthetic TLS parser fixture, never deployed or committed.

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def receipt(self, *, backend_error=None):
        path = self.base / (self.id().split(".")[-1] + ".PUBLIC.json")
        args = SimpleNamespace(package=self.package, manifest_sha256=self.qa.TARGET["backend_bundle_manifest_sha256"], receipt=path)
        before = SimpleNamespace(returncode=1, stderr=b"No such image", stdout=b"")
        provider_result = (self.bundle, self.source, self.bundle["image_identity_proof"], copy.deepcopy(self.observed))
        with patch.object(W, "os", SimpleNamespace(geteuid=lambda: 0)), \
                patch.object(W, "platform", SimpleNamespace(system=lambda: "Linux", machine=lambda: "x86_64")), \
                patch.object(W, "artifact", return_value=self.a), \
                patch.object(subprocess, "run", return_value=before), \
                patch.object(self.a, "command", return_value=b"synthetic image load seam; no Docker"), \
                patch.object(W, "backend", return_value=provider_result, side_effect=backend_error):
            W.import_backend(args)
        return path, path.read_bytes()

    def packet(self, path, receipt):
        now = time.time()

        def utc(epoch):
            return datetime.fromtimestamp(epoch, UTC).isoformat().replace("+00:00", "Z")

        start, end = now + 10, now + 810
        sessions = {role: {"token": "SYNTHETIC-NOT-AUTHENTICATION-" + role, "user_id": number,
                           "project_ids": list(range(1, 41)), "scopes": ["escalation:write"] if role == "service" else [],
                           "expires_at": utc(end + 120)}
                    for number, role in enumerate(["manager", "developer", "reviewer", "service"], 1)}
        clients = []
        for client in range(400):
            pid = client % 40 + 1
            clients.append({"client_id": client, "project_id": pid, "project_manager_ids": [1],
                            "transition_task": {"id": 2 * client + 1, "project_id": pid, "state": 2, "owner_id": 2,
                                                "plan": {"planned_end": utc(end + 86460)}},
                            "escalation_task": {"id": 2 * client + 2, "project_id": pid, "state": 1, "schedule_version": 1},
                            "escalation_event": {"task_id": 2 * client + 2, "project_id": pid, "schedule_version": 1, "rule_version": 1}})
        files = {"source_manifest": self.source_bytes, "backend_bundle_manifest": self.bundle_bytes,
                 "backend_import_receipt": receipt, "ca": self.ca}
        packet = {"schema": "NEUTRAL_772_INPUTS_V2_0B_V24", "run_id": "synthetic-r30-receipt-contract",
                  "packet_nonce": "a" * 64, "created_at": utc(now),
                  "window": {"start_utc": utc(start), "end_utc": utc(end), "cost_stop_utc": utc(end + 90)},
                  "identity": self.qa.TARGET.copy(), "loaded_receipt_sha256": self.qa.sha(receipt),
                  "loaded_receipt_reference": {"original_path": str(path), "observed_at": utc(now), "sha256": self.qa.sha(receipt)},
                  "environment": {"origin": "https://10.0.0.1:26445", "connect_ip": "10.0.0.1", "ca_sha256": self.qa.sha(self.ca)},
                  "sessions": sessions, "inventory": {"schema": "772-inventory-v1", "captured_at": utc(now), "rule_version": 1, "clients": clients},
                  "fixture_sha256": "f" * 64, "counts": {"projects": 40, "tasks": 800, "dependencies": 0, "reviews": 0, "decisions": 0}}
        packet["binding_sha256"] = self.qa.sha(self.qa.encoded(packet))
        return packet, files, now

    def test_original_provider_json_passes_published_pure_validate(self):
        path, raw = self.receipt()
        packet, files, now = self.packet(path, raw)
        result = self.qa.validate(packet, files, packet["run_id"], now=now)
        self.assertEqual(result["actual_import_receipt_runtime_files"], 60)

    def test_provider_preserves_observed_structure_and_actual_count(self):
        _, raw = self.receipt()
        value = json.loads(raw)
        self.assertEqual(value["package_resolution"], self.observed)
        self.assertEqual(value["full_runtime_files"], len(self.observed["files"]))
        self.assertEqual(len(value["package_resolution"]["files"]), 60)

    def test_adapter_rejects_old_string_with_all_hashes_rebound(self):
        path, raw = self.receipt()
        value = json.loads(raw)
        value["package_resolution"] = "old fixed description; must not pass"
        packet, files, now = self.packet(path, self.qa.encoded(value))
        with self.assertRaisesRegex(self.qa.Stop, "ACTUAL_IDENTITY_AND_PACKAGE_RESOLUTION_REQUIRED"):
            self.qa.validate(packet, files, packet["run_id"], now=now)

    def test_adapter_rejects_receipt_bytes_changed_after_binding(self):
        path, raw = self.receipt()
        packet, files, now = self.packet(path, raw)
        files["backend_import_receipt"] += b"\n"
        with self.assertRaisesRegex(self.qa.Stop, "ACTUAL_IMPORT_RECEIPT_BYTES_BINDING"):
            self.qa.validate(packet, files, packet["run_id"], now=now)

    def test_failed_backend_validation_does_not_publish_receipt(self):
        with self.assertRaisesRegex(ValueError, "SYNTHETIC backend validation refused"):
            self.receipt(backend_error=ValueError("SYNTHETIC backend validation refused"))
        self.assertFalse((self.base / (self.id().split(".")[-1] + ".PUBLIC.json")).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
