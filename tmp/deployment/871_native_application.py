"""Deployment-only bad-input/source/secret/owner guards; no business or network service."""

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("native_application", ROOT / "deployment/native/application.py")
appmod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(appmod)


class ApplicationGuards(unittest.TestCase):
    def setUp(self):
        directory = ROOT / ".agent-worktrees/.runtime/native-application-guards"
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=directory)
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.base = self.project / ".agent-worktrees/.runtime/native-demo-20261023"
        self.base.mkdir(mode=0o700, parents=True)
        self.commit = "b" * 40
        self.source = self.base / "source" / self.commit
        self.source.mkdir(mode=0o700, parents=True)
        files = {
            "backend/t44/api.py": b"# Guard fixture, never executed\n",
            "frontend/src/main.ts": b"// Guard fixture\n",
            "backend/requirements.lock": b"# Lock fixture\n",
            "frontend/pnpm-lock.yaml": b"lockfileVersion: '9.0'\n",
            "backend/t44/resources/escalation-rules.json": b'{"scan_interval_seconds":60}\n',
        }
        for name, data in files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.binding = {"source_commit": self.commit,
                        "source_root": str(self.source.relative_to(self.project)),
                        "source_files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
                        "python_file_count": 1, "ts_vue_file_count": 1}
        self.binding_file = self.project / "binding.json"
        self.write_binding()
        db = {"host": "127.0.0.1", "port": 13306, "database": "t44_native_demo",
              "username": "t44_native_app", "password": "guard-database-private-value"}
        env = {"DATABASE_URL": "mysql+pymysql://t44_native_app:guard-database-private-value@127.0.0.1:13306/t44_native_demo",
               "T44_DATABASE": "t44_native_demo", "PYTHONPATH": "/initialization_0549/backend",
               "T44_SESSION_TTL_SECONDS": "3600"}
        accounts = {role: {"username": role, "password": "guard-" + role + "-private-value"}
                    for role in ("manager", "developer", "reviewer")}
        for name, value in [("environment", env), ("database", db), ("credentials", accounts)]:
            appmod.write_json(self.base / (name + ".json"), value)
        self.dependency = self.base / "dependencies/guard_dependencies"
        self.dependency.mkdir(mode=0o700, parents=True)
        appmod.write_json(self.dependency / "ready.json", {
            "backend_lock_sha256": self.binding["source_files"]["backend/requirements.lock"],
            "frontend_lock_sha256": self.binding["source_files"]["frontend/pnpm-lock.yaml"],
        })
        (self.dependency / "source/frontend/node_modules").mkdir(parents=True)
        broker_base = self.project / ".agent-worktrees/.runtime/fake_owned_broker"
        broker_base.mkdir(mode=0o700)
        cookie, credentials = broker_base / "cookie", broker_base / "amqp.json"
        appmod.private_write(cookie, b"guard-broker-cookie-private-value\n")
        appmod.write_json(credentials, {"username": "guard_broker", "vhost": "guard.vhost",
                                       "password": "guard-amqp-private-value"})
        self.broker = SimpleNamespace(run=broker_base, cookie=cookie, credentials=credentials)

    def write_binding(self):
        self.binding_file.write_text(json.dumps(self.binding))

    def prepare(self):
        with patch.object(appmod.broker_runtime, "NativeBroker") as broker:
            broker.return_value = self.broker
            broker.prepare.return_value = self.broker
            return appmod.Application.prepare(self.project, self.binding_file, self.commit, self.dependency)

    def test_exact_source_hash_and_denominator_required(self):
        appmod.verify_binding(self.project, self.binding_file, self.commit)
        (self.source / "backend/t44/api.py").write_text("changed")
        with self.assertRaises(ValueError):
            appmod.verify_binding(self.project, self.binding_file, self.commit)

    def test_explicit_expected_commit_does_not_accept_other_candidate(self):
        with self.assertRaises(ValueError):
            appmod.verify_binding(self.project, self.binding_file, "a" * 40)
        self.binding["python_file_count"] = 2
        self.write_binding()
        with self.assertRaises(ValueError):
            appmod.verify_binding(self.project, self.binding_file, self.commit)

    def test_deployment_and_vite_files_are_hashed_but_not_business_denominator(self):
        for name in ([f"backend/t44/module_{index}.py" for index in range(43)]
                     + [f"frontend/src/module_{index}.ts" for index in range(19)]
                     + ["deployment/guard_tool.py", "deployment/guard_tool2.py", "frontend/vite.config.ts"]):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"# Extra hash-checked configuration fixture\n")
            self.binding["source_files"][name] = digest_file(path)
        self.binding.update(python_file_count=44, ts_vue_file_count=20)
        self.write_binding()
        appmod.verify_binding(self.project, self.binding_file, self.commit)
        (self.source / "deployment/guard_tool.py").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            appmod.verify_binding(self.project, self.binding_file, self.commit)
        (self.source / "deployment/guard_tool.py").write_bytes(b"# Extra hash-checked configuration fixture\n")
        (self.source / "backend/t44/module_0.py").write_bytes(b"changed production source")
        with self.assertRaises(ValueError):
            appmod.verify_binding(self.project, self.binding_file, self.commit)
        (self.source / "backend/t44/module_0.py").write_bytes(b"# Extra hash-checked configuration fixture\n")
        (self.source / "backend/t44/module_0.py").unlink()
        with self.assertRaises(ValueError):
            appmod.verify_binding(self.project, self.binding_file, self.commit)

    def test_manifest_traversal_or_test_path_rejected_before_file_read(self):
        for name in ["../private.json", "tmp/independent/not_a_real_file.py"]:
            self.binding["source_files"] = {name: "0" * 64}
            self.write_binding()
            with self.assertRaises(ValueError):
                appmod.verify_binding(self.project, self.binding_file)

    def test_manifest_symlink_rejected(self):
        path = self.source / "backend/t44/api.py"
        path.unlink()
        path.symlink_to(self.source / "frontend/src/main.ts")
        with self.assertRaises(ValueError):
            appmod.verify_binding(self.project, self.binding_file)

    def test_old_database_or_admin_user_rejected(self):
        path = self.base / "database.json"
        original = json.loads(path.read_text())
        for field, value in [("database", "t44_demo_v11"), ("username", "root"), ("port", True)]:
            changed = {**original, field: value}
            path.write_text(json.dumps(changed))
            with self.assertRaises(ValueError):
                appmod.load_inputs(self.project)

    def test_public_private_inputs_rejected(self):
        (self.base / "environment.json").chmod(0o644)
        with self.assertRaises(ValueError):
            appmod.load_inputs(self.project)

    def test_prepare_copies_pythonpath_without_modifying_staging_input(self):
        original = (self.base / "environment.json").read_bytes()
        app = self.prepare()
        self.assertEqual((self.base / "environment.json").read_bytes(), original)
        self.assertEqual(app.environment["PYTHONPATH"], str(app.source / "backend"))
        self.assertEqual(app.environment["T44_SESSION_TTL_SECONDS"], "300")
        self.assertEqual((app.run / "secrets/environment.json").stat().st_mode & 0o777, 0o600)
        appmod.verify_copy(self.binding, app.source)

    def test_ui_environment_has_no_database_amqp_or_token(self):
        app = self.prepare()
        env = app.env(ui=True)
        for key in ("DATABASE_URL", "AMQP_URL", "T44_SCHEDULER_TOKEN_FILE", "PYTHONPATH"):
            self.assertNotIn(key, env)

    def test_overlay_points_only_to_owner_and_correct_proxy(self):
        app = self.prepare()
        text = (app.source / "frontend/vite.native.config.mjs").read_text()
        self.assertIn("127.0.0.1:18088", text)
        self.assertIn('"port": 5178', text)
        self.assertIn('"strictPort": true', text)
        self.assertNotIn('"allow": ["' + str(self.project) + '"', text)
        self.assertEqual(digest_file(app.source / "frontend/src/main.ts"), self.binding["source_files"]["frontend/src/main.ts"])

    def test_foreign_dependency_rejected_before_run_or_broker_creation(self):
        with patch.object(appmod.broker_runtime, "NativeBroker") as broker:
            with self.assertRaises(ValueError):
                appmod.Application.prepare(self.project, self.binding_file, self.commit, Path("/usr/local"))
            broker.prepare.assert_not_called()
        self.assertFalse((self.base / "runs").exists())

    def test_source_changes_after_prepare_rejected(self):
        app = self.prepare()
        (app.source / "frontend/src/main.ts").write_text("changed")
        with patch.object(appmod.broker_runtime, "NativeBroker"), self.assertRaises(ValueError):
            appmod.Application(self.project, app.run)

    def test_wrong_private_pythonpath_rejected(self):
        app = self.prepare()
        path = app.run / "secrets/environment.json"
        value = json.loads(path.read_text())
        value["PYTHONPATH"] = "/old_source/backend"
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            appmod.Application(self.project, app.run)

    def test_public_receipt_rejects_real_fixture_secrets(self):
        app = self.prepare()
        for secret in app.secret_literals():
            with self.assertRaises(ValueError):
                app.receipt("bad_payload", success=False, untrusted=secret.decode())
        self.assertEqual(list((app.run / "receipts").glob("*.json")), [])

    def test_pid_reuse_and_wrong_cwd_never_signalled(self):
        app = self.prepare()
        record = {"pid": 123, "uid": os.getuid(), "pgid": 123, "started": "old",
                  "command_sha256": "command", "cwd": str(app.source)}
        with patch.object(app, "current_record", return_value=record), \
                patch.object(appmod.broker_runtime, "process_identity", return_value={**record, "started": "new"}), \
                patch.object(appmod.os, "kill") as kill:
            with self.assertRaises(ValueError):
                app.stop_role("api")
            kill.assert_not_called()
        with patch.object(app, "current_record", return_value=record), \
                patch.object(appmod.broker_runtime, "process_identity", return_value=record), \
                patch.object(appmod, "current_cwd", return_value=Path("/foreign")), \
                patch.object(appmod.os, "kill") as kill:
            with self.assertRaises(ValueError):
                app.stop_role("api")
            kill.assert_not_called()

    def test_occupied_app_port_never_stops_any_process(self):
        with patch.object(appmod.socket, "socket") as socket_mock, patch.object(appmod.os, "kill") as kill:
            socket_mock.return_value.__enter__.return_value.bind.side_effect = OSError("busy")
            with self.assertRaises(OSError):
                appmod.assert_app_ports_free()
            kill.assert_not_called()

    def test_sql_writer_is_rejected_before_driver_import(self):
        app = self.prepare()
        for sql in ("DELETE FROM tasks", "DROP DATABASE t44_native_demo", "UPDATE tasks SET state=6"):
            with self.assertRaises(ValueError):
                app.select(sql)

    def test_boolean_project_id_cannot_reach_service_cli(self):
        app = self.prepare()
        with patch.object(app, "cli") as cli:
            with self.assertRaises(ValueError):
                app.issue_service([True])
            cli.assert_not_called()

    def test_listener_wildcard_or_wrong_port_rejected(self):
        app = self.prepare()
        record = {"pid": 123}
        for address in ("*:18088", "127.0.0.1:18080"):
            with patch.object(app, "current_record", return_value=record), \
                    patch.object(app, "own", return_value=record), \
                    patch.object(appmod.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="n" + address)), \
                    self.assertRaises(ValueError):
                app.listeners("api")

    def test_scanner_flock_must_really_be_held(self):
        app = self.prepare()
        path = app.run / "state/scanner.lock"
        appmod.private_write(path, b"")
        record = {"pid": 123}
        with patch.object(app, "current_record", return_value=record), patch.object(app, "own", return_value=record):
            with self.assertRaises(RuntimeError):
                app.scanner_lock()
            with path.open("rb") as lock:
                appmod.fcntl.flock(lock, appmod.fcntl.LOCK_EX | appmod.fcntl.LOCK_NB)
                self.assertTrue(app.scanner_lock()["held"])


def digest_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main(verbosity=2)
