"""Opt-in, one-shot synthetic validator diagnostic. Import never runs the benchmark."""

import argparse
import cProfile
import hashlib
import json
import pstats
import resource
import signal
import sysconfig
import time
from importlib.metadata import version
from pathlib import Path

SOURCE = "bc5aef9c62393134582affb7a690acb33ac2b833"
CONTRACTS_SHA = "ee2a72d0ee435a63686e80548da2fdc1b0b2df05c399820e19973f8100dc8cdc"
SPEC_SHA = "a77a5cd635b8f6a9927b60f9befac017055442504e34a95b40eddda809e2782f"
ROUNDS = 30
PROFILE_ROUNDS = 5


class Deadline(BaseException):
    """Do not let the expected referencing-exception capture swallow a time limit."""


def cases():
    def ref(name):
        return {"$ref": f"#/components/schemas/{name}"}

    plan = {
        "planned_start": "2026-10-24T00:00:00Z",
        "planned_end": "2026-10-25T00:00:00Z",
        "estimated_hours": 8,
        "buffer_hours": 1,
        "delay_contingency": "Synthetic local diagnostic",
    }
    evidence = [{"kind": 2, "locator": "synthetic/profile", "description": "Synthetic"}]
    task = {
        "title": "Synthetic",
        "iteration_id": 1,
        "owner_id": 1,
        "plan": plan,
        "dependency_task_ids": [],
    }
    values = [
        ("plan-valid", ref("Plan"), plan, True),
        ("plan-extra", ref("Plan"), {**plan, "extra": 1}, False),
        ("plan-calendar", ref("Plan"), {**plan, "planned_end": "2026-02-30T00:00:00Z"}, False),
        (
            "plan-year1000",
            ref("Plan"),
            {
                **plan,
                "planned_start": "1000-01-01T00:00:00Z",
                "planned_end": "1000-01-02T00:00:00Z",
            },
            True,
        ),
        (
            "plan-year9999",
            ref("Plan"),
            {
                **plan,
                "planned_start": "9999-01-01T00:00:00Z",
                "planned_end": "9999-01-02T00:00:00Z",
            },
            True,
        ),
        ("plan-boolean-hours", ref("Plan"), {**plan, "estimated_hours": True}, False),
        ("id-boolean", ref("Id"), True, False),
        ("id-integral-float", ref("Id"), 1.0, True),
        ("evidence-valid", ref("EvidenceRefs"), evidence, True),
        ("evidence-boolean", ref("EvidenceRefs"), [{**evidence[0], "kind": True}], False),
        ("task-valid", ref("TaskCreate"), task, True),
        (
            "task-nested-invalid",
            ref("TaskCreate"),
            {**task, "owner_id": True, "plan": {**plan, "extra": 1}},
            False,
        ),
        ("transition-valid", ref("TransitionRequest"), {"expected_version": 1, "action": 1}, True),
        (
            "transition-invalid",
            ref("TransitionRequest"),
            {"expected_version": True, "action": 0},
            False,
        ),
        (
            "contract-valid",
            ref("ContractValidationRequest"),
            {"category": 1, "payload": task},
            True,
        ),
        (
            "contract-invalid",
            ref("ContractValidationRequest"),
            {"category": 1, "payload": {**task, "extra": 1}},
            False,
        ),
        (
            "generated-wrapper",
            {
                "type": "object",
                "properties": {"body": ref("TaskCreate")},
                "required": ["body"],
                "additionalProperties": False,
            },
            {"body": task},
            True,
        ),
        ("all105-errors", {"type": "array", "items": ref("Id")}, [True] * 105, False),
        ("unknown-local-ref", ref("ProfileMissing"), {}, "raise"),
    ]
    return [
        {"name": name, "schema": schema, "value": value, "expected": expected}
        for name, schema, value, expected in values
    ]


def signature(factory, case):
    try:
        errors = list(factory(case["schema"]).iter_errors(case["value"]))
    except Exception as error:
        return {
            "outcome": "exception",
            "exception": type(error).__module__ + "." + type(error).__name__,
        }
    return {
        "outcome": "invalid" if errors else "valid",
        "total_errors": len(errors),
        "violations": [
            [
                "/" + "/".join(map(str, error.absolute_path)),
                str(error.validator),
                f"Does not satisfy {error.validator}",
            ]
            for error in errors[:100]
        ],
    }


