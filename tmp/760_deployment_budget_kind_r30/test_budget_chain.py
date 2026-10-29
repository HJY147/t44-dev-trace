"""R30-BUDGET-KIND-01 regression: real derive/binding/flock and GEN probe entry, no network."""

import importlib.util
import shutil
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("r30budgetwindow", ROOT / "deployment/cloud-reuse/r30-window.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
OLD_SHA = "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d"
OLD_KIND = "exact-pinned-production-entry-generation-v4"


class NonNetworkMysqlBoundary(RuntimeError):
    pass


class R30BudgetChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        cls.base = Path(cls.scratch.name).resolve()
        cls.profile = cls.base / "profile"
        cls.metadata = M.derive(SimpleNamespace(
            package=(ROOT / "tmp/761_deployment_preparation_r30/official-artifact-12880320744").resolve(),
            manifest_sha256="b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345",
            run_id="r30budget01", stop_utc=(datetime.now(UTC) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            output=cls.profile))
        cls.a = M.artifact()
        cls.g = M.load(cls.profile / "generation.py", cls.metadata["derived_files"]["generation.py"]["sha256"])
        cls.b = M.load(cls.profile / "mysql-budget.py", cls.g.BUDGET_SHA)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def phase(self, kind=None):
        path = self.base / self.id().split(".")[-1]
        path.mkdir(mode=0o700)
        (path / "receipts").mkdir(mode=0o700)
        shutil.copyfile(self.profile / "mysql-budget.py", path / "mysql-budget.py")
        (path / "mysql-budget.py").chmod(0o600)
        value = {"generation_kind": kind or self.metadata["kind"], "source_sha": self.g.SOURCE,
                 "stop_utc": self.metadata["stop_utc"], "phase": "p", "api_workers": 64,
                 "v4_pool_plan": self.b.pool_plan("p", 64, 5, 0),
                 "project": "t44-cloud-r30budget01-p", "database": "t44c_r30budget01_p"}
        self.a.save(path / "binding.json", value)
        return path, self.a.sha(path / "binding.json"), value

    def test_derived_budget_accepts_exact_r30_binding(self):
        path, expected, value = self.phase()
        self.assertEqual(self.b.KIND, self.metadata["kind"])
        self.assertEqual(self.b.checked_binding(path, expected), value)

    def test_real_operation_lock_enters_after_derived_binding_check(self):
        path, expected, _ = self.phase()
        with self.b.operation_lock(path, expected, timeout_seconds=0) as descriptor:
            self.assertGreaterEqual(descriptor, 0)
            self.assertTrue((path / ".v4-operation.lock").is_file())

    def test_gen_probe_budget_reaches_mysql_boundary_without_network(self):
        path, expected, value = self.phase()
        commands = []

        def command(argv):
            self.assertEqual(argv, ["systemctl", "is-active", "--quiet", "synthetic-r30-stop.timer"])
            commands.append(argv)
            return b""

        def live(_lib, _value, role):
            self.assertEqual(role, "mysql")
            raise NonNetworkMysqlBoundary("mysql live boundary reached; no Docker or SQL executed")

        value["timer_unit"] = "synthetic-r30-stop.timer"
        (path / "binding.json").unlink()
        self.a.save(path / "binding.json", value)
        expected = self.a.sha(path / "binding.json")
        factory = M.load(self.profile / "factory.py", M.FACTORY_SHA)
        lib = SimpleNamespace(expiry=factory.expiry, command=command)
        args = SimpleNamespace(action="probe-budget", phase_dir=path, binding_sha256=expected)
        with patch.object(self.g, "phase_binding", return_value=(lib, value)), patch.object(self.g, "live", side_effect=live):
            with self.assertRaisesRegex(NonNetworkMysqlBoundary, "mysql live boundary reached"):
                self.g.operate(args)
        self.assertEqual(len(commands), 1)

    def test_old_v4_kind_is_refused(self):
        path, expected, _ = self.phase(OLD_KIND)
        with self.assertRaisesRegex(ValueError, "V4_ONLY_NO_OLD_CAMPAIGN_ADOPTION"):
            self.b.checked_binding(path, expected)

    def test_only_budget_kind_literal_changes_and_new_pin_is_complete(self):
        original = M.HERE / "v4/mysql-budget.py"
        self.assertEqual(self.a.sha(original), OLD_SHA)
        before = original.read_text()
        self.assertEqual(before.count('KIND = "' + OLD_KIND + '"'), 1)
        expected = before.replace('KIND = "' + OLD_KIND + '"', 'KIND = "' + M.KIND + '"')
        self.assertEqual((self.profile / "mysql-budget.py").read_text(), expected)
        self.assertEqual(self.a.sha(self.profile / "mysql-budget.py"), self.g.BUDGET_SHA)
        self.assertNotEqual(self.g.BUDGET_SHA, OLD_SHA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
