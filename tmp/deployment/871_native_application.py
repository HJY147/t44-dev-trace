"""Deployment-only bad-input/source/secret/owner guards; no business or network service."""

import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import Mock, call, patch

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

    def test_short_command_identity_race_means_absent_never_signal(self):
        with patch.object(appmod.broker_runtime, "process_identity", side_effect=ProcessLookupError), \
                patch.object(appmod.os, "kill") as kill:
            self.assertIsNone(appmod.process_identity(123))
            kill.assert_not_called()

    def test_actual_rabbit_typed_connection_shape_and_bad_peers(self):
        row = {"user": "fixture-user", "vhost": "fixture-vhost", "peer_host": [127, 0, 0, 1],
               "client_properties": [["product", "longstr", "Pika Python Client Library"]]}
        self.assertEqual(appmod.connection_products([row], "fixture-user", "fixture-vhost"),
                         ["Pika Python Client Library"])
        for peer in ([0, 0, 0, 0], [127, 0, 0, True], [256, 0, 0, 1], "192.0.2.1"):
            with self.assertRaises(ValueError):
                appmod.connection_products([{**row, "peer_host": peer}], "fixture-user", "fixture-vhost")
        with self.assertRaises(ValueError):
            appmod.connection_products([row], "other-user", "fixture-vhost")

    def test_prior_delivery_cannot_rebind_source_or_boolean_event_id(self):
        previous = self.prepare()
        evidence = {"source_commit": self.commit, "origin_run": previous.run.name,
                    "all_exact_recipient_sets_match": True, "all_events_linked_to_origin_scan_and_utc": True,
                    "new_publish_by_later_cycle_claimed": False, "event_ids": [True], "scan_ids": [1, 2]}
        appmod.write_json(previous.run / "state/delivery-evidence.json", evidence)
        with self.assertRaises(ValueError):
            appmod.Application.prepare(self.project, self.binding_file, self.commit, self.dependency, previous.run)
        evidence.update(event_ids=[1], source_commit="a" * 40)
        appmod.replace_json(previous.run / "state/delivery-evidence.json", evidence)
        with self.assertRaises(ValueError):
            appmod.Application.prepare(self.project, self.binding_file, self.commit, self.dependency, previous.run)

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


