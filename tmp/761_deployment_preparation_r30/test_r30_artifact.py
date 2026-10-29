"""Deployment-owned offline boundary tests, with real Git context and hostile archives."""

import copy
import gzip
import hashlib
import importlib.util
import io
import json
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("r30", ROOT / "deployment/cloud-reuse/r30-backend-artifact.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class R30Boundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        cls.base = Path(cls.scratch.name)
        cls.package = cls.base / "package"
        cls.manifest = M.prepare(ROOT, cls.package, "r30test0001")
        cls.expected = M.sha(cls.package / "source-manifest.json")

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def clone(self, name):
        path = self.base / self.id().split(".")[-1] / name
        path.parent.mkdir(exist_ok=True)
        shutil.copytree(self.package, path)
        return path

    def test_real_git_prepare_and_verify_never_calls_docker(self):
        original = M.command

        def git_only(argv, timeout=120):
            self.assertEqual(str(argv[0]), "git")
            return original(argv, timeout)

        with patch.object(M, "command", side_effect=git_only):
            value, _ = M.verify_source(self.package, self.expected)
        self.assertEqual(value["source_sha"], M.SOURCE)
        self.assertEqual(len([r for r in value["files"] if r["path"].startswith("backend/t44/")]), 51)

    def test_frozen_schema_change_is_explicit_and_canonical_ddl_is_unchanged(self):
        value = json.loads((self.package / "frozen-comparison.json").read_text())
        self.assertFalse(value["all_47_equal"])
        self.assertEqual([r["path"] for r in value["differences"]], [M.SCHEMA])
        self.assertEqual(len(value["unchanged_files"]), 46)
        self.assertIn("backend/t44/persistence/schema_v1.sql", [r["path"] for r in value["unchanged_files"]])

    def test_exclusive_output_preserves_first_source_package(self):
        before = M.sha(self.package / "source-manifest.json")
        with self.assertRaises(FileExistsError):
            M.prepare(ROOT, self.package, "r30test0001")
        self.assertEqual(M.sha(self.package / "source-manifest.json"), before)

    def test_wrong_manifest_hash_refused(self):
        with self.assertRaisesRegex(ValueError, "PINNED_SOURCE_MANIFEST_HASH"):
            M.verify_source(self.package, "0" * 64)

    def test_stale_f7_source_identity_refused_even_with_rehashed_manifest(self):
        package = self.clone("stale")
        value = copy.deepcopy(self.manifest)
        value["source_sha"] = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
        (package / "source-manifest.json").write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "EXACT_SOURCE_SCHEMA"):
            M.verify_source(package, M.sha(package / "source-manifest.json"))

    def test_compressed_context_corruption_refused(self):
        package = self.clone("corrupt")
        with (package / "source-runtime-context.tar.gz").open("ab") as stream:
            stream.write(b"changed")
        with self.assertRaisesRegex(ValueError, "SOURCE_OBJECT_HASH_OR_SIZE"):
            M.verify_source(package, self.expected)

    def test_missing_object_refused(self):
        package = self.clone("missing")
        (package / "frozen-comparison.json").unlink()
        with self.assertRaises(FileNotFoundError):
            M.verify_source(package, self.expected)

    def test_symlink_source_object_refused(self):
        package = self.clone("symlink")
        (package / "frozen-comparison.json").unlink()
        (package / "frozen-comparison.json").symlink_to(self.package / "frozen-comparison.json")
        with self.assertRaisesRegex(ValueError, "REGULAR_SINGLE_LINK"):
            M.verify_source(package, self.expected)

    def test_extra_object_in_manifest_refused(self):
        package = self.clone("extra")
        value = copy.deepcopy(self.manifest)
        value["objects"]["unexpected.private"] = {"sha256": "0" * 64, "bytes": 0}
        (package / "source-manifest.json").write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "EXACT_SOURCE_SCHEMA"):
            M.verify_source(package, M.sha(package / "source-manifest.json"))

    def test_archive_rejects_traversal_links_duplicates_and_private_paths(self):
        for name, kind, duplicate in [("../escape", "file", False),
                                      ("backend/t44/link", "link", False),
                                      ("backend/t44/a.py", "file", True),
                                      (".runtime/session.json", "file", False)]:
            with self.subTest(name=name):
                output = io.BytesIO()
                with tarfile.open(fileobj=output, mode="w") as archive:
                    entry = tarfile.TarInfo(name)
                    entry.size = 1
                    if kind == "link":
                        entry.type, entry.linkname, entry.size = tarfile.SYMTYPE, "/etc/passwd", 0
                    archive.addfile(entry, io.BytesIO(b"x"))
                    if duplicate:
                        archive.addfile(entry, io.BytesIO(b"x"))
                with self.assertRaisesRegex(ValueError, "UNSAFE_DUPLICATE"):
                    M.archive_rows(output.getvalue())

    def test_runtime_probe_refuses_stale_missing_wrong_uid_and_mode(self):
        rows = [r for r in self.manifest["files"] if r["path"] not in M.RUNTIME_EXCLUDED]
        for uid, candidate in [(0, rows), (10001, rows[:-1]),
                               (10001, rows + [{"path": "backend/stale.py"}]),
                               (10001, [{**rows[0], "mode": 0o600}] + rows[1:])]:
            with self.subTest(uid=uid, count=len(candidate)):
                with self.assertRaisesRegex(ValueError, "EXACT_NONROOT_RUNTIME"):
                    M.verify_runtime({"uid": uid, "files": candidate}, self.manifest["files"])

    def test_nonroot_materialized_files_match_source_without_mode_loss(self):
        value, contents = M.verify_source(self.package, self.expected)
        context = self.base / "materialized"
        M.materialize(context, value, contents)
        for row in value["files"]:
            target = context / row["path"]
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), row["sha256"])
            self.assertEqual(target.stat().st_mode & 0o777, row["mode"])
        self.assertTrue(all(p.stat().st_mode & 0o777 == 0o755 for p in context.rglob("*") if p.is_dir()))

    def test_source_archive_has_actual_git_object_bytes(self):
        raw = gzip.decompress((self.package / "source-runtime-context.tar.gz").read_bytes())
        rows, contents = M.archive_rows(raw)
        self.assertEqual(rows, self.manifest["files"])
        self.assertEqual(contents[M.SCHEMA], M.command(["git", "-C", ROOT, "show", M.SOURCE + ":" + M.SCHEMA]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
