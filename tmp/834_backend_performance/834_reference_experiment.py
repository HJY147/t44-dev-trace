"""Opt-in diagnostic-only local-ref expansion; never imported by the product."""

import contextlib
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path


class Ineligible(Exception):
    """Retain the original validator for contexts whose ref semantics are not in scope."""


def factory(original, spec):
    def candidate(schema):
        memo, active = {}, set()

        def expand(value):
            if isinstance(value, dict):
                if any(
                    key in value
                    for key in (
                        "$id",
                        "$schema",
                        "$anchor",
                        "$dynamicAnchor",
                        "$dynamicRef",
                        "unevaluatedProperties",
                        "unevaluatedItems",
                    )
                ):
                    raise Ineligible()
                if "$ref" in value:
                    if len(value) != 1:
                        raise Ineligible()
                    ref = value["$ref"]
                    prefix = "#/components/schemas/"
                    name = ref.removeprefix(prefix)
                    if ref.startswith(prefix) and name in spec["components"]["schemas"]:
                        if ref in active:
                            raise Ineligible()
                        if ref not in memo:
                            active.add(ref)
                            memo[ref] = expand(spec["components"]["schemas"][name])
                            active.remove(ref)
                        return memo[ref]
                return {key: expand(item) for key, item in value.items()}
            if isinstance(value, list):
                return [expand(item) for item in value]
            return value

        with contextlib.suppress(Ineligible):
            schema = expand(schema)
        return original(schema)

    return candidate


def main():
    # All operational imports are gated by running this script, not by importing the factory.
    from t44 import api, contracts
    from t44.services import application, history

    assert api.violations is application.violations is history.violations is contracts.violations
    root = Path(__file__).resolve().parents[2]
    raw = Path(__file__).read_bytes()
    assert raw == subprocess.check_output(
        ["git", "show", "HEAD:tmp/834_backend_performance/834_reference_experiment.py"], cwd=root
    )
    original_validator, original_violations = contracts.validator, contracts.violations
    spec_before = json.dumps(contracts.SPEC, sort_keys=True)
    candidate = factory(original_validator, contracts.SPEC)

    def reference_violations(schema, value):
        # The driver's response checker remains the original implementation.
        return [
            {"path": "/" + "/".join(map(str, error.absolute_path)), "rule": str(error.validator)}
            for error in original_validator(schema).iter_errors(value)
        ]

    driver_path = Path(__file__).with_name("834_request_profile.py")
    module_spec = importlib.util.spec_from_file_location("request_cpu_diagnostic", driver_path)
    driver = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(driver)
    original_run = driver.run

    def run(args, project, report):
        report["experiment"] = {
            "kind": "diagnostic-only per-call local-ref expansion; no production change",
            "tool_sha256": hashlib.sha256(raw).hexdigest(),
            "cross_request_cache": False,
            "response_reference_checker": "original factory, never the candidate",
            "fallback": "ref siblings, scope/draft/dynamic/unevaluated keywords or cycles",
        }
        return original_run(args, project, report)

    driver.run = run
    contracts.validator = candidate
    # Product aliases were imported before this change. Only the diagnostic client's
    # later import sees this checker; production violations still call the candidate.
    contracts.violations = reference_violations
    try:
        driver.main()
        assert json.dumps(contracts.SPEC, sort_keys=True) == spec_before
    finally:
        contracts.validator, contracts.violations = original_validator, original_violations


if __name__ == "__main__":
    main()