class CaptureGuards(unittest.TestCase):
    """Only mocked finite commands; never construct an Application or open inputs."""

    observations: ClassVar[list[dict]] = []

    def scenario(self, replies):
        directory = ROOT / ".agent-worktrees/.runtime/native-capture-timeout-guards"
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=directory)
        self.addCleanup(temporary.cleanup)
        logs = Path(temporary.name)
        process = SimpleNamespace(pid=123, returncode=None)
        pending, timeouts = list(replies), []

        def communicate(*, timeout):
            timeouts.append(timeout)
            outcome = pending.pop(0)
            if outcome == "timeout":
                raise appmod.subprocess.TimeoutExpired("synthetic-owned-command", timeout,
                                                       output=b"synthetic partial stdout", stderr=b"synthetic partial stderr")
            process.returncode = outcome
            return b"synthetic stdout", b"synthetic stderr"

        process.communicate = communicate
        identity = {"pid": 123, "uid": os.getuid(), "pgid": 123, "started": "synthetic-start",
                    "command_sha256": "synthetic-command-hash"}
        result, error = None, None
        with patch.object(appmod.subprocess, "Popen", return_value=process) as popen, \
                patch.object(appmod, "process_identity", return_value=identity), \
                patch.object(appmod.time, "sleep"), patch.object(appmod.os, "kill") as kill:
            try:
                result = appmod.capture(["synthetic-owned-command"], Path("/synthetic-owned-source"), {}, logs, timeout=1)
            except RuntimeError as failure:
                error = str(failure)
        popen.assert_called_once()
        if "timeout" in replies:
            kill.assert_called_once_with(123, appmod.signal.SIGTERM)
        else:
            kill.assert_not_called()
        receipts = list(logs.glob("*.json"))
        receipt = json.loads(receipts[0].read_text()) if receipts else None
        self.assertLessEqual(len(receipts), 1)
        observation = {"scenario": self._testMethodName, "communicate_timeouts": timeouts,
                       "returned_normally": result is not None, "error": error,
                       "actual_child_returncode": process.returncode, "receipt": receipt,
                       "actual_os_processes_started": 0, "actual_os_signals_sent": 0,
                       "actual_private_inputs_read": False}
        type(self).observations.append(observation)
        return observation

    def test_normal_zero_returns_success_without_timeout(self):
        result = self.scenario([0])
        self.assertTrue(result["returned_normally"])
        self.assertIsNone(result["error"])
        self.assertEqual(result["receipt"]["exit_code"], 0)
        self.assertIs(result["receipt"].get("timed_out"), False)
        self.assertIs(result["receipt"].get("success"), True)
        self.assertIs(result["receipt"].get("stop_unconfirmed"), False)
        self.assertEqual(result["communicate_timeouts"], [1])

    def test_normal_nonzero_preserves_code_and_fails(self):
        result = self.scenario([7])
        self.assertFalse(result["returned_normally"])
        self.assertEqual(result["error"], "OWNED_COMMAND_FAILED")
        self.assertEqual(result["receipt"]["exit_code"], 7)
        self.assertIs(result["receipt"].get("timed_out"), False)
        self.assertIs(result["receipt"].get("success"), False)

    def test_original_timeout_then_cleanup_zero_is_rejected(self):
        result = self.scenario(["timeout", 0])
        rejected = not result["returned_normally"] and result["error"] is not None
        marker = result["receipt"] is not None and result["receipt"].get("timed_out") is True
        self.assertTrue(rejected and marker,
                        "NATIVE-CAPTURE-TIMEOUT-01: initial TimeoutExpired followed by cleanup exit0 was returned as successful command without timeout marker")
        self.assertEqual(result["error"], "OWNED_COMMAND_TIMEOUT")
        self.assertEqual(result["receipt"]["exit_code"], 0)
        self.assertIs(result["receipt"].get("success"), False)
        self.assertIs(result["receipt"].get("stop_unconfirmed"), False)
        self.assertEqual(result["communicate_timeouts"], [1, 5])

    def test_timeout_then_nonzero_preserves_actual_code(self):
        result = self.scenario(["timeout", -15])
        self.assertFalse(result["returned_normally"])
        self.assertEqual(result["error"], "OWNED_COMMAND_TIMEOUT")
        self.assertEqual(result["receipt"]["exit_code"], -15)
        self.assertIs(result["receipt"].get("timed_out"), True)
        self.assertIs(result["receipt"].get("success"), False)

    def test_cleanup_timeout_records_unconfirmed_and_actual_null_code(self):
        result = self.scenario(["timeout", "timeout"])
        self.assertFalse(result["returned_normally"])
        self.assertEqual(result["error"], "COMMAND_STOP_UNCONFIRMED")
        self.assertIsNone(result["receipt"]["exit_code"])
        self.assertIs(result["receipt"].get("timed_out"), True)
        self.assertIs(result["receipt"].get("success"), False)
        self.assertIs(result["receipt"].get("stop_unconfirmed"), True)
        self.assertEqual(result["receipt"]["stdout_sha256"], hashlib.sha256(b"synthetic partial stdout").hexdigest())
        self.assertEqual(result["receipt"]["stderr_sha256"], hashlib.sha256(b"synthetic partial stderr").hexdigest())


