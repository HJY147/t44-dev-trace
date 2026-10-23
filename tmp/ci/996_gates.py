"""CI guard unit tests; synthetic reports are never reported as application tests."""

import contextlib
import importlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/ci"))
run_tests = importlib.import_module("run_tests")
frontend = importlib.import_module("check_frontend_coverage")


class TruthfulGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_junit_empty_and_skipped_cannot_pass(self):
        report = self.root / "junit.xml"
        for content in ["<testsuites/>", "<testsuite><testcase><skipped/></testcase></testsuite>"]:
            report.write_text(content)
            self.assertFalse(run_tests.junit_has_real_success(report))

    def test_junit_actual_success_required(self):
        report = self.root / "junit.xml"
        report.write_text("<testsuite><testcase name='case'/></testsuite>")
        self.assertTrue(run_tests.junit_has_real_success(report))
        report.write_text("<testsuite><testcase><failure/></testcase></testsuite>")
        self.assertFalse(run_tests.junit_has_real_success(report))

    def frontend_report(self, line_covered=8, include_vue=True, passed=1):
        source = self.root / "frontend/src"
        folder = self.root / "frontend/coverage"
        source.mkdir(parents=True)
        folder.mkdir(parents=True)
        (source / "main.ts").write_text("export const example = 1")
        (source / "Page.vue").write_text("<template>Example</template>")
        (source / "env.d.ts").write_text("declare const value: string")
        measured = {str(source / "main.ts"): {}}
        if include_vue:
            measured[str(source / "Page.vue")] = {}
        (folder / "test-results.json").write_text(json.dumps({"success": True, "numPassedTests": passed, "numPendingTests": 0}))
        (folder / "coverage-final.json").write_text(json.dumps(measured))
        metrics = {key: {"total": 10, "covered": 0, "pct": 0} for key in ["statements", "branches", "functions", "lines"]}
        metrics["lines"] = {"total": 10, "covered": line_covered, "pct": line_covered * 10}
        (folder / "coverage-summary.json").write_text(json.dumps({"total": metrics}))

    def test_unmeasured_vue_source_cannot_hide_behind_high_average(self):
        self.frontend_report(include_vue=False)
        with patch.object(frontend, "ROOT", self.root), self.assertRaises(ValueError):
            frontend.main()

    def test_frontend_zero_tests_cannot_pass(self):
        self.frontend_report(passed=0)
        with patch.object(frontend, "ROOT", self.root), self.assertRaises(ValueError):
            frontend.main()

    def test_frontend_only_line_threshold_is_enforced(self):
        self.frontend_report()
        with patch.object(frontend, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()):
            frontend.main()

    def test_frontend_line_coverage_below_eighty_is_rejected(self):
        self.frontend_report(line_covered=7)
        with patch.object(frontend, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            frontend.main()


if __name__ == "__main__":
    unittest.main()
