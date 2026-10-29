"""Explicit external seams only; no Docker, SQL, HTTP, cloud or producer execution."""
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("future_http", ROOT / "deployment/cloud-reuse/r30-http-prepare.py")
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)
A = R.tools()
COMMIT = "cb966f2117730d6b60227e85e30b6a8b0e3cc79a"
MANIFEST = "0fc61e463692622f167548b7b00aed42fc18a58a0ae127317d6138e0a6136b8b"


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = tempfile.TemporaryDirectory(prefix="future-http-", dir=ROOT / "tmp/755_deployment_future_http_r30")
        cls.base = Path(cls.storage.name)
        cls.code = cls.base / "producer"
        cls.code.mkdir(mode=0o755)
        prefix = "agents/backend/neutral-r30-cas/"
        raw = subprocess.check_output(["git", "show", COMMIT + ":" + prefix + "code-manifest.PUBLIC.json"], cwd=ROOT)
        assert A.digest(raw) == MANIFEST
        (cls.code / "code-manifest.PUBLIC.json").write_bytes(raw)
        for name in json.loads(raw)["files"]:
            (cls.code / name).write_bytes(subprocess.check_output(["git", "show", COMMIT + ":" + prefix + name], cwd=ROOT))

    @classmethod
    def tearDownClass(cls):
        cls.storage.cleanup()

    def setUp(self):
        self.anchor = int(time.time())
        self.home = Path(tempfile.mkdtemp(dir=self.base))
        self.home.chmod(0o700)
        phase = self.home / "phase"
        phase.mkdir(mode=0o700)
        self.args = SimpleNamespace(phase_dir=phase, binding_sha256=None, code_dir=self.code,
             code_manifest=self.code / "code-manifest.PUBLIC.json", code_manifest_sha256=MANIFEST,
             plan=self.home / "plan.json", accounts=self.home / "accounts.json", service=self.home / "service.json",
             import_receipt=self.home / "import.json", ca=self.home / "ca.pem", output_dir=self.home / "new")
        self.proof = {"success": True, "actual_id": "sha256:" + "a3" * 32, "config_id": R.CONFIG,
                      "identity_kind": "oci-descriptor-to-original-config", "ordered_layer_count": 11,
                      "actual_descriptor_sha256_recomputed_from_archive": True,
                      "all_config_and_layer_descriptors_sha256_size_verified": True}
        self.value = {"kind": "isolated-cloud-campaign", "generation_kind": A.KIND, "source_sha": R.SOURCE,
             "phase": "p", "project": "t44-cloud-r30future02-p", "database": "t44c_r30future02_p",
             "images": {"backend": {"alias": R.ALIAS}}, "config_ids": {"backend": R.CONFIG},
             "image_ids": {"backend": self.proof["actual_id"]}, "cryptographic_transport_proofs": {"backend": self.proof},
             "source_manifest_sha256": R.SOURCE_MANIFEST, "upgrade_binding_sha256": R.BUNDLE,
             "stop_utc": self.stamp(2040), "tls": {"ca_sha256": A.digest(b"synthetic CA fixture")},
             "file_hashes": {"controller.py": "bc" * 32}}
        receipt = {"kind": "r30-backend-import-receipt-v1", "source_sha": R.SOURCE, "identity": self.proof,
             "bundle_manifest_sha256": R.BUNDLE, "source_manifest_sha256": R.SOURCE_MANIFEST,
             "full_runtime_files": 60, "package_resolution": {"files": [{"i": i} for i in range(60)],
                "uid": 10001, "business_env_absent": True, "package_origin": "/app/backend/t44/__init__.py"}}
        self.put(self.args.import_receipt, receipt)
        self.put(phase / "binding.json", self.value)
        self.args.binding_sha256 = A.digest((phase / "binding.json").read_bytes())
        self.plan = {"schema": "t44-neutral-r30-plan-v1", "synthetic": True, "root_admit_preparation": True,
            "benchmark_grant_allow": False, "run_id": "r30future02", "namespace": self.value["project"],
            "source": {"git_commit": R.SOURCE, "actual_loaded_receipt_sha256": A.digest(self.args.import_receipt.read_bytes())},
            "target": {"compose_project": self.value["project"], "database": self.value["database"],
                       "binding_sha256": self.args.binding_sha256, "ca_sha256": self.value["tls"]["ca_sha256"]},
            "gen_binding": {"path": "/neutral-input/binding.json", "sha256": self.args.binding_sha256},
            "window": {"start_utc": self.stamp(1140), "end_utc": self.stamp(1920), "stop_utc": self.value["stop_utc"]},
            "lifecycle": {"t0_utc": self.stamp(-60), "packet_cutoff_utc": self.stamp(990), "cost_stop_utc": self.stamp(2340)}}
        self.put(self.args.plan, self.plan)
        self.put(self.args.accounts, {"fixture": "not real accounts"})
        self.put(self.args.service, {"fixture": "not a real session"})
        self.args.ca.write_bytes(b"synthetic CA fixture")
        shutil.copyfile(ROOT / "agents/deployment/preparation-r30/window-r30window01/factory.py", phase / "factory.py")
        self.gen = SimpleNamespace(phase_binding=lambda *_: (None, self.value), BUDGET_SHA=A.BUDGET_SHA, R30_ADAPTER_SHA=A.ADAPTER_SHA)

    def stamp(self, offset):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.anchor + offset))

    def put(self, path, value):
        path.write_text(json.dumps(value))
        path.chmod(0o600)

    def checked(self):
        with patch.object(A, "require_host"), patch.object(A, "module", return_value=self.gen):
            return R.checked(self.args, A)

    def test_real_final18_staging_fixed_runtime_http_argv_and_modes(self):
        value, inputs, timeout = self.checked()
        self.assertGreater(timeout, 1)
        code = A.producer_files(self.args)
        self.assertEqual(len(code), 19)
        with patch.object(A, "container_owner"):
            A.stage(self.args, inputs, code)
        self.assertEqual((self.args.output_dir / "inputs/plan.json").read_bytes(), self.args.plan.read_bytes())
        for path in (self.args.output_dir / "code").iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o644)
        fixed = R.argv(self.args, value, value["project"] + "_edge", "new-name")
        self.assertNotIn("--env", fixed)
        self.assertNotIn("--env-file", fixed)
        self.assertNotIn("compose", fixed)
        self.assertEqual(fixed.count("--network"), 1)
        self.assertIn(R.ALIAS, fixed)
        self.assertIn("/neutral-code/prepare_http.py", fixed)
        for key, limit in (("--cpus", "2"), ("--memory", "1g"), ("--pids-limit", "128"),
                           ("--tmpfs", "/tmp:rw,nosuid,nodev,size=32m")):
            self.assertEqual(fixed[fixed.index(key) + 1], limit)
        self.assertEqual(R.argv(self.args, value, "edge", "new", runtime=True)[-3:],
                         ["-B", "/neutral-code/escalation_readback.py", "--check-runtime-only"])
        with patch.dict(os.environ, {"DATABASE_URL": "fixture", "PYTHONPATH": "fixture", "DOCKER_HOST": "fixture"}):
            self.assertFalse({"DATABASE_URL", "PYTHONPATH", "DOCKER_HOST"} & R.environment().keys())

    def test_source_namespace_old_run_and_expired_packet_refused_before_docker(self):
        for field, value in (("run_id", "r30window01"), ("namespace", "wrong")):
            saved = self.plan[field]
            self.plan[field] = value
            self.put(self.args.plan, self.plan)
            with self.assertRaises(ValueError):
                self.checked()
            self.plan[field] = saved
        self.plan["source"]["git_commit"] = "f7" * 20
        self.put(self.args.plan, self.plan)
        with self.assertRaises(ValueError):
            self.checked()
        self.plan["source"]["git_commit"] = R.SOURCE
        for section, key, bad in (("lifecycle", "cost_stop_utc", self.value["stop_utc"]),
                                  ("lifecycle", "packet_cutoff_utc", self.stamp(1000)),
                                  ("window", "end_utc", self.stamp(2100))):
            saved = self.plan[section][key]
            self.plan[section][key] = bad
            self.put(self.args.plan, self.plan)
            with self.assertRaises(ValueError):
                self.checked()
            self.plan[section][key] = saved
        self.plan["lifecycle"]["packet_cutoff_utc"] = self.stamp(-1)
        self.put(self.args.plan, self.plan)
        with self.assertRaises(ValueError):
            self.checked()

    def test_docker29_actual_id_distinct_config_and_business_env_refusal(self):
        image = {"Id": self.proof["actual_id"], "Descriptor": {"digest": self.proof["actual_id"]},
            "Os": "linux", "Architecture": "amd64", "RootFS": {"Type": "layers", "Layers": ["fixture"] * 11},
            "Config": {"Env": ["PYTHONPATH=/app/backend"], "Labels": {"org.opencontainers.image.revision": R.SOURCE,
                "io.t44.source-archive-sha256": "275970aa18117751e3a4fc8c404d0750cb9698310a70146d64061a634c37bf09"}}}
        edge = {"Name": self.value["project"] + "_edge", "Labels": {"com.docker.compose.project": self.value["project"],
                                                                             "com.docker.compose.network": "edge"}}
        with patch.object(R, "command", side_effect=[[image], [edge]]):
            self.assertEqual(R.image_and_edge(self.value), edge["Name"])
        for mutation in (lambda x: x["Config"]["Env"].append("DATABASE_URL=forbidden"),
                         lambda x: x.update(Id="sha256:" + "cd" * 32),
                         lambda x: x["Descriptor"].update(digest=R.CONFIG)):
            bad = copy.deepcopy(image)
            mutation(bad)
            with patch.object(R, "command", return_value=[bad]), self.assertRaises(ValueError):
                R.image_and_edge(self.value)

    def test_extra_python_and_tampered_declared_bytes_rejected(self):
        other = self.home / "code"
        shutil.copytree(self.code, other)
        self.args.code_dir = other
        self.args.code_manifest = other / "code-manifest.PUBLIC.json"
        (other / "verify-local.py").write_text("# not a runtime file")
        with self.assertRaises(ValueError):
            A.producer_files(self.args)
        (other / "verify-local.py").unlink()
        (other / "prepare_http.py").write_text("# changed bytes")
        with self.assertRaises(ValueError):
            A.producer_files(self.args)

    def test_full_runner_success_and_timeout_preserve_original_prefix(self):
        for fail in (False, True):
            self.args.output_dir = self.home / ("failure" if fail else "success")
            calls = []
            def child(cmd, out, err, stdin, timeout, env, cleanup, calls=calls, fail=fail):
                calls.append(cmd)
                is_runtime = "--check-runtime-only" in cmd
                payload = {"kind": "NEUTRAL_HTTP_RUNTIME_FUNCTION_PROBE_ONLY", "required_backend_config": R.CONFIG,
                           "actual_image_identity_verified_by_probe": False}
                out.write_bytes(json.dumps(payload).encode() if is_runtime else b"original prefix\n")
                err.write_bytes(b"original stderr\n")
                out.chmod(0o600)
                err.chmod(0o600)
                if fail and not is_runtime:
                    cleanup(stop=True)
                    raise subprocess.TimeoutExpired(cmd, timeout)
                cleanup(stop=False)
                return 0
            with patch.object(R, "tools", return_value=A), patch.object(A, "require_host"), \
                 patch.object(A, "module", return_value=self.gen), patch.object(A, "container_owner"), \
                 patch.object(R, "image_and_edge", return_value=self.value["project"] + "_edge"), \
                 patch.object(A, "run_child", side_effect=child), patch.object(R, "owned_exit") as cleanup:
                if fail:
                    with self.assertRaises(subprocess.TimeoutExpired):
                        R.run(self.args)
                    self.assertTrue(cleanup.call_args.kwargs["stop"])
                else:
                    self.assertEqual(R.run(self.args)["status"], "CHILD_EXITED_ZERO_NOT_ACCEPTANCE")
            self.assertEqual(len(calls), 2)
            receipt = json.loads((self.args.output_dir / "execution.PUBLIC.json").read_bytes())
            self.assertEqual(receipt["status"], "FAILED_PREFIX_PRESERVED" if fail else "CHILD_EXITED_ZERO_NOT_ACCEPTANCE")
            self.assertEqual((self.args.output_dir / "logs/http.stdout.private").read_bytes(), b"original prefix\n")
            self.assertEqual(self.args.plan.read_bytes(), (self.args.output_dir / "inputs/plan.json").read_bytes())
        name = "only-this-new-child"
        row = {"Name": "/" + name, "Image": self.proof["actual_id"],
               "Config": {"Labels": {"io.t44.r30.http.owner": self.value["project"]}},
               "State": {"Running": True}}
        exited = copy.deepcopy(row)
        exited["State"]["Running"] = False
        response = lambda data: subprocess.CompletedProcess([], 0, json.dumps([data]).encode(), b"")
        with patch.object(R.subprocess, "run", side_effect=[response(row), subprocess.CompletedProcess([], 0), response(exited)]) as host:
            R.owned_exit(self.value, name, stop=True)
            self.assertEqual(host.call_args_list[1].args[0], [*R.DOCKER, "stop", "--time", "5", name])
        row["Config"]["Labels"]["io.t44.r30.http.owner"] = "different-owner"
        with patch.object(R.subprocess, "run", return_value=response(row)) as host, self.assertRaises(ValueError):
            R.owned_exit(self.value, name, stop=True)
        self.assertEqual(host.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
