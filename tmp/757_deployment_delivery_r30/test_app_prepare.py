"""Fixed APP command ordering, complete private prefixes, bounded public metadata, no Docker/HTTP."""

import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("app_prepare", ROOT / "deployment/cloud-reuse/r30-app-prepare.py")
W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W)


class AppPreparation(unittest.TestCase):
    def scenario(self, *, fail_idle=False, wrong_proof=False):
        scratch = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(scratch.cleanup)
        base = Path(scratch.name).resolve()
        ops = base / "ops"
        shutil.copytree(ROOT / "agents/deployment/preparation-r30/window-r30window01", ops / "profile")
        package = base / "package"
        package.mkdir(mode=0o700)
        (package / "backend-bundle-manifest.json").write_text("SYNTHETIC package seam")
        original = base / "fixed-public-proof.jsonl"
        original.write_bytes(b"SYNTHETIC public proof boundary".ljust(50297, b" "))
        proof_hash = W.sha(original)
        args = SimpleNamespace(ops=ops, package=package, run_root=base, profile_sha256=W.PROFILE_SHA, app_ip="10.0.0.10")
        calls = []

        def run(argv, *, stdout, stderr, **kwargs):
            argv = list(map(str, argv))
            script = Path(argv[1]).name
            action = argv[2]
            calls.append(action)
            result = {"success": True, "SYNTHETIC": "explicit command seam"}
            if script == "r30-window.py" and action == "import-backend":
                W.save(Path(argv[argv.index("--receipt") + 1]), {"full_runtime_files": 60, "SYNTHETIC": True})
            elif action == "prepare":
                phase = base / "run/campaign/p"
                phase.mkdir(mode=0o700, parents=True)
                W.save(phase / "binding.json", {"project": "t44-cloud-r30window01-p", "database": "t44c_r30window01_p"})
                result = {"phases": {"p": {"phase_dir": str(phase), "binding_sha256": W.sha(phase / "binding.json"),
                                           "project": "t44-cloud-r30window01-p", "database": "t44c_r30window01_p"}}}
            elif action == "probe-budget":
                probe = base / "run/synthetic-probe.PUBLIC.json"
                W.save(probe, {"SYNTHETIC": "not a MySQL observation"})
                result = {"budget_receipt": str(probe), "budget_receipt_sha256": W.sha(probe)}
            elif action == "idle":
                result["resources"] = [{"role": role, "state": {"Running": True}} for role in ("mysql", "rabbitmq", "api", "consumer", "web", "tls-gateway")]
                result["resources"].append({"role": "scheduler", "absent": True})
            stdout.write(json.dumps(result).encode() + b"\n")
            stderr.write(("full private prefix for " + action + "\n").encode())
            return SimpleNamespace(returncode=3 if fail_idle and action == "idle" else 0)

        captured = io.BytesIO()
        with patch.object(W, "require_host"), patch.object(W, "PROOF", original), \
                patch.object(W, "PROOF_SHA", "0" * 64 if wrong_proof else proof_hash), \
                patch.object(W.time, "time", return_value=W.epoch(W.T0) + 20), \
                patch.object(subprocess, "run", side_effect=run), patch.object(W.sys, "stdout", SimpleNamespace(buffer=captured)):
            code = W.Preparation(args).finish()
        return base, calls, code, captured.getvalue()

    def test_exact_order_full_private_prefixes_and_idle_only(self):
        base, calls, code, raw = self.scenario()
        self.assertEqual(code, 0)
        self.assertEqual(calls, ["verify-bundle", "import-backend", "verify-cache", "prepare", "arm", "config", "infra", "probe-budget", "migrate", "idle"])
        value = json.loads(raw)
        self.assertFalse(value["sessions_issued"])
        self.assertFalse(value["seed_requested"])
        self.assertFalse(value["F_started"])
        self.assertLessEqual(len(raw), 22000)
        for step in value["steps"]:
            for name in ("stdout", "stderr"):
                path = Path(step[name]["path"])
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(W.sha(path), step[name]["sha256"])
        self.assertTrue((base / "run/preparation.PUBLIC.json").is_file())

    def test_failure_preserves_idle_prefix_and_runs_owned_stop(self):
        base, calls, code, raw = self.scenario(fail_idle=True)
        self.assertEqual(code, 1)
        self.assertEqual(calls[-1], "stop")
        self.assertFalse(json.loads(raw)["success"])
        self.assertIn("full private prefix", (base / "run/commands/10-idle.stderr.private").read_text())
        self.assertTrue((base / "run/failure.private.json").is_file())

    def test_wrong_original_public_proof_refuses_without_search_or_child(self):
        _, calls, code, raw = self.scenario(wrong_proof=True)
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        self.assertFalse(json.loads(raw)["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
