"""Private credential lifecycle guards; backend calls are mocked, not product tests."""

import contextlib
import json
import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from deployment import credential_admin


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.directory.chmod(0o700)
        self.target = self.directory / "scheduler-token.json"
        self.next_session = 100

    def backend(self, *arguments):
        if arguments[0] == "revoke-session":
            return {"revoked_sessions": 1}
        self.next_session += 1
        path = Path(arguments[arguments.index("--token-file") + 1])
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump({"access_token": "synthetic-test-only-" * 3, "session_id": self.next_session,
                       "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()}, stream)
        return {"session_id": self.next_session}

    def test_issue_is_private_and_never_returns_token(self):
        with patch.object(credential_admin, "backend", side_effect=self.backend):
            result = credential_admin.issue([2, 1], name="scheduler", rotate=False, credential=self.target)
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("access_token", json.dumps(result))
        self.assertEqual(credential_admin.private_metadata(self.target)["session_id"], result["session_id"])

    def test_initial_issuance_cannot_overwrite(self):
        with patch.object(credential_admin, "backend", side_effect=self.backend):
            credential_admin.issue([1], name="scheduler", rotate=False, credential=self.target)
            original = self.target.read_bytes()
            with self.assertRaises(ValueError):
                credential_admin.issue([1], name="scheduler", rotate=False, credential=self.target)
            self.assertEqual(original, self.target.read_bytes())

    def test_rotate_changes_inode_and_revokes_old_session(self):
        with patch.object(credential_admin, "backend", side_effect=self.backend) as backend:
            first = credential_admin.issue([1], name="scheduler", rotate=False, credential=self.target)
            inode = self.target.stat().st_ino
            result = credential_admin.issue([1], name="scheduler", rotate=True, credential=self.target)
            self.assertNotEqual(inode, self.target.stat().st_ino)
            self.assertTrue(result["previous_session_revoked"])
            backend.assert_any_call("revoke-session", "--session-id", str(first["session_id"]))

    def test_group_readable_file_and_missing_scopes_are_rejected(self):
        with patch.object(credential_admin, "backend", side_effect=self.backend):
            credential_admin.issue([1], name="scheduler", rotate=False, credential=self.target)
        self.target.chmod(0o640)
        with self.assertRaises(ValueError):
            credential_admin.private_metadata(self.target)
        with self.assertRaises(ValueError):
            credential_admin.issue([], name="scheduler", rotate=True, credential=self.target)

    def test_failed_backend_preserves_existing_private_file(self):
        with patch.object(credential_admin, "backend", side_effect=self.backend):
            credential_admin.issue([1], name="scheduler", rotate=False, credential=self.target)
        original = self.target.read_bytes()
        with patch.object(credential_admin, "backend", side_effect=RuntimeError("synthetic backend failure")), \
                contextlib.suppress(RuntimeError):
            credential_admin.issue([1], name="scheduler", rotate=True, credential=self.target)
        self.assertEqual(original, self.target.read_bytes())

    def test_expired_credential_can_be_explicitly_renewed(self):
        with patch.object(credential_admin, "backend", side_effect=self.backend):
            credential_admin.issue([1], name="scheduler", rotate=False, credential=self.target)
            content = json.loads(self.target.read_text())
            content["expires_at"] = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
            self.target.write_text(json.dumps(content))
            result = credential_admin.issue([1], name="scheduler", rotate=True, credential=self.target)
            self.assertTrue(result["rotated"])
            self.assertTrue(result["previous_session_revoked"])


if __name__ == "__main__":
    unittest.main()
