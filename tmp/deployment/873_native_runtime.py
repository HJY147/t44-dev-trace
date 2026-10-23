"""Deployment-owned guards; synthetic files/process identities, no service startup."""

import base64
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("native_runtime", ROOT / "deployment/native/runtime.py")
native = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native)


class NativeGuards(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / ".agent-worktrees/.runtime/native-guard-fixtures"
        scratch.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        base = self.project / ".agent-worktrees/.runtime/native-mq-20261023"
        self.prefix, self.rabbit = base / "erlang", base / "rabbit"
        for path in (self.prefix / "bin/erl", self.prefix / "bin/epmd",
                     self.rabbit / "sbin/rabbitmq-server"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#!/bin/sh\nexit 0\n")
            path.chmod(0o700)
        self.layout = base / "layout.json"
        self.layout.write_text(json.dumps({"prefix": str(self.prefix),
                                           "rabbitmq_binary": str(self.rabbit)}))

    def prepare(self, run_id="guard_case_1234"):
        return native.NativeBroker.prepare(self.project, self.layout, run_id)

    def test_preparation_is_private_and_exclusive(self):
        broker = self.prepare()
        original = broker.cookie.read_bytes()
        for path in (broker.cookie, broker.credentials, broker.run / "manifest.json",
                     broker.run / "config/definitions.json"):
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(broker.run.stat().st_mode & 0o777, 0o700)
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(broker.cookie.read_bytes(), original)

    def test_definitions_omit_guest_and_limit_resource_scope(self):
        broker = self.prepare()
        definitions = json.loads((broker.run / "config/definitions.json").read_text())
        self.assertEqual(len(definitions["users"]), 1)
        self.assertNotEqual(definitions["users"][0]["name"], "guest")
        self.assertEqual(definitions["users"][0]["tags"], [])
        permission = definitions["permissions"][0]
        for key in ("configure", "write", "read"):
            self.assertEqual(permission[key], native.RESOURCE_PATTERN)
            self.assertNotEqual(permission[key], ".*")
        self.assertEqual(definitions["vhosts"], [{"name": broker.manifest["vhost"]}])

    def test_salted_hash_matches_real_source_algorithm(self):
        broker = self.prepare()
        definition = json.loads((broker.run / "config/definitions.json").read_text())["users"][0]
        encoded = base64.b64decode(definition["password_hash"])
        password = json.loads(broker.credentials.read_text())["password"].encode()
        self.assertEqual(len(encoded), 36)
        self.assertEqual(encoded[4:], hashlib.sha256(encoded[:4] + password).digest())
        self.assertEqual(definition["hashing_algorithm"], "rabbit_password_hashing_sha256")

    def test_cookie_arguments_have_no_secret_and_only_ascii_expression(self):
        broker = self.prepare()
        args, marker = broker.make_args(server=True)
        content = args.read_bytes()
        self.assertNotIn(broker.cookie.read_bytes().strip(), content)
        self.assertNotIn(b"-setcookie", content)
        self.assertIn(b"-nocookie\n", content)
        self.assertIn(b"-start_epmd false", content)
        self.assertLess(content.index(b"-sname"), content.index(b"-eval"))
        expression = content.split(b"-eval ", 1)[1].strip()
        self.assertTrue(expression.isascii())
        self.assertNotIn(b" ", expression)
        self.assertFalse(marker.exists())

    def test_env_preserves_homes_and_does_not_inherit_service_secrets(self):
        broker = self.prepare()
        with patch.dict(os.environ, {"HOME": "/original-home", "home": "original-lower",
                                     "CODEX_HOME": "original-codex", "DATABASE_URL": "private-db",
                                     "RABBITMQ_ERLANG_COOKIE": "private-cookie",
                                     "RABBITMQ_LOG": "debug"}):
            env = broker.env()
            self.assertEqual(env["HOME"], os.environ["HOME"])
            self.assertEqual(env["home"], os.environ["home"])
            self.assertEqual(env["CODEX_HOME"], os.environ["CODEX_HOME"])
            self.assertNotIn("DATABASE_URL", env)
            self.assertNotIn("RABBITMQ_ERLANG_COOKIE", env)
            self.assertEqual(env["RABBITMQ_LOG"], "warning")
            self.assertEqual(os.environ["RABBITMQ_LOG"], "debug")
            self.assertEqual(env["ERL_EPMD_ADDRESS"], "127.0.0.1")
            self.assertEqual(env["RABBITMQ_CONF_ENV_FILE"], "config/rabbitmq-env.conf")
            self.assertTrue((broker.run / env["RABBITMQ_CONF_ENV_FILE"]).is_file())

    def test_run_path_traversal_and_foreign_dependencies_rejected(self):
        with self.assertRaises(ValueError):
            self.prepare("../foreign")
        value = json.loads(self.layout.read_text())
        value["prefix"] = "/usr/local/erlang"
        self.layout.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            self.prepare()

    def test_cookie_symlink_and_public_mode_rejected(self):
        broker = self.prepare()
        broker.cookie.chmod(0o644)
        with self.assertRaises(ValueError):
            native.NativeBroker(self.project, broker.run)
        broker.cookie.chmod(0o600)
        target = broker.cookie.with_name("original-cookie")
        broker.cookie.rename(target)
        broker.cookie.symlink_to(target)
        with self.assertRaises(ValueError):
            native.NativeBroker(self.project, broker.run)

    def test_only_exact_loopback_node_names_accepted(self):
        for node in ("rabbit@foreign.example", "t44_native_demo_x@localhost -setcookie secret"):
            with self.assertRaises(ValueError):
                native.cookie_args(Path("cookie"), Path("marker"), node, "run", 1, 1)

    def test_owner_requires_pid_uid_start_time_pgid_and_command(self):
        original = {"pid": 123, "uid": os.getuid(), "started": "time", "pgid": 123,
                    "command_sha256": "fingerprint"}
        self.assertTrue(native.same_owner(original, dict(original)))
        for key in original:
            changed = dict(original)
            changed[key] = "changed"
            self.assertFalse(native.same_owner(original, changed))
        self.assertFalse(native.same_owner(original, None))

    def test_foreign_owner_never_signalled(self):
        broker = self.prepare()
        record = {"pid": 123, "uid": os.getuid(), "started": "time", "pgid": 123,
                  "command_sha256": "expected"}
        native.private_json(broker.state_path("rabbit"), record)
        with patch.object(native, "process_identity", return_value={**record, "started": "new"}), \
                patch.object(native.os, "killpg") as kill:
            with self.assertRaises(ValueError):
                broker.signal_owned("rabbit")
            kill.assert_not_called()

    def test_busy_ports_do_not_stop_any_process(self):
        with patch.object(native.socket, "socket") as socket_mock, \
                patch.object(native.os, "killpg") as kill:
            socket_mock.return_value.__enter__.return_value.bind.side_effect = OSError("busy")
            with self.assertRaises(OSError):
                native.assert_ports_free()
            kill.assert_not_called()

    def test_partial_stop_is_false_and_does_not_stop_epmd(self):
        broker = self.prepare()
        with patch.object(broker, "owner", return_value=({}, {"pid": 123})), \
                patch.object(broker, "execute", side_effect=RuntimeError("failure")), \
                patch.object(broker, "wait_stopped", return_value=False), \
                patch.object(broker, "signal_owned") as signal_owned:
            receipt = broker.stop()
        self.assertFalse(receipt["success"])
        signal_owned.assert_not_called()
        self.assertTrue(any(step["success"] is False for step in receipt["steps"]))

    def test_ps_getpgid_exit_race_is_absent_without_signal(self):
        result = native.subprocess.CompletedProcess([], 0, str(os.getuid()) + " Fri Oct 23 21:00:00 2026 own-command", "")
        with patch.object(native.subprocess, "run", return_value=result), \
                patch.object(native.os, "getpgid", side_effect=ProcessLookupError), \
                patch.object(native.os, "killpg") as kill:
            self.assertIsNone(native.process_identity(123))
            kill.assert_not_called()

    def test_no_wait_shutdown_still_requires_independent_exit(self):
        broker = self.prepare()
        with patch.object(broker, "owner", side_effect=[({}, {"pid": 123}), ({}, None)]), \
                patch.object(broker, "execute", return_value=("", {"receipt_id": "fixture"})) as execute, \
                patch.object(broker, "wait_stopped", return_value=True), \
                patch.object(broker, "signal_owned", return_value={"success": True, "needed": False}):
            receipt = broker.stop()
        execute.assert_called_once_with("rabbitmqctl", ["shutdown", "--no-wait"], timeout=25)
        self.assertTrue(receipt["success"])
        self.assertTrue(any(step["action"] == "rabbit_exit_observed" and step["success"] for step in receipt["steps"]))

    def test_non_loopback_listener_rejected(self):
        broker = self.prepare()
        result = native.subprocess.CompletedProcess([], 0, "p123\nn*:25674\n", "")
        with patch.object(broker, "owner", return_value=({}, {"pid": 123})), \
                patch.object(native.subprocess, "run", return_value=result), self.assertRaises(ValueError):
            broker.listeners("rabbit")

    def test_config_has_no_management_and_has_explicit_loopback(self):
        broker = self.prepare()
        text = (broker.run / "config/rabbitmq.conf").read_text()
        self.assertIn("listeners.tcp.1 = 127.0.0.1:25674", text)
        self.assertIn("distribution.listener.interface = 127.0.0.1", text)
        self.assertIn("log.file.level = warning", text)
        self.assertEqual((broker.run / "config/enabled_plugins").read_text(), "[].\n")

    def test_rabbit_cannot_start_before_owned_epmd_listener(self):
        broker = self.prepare()
        with patch.object(native, "assert_ports_free"), \
                patch.object(broker, "spawn") as spawn, \
                patch.object(broker, "wait_epmd_ready", side_effect=RuntimeError("not ready")), self.assertRaises(RuntimeError):
            broker.start()
        self.assertEqual([call.args[0] for call in spawn.call_args_list], ["epmd"])

    def test_deterministic_inspection_failure_is_not_retried(self):
        broker = self.prepare()
        path, marker = broker.make_args(server=True)
        marker.write_text("ready")
        with patch.object(native, "assert_ports_free"), \
                patch.object(broker, "make_args", return_value=(path, marker)), \
                patch.object(broker, "spawn"), patch.object(broker, "wait_epmd_ready"), \
                patch.object(broker, "execute", return_value=("", {})) as execute, \
                patch.object(broker, "inspect", side_effect=RuntimeError("DETERMINISTIC_FAILURE")) as inspect:
            result = broker.start()
        self.assertFalse(result["success"])
        self.assertEqual(result["inspection_error"], "DETERMINISTIC_FAILURE")
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(inspect.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
