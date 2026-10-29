"""Real Git/source/generic build functions; Docker/image observation explicitly mocked."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("final_bundle", ROOT / "deployment/cloud-reuse/final-image-bundle.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


class FinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(dir=ROOT / "tmp/753_deployment_final_window")
        cls.root = Path(cls.tmp.name)
        cls.repo = cls.root / "source"
        g, raw, _ = F.source_data(ROOT, "9ac926d5381a8154dcbc87036bb316acc1fa201f")
        g.extract_context(raw, cls.repo)
        (cls.repo / "compose.yaml").write_bytes(g.command(["git", "-C", ROOT, "show", "9ac926d5:compose.yaml"]))
        with (cls.repo / "backend/requirements.lock").open("a") as out:
            out.write("\n# SYNTHETIC sqlglot lock seam, never installed\n")
        (cls.repo / "backend/t44/synthetic_test_only.py").write_text("# SYNTHETIC new file; no application execution\n")
        for cmd in (["git", "init", "--quiet"], ["git", "add", "."],
                    ["git", "-c", "user.name=Deployment Mock", "-c", "user.email=mock@example.invalid", "commit", "--quiet", "-m", "synthetic source fixture"]):
            subprocess.run(cmd, cwd=cls.repo, check=True, capture_output=True)
        cls.source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cls.repo).decode().strip()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def build(self, suffix):
        output = self.root / suffix
        g, raw, files = F.source_data(self.repo, self.source)
        original = g.command
        calls = []
        source_hash = F.digest(raw)
        def command(argv, *, timeout=600):
            cmd = list(map(str, argv))
            if cmd[0] != "docker":
                return original(cmd, timeout=timeout)
            calls.append(cmd)
            if "inspect" in cmd:
                alias = cmd[-1]
                role = next((r for r in g.PINS if r in alias), "backend" if "backend" in alias else "web")
                labels = {"org.opencontainers.image.revision": self.source, "io.t44.source-archive-sha256": source_hash} if role in {"backend", "web"} else {}
                return json.dumps([{"Id": "sha256:" + F.digest(role.encode()), "Os": "linux", "Architecture": "amd64",
                    "RepoDigests": [g.PINS[role]] if role in g.PINS else [], "Config": {"Labels": labels}}]).encode()
            if cmd[3:5] == ["image", "save"]:
                Path(cmd[6]).write_bytes(b"SYNTHETIC IMAGE ARCHIVE SEAM; not a real image")
            return b""
        g.command = command
        p = SimpleNamespace(scan_archive=lambda _: None, actual_image=lambda _: None,
             prove_role=lambda graph, role, row, source, actual: {"success": True, "actual_id": row["image_id"], "config_id": row["image_id"], "identity_kind": "MOCK_ONLY"})
        def observe(_):
            rows = F.context_rows(output / "work/context", files)
            return {"uid": 10001, "business_env_absent": True, "package_origin": "/app/backend/t44/__init__.py", "files": F.runtime_rows(rows)}
        with patch.object(F, "generic", return_value=g), patch.object(F, "proof", return_value=p), \
             patch.object(F, "archive_config_ids", side_effect=lambda graph, images: {r: row["image_id"] for r, row in images.items()}), \
             patch.object(F, "observe_runtime", side_effect=observe):
            result = F.build(self.repo, self.source, output)
        return output, result, calls

    def test_new_source_lock_and_count_real_generic_build_two_only(self):
        out, result, calls = self.build("positive")
        source = json.loads((out / "source-manifest.json").read_bytes())
        self.assertNotEqual(source["dependency_lock_sha256"], F.generic().EXPECTED_LOCK)
        self.assertEqual(source["dependency_lock_sha256"], F.sha(self.repo / "backend/requirements.lock"))
        self.assertTrue(any(r["path"].endswith("synthetic_test_only.py") for r in source["backend_runtime_files"]))
        saved = [c for c in calls if c[3:5] == ["image", "save"] and len(c[7:]) == 2]
        self.assertEqual(saved[0][7:], ["t44-backend:src-" + self.source, "t44-web:src-" + self.source])
        self.assertEqual(result["status"], "BUILT_NOT_ROOT_APPROVED_OR_LOADED")
        F.verify(out, result["manifest_sha256"])

    def test_actual_bytes_and_nonroot_dynamic_set_refuse(self):
        out, result, _ = self.build("negative")
        source = json.loads((out / "source-manifest.json").read_bytes())
        observed = json.loads((out / "actual-runtime-files.json").read_bytes())
        for mutate in (lambda x: x.update(uid=0), lambda x: x["files"].pop(), lambda x: x.update(business_env_absent=False)):
            data = json.loads(json.dumps(observed))
            mutate(data)
            with self.assertRaises(ValueError):
                F.verify_runtime(data, source["files"])
        (out / "actual-runtime-files.json").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            F.verify(out, result["manifest_sha256"])

    def test_real_derive_binding_actual_9e_lock_entry_and_observer_horizon(self):
        out, result, _ = self.build("derive-input")
        stop = datetime.now(UTC).replace(microsecond=0) + timedelta(minutes=35)
        args = SimpleNamespace(package=out, manifest_sha256=result["manifest_sha256"], run_id="r30final02",
            stop_utc=stop.strftime("%Y-%m-%dT%H:%M:%SZ"), cost_stop_utc=(stop + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"), output=self.root / "derived")
        F.derive(args)
        profile = json.loads((args.output / "profile.json").read_bytes())
        budget = F.load(args.output / "mysql-budget.py", F.BUDGET_SHA)
        self.assertEqual(budget.KIND, F.KIND)
        self.assertIn('HARDSTOP = "' + args.cost_stop_utc + '"', (args.output / "resource-stream.py").read_text())
        self.assertIn('HARDSTOP = "' + args.stop_utc + '"', (args.output / "generation.py").read_text())
        phase = self.root / "phase"
        phase.mkdir(mode=0o700)
        F.save(phase / "binding.json", {"generation_kind": F.KIND})
        binding_sha = F.sha(phase / "binding.json")
        self.assertEqual(budget.checked_binding(phase, binding_sha)["generation_kind"], F.KIND)
        with budget.operation_lock(phase, binding_sha):
            self.assertTrue((phase / ".v4-operation.lock").is_file())
        self.assertEqual(profile["source_sha"], self.source)

    def test_runtime_wrappers_bind_original_new_source_profile(self):
        out, result, _ = self.build("runtime-input")
        stop = datetime.now(UTC).replace(microsecond=0) + timedelta(minutes=35)
        gen = self.root / "runtime-gen"
        F.derive(SimpleNamespace(package=out, manifest_sha256=result["manifest_sha256"], run_id="r30final03",
            stop_utc=stop.strftime("%Y-%m-%dT%H:%M:%SZ"), cost_stop_utc=(stop + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"), output=gen))
        template = F.load(ROOT / "deployment/cloud-reuse/final-runtime-profile.py", F.sha(ROOT / "deployment/cloud-reuse/final-runtime-profile.py"))
        source = json.loads((out / "source-profile.PUBLIC.json").read_bytes())
        args = SimpleNamespace(source_profile=out / "mock-root-approved-profile.json", source_profile_sha256=None,
            source_manifest=out / "source-manifest.json", gen_profile=gen, gen_profile_sha256=F.sha(gen / "profile.json"), output=self.root / "runtime-output")
        source["root_approved"] = True  # SYNTHETIC local fixture only; never a real admission.
        F.save(args.source_profile, source)
        args.source_profile_sha256 = F.sha(args.source_profile)
        template.derive(args)
        admin = F.load(args.output / "r30-neutral-admin.py", F.sha(args.output / "r30-neutral-admin.py"))
        http = F.load(args.output / "http-prepare.py", F.sha(args.output / "http-prepare.py"))
        self.assertEqual(admin.SOURCE, self.source)
        self.assertEqual(http.CONFIG, source["backend_config_id"])
        self.assertEqual(http.ADMIN_SHA, F.sha(args.output / "r30-neutral-admin.py"))
        plan = {"source_profile": {"path": "/neutral-input/source-profile.PUBLIC.json", "sha256": args.source_profile_sha256}}
        self.assertEqual(http._source_profile(args, admin.pinned, plan), args.source_profile.read_bytes())
        plan["source_profile"]["sha256"] = "00" * 32
        with self.assertRaises(ValueError):
            http._source_profile(args, admin.pinned, plan)

    def test_encrypted_backup_real_openssl_full_local_decryption(self):
        backup = F.load(ROOT / "deployment/cloud-reuse/final-app-backup.py", F.sha(ROOT / "deployment/cloud-reuse/final-app-backup.py"))
        folder = self.root / "backup-roundtrip"
        folder.mkdir(mode=0o700)
        cert, key = folder / "recipient.pem", folder / "key.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key),
                        "-out", str(cert), "-days", "1", "-subj", "/CN=synthetic-backup-test-only"], check=True, capture_output=True)
        (folder / "synthetic-data").write_bytes(b"SYNTHETIC APP DATA, NOT CLOUD OR QA MATERIAL\n" * 200)
        cipher = folder / "APP.cms"
        result = backup.encrypt_stream(["tar", "-czf", "-", "-C", str(folder), "synthetic-data"], cert, cipher, folder / "private.log", 10)
        receipt = folder / "receipt.json"
        F.save(receipt, result)
        args = SimpleNamespace(backup=cipher, backup_sha256=F.sha(cipher), receipt=receipt, receipt_sha256=F.sha(receipt),
                               output=folder / "local.private.log", recipient_cert=cert, private_key=key)
        self.assertEqual(backup.local_verify(args)["status"], "FULL_LOCAL_DECRYPT_MATCH_NOT_RELEASE_AUTHORITY")
        args.backup_sha256 = "aa" * 32
        with self.assertRaises(ValueError):
            backup.local_verify(args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
