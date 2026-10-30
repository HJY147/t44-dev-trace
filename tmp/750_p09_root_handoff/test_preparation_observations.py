"""Offline handoff regression: progress updates are evidence, fixed identities cannot change."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'unpack_p09', ROOT / 'agents/deployment/final-window/P09-COLLECT-UNPACK.PUBLIC.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def row(preparation, clock=None):
    files = {'preparation.PUBLIC.json': preparation}
    if clock is not None:
        files['timeplan.PUBLIC.json'] = clock
    return json.dumps({'kind': 'USER_P09_PUBLIC_COLLECTOR', 'event': 'BOOTSTRAP_READY',
                       'files': {name: {'status': 'PRESENT', 'bytes': len(raw),
                                       'sha256': hashlib.sha256(raw).hexdigest(),
                                       'zlib_b64': base64.b64encode(zlib.compress(raw)).decode()}
                                 for name, raw in files.items()}})


class ProgressEvidenceTests(unittest.TestCase):
    def test_progress_preserves_both_originals_and_replay_is_idempotent(self):
        early = b'{"status":"PREPARING"}\n'
        ready = b'{"status":"READY"}\n'
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / 'evidence'
            first = MODULE.unpack(row(early), dest)
            last = MODULE.unpack(row(ready), dest)
            self.assertEqual((dest / 'preparation.PUBLIC.json').read_bytes(), early)
            self.assertEqual((dest / first['preparation_observation']).read_bytes(), early)
            self.assertEqual((dest / last['preparation_observation']).read_bytes(), ready)
            self.assertEqual(MODULE.unpack(row(ready), dest), last)
            self.assertEqual(len(list((dest / 'preparation-observations').iterdir())), 2)

    def test_fixed_clock_change_still_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / 'evidence'
            clock = b'{"run_id":"r30finalp09","start_utc":"original"}\n'
            changed = b'{"run_id":"r30finalp09","start_utc":"changed"}\n'
            MODULE.unpack(row(b'{}', clock), dest)
            with self.assertRaisesRegex(ValueError, 'EXISTING_ORIGINAL_DIFFERS'):
                MODULE.unpack(row(b'{}', changed), dest)
            self.assertEqual((dest / 'timeplan.PUBLIC.json').read_bytes(), clock)

    def test_progress_sha_mismatch_refused_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / 'evidence'
            value = json.loads(row(b'{}'))
            value['files']['preparation.PUBLIC.json']['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'SHA_MISMATCH'):
                MODULE.unpack(json.dumps(value), dest)
            self.assertFalse(dest.exists())

    def test_observation_directory_symlink_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / 'evidence'
            dest.mkdir()
            elsewhere = Path(folder) / 'elsewhere'
            elsewhere.mkdir()
            (dest / 'preparation-observations').symlink_to(elsewhere)
            with self.assertRaisesRegex(ValueError, 'SYMLINK_REFUSED'):
                MODULE.unpack(row(b'{}'), dest)
            self.assertEqual(list(elsewhere.iterdir()), [])

    def test_unrecognized_top_level_preparation_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / 'evidence'
            MODULE.unpack(row(b'{"status":"PREPARING"}'), dest)
            (dest / 'preparation.PUBLIC.json').write_bytes(b'{"status":"tampered"}')
            with self.assertRaisesRegex(ValueError, 'FIRST_OBSERVATION_ARCHIVE'):
                MODULE.unpack(row(b'{"status":"READY"}'), dest)


if __name__ == '__main__':
    unittest.main()
