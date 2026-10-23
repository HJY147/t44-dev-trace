"""Deployment safety tests use local temporary files and mocked Docker only."""

import argparse
import contextlib
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deployment import ops


class OperationsSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name)
        self.env = self.path / ".env"
        with contextlib.redirect_stdout(io.StringIO()):
            ops.generate_env(self.env)
        self.values = ops.load_env(self.env)

    def recovery(self):
        source = self.path / "backup.sql"
        source.write_text("CREATE TABLE example (id INT);\n")
        manifest = {"format": "t44-table-dump-v1", "database": "t44", "table_count": 1,
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        source.with_name(source.name + ".manifest.json").write_text(json.dumps(manifest))
        return argparse.Namespace(database="t44_recovered", project="t44-restore-test",
                                  confirm_target="t44-restore-test/t44_recovered", input=source, execute=False)

    def test_generated_secrets_are_independent_and_private(self):
        self.assertEqual(stat.S_IMODE(self.env.stat().st_mode), 0o600)
        names = ["MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "RABBITMQ_DEFAULT_PASS"]
        self.assertEqual(len({self.values[name] for name in names}), 3)
        self.assertTrue(all(len(self.values[name]) == 64 for name in names))

    def test_existing_file_or_symlink_is_never_overwritten(self):
        original = self.env.read_bytes()
        with self.assertRaises(FileExistsError):
            ops.generate_env(self.env)
        symlink = self.path / "symlink"
        symlink.symlink_to(self.env)
        with self.assertRaises(FileExistsError):
            ops.generate_env(symlink)
        self.assertEqual(original, self.env.read_bytes())

    def test_group_readable_configuration_is_rejected(self):
        self.env.chmod(0o640)
        with self.assertRaises(ValueError):
            ops.load_env(self.env)

    def test_backup_wrong_target_rejected_before_docker(self):
        with patch.object(ops, "query") as query, patch.object(ops, "compose") as compose:
            with self.assertRaises(ValueError):
                ops.backup(self.env, self.values, "another_database", self.path / "output.sql")
            query.assert_not_called()
            compose.assert_not_called()

    def test_backup_never_silently_omits_programmable_objects(self):
        with patch.object(ops, "query", return_value="1"), patch.object(ops, "compose") as compose:
            with self.assertRaises(ValueError):
                ops.backup(self.env, self.values, "t44", self.path / "output.sql")
            compose.assert_not_called()

    def test_restore_live_database_is_rejected_before_docker(self):
        args = self.recovery()
        args.database = "t44"
        with patch.object(ops, "compose") as compose:
            with self.assertRaises(ValueError):
                ops.restore(self.env, self.values, args)
            compose.assert_not_called()

    def test_restore_requires_exact_project_database_confirmation(self):
        args = self.recovery()
        args.confirm_target = "t44-restore-test/wrong"
        with self.assertRaises(ValueError):
            ops.restore(self.env, self.values, args)

    def test_restore_modified_dump_is_rejected_before_docker(self):
        args = self.recovery()
        args.input.write_text("changed")
        with patch.object(ops.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                ops.restore(self.env, self.values, args)
            run.assert_not_called()

    def test_restore_plan_never_calls_docker(self):
        with patch.object(ops.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()):
            ops.restore(self.env, self.values, self.recovery())
            run.assert_not_called()

    def test_existing_recovery_volume_is_rejected_without_reset(self):
        args = self.recovery()
        args.execute = True
        with patch.object(ops.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)), \
                patch.object(ops, "compose") as compose, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                ops.restore(self.env, self.values, args)
            compose.assert_not_called()

    def test_compose_target_ignores_inherited_docker_host_and_database(self):
        with patch.dict(os.environ, {"DOCKER_HOST": "tcp://unintended:2375", "MYSQL_DATABASE": "wrong"}), \
                patch.object(ops.subprocess, "run") as run:
            ops.compose(self.env, self.values, "config", "--quiet")
            command = run.call_args.args[0]
            environment = run.call_args.kwargs["env"]
            self.assertEqual(command[:3], ["docker", "--context", "default"])
            self.assertNotIn("DOCKER_HOST", environment)
            self.assertEqual(environment["MYSQL_DATABASE"], "t44")


if __name__ == "__main__":
    unittest.main()
