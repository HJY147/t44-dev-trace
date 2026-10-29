"""Post-run pure guard supplements; no HTTP/DB, never rewrite the pre-timing guard count."""

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from prototype import FastGate

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "profile"))
from diagnose import SOURCE, export_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    assert args.output.parent.resolve() == root / "agents/backend/p16-schema-response-20261028"
    report = {
        "source": SOURCE,
        "stage": "post-timing-pure-supplement-only",
        "HTTP_calls": 0,
        "DB_calls": 0,
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": [],
        "false_accept": False,
    }
    with args.output.open("x") as output:
        try:
            with tempfile.TemporaryDirectory(prefix="t44-schema-pure-") as tmp:
                exported = Path(tmp)
                export_source(root, exported)
                sys.path.insert(0, str(exported / "backend"))
                from t44.contracts import SPEC, violations

                unique = {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {"anyOf": [{"type": "integer"}, {"type": "boolean"}, {"type": "object"}]},
                }
                nested = {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}}
                default = {"type": "object", "properties": {"a": {"type": "integer", "default": 1}}}
                cases = [
                    ("duplicate-scalar", unique, [1, 1]),
                    ("bool-integer-distinct", unique, [True, 1]),
                    ("duplicate-object-order", unique, [{"a": 1, "b": 2}, {"b": 2, "a": 1}]),
                    ("nested-invalid-truncation100", nested, [[False] * 105]),
                    ("default-not-inserted", default, {}),
                    ("integer-float", {"type": "integer"}, 1.0),
                    ("integer-bool-rejected", {"type": "integer"}, True),
                    ("boolean-integer-rejected", {"type": "boolean"}, 1),
                    ("enum-bool-number-distinct", {"enum": [1]}, True),
                    ("const-bool-number-distinct", {"const": True}, 1),
                    ("quarter-invalid", {"type": "number", "multipleOf": 0.25}, 0.1),
                    ("quarter-valid", {"type": "number", "multipleOf": 0.25}, 0.5),
                    ("regex-newline-fallback", {"type": "string", "pattern": "^a$"}, "a\n"),
                ]
                for name, schema, value in cases:
                    before = copy.deepcopy(value)
                    expected = violations(schema, value)
                    gate = FastGate([schema], violations, SPEC)
                    actual = gate(schema, value)
                    entry = {
                        "label": name,
                        "expected": expected,
                        "actual": actual,
                        "gate_counts": dict(gate.counts),
                        "value_unchanged": value == before,
                    }
                    report["cases"].append(entry)
                    if actual != expected or value != before:
                        report["false_accept"] = bool(expected) and actual == []
                        raise ValueError("SUPPLEMENT_FAIL_SEAL_NO_MORE_TIMING")
                assert len(report["cases"][3]["expected"]) == 100
                report["status"] = "passed"
        except BaseException as error:
            report.update(status="failed", failure_class=type(error).__name__)
            raise
        finally:
            json.dump(report, output, indent=2)
            output.write("\n")
    print(
        json.dumps({"status": report["status"], "cases": len(report["cases"]), "false_accept": report["false_accept"]})
    )


if __name__ == "__main__":
    main()
