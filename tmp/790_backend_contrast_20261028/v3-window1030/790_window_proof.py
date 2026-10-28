"""Exact raw/AST delta proof against frozen v2; public owned files only, no cloud reads."""

import ast
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OLD_MANIFEST = "640b3d386a756547d940b638ef6ccfc9bc49adaa2c071a2794aca8464b2edd84"
TEST_EDITS = (
    ("2026-10-28T07:30:00Z", "2026-10-28T10:30:00Z"),
    ("2026-10-28T07:30:00", "2026-10-28T10:30:00"),
    ("2026-10-28T08:00:00Z", "2026-10-28T11:00:00Z"),
    (
        "datetime(2026, 10, 28, 7, 30, tzinfo=UTC)",
        "datetime(2026, 10, 28, 10, 30, tzinfo=UTC)",
    ),
    (
        "datetime(2026, 10, 28, 7, 29, 58, tzinfo=UTC)",
        "datetime(2026, 10, 28, 10, 29, 58, tzinfo=UTC)",
    ),
    ("[(7, 29), (8, 0)]", "[(10, 29), (11, 0)]"),
    ("r28p7gen01", "r28p16gen02"),
    ('("api_workers", 16)', '("api_workers", 7)'),
    ('"api_workers": 7', '"api_workers": 16'),
    ('"workers": 7', '"workers": 16'),
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(raw):
    return ast.dump(ast.parse(raw), include_attributes=False)


def rewrite(raw, changes):
    for before, after in changes:
        raw = raw.replace(before, after)
    return raw


def attest(old, new, edits):
    expected = rewrite(old, edits)
    assert new == expected, "Only explicit raw substitutions permitted"
    assert dump(new) == dump(expected)
    old_tree, new_tree = ast.parse(old), ast.parse(new)
    old_asserts = [node for node in ast.walk(old_tree) if isinstance(node, ast.Assert)]
    new_asserts = [node for node in ast.walk(new_tree) if isinstance(node, ast.Assert)]
    assert len(old_asserts) == len(new_asserts)
    for before, after in zip(old_asserts, new_asserts, strict=True):
        original = ast.get_source_segment(old, before)
        rewritten = rewrite(original, edits)
        assert ast.dump(ast.parse(rewritten).body[0]) == ast.dump(after)
    before_names = [node.name for node in ast.walk(old_tree) if isinstance(node, ast.FunctionDef)]
    after_names = [node.name for node in ast.walk(new_tree) if isinstance(node, ast.FunctionDef)]
    assert before_names == after_names
    return {
        "old_sha256": sha(old.encode()),
        "new_sha256": sha(new.encode()),
        "exact_raw_allowlist": True,
        "whole_AST_equals_only_authorized_data_replacements": True,
        "old_assertions": len(old_asserts),
        "new_assertions": len(new_asserts),
        "assertions_removed": 0,
        "functions_removed_or_renamed": 0,
        "assertion_AST_equal_after_authorized_literal_data_replacements": True,
    }


def main():
    old_manifest_raw = (BASE / "manifest.json").read_bytes()
    assert sha(old_manifest_raw) == OLD_MANIFEST
    old_manifest = json.loads(old_manifest_raw)
    new_manifest_raw = (HERE / "manifest.json").read_bytes()
    new_manifest = json.loads(new_manifest_raw)
    assert new_manifest["tool_version"] == 3
    assert new_manifest["supersedes_manifest_sha256"] == OLD_MANIFEST
    assert new_manifest["window_utc"] == "2026-10-28T10:30:00Z"
    assert set(new_manifest["files"]) == set(old_manifest["files"])
    result = {"diagnostic_files": {}, "tests": {}, "transport": {}}
    for name, row in old_manifest["files"].items():
        before, after = (BASE / name).read_text(), (HERE / name).read_text()
        assert sha(before.encode()) == row["sha256"]
        edits = []
        if name in {"790_bootstrap.py", "edge/790_http.py"}:
            edits = [
                (
                    "HARDSTOP = datetime(2026, 10, 28, 7, 30, tzinfo=UTC)",
                    "HARDSTOP = datetime(2026, 10, 28, 10, 30, tzinfo=UTC)",
                )
            ]
            assert before.count(edits[0][0]) == 1
        result["diagnostic_files"][name] = attest(before, after, edits)
        assert new_manifest["files"][name] == {
            "bytes": len(after.encode()),
            "sha256": sha(after.encode()),
        }
    for name in ("790_checks.py", "790_deadline_abort_checks.py"):
        result["tests"][name] = attest(
            (BASE / name).read_text(), (HERE / name).read_text(), TEST_EDITS
        )
    result["transport"]["helper"] = attest(
        (BASE / "transport/790_transfer.py").read_text(),
        (HERE / "transport/790_transfer.py").read_text(),
        [
            (
                "STOP = datetime(2026, 10, 28, 7, 30, tzinfo=UTC)",
                "STOP = datetime(2026, 10, 28, 10, 30, tzinfo=UTC)",
            )
        ],
    )
    result["transport"]["tests"] = attest(
        (BASE / "transport/test_790_transfer.py").read_text(),
        (HERE / "transport/test_790_transfer.py").read_text(),
        [("2026-10-28T07:30:00Z", "2026-10-28T10:30:00Z")],
    )
    for name in ("790_bootstrap.py", "790_host.py", "790_load.py", "transport/790_transfer.py"):
        tree = ast.parse((HERE / name).read_text(), feature_version=(3, 10))
        assert not any(
            isinstance(node, ast.ImportFrom)
            and node.module == "datetime"
            and any(alias.name == "UTC" for alias in node.names)
            for node in ast.walk(tree)
        )
    cases = list(ET.parse(HERE / "local-final.xml").getroot().iter("testcase"))
    diagnostic = [case for case in cases if ".transport." not in case.attrib["classname"]]
    transport = [case for case in cases if ".transport." in case.attrib["classname"]]
    assert len(diagnostic) == 33 and len(transport) == 13
    assert not any(
        case.find(kind) is not None for case in cases for kind in ("failure", "error", "skipped")
    )
    result.update(
        {
            "old_manifest_sha256": OLD_MANIFEST,
            "new_manifest_sha256": sha(new_manifest_raw),
            "diagnostic_cases_passed": len(diagnostic),
            "transport_cases_passed": len(transport),
            "failure_error_skip": 0,
            "no_cloud_or_independent_execution": True,
            "600s_ttl_cohorts_thresholds_and_fail_stop_byte_identical": True,
            "host_python310_AST": True,
            "old_v2_manifest_and_seven_files_exactly_preserved": True,
        }
    )
    destination = HERE / "verification.json"
    with destination.open("x") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(
        json.dumps(
            {
                "verification_sha256": sha(destination.read_bytes()),
                "diagnostic_passed": 33,
                "transport_passed": 13,
                "manifest_sha256": result["new_manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
