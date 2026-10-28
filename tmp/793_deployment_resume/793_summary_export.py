"""Bounded observer transport checks only; no SUT or cloud execution."""

import copy
import importlib.util
import json
import os
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "summary_export", ROOT / "deployment/cloud-reuse/observer-summary-export.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class SummaryTransport(unittest.TestCase):
    def setUp(self):
        self.raw = json.dumps(
            {"synthetic": random.Random(793).randbytes(50000).hex()}
        ).encode()
        self.patches = [
            patch.object(M, "RAW_BYTES", len(self.raw)),
            patch.object(M, "RAW_SHA", M.digest(self.raw)),
        ]
        for context in self.patches:
            context.start()
        first = M.encode(self.raw, 0)
        self.rows = [M.encode(self.raw, i) for i in range(first["chunks"])]

    def tearDown(self):
        for context in reversed(self.patches):
            context.stop()

    def test_multichunk_roundtrip_in_any_order_and_bounded_output(self):
        self.assertGreater(len(self.rows), 1)
        self.assertEqual(M.decode(list(reversed(self.rows))), self.raw)
        self.assertLess(max(len(json.dumps(row)) for row in self.rows), 14000)

    def test_missing_chunk_rejected(self):
        with self.assertRaises(ValueError):
            M.decode(self.rows[:-1])

    def test_duplicate_chunk_rejected(self):
        with self.assertRaises(ValueError):
            M.decode([self.rows[0], *self.rows[:-1]])

    def test_chunk_corruption_rejected(self):
        bad = copy.deepcopy(self.rows)
        bad[0]["base64"] = "A" + bad[0]["base64"][1:]
        with self.assertRaises(ValueError):
            M.decode(bad)

    def test_manifest_mismatch_rejected(self):
        bad = copy.deepcopy(self.rows)
        bad[-1]["gzip_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            M.decode(bad)

    def test_offset_corruption_rejected(self):
        bad = copy.deepcopy(self.rows)
        bad[1]["offset"] += 1
        with self.assertRaises(ValueError):
            M.decode(bad)

    def test_approved_source_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            M.encode(self.raw + b"x", 0)
        for index in (-1, len(self.rows), True):
            with self.assertRaises(ValueError):
                M.encode(self.raw, index)

    def test_wrong_whole_compressed_hash_rejected(self):
        bad = copy.deepcopy(self.rows)
        for row in bad:
            row["gzip_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            M.decode(bad)

    def test_real_regular_read_and_hash_rejection(self):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "tmp/793_deployment_resume"
        ) as folder:
            path = Path(folder) / "original.json"
            path.write_bytes(self.raw)
            self.assertEqual(
                M.read_checked(path, len(self.raw), M.digest(self.raw)), self.raw
            )
            with self.assertRaises(ValueError):
                M.read_checked(path, len(self.raw), "0" * 64)
            with self.assertRaises(ValueError):
                M.read_checked(path, len(self.raw) + 1, M.digest(self.raw))

    def test_symlink_source_refused(self):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "tmp/793_deployment_resume"
        ) as folder:
            source = Path(folder) / "original.json"
            source.write_bytes(self.raw)
            link = Path(folder) / "link.json"
            link.symlink_to(source)
            with self.assertRaises(OSError):
                M.read_checked(link, len(self.raw), M.digest(self.raw))

    def test_fixed_descriptor_output_does_not_overwrite(self):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "tmp/793_deployment_resume"
        ) as folder:
            os.chmod(folder, 0o700)
            path = Path(folder) / "received.json"
            M.write_new(path, self.raw)
            self.assertEqual(path.read_bytes(), self.raw)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                M.write_new(path, b"different")
            self.assertEqual(path.read_bytes(), self.raw)

    def test_symlink_output_refused_without_modifying_target(self):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "tmp/793_deployment_resume"
        ) as folder:
            os.chmod(folder, 0o700)
            target, link = Path(folder) / "target", Path(folder) / "link"
            target.write_bytes(b"keep")
            link.symlink_to(target)
            with self.assertRaises(OSError):
                M.write_new(link, self.raw)
            self.assertEqual(target.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