def measured(function):
    wall, cpu = time.perf_counter(), time.process_time()
    value = function()
    return {
        "wall_seconds": time.perf_counter() - wall,
        "cpu_seconds": time.process_time() - cpu,
        "result": value,
    }


def constructor(factory, samples):
    for _ in range(ROUNDS):
        for case in samples:
            factory(case["schema"])
    return {"instances_constructed": ROUNDS * len(samples)}


def iterate(jobs):
    counts = {"jobs": 0, "errors": 0, "referencing_exceptions": 0}
    for validator, case in jobs:
        try:
            counts["errors"] += len(list(validator.iter_errors(case["value"])))
        except Exception:
            counts["referencing_exceptions"] += 1
        counts["jobs"] += 1
    return counts


def safe_file(filename, project):
    path = Path(filename)
    if filename.startswith("<") or filename == "~":
        return filename
    if path.is_relative_to(project):
        return str(path.relative_to(project))
    if "site-packages/" in filename:
        return "site-packages/" + filename.split("site-packages/", 1)[1]
    stdlib = Path(sysconfig.get_paths()["stdlib"])
    return "stdlib/" + str(path.relative_to(stdlib)) if path.is_relative_to(stdlib) else path.name


def profile(factory, samples, project):
    profiler = cProfile.Profile()
    try:
        profiler.enable()
        for _ in range(PROFILE_ROUNDS):
            for case in samples:
                signature(factory, case)
    finally:
        profiler.disable()
    rows = [
        {
            "file": safe_file(file, project),
            "line": line,
            "function": function,
            "primitive_calls": values[0],
            "total_calls": values[1],
            "exclusive_seconds": values[2],
            "inclusive_seconds": values[3],
        }
        for (file, line, function), values in pstats.Stats(profiler).stats.items()
    ]
    return {
        "clock": "cProfile default elapsed timer; inclusive values overlap",
        "calls": PROFILE_ROUNDS * len(samples),
        "functions": sorted(rows, key=lambda row: row["inclusive_seconds"], reverse=True),
    }