class ServeGuards(unittest.TestCase):
    """New serve control only; no Application constructor, real signal or service."""

    def setUp(self):
        base = ROOT / ".agent-worktrees/.runtime/native-bounded-serve-guards"
        base.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.app = object.__new__(appmod.Application)
        self.app.project = self.root
        self.app.run = self.root / "fresh_run"
        (self.app.run / "state").mkdir(mode=0o700, parents=True)
        self.app.python = Path("/synthetic/python")
        self.app.manifest = {"source_commit": appmod.NATIVE_DEMO_SOURCE,
                             "controller_sha256": digest_file(ROOT / "deployment/native/application.py")}
        self.app.binding = {"source_commit": appmod.NATIVE_DEMO_SOURCE}
        self.app.current_record = Mock(return_value=None)
        self.app.receipt = Mock(side_effect=lambda action, **fields: {"action": action, **fields})
        self.app._serve_control = None
        self.app.issued = []
        self.identity = {"pid": 123, "uid": os.getuid(), "pgid": 456, "started": "synthetic-start",
                         "command_sha256": "synthetic-command"}

    def prepared_serve(self, *, ready=True, cleanup=True):
        def cycle(*, serve_control):
            serve_control.ready = ready
            serve_control.reason = "duration_elapsed"
            serve_control.cleaning = True
            return {"success": ready and cleanup, "error": None, "actions": [], "cleanup": {"success": cleanup}}
        self.app.run_cycle = Mock(side_effect=cycle)
        with patch.object(appmod, "process_identity", return_value=self.identity), \
                patch.object(appmod, "current_cwd", return_value=self.root), \
                patch.object(appmod.signal, "signal"):
            return self.app.serve(180)

    def stopped_resource_fixture(self):
        state = self.app.run / "state"
        appmod.write_json(state / "serve-owner.json", self.identity)
        records = []
        for index, role in enumerate(("api", "consumer", "scanner", "ui")):
            for generation in ("old", "current"):
                record = {"role": role, "generation": generation, "pid": 1000 + len(records)}
                records.append(record)
                appmod.write_json(state / f"{role}-{generation}.json", record)
            appmod.write_json(state / f"{role}-current-pointer.json", {"record": f"{role}-current.json"})
        workers = [{"pid": 2000 + index} for index in range(4)]
        tracker = [{"pid": 2010}]
        appmod.write_json(state / "api-children.json", {"workers": workers, "tracker": tracker})
        return records, workers + tracker

    def mocked_stopped_observation(self, live_pid):
        self.app.own = Mock(side_effect=lambda record, **_kwargs:
                            self.identity if record["pid"] == live_pid else None)
        with patch.object(appmod.time, "monotonic", side_effect=[0, 11]), \
                patch.object(appmod.time, "sleep") as sleep, \
                patch.object(appmod.os, "kill") as kill, \
                patch.object(appmod, "process_identity") as identity:
            result = self.app.verify_stopped()
        sleep.assert_not_called()
        kill.assert_not_called()
        identity.assert_not_called()
        return result

    def test_stopped_resources_exclude_live_serve_runner(self):
        records, children = self.stopped_resource_fixture()
        result = self.mocked_stopped_observation(self.identity["pid"])
        self.assertTrue(result["success"])
        self.assertEqual({item["pid"] for item in result["observations"]},
                         {record["pid"] for record in records + children})
        self.assertEqual(len(self.app.own.call_args_list), len(records + children))
        self.assertNotIn(call(self.identity, leader=True), self.app.own.call_args_list)

    def test_stopped_resources_still_reject_live_role_in_any_generation(self):
        records, _children = self.stopped_resource_fixture()
        for record in records:
            with self.subTest(role=record["role"], generation=record["generation"]):
                result = self.mocked_stopped_observation(record["pid"])
                self.assertFalse(result["success"])
                self.assertEqual([item["pid"] for item in result["observations"] if not item["absent"]],
                                 [record["pid"]])
                self.assertIn(call(record, leader=True), self.app.own.call_args_list)

    def test_stopped_resources_still_reject_live_api_worker_or_tracker(self):
        _records, children = self.stopped_resource_fixture()
        for record in children:
            with self.subTest(pid=record["pid"]):
                result = self.mocked_stopped_observation(record["pid"])
                self.assertFalse(result["success"])
                self.assertEqual([item["pid"] for item in result["observations"] if not item["absent"]],
                                 [record["pid"]])
                self.assertIn(call(record, leader=False), self.app.own.call_args_list)

    def test_duration_is_explicit_real_integer_in_range(self):
        for value in (True, False, 179, 14401, 180.0, "360", None):
            with self.assertRaises(ValueError):
                appmod.BoundedServe(value)
        for value in (180, 360, 14400):
            self.assertEqual(appmod.BoundedServe(value).duration, value)

    def test_signal_only_marks_and_handlers_restore_even_on_failure(self):
        control = appmod.BoundedServe(180)
        with patch.object(appmod.signal, "signal", return_value="synthetic-previous") as change, \
                patch.object(appmod.os, "kill") as kill:
            with self.assertRaisesRegex(RuntimeError, "synthetic-failure"), control.signals():
                control.request_stop(appmod.signal.SIGTERM)
                self.assertEqual(control.reason, "SIGTERM")
                control.request_stop(appmod.signal.SIGINT)
                self.assertEqual(control.reason, "SIGTERM")
                with self.assertRaises(appmod.ServeStopRequested):
                    control.check()
                control.cleaning = True
                control.check()
                raise RuntimeError("synthetic-failure")
            kill.assert_not_called()
        self.assertEqual(change.call_args_list[-2:], [call(appmod.signal.SIGINT, "synthetic-previous"),
                                                     call(appmod.signal.SIGTERM, "synthetic-previous")])

    def test_monotonic_deadline_requests_stop(self):
        with patch.object(appmod.time, "monotonic", return_value=100):
            control = appmod.BoundedServe(180)
        with patch.object(appmod.time, "monotonic", return_value=280), self.assertRaises(appmod.ServeStopRequested):
            control.check()
        self.assertEqual(control.reason, "duration_elapsed")

    def test_early_stop_and_runtime_failure_both_reach_owned_cleanup(self):
        for failure in (appmod.ServeStopRequested("SERVE_STOP_REQUESTED"), RuntimeError("SERVE_ROTATION_FAILED")):
            control = appmod.BoundedServe(180)
            control.reason = "SIGINT"
            control.retired_sessions = {1}
            self.app.issued = [1, 2]
            self.app.check_serve_stop = Mock(side_effect=failure)
            self.app.cleanup = Mock(return_value={"success": True})
            result = self.app.run_cycle(serve_control=control)
            self.assertFalse(result["success"])
            self.assertTrue(result["cleanup"]["success"])
            self.app.cleanup.assert_called_once_with(broker_started=False)
            self.assertTrue(control.cleaning)
            self.assertEqual(self.app.issued, [2])

    def test_serve_wrapper_registers_once_and_reports_ready_separately(self):
        result = self.prepared_serve()
        self.assertTrue(result["success"])
        self.assertTrue(result["cleanup_success"])
        self.assertIsNone(self.app._serve_control)
        owner = self.app.run / "state/serve-owner.json"
        self.assertEqual(owner.stat().st_mode & 0o777, 0o600)
        self.assertIn("stop", json.loads(owner.read_text())["stop_argv"])
        with patch.object(appmod, "process_identity", return_value=self.identity), \
                patch.object(appmod, "current_cwd", return_value=self.root), self.assertRaises(FileExistsError):
            self.app.serve(180)
        self.app.run_cycle.assert_called_once()

    def test_pre_ready_stop_never_claims_capability_success(self):
        result = self.prepared_serve(ready=False)
        self.assertFalse(result["success"])
        self.assertFalse(result["capability_ready"])
        self.assertTrue(result["cleanup_success"])

    def test_cleanup_failure_remains_false_after_ready(self):
        result = self.prepared_serve(cleanup=False)
        self.assertFalse(result["success"])
        self.assertTrue(result["capability_ready"])
        self.assertFalse(result["cleanup_success"])

    def test_invalid_source_controller_or_used_role_rejected_before_runner(self):
        original = dict(self.app.manifest)
        cases = [("source_commit", "a" * 40), ("controller_sha256", "0" * 64), ("used_role", True)]
        for field, value in cases:
            self.app.manifest = dict(original)
            self.app.current_record = Mock(return_value={"pid": 123} if field == "used_role" else None)
            if field != "used_role":
                self.app.manifest[field] = value
            with patch.object(appmod, "process_identity") as identity, self.assertRaises(ValueError):
                self.app.serve(180)
            identity.assert_not_called()
        self.assertFalse((self.app.run / "state/serve-owner.json").exists())

    def test_ready_login_reclaims_only_own_session_before_long_hold(self):
        self.app.user_token = "synthetic-readiness-bearer"
        appmod.write_json(self.app.run / "state/user-session.json", {"session_id": 17})
        self.app.http = Mock(return_value=(200, {}))
        self.app.revoke_service = Mock(return_value={"success": True})
        result = self.app.release_serve_login()
        self.assertTrue(result["success"])
        self.app.revoke_service.assert_called_once_with(17)
        self.assertIsNone(self.app.user_token)
        self.assertEqual(json.loads((self.app.run / "state/user-session-reclaimed.json").read_text()), {"session_id": 17})

    def test_stop_matches_exact_runner_pid_without_group_signal(self):
        self.prepared_serve()
        with patch.object(appmod, "process_identity", return_value=self.identity), \
                patch.object(appmod, "current_cwd", return_value=self.root), \
                patch.object(appmod.os, "kill") as kill, patch.object(appmod.os, "killpg") as killpg:
            result = self.app.stop_serve()
        kill.assert_called_once_with(123, appmod.signal.SIGTERM)
        killpg.assert_not_called()
        self.assertTrue(result["signal_sent"])
        self.assertFalse(result["cleanup_confirmed"])

    def test_stop_identity_or_cwd_mismatch_never_signals(self):
        self.prepared_serve()
        for identity, cwd in (({**self.identity, "started": "reused-pid"}, self.root),
                              (self.identity, Path("/synthetic/foreign"))):
            with patch.object(appmod, "process_identity", return_value=identity), \
                    patch.object(appmod, "current_cwd", return_value=cwd), patch.object(appmod.os, "kill") as kill:
                with self.assertRaises(ValueError):
                    self.app.stop_serve()
                kill.assert_not_called()

    def test_absent_runner_is_not_cleanup_confirmation(self):
        self.prepared_serve()
        appmod.replace_json(self.app.run / "state/serve-status.json", {"phase": "stopping", "cleanup_success": False})
        with patch.object(appmod, "process_identity", return_value=None), patch.object(appmod.os, "kill") as kill:
            result = self.app.stop_serve()
            self.assertFalse(result["success"])
            self.assertFalse(result["cleanup_confirmed"])
            kill.assert_not_called()

    def rotation_fixture(self):
        events = []
        self.app.check_serve_stop = Mock()
        self.app.stop_role = Mock(side_effect=lambda role: events.append("drain:" + role) or {"success": True})
        self.app.select = Mock(return_value=[{"id": 12}])
        self.app.issue_service = Mock(side_effect=lambda projects: events.append("issue_atomic_publish") or
                                      {"success": True, "session_id": 2})
        self.app.revoke_service = Mock(side_effect=lambda session: events.append("revoke_old") or {"success": True})
        self.app.spawn = Mock(side_effect=lambda role: events.append("spawn:" + role))
        self.app.wait_scans = Mock(side_effect=lambda *args, **kwargs: events.append("persisted_tick") or {"success": True})
        self.app.scanner_lock = Mock(side_effect=lambda: events.append("lock_held") or {"success": True})
        return events

    def test_rotation_order_and_only_scanner_restarts(self):
        events = self.rotation_fixture()
        control = appmod.BoundedServe(360)
        replacement = self.app.rotate_serve_scanner(control, [1, 2], {"session_id": 1}, [])
        self.assertEqual(events, ["drain:scanner", "issue_atomic_publish", "revoke_old", "spawn:scanner",
                                  "persisted_tick", "lock_held"])
        self.app.spawn.assert_called_once_with("scanner")
        self.assertEqual(replacement["session_id"], 2)
        self.assertEqual(control.retired_sessions, {1})
        self.assertEqual(control.additional_rotations, 1)

    def test_rotation_failures_do_not_restart_or_claim_completion(self):
        for phase in ("drain", "revoke", "tick"):
            self.rotation_fixture()
            control = appmod.BoundedServe(360)
            if phase == "drain":
                self.app.stop_role.side_effect = None
                self.app.stop_role.return_value = {"success": False}
            elif phase == "revoke":
                self.app.revoke_service.side_effect = None
                self.app.revoke_service.return_value = {"success": False}
            else:
                self.app.wait_scans.side_effect = RuntimeError("PERSISTED_SCANS_TIMEOUT")
            with self.assertRaises(RuntimeError):
                self.app.rotate_serve_scanner(control, [1, 2], {"session_id": 1}, [])
            self.assertEqual(control.additional_rotations, 0)
            if phase != "tick":
                self.app.spawn.assert_not_called()

    def test_hold_rotates_only_with_expiry_margin(self):
        for seconds, rotate in ((240, False), (60, True)):
            control = appmod.BoundedServe(360)
            control.check = Mock(side_effect=[None, appmod.ServeStopRequested("SERVE_STOP_REQUESTED")])
            self.app.release_serve_login = Mock(return_value={"success": True})
            self.app.current_record = Mock(return_value={"pid": 123})
            self.app.own = Mock(return_value={"pid": 123})
            self.app.rotate_serve_scanner = Mock(return_value={"expires_at": appmod.datetime.now(appmod.UTC)
                                                             + appmod.timedelta(seconds=300)})
            self.app.http = Mock(side_effect=[(401, {}), (200, b"<html></html>")])
            self.app.api_workers = Mock(return_value={"success": True})
            self.app.serve_status = Mock()
            with patch.object(appmod.time, "sleep"), self.assertRaises(appmod.ServeStopRequested):
                self.app.serve_hold(control, [1, 2], {"expires_at": appmod.datetime.now(appmod.UTC)
                                                    + appmod.timedelta(seconds=seconds)}, [])
            self.assertEqual(self.app.rotate_serve_scanner.call_count, int(rotate))

    def test_public_summary_omits_nested_accounts_and_personal_content(self):
        control = appmod.BoundedServe(180)
        control.ready = True
        cycle = {"success": True, "error": None, "cleanup": {"success": True}, "actions": [
            {"action": "start", "users": [{"user": "synthetic-private-account"}], "cookie": "synthetic-cookie"},
            {"action": "existing_normal_delivery", "success": True, "origin_run": "app_synthetic_origin",
             "confirmed_events": 16, "notification_count": 26, "new_publish_by_this_cycle_claimed": False,
             "recipients": ["synthetic-personal-name"], "access_token": "synthetic-bearer"}]}
        encoded = json.dumps(self.app.serve_summary(control, cycle))
        for value in ("synthetic-private-account", "synthetic-cookie", "synthetic-personal-name", "synthetic-bearer"):
            self.assertNotIn(value, encoded)

    def test_default_run_cli_still_calls_original_cycle_without_control(self):
        app = Mock()
        app.run_cycle.return_value = {"success": True}
        argv = ["application.py", "--project-root", str(self.root), "run", "--run-dir", str(self.app.run)]
        with patch.object(appmod.sys, "argv", argv), patch.object(appmod, "Application", return_value=app), \
                patch.object(appmod.sys, "stdout", io.StringIO()):
            self.assertEqual(appmod.main(), 0)
        app.run_cycle.assert_called_once_with()
        app.serve.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
