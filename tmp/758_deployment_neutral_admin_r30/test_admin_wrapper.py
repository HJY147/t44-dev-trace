"""Real 9e flock/admit and actual CLI JSON serializer with only external side effects replaced."""

import argparse
import ast
import contextlib
import copy
import fcntl
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


W = load(ROOT / "deployment/cloud-reuse/r30-neutral-admin.py", "neutral_admin_wrapper")
WINDOW = load(ROOT / "deployment/cloud-reuse/r30-window.py", "neutral_admin_window")


class AdminWrapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        cls.base = Path(cls.temp.name).resolve()
        cls.profile_dir = cls.base / "profile"
        WINDOW.derive(SimpleNamespace(package=ROOT / "tmp/761_deployment_preparation_r30/official-artifact-12880320744",
                      manifest_sha256="b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345",
                      run_id="r30window01", stop_utc=(datetime.now(UTC) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"), output=cls.profile_dir))
        cls.profile = json.loads((cls.profile_dir / "profile.json").read_text())
        cls.cli_source = subprocess.check_output(["git", "-C", str(ROOT), "show", W.SOURCE + ":backend/t44/cli.py"])
        cls.cli_hash = hashlib.sha256(cls.cli_source).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setup_phase(self, mode="counts", *, source=None, project=None):
        base = self.base / (self.id().split(".")[-1] + "-" + mode)
        base.mkdir(mode=0o700)
        phase = base / "phase"
        phase.mkdir(mode=0o700)
        (phase / "receipts").mkdir(mode=0o700)
        for origin, target in [("generation.py", "controller.py"), ("factory.py", "factory.py"), ("mysql-budget.py", "mysql-budget.py")]:
            shutil.copyfile(self.profile_dir / origin, phase / target)
            (phase / target).chmod(0o600)
        g = W.module(phase / "controller.py", self.profile["derived_files"]["generation.py"]["sha256"])
        budget = g.budget_module(phase)
        value = {"kind": "isolated-cloud-campaign", "generation_kind": W.KIND, "source_sha": source or W.SOURCE,
                 "project": project or "t44-cloud-r30window01-p", "database": "t44c_r30window01_p", "phase": "p",
                 "entrypoint": "t44.api:app", "profiling": False, "stop_utc": self.profile["stop_utc"], "api_workers": 64,
                 "v4_pool_plan": budget.pool_plan("p", 64, 5, 0), "timer_unit": "synthetic-r30-stop.timer",
                 "images": {"backend": {"alias": "synthetic-exact-backend"}},
                 "image_ids": {"backend": W.CONFIG}, "config_ids": {"backend": W.CONFIG}}
        composition = {"services": {"credential-admin": {"image": "synthetic-exact-backend", "networks": ["data"], "pull_policy": "never"}}}
        W.save(phase / "compose.json", composition)
        W.write(phase / "application.env", b"SYNTHETIC_TEST_ONLY=1\n")
        W.write(phase / "nginx.conf", b"SYNTHETIC_TEST_ONLY\n")
        value["file_hashes"] = {name: W.digest((phase / name).read_bytes()) for name in ["compose.json", "application.env", "nginx.conf", "controller.py", "factory.py", "mysql-budget.py"]}
        W.save(phase / "binding.json", value)
        binding_hash = W.digest((phase / "binding.json").read_bytes())
        identity = {"synthetic_mysql_identity": "no actual process or server"}
        sample = {"max_connections": 384, "server_uuid": "00000000-0000-0000-0000-000000000001"}
        probe = {"kind": "actual-owned-mysql-budget-v4", "binding_sha256": binding_hash, "source_sha": value["source_sha"],
                 "stop_utc": value["stop_utc"], "mysql_identity": identity, "connection_budget": value["v4_pool_plan"], "actual_mysql_sample": sample}
        probe_file = phase / "receipts" / ("mysql-budget-" + "a" * 32 + ".PUBLIC.json")
        W.save(probe_file, probe)
        probe_hash = W.digest(probe_file.read_bytes())
        imported = base / "import.PUBLIC.json"
        W.save(imported, {"SYNTHETIC": "not an actual import proof"})
        plan = {"schema": "t44-neutral-r30-plan-v1", "synthetic": True, "root_admit_preparation": True, "benchmark_grant_allow": False,
                "run_id": "r30window01", "namespace": value["project"],
                "source": {"git_commit": value["source_sha"], "actual_loaded_receipt_sha256": W.digest(imported.read_bytes())},
                "target": {"compose_project": value["project"], "database": value["database"], "binding_sha256": binding_hash,
                           "mysql_host": "mysql", "mysql_port": 3306, "mysql_user": value["database"] + "_app"},
                "window": {"stop_utc": value["stop_utc"]}, "budget": {"helper_sha256": W.BUDGET_SHA, "actual_admission_receipt_sha256": probe_hash},
                "gen_binding": {"path": "/neutral-input/binding.json", "sha256": binding_hash},
                "authorized_project_ids": []}
        intent = {"run_id": plan["run_id"], "namespace": plan["namespace"], "database": value["database"]}
        plan_file, intent_file = base / "plan.private.json", base / "intent.private.json"
        W.save(plan_file, plan)
        W.save(intent_file, intent)
        code = base / "producer"
        code.mkdir(mode=0o700)
        W.write(code / "admin.py", b"# SYNTHETIC producer; never executed\n")
        W.write(code / "guard.py", b"# SYNTHETIC declared dependency\n")
        manifest = code / "code-manifest.PUBLIC.json"
        W.save(manifest, {"files": {name: {"bytes": (code / name).stat().st_size, "sha256": W.digest((code / name).read_bytes())} for name in ["admin.py", "guard.py"]}})
        account_file = base / "accounts.private.json"
        W.save(account_file, {role: {"username": "synthetic-" + role, "password": None, "user_id": None} for role in W.ACCOUNT_ROLES})
        args = SimpleNamespace(mode=mode, phase_dir=phase, profile_json=self.profile_dir / "profile.json",
                               profile_sha256=W.digest((self.profile_dir / "profile.json").read_bytes()), binding_sha256=binding_hash,
                               budget_receipt=probe_file, budget_receipt_sha256=probe_hash, plan=plan_file, intent=intent_file,
                               import_receipt=imported, code_dir=code, code_manifest=manifest,
                               code_manifest_sha256=W.digest(manifest.read_bytes()), output_dir=base / "attempt", accounts=account_file)
        self.events, self.child_calls, self.lock_observations = [], [], []
        real_phase = g.phase_binding

        def phase_binding(*a, **kw):
            lib, actual = real_phase(*a, **kw)

            def command(argv):
                self.events.append("host-read")
                if argv[:4] == ["docker", "--context", "default", "image"]:
                    return W.CONFIG.encode() + b"\n"
                self.assertEqual(argv, ["systemctl", "is-active", "--quiet", value["timer_unit"]])
                return b""

            lib.command = command
            return lib, actual

        self.context = (args, value, g, budget, phase_binding, identity, sample)
        return args

    def lock_held(self):
        args = self.context[0]
        with (args.phase_dir / ".v4-operation.lock").open("r+b") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self.lock_observations.append("blocked")
            else:
                fcntl.flock(f, fcntl.LOCK_UN)
                raise AssertionError("actual operation lock was not held")

    def original_cli(self, username, password, *, fail=False):
        tree = ast.parse(self.cli_source)
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"_parser", "main"}]
        globals_ = {"argparse": argparse, "json": json, "re": re, "sys": sys, "wire": lambda v: v,
                    "HASHER": SimpleNamespace(hash=lambda value: "SYNTHETIC hash not persisted"),
                    "Settings": SimpleNamespace(from_env=lambda: SimpleNamespace(mysql_settings=lambda: object())),
                    "create_mysql_engine": lambda settings: object(), "SqlAlchemyUnitOfWorkFactory": lambda engine: object()}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "exact-source0b-cli-functions", "exec"), globals_)
        persistence = types.ModuleType("t44.persistence.accounts")

        def initialize_user(*a, **kw):
            if fail:
                raise ValueError("SYNTHETIC duplicate account boundary")
            return 1001 + W.ACCOUNT_ROLES.index(username.removeprefix("synthetic-"))

        persistence.initialize_user = initialize_user
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(sys.modules, {"t44": types.ModuleType("t44"), "t44.persistence": types.ModuleType("t44.persistence"),
                                     "t44.persistence.accounts": persistence}), \
                patch.object(sys, "stdin", io.StringIO(password)), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = globals_["main"](["init-user", "--username", username, "--display-name", username, "--password-stdin"])
        return status, out.getvalue().encode(), err.getvalue().encode()

    def invoke(self, args, *, fail_role=None, admit_failure=False):
        _, value, g, budget, phase_binding, identity, sample = self.context
        original_module = W.module

        def module(path, expected):
            W.pinned(path, expected)
            return g

        def measure(actual, live):
            self.lock_held()
            self.events.append("actual-admit-measure")
            if admit_failure:
                raise ValueError("SYNTHETIC live budget refusal")
            return identity, sample, budget.checked_plan(actual)

        def runner(argv, out, err, stdin, timeout, env, cleanup):
            self.lock_held()
            self.events.append("child-start")
            self.child_calls.append(copy.deepcopy(argv))
            if args.mode == "init-accounts":
                username = argv[argv.index("--username") + 1]
                self.assertNotIn(stdin.decode().strip(), " ".join(argv))
                status, output, error = self.original_cli(username, stdin.decode(), fail=username == "synthetic-" + str(fail_role))
            else:
                self.assertEqual(argv[argv.index("credential-admin") + 1:], ["-B", "/neutral-code/admin.py", args.mode,
                    "--plan", "/neutral-input/plan.json", "--intent", "/neutral-input/intent.json", "--budget-proof", "/neutral-input/budget.PUBLIC.json",
                    "--import-receipt", "/neutral-input/backend-import-receipt.json", "--binding", "/neutral-input/binding.json",
                    "--output", "/neutral-output/result", "--root-budget-admitted"])
                status, output, error = 0, b"SYNTHETIC child stdout prefix\n", b"SYNTHETIC child stderr prefix\n"
                result = args.output_dir / "output/result"
                result.mkdir(mode=0o700)
                W.save(result / {"counts": "counts.json", "service": "service.json", "seed": "seed-result.json"}[args.mode], {"SYNTHETIC": True})
            done = threading.Event()
            monitor_errors = []

            def monitor():
                while not done.wait(0.005):
                    try:
                        self.lock_held()  # Host-only test observation, no runtime child lock protocol.
                    except BaseException as error:
                        monitor_errors.append(error)
                        break

            watcher = threading.Thread(target=monitor)
            watcher.start()
            script = "import sys,time;sys.stdin.buffer.read();sys.stdout.buffer.write(bytes.fromhex(sys.argv[1]));sys.stdout.flush();sys.stderr.buffer.write(bytes.fromhex(sys.argv[2]));sys.stderr.flush();time.sleep(.04);sys.exit(int(sys.argv[3]))"
            try:
                result = W.run_child([sys.executable, "-c", script, output.hex(), error.hex(), str(status)], out, err, stdin, timeout, os.environ.copy(), lambda stop=False: self.lock_held())
            finally:
                done.set()
                watcher.join()
            self.assertFalse(monitor_errors)
            self.lock_held()
            self.events.append("child-exit")
            return result

        with patch.object(W, "require_host"), patch.object(W, "container_owner"), patch.object(W, "private_result"), \
                patch.object(W, "module", side_effect=module), patch.object(g, "phase_binding", side_effect=phase_binding), \
                patch.object(g, "budget_module", return_value=budget), patch.object(budget, "measure", side_effect=measure), \
                patch.object(budget, "verify_runtime_environment", return_value=[]):
            self.assertIsNotNone(original_module)
            return W.run_admin(args, runner=runner)

    def test_counts_lock_covers_complete_real_surrogate_process(self):
        args = self.setup_phase()
        originals = {p: p.read_bytes() for p in [args.plan, args.intent, args.import_receipt, args.budget_receipt, args.phase_dir / "binding.json"]}
        result = self.invoke(args)
        self.assertGreaterEqual(len(self.lock_observations), 3)
        self.assertLess(self.events.index("actual-admit-measure"), self.events.index("child-start"))
        self.assertTrue(result["output"].endswith("/output/result/counts.json"))
        self.assertEqual((args.output_dir / "code").stat().st_mode & 0o777, 0o755)
        for path, before in originals.items():
            self.assertEqual(path.read_bytes(), before)
        admission = json.loads((args.output_dir / "admission.PUBLIC.json").read_text())
        self.assertEqual(admission["actual_admit_return"]["budget_receipt_sha256"], args.budget_receipt_sha256)
        self.assertEqual(len(self.child_calls), 1)
        with (args.phase_dir / ".v4-operation.lock").open("r+b") as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_init_accounts_serializes_actual_cli_main_json(self):
        args = self.setup_phase("init-accounts")
        before = args.accounts.read_bytes()
        result = self.invoke(args)
        actual = json.loads(Path(result["output"]).read_text())
        self.assertEqual([actual[r]["user_id"] for r in W.ACCOUNT_ROLES], [1001, 1002, 1003])
        self.assertTrue(all(actual[r]["password"] for r in W.ACCOUNT_ROLES))
        self.assertEqual(args.accounts.read_bytes(), before)
        self.assertEqual(len(self.child_calls), 3)
        self.assertEqual(self.events.count("actual-admit-measure"), 1)
        for role in W.ACCOUNT_ROLES:
            self.assertEqual(set(json.loads((args.output_dir / "logs" / (role + ".stdout.private")).read_text())), {"user_id"})

    def test_seed_and_service_keep_exact_fixed_arguments_and_paths(self):
        for mode, filename in [("seed", "seed-result.json"), ("service", "service.json")]:
            with self.subTest(mode=mode):
                args = self.setup_phase(mode)
                result = self.invoke(args)
                self.assertTrue(result["output"].endswith("/output/result/" + filename))
                self.assertEqual(len(self.child_calls), 1)

    def test_cli_duplicate_failure_retains_first_account_and_all_prefixes(self):
        args = self.setup_phase("init-accounts")
        with self.assertRaisesRegex(RuntimeError, "ADMIN_CHILD_FAILED_NO_RETRY_PREFIX_PRESERVED"):
            self.invoke(args, fail_role="developer")
        self.assertEqual(len(self.child_calls), 2)
        self.assertTrue((args.output_dir / "manager-account.private.json").is_file())
        self.assertIn("COMMAND_FAILED", (args.output_dir / "logs/developer.stderr.private").read_text())
        self.assertTrue((args.output_dir / "output/accounts.generated.private.json").is_file())
        self.assertFalse((args.output_dir / "output/accounts.initialized.private.json").exists())

    def test_old_source_is_refused_before_child(self):
        args = self.setup_phase(source="f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f")
        with self.assertRaisesRegex(ValueError, "EXACT_PRODUCTION_F4_GENERATION_REQUIRED"):
            self.invoke(args)
        self.assertFalse(args.output_dir.exists())
        self.assertFalse(self.child_calls)

    def test_wrong_namespace_pair_is_refused_before_child(self):
        args = self.setup_phase(project="t44-cloud-r30other01-p")
        with self.assertRaisesRegex(ValueError, "EXACT_R30_SOURCE_RUN_PROJECT_DATABASE_STOP_REQUIRED"):
            self.invoke(args)
        self.assertFalse(args.output_dir.exists())
        self.assertFalse(self.child_calls)

    def test_live_admission_failure_has_no_child_or_completion(self):
        args = self.setup_phase()
        with self.assertRaisesRegex(ValueError, "SYNTHETIC live budget refusal"):
            self.invoke(args, admit_failure=True)
        self.assertFalse(self.child_calls)
        self.assertFalse((args.output_dir / "completion.PUBLIC.json").exists())

    def test_modified_producer_is_refused_before_child(self):
        args = self.setup_phase()
        (args.code_dir / "admin.py").write_text("changed")
        with self.assertRaisesRegex(ValueError, "PRODUCER_CODE_BYTES_OR_HASH_CHANGED"):
            self.invoke(args)
        self.assertFalse(self.child_calls)

    def test_actual_final_producer_manifest_stage_and_fixed_argv(self):
        args = self.setup_phase()
        actual = args.output_dir.parent / "actual-final-producer"
        actual.mkdir(mode=0o700)
        commit = "0a34a81e9fb59abf6c500f5acbe284c053d1f903"
        prefix = "agents/backend/neutral-r30/"
        manifest = subprocess.check_output(["git", "-C", str(ROOT), "show", commit + ":" + prefix + "code-manifest.PUBLIC.json"])
        self.assertEqual(W.digest(manifest), "7c9d08a6b1b521dfb2046c8354686e367354d81f69c0813eb3ccfad42cfe841d")
        declared = json.loads(manifest)
        for name, expected in declared["files"].items():
            content = subprocess.check_output(["git", "-C", str(ROOT), "show", commit + ":" + prefix + name])
            self.assertEqual(W.digest(content), expected)
            self.assertEqual(len(content), declared["file_sizes"][name])
            W.write(actual / name, content)
        W.write(actual / "code-manifest.PUBLIC.json", manifest)
        args.code_dir, args.code_manifest = actual, actual / "code-manifest.PUBLIC.json"
        args.code_manifest_sha256 = W.digest(manifest)
        self.invoke(args)
        for name, expected in declared["files"].items():
            self.assertEqual(W.digest((args.output_dir / "code" / name).read_bytes()), expected)
        self.assertEqual(len(self.child_calls), 1)

    def test_host_binding_path_in_original_plan_is_refused(self):
        args = self.setup_phase()
        plan = json.loads(args.plan.read_bytes())
        plan["gen_binding"]["path"] = str(args.phase_dir / "binding.json")
        args.plan.unlink()
        W.save(args.plan, plan)
        with self.assertRaisesRegex(ValueError, "EXACT_ORIGINAL_PLAN_INTENT_BINDING_AND_PROBE_REQUIRED"):
            self.invoke(args)
        self.assertFalse(self.child_calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