def write_json(path, report):
    part = path.with_suffix(path.suffix + ".part")
    part.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    part.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--tool-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.run:
        parser.error("Explicit --run is required; import alone performs no diagnostic")
    project = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if not output.is_relative_to(project / "agents/backend/source-budget-profile"):
        parser.error("Output is restricted to this role's public synthetic evidence directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as initial:
        initial.write('{"status":"starting"}\n')
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    report = {
        "status": "running",
        "source_commit": SOURCE,
        "tool_commit": args.tool_commit,
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "single sequential pure synthetic CPU batch, not HTTP/SQL/load/thread safety",
        "limits": {"wall_seconds": 15, "cpu_soft_seconds": 12, "cpu_hard_seconds": 15},
        "rounds": ROUNDS,
        "profile_rounds": PROFILE_ROUNDS,
        "phases": {},
    }

    def deadline(_signal, _frame):
        raise Deadline()

    signal.signal(signal.SIGALRM, deadline)
    signal.signal(signal.SIGXCPU, deadline)
    resource.setrlimit(resource.RLIMIT_CPU, (12, 15))
    signal.setitimer(signal.ITIMER_REAL, 15)
    exit_code = 1
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
        from t44 import contracts as production

        actual = Path(production.__file__).resolve()
        spec_path = actual.with_name("openapi.json")
        assert actual == project / "backend/t44/contracts/__init__.py"
        assert hashlib.sha256(actual.read_bytes()).hexdigest() == CONTRACTS_SHA
        assert hashlib.sha256(spec_path.read_bytes()).hexdigest() == SPEC_SHA
        assert version("jsonschema") == "4.26.0" and version("referencing") == "0.37.0"
        report["actual_import"] = {
            "module": str(actual.relative_to(project)),
            "contracts_sha256": CONTRACTS_SHA,
            "spec_sha256": SPEC_SHA,
            "jsonschema": version("jsonschema"),
            "referencing": version("referencing"),
        }
        spec_before = json.dumps(production.SPEC, sort_keys=True)
        root_start = measured(
            lambda: Draft202012Validator(
                {"$id": "urn:t44:api", **production.SPEC},
                format_checker=FormatChecker(),
                registry=Registry().with_resource(
                    "urn:t44:api",
                    Resource.from_contents(production.SPEC, default_specification=DRAFT202012),
                ),
            )
        )
        root = root_start.pop("result")
        checker_names = tuple(sorted(root.format_checker.checkers))
        report["prototype_one_off_root"] = root_start
        factories = {
            "production": production.validator,
            "prototypeC": lambda schema: root.evolve(schema=schema),
        }
        samples = cases()
        samples_before = json.dumps(samples, sort_keys=True)
        report["samples"] = samples
        report["equivalence"] = []
        for case in samples:
            original, candidate = (signature(factory, case) for factory in factories.values())
            expected = (
                "exception"
                if case["expected"] == "raise"
                else ("valid" if case["expected"] else "invalid")
            )
            row = {
                "case": case["name"],
                "production": original,
                "prototypeC": candidate,
                "equal": original == candidate,
                "expected_met": original["outcome"] == candidate["outcome"] == expected,
            }
            report["equivalence"].append(row)
            if not row["equal"] or not row["expected_met"]:
                raise AssertionError("Synthetic case mismatch; preserve original and stop")
        report["instance_boundaries"] = {}
        for mode, factory in factories.items():
            a, b = (
                factory({"$ref": "#/components/schemas/Id"}),
                factory({"$ref": "#/components/schemas/Id"}),
            )
            ga, gb = a.iter_errors(True), b.iter_errors(1)
            first, other, rest = next(ga, None), list(gb), list(ga)
            assert a is not b and ga is not gb and first is not None and other == [] and rest == []
            report["instance_boundaries"][mode] = {
                "distinct_validators": True,
                "distinct_interleaved_generators": True,
                "format_checker_shared_between_derived": a.format_checker is b.format_checker,
            }
        for mode, factory in factories.items():
            report["phases"][mode] = {
                "construct": measured(lambda factory=factory: constructor(factory, samples))
            }
            setup = measured(
                lambda factory=factory: [
                    (factory(case["schema"]), case) for _ in range(ROUNDS) for case in samples
                ]
            )
            jobs = setup.pop("result")
            report["phases"][mode]["iterate_setup_excluded"] = setup
            report["phases"][mode]["iter_errors"] = measured(lambda jobs=jobs: iterate(jobs))
            del jobs
            report["phases"][mode]["profile"] = profile(factory, samples, project)
            write_json(output, report)
        expected_errors = (
            sum(row["production"].get("total_errors", 0) for row in report["equivalence"]) * ROUNDS
        )
        expected_exceptions = (
            sum(row["production"]["outcome"] == "exception" for row in report["equivalence"])
            * ROUNDS
        )
        for phase in report["phases"].values():
            assert phase["iter_errors"]["result"] == {
                "jobs": ROUNDS * len(samples),
                "errors": expected_errors,
                "referencing_exceptions": expected_exceptions,
            }
        assert tuple(sorted(root.format_checker.checkers)) == checker_names
        report["checker_names_unchanged"] = True
        assert json.dumps(production.SPEC, sort_keys=True) == spec_before
        assert json.dumps(samples, sort_keys=True) == samples_before
        report["spec_and_inputs_unchanged"] = True
        report["status"] = "completed_limited_samples"
        exit_code = 0
    except Deadline:
        report["status"] = "time_limit_incomplete"
    except BaseException as error:
        report["status"] = "failed_preserved"
        report["exception_type"] = type(error).__name__
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        report["total_wall_seconds"] = time.perf_counter() - started_wall
        report["total_cpu_seconds"] = time.process_time() - started_cpu
        write_json(output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "wall": report["total_wall_seconds"],
                "cpu": report["total_cpu_seconds"],
                "output": str(output.relative_to(project)),
            }
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
