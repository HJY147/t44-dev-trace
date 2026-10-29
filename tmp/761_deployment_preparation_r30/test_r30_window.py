"""Fresh-window adapter boundaries; no live Docker, cloud, sessions, or independent cases."""

import ast
import importlib.util
import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("r30window", ROOT / "deployment/cloud-reuse/r30-window.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
PACKAGE = Path(__file__).parent / "official-artifact-12880320744"
BUNDLE = "b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345"


class WindowBoundaries(unittest.TestCase):
    def args(self, output, **updates):
        result = dict(package=PACKAGE.resolve(), manifest_sha256=BUNDLE, run_id="r30fixture01",
                      stop_utc=(datetime.now(UTC) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      output=output)
        return SimpleNamespace(**(result | updates))

    def test_derive_real_verified_artifact_preserves_stack_operations_and_budget(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            output = Path(scratch) / "derived"
            args = self.args(output)
            value = M.derive(args)
            a = M.artifact()
            v4 = M.load(M.HERE / "v4/derive-profile.py", M.V4_SHA)
            baseline = v4.derive_texts(v4.parent(), a.SOURCE, args.stop_utc, 53)["generation.py"]
            baseline = baseline.replace(v4.KIND, M.KIND).replace("target_frontend_frozen_equal_file_set_sha256", "r30_46_unchanged_frozen_file_set_sha256")
            before = {n.name: ast.dump(n) for n in ast.parse(baseline).body if isinstance(n, ast.FunctionDef)}
            after = {n.name: ast.dump(n) for n in ast.parse((output / "generation.py").read_text()).body if isinstance(n, ast.FunctionDef)}
            self.assertEqual(before.keys(), after.keys())
            self.assertEqual([n for n in before if before[n] != after[n]], ["verified_images", "prepare"])
            self.assertEqual(value["source_probe_backend_files"], 53)
            self.assertEqual(value["full_runtime_context_files"], 60)
            self.assertEqual(value["original_budget_sha256"], "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d")
            self.assertEqual(value["derived_budget_sha256"], a.sha(output / "mysql-budget.py"))
            self.assertNotEqual(value["derived_budget_sha256"], value["original_budget_sha256"])
            self.assertIn("EXACT_R30_WINDOW_RUN_ID_REQUIRED", (output / "generation.py").read_text())
            for name, metadata in value["derived_files"].items():
                self.assertEqual(a.sha(output / name), metadata["sha256"])
                compile((output / name).read_bytes(), name, "exec")

    def test_old_deadline_refused_before_writing(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            output = Path(scratch) / "expired"
            with self.assertRaisesRegex(ValueError, "NEW_WINDOW_30_MINUTES"):
                M.derive(self.args(output, stop_utc="2026-10-28T20:00:00Z"))
            self.assertFalse(output.exists())

    def test_wrong_bundle_refused_before_writing(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            output = Path(scratch) / "wrong"
            with self.assertRaisesRegex(ValueError, "ROOT_PINNED_BACKEND"):
                M.derive(self.args(output, manifest_sha256="0" * 64))
            self.assertFalse(output.exists())

    def test_legacy_upgrade_binding_path_refused(self):
        args = SimpleNamespace(source_package=PACKAGE, upgrade_binding=PACKAGE / "upgrade-binding.json")
        with self.assertRaisesRegex(ValueError, "EXPLICIT_R30_BACKEND_BUNDLE_PATH"):
            M.verified_images(args, None)

    def test_unproven_cache_proof_refused_without_docker(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            path = Path(scratch) / "synthetic-public-proof.jsonl"
            path.write_text(json.dumps({"kind": "proof_final", "all_seven_proven": True}))
            with self.assertRaisesRegex(ValueError, "ORIGINAL_FULL_PUBLIC_IMAGE_PROOF"):
                M.cached_roles(path)

    def test_import_refuses_nonlinux_before_calling_docker(self):
        with patch.object(M.platform, "system", return_value="Darwin"):
            with self.assertRaisesRegex(ValueError, "ROOT_LINUX_AMD64"):
                M.import_backend(SimpleNamespace())

    def test_adapter_is_exclusive_and_old_helpers_not_written(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            output = Path(scratch) / "profile"
            M.derive(self.args(output))
            self.assertFalse((output / "backend-upgrade.py").exists())
            self.assertFalse((output / "source-artifact-receive.py").exists())
            with self.assertRaises(FileExistsError):
                M.derive(self.args(output))


if __name__ == "__main__":
    unittest.main(verbosity=2)
