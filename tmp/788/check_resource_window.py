"""Hand-calculated CLI fixtures; no production sampler or cloud access."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("resource_window.py")
BEGIN = "2026-10-28T00:00:01Z"
END = "2026-10-28T00:00:04Z"


def sample(second, role="api", cpu=None, rss=None, memory=None, sequence=None):
    return {
        "kind": "resource_sample",
        "utc": f"2026-10-28T00:00:{second:02d}Z",
        "monotonic_ns": second * 1_000_000_000,
        "sequence": sequence or second + 1,
        "role": role,
        "resource_id": "fixture/" + role,
        "cpu_percent": cpu,
        "rss_bytes": rss,
        "cgroup_memory_bytes": memory,
    }


class ResourceWindowChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.raw = Path(self.directory.name) / "input.jsonl"

    def write_rows(self, rows):
        self.raw.write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in rows))
        return hashlib.sha256(self.raw.read_bytes()).hexdigest()

    def run_cli(self, digest, path=None, begin=BEGIN, end=END):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--raw",
                str(path or self.raw),
                "--sha256",
                digest,
                "--begin",
                begin,
                "--end",
                end,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_known_percentiles_memory_and_window_coverage(self):
        rows = [{"kind": "resource_header", "utc": "2026-10-28T00:00:00Z", "interval_seconds": 1}]
        for second, cpu, rss, memory in [
            (0, None, 1, 1),
            (1, 50, 12, 999),
            (2, 150, 88, 900),
            (3, 200, 30, 800),
            (4, 400, 20, 700),
            (6, 9999, 9999, 9999),
        ]:
            rows.append(sample(second, cpu=cpu, rss=rss, memory=memory))
        for second in (1, 2, 3, 4):
            row = sample(second, role="scheduler")
            row["missing_reason"] = "ValueError:missing_role"
            rows.append(row)
        rows += [{"kind": "resource_sampling_error", "utc": f"2026-10-28T00:00:0{s}Z"} for s in (2, 7)]
        rows.append({"kind": "resource_final", "utc": "2026-10-28T00:00:08Z"})
        digest = self.write_rows(rows)
        before = self.raw.read_bytes(), self.raw.stat().st_mtime_ns
        result = self.run_cli(digest)
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)
        api = out["roles"]["api"]
        self.assertEqual(
            api["cpu_percent"], {"valid": 4, "null_or_absent": 0, "invalid": 0, "max": 400, "p50": 150, "p95": 400}
        )
        self.assertEqual(api["rss_bytes"]["max"], 88)
        self.assertEqual(api["cgroup_memory_bytes"]["max"], 999)
        self.assertEqual(api["start_gap"]["max_seconds"], 1)
        self.assertEqual(api["head_delay_seconds"], 0)
        self.assertEqual(api["tail_gap_seconds"], 0)
        self.assertEqual(out["sampling_error_rows_in_window"], 1)
        self.assertEqual(out["record_counts"]["resource_sampling_error"], 2)
        scheduler = out["roles"]["scheduler"]
        self.assertEqual(scheduler["missing_role_rows"], 4)
        self.assertIsNone(scheduler["cpu_percent"]["p95"])
        self.assertIsNone(scheduler["rss_bytes"]["max"])
        self.assertIsNone(out["roles"]["mysql"]["start_gap"]["max_seconds"])
        self.assertIsNone(out["roles"]["mysql"]["cpu_percent"]["p50"])
        self.assertTrue(out["stream_header_first"] and out["stream_final_last"])
        self.assertIsNone(out["performance_verdict"])
        self.assertLess(len(result.stdout), 32769)
        self.assertEqual(before, (self.raw.read_bytes(), self.raw.stat().st_mtime_ns))

    def test_gap_missing_sequence_and_invalid_metrics(self):
        a = sample(1, cpu=-1, rss=True, memory=float("inf"))
        b = sample(4, cpu=250, rss=10, memory=100)
        digest = self.write_rows([a, b])
        out = json.loads(self.run_cli(digest).stdout)["roles"]["api"]
        self.assertEqual(out["start_gap"]["max_seconds"], 3)
        self.assertEqual(out["unobserved_sequences_between_samples"], 2)
        self.assertEqual(out["cpu_percent"]["invalid"], 1)
        self.assertEqual(out["rss_bytes"]["invalid"], 1)
        self.assertEqual(out["cgroup_memory_bytes"]["invalid"], 1)
        self.assertEqual(out["cpu_percent"]["p95"], 250)

    def test_absent_sequences_are_unknown_not_zero(self):
        rows = [sample(1), sample(2)]
        for row in rows:
            del row["sequence"]
        out = json.loads(self.run_cli(self.write_rows(rows)).stdout)["roles"]["api"]
        self.assertEqual(out["sequence_numeric_samples"], 0)
        self.assertEqual(out["sequence_known_pair_count"], 0)
        self.assertIsNone(out["unobserved_sequences_between_samples"])
        self.assertIsNone(out["sequence_nonincreasing_pairs"])

    def test_rejects_wrong_digest_symlink_truncated_and_zero_window(self):
        digest = self.write_rows([sample(1)])
        link = self.raw.with_name("link.jsonl")
        link.symlink_to(self.raw)
        cases = [("0" * 64, self.raw, BEGIN, END), (digest, link, BEGIN, END), (digest, self.raw, BEGIN, BEGIN)]
        self.raw.write_bytes(self.raw.read_bytes().rstrip(b"\n"))
        cases.append((hashlib.sha256(self.raw.read_bytes()).hexdigest(), self.raw, BEGIN, END))
        for sha, path, begin, end in cases:
            with self.subTest(path=path.name, begin=begin, sha=sha):
                result = self.run_cli(sha, path=path, begin=begin, end=end)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    json.loads(result.stdout), {"error": "RESOURCE_WINDOW_INPUT_REJECTED", "performance_verdict": None}
                )
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
