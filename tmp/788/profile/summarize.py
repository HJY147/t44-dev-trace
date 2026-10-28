"""Derive exclusive CPU groups and separate unprofiled/profiled measurements."""

import gzip
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[3]
    folder = root / "agents/backend/cpu-profile-20261028"
    inputs = (
        ("baseline-01.json", "0df044fba87bfe581125774ca2bc7006e76d34bb8b8f7b4b5f8ba4e9db5e532e"),
        ("query-construction-01.json", None),
    )
    objects, manifest = {}, []
    for name, expected in inputs:
        data = (folder / name).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if expected is not None and digest != expected:
            raise ValueError("EXPECTED_BASELINE_HASH")
        obj = json.loads(data)
        if obj["status"] != "completed":
            raise ValueError("COMPLETED_INPUT_ONLY")
        compressed = gzip.compress(data, mtime=0)
        if gzip.decompress(compressed) != data:
            raise ValueError("GZIP_ROUNDTRIP")
        with (folder / (name + ".gz")).open("xb") as output:
            output.write(compressed)
        manifest.append(
            {
                "raw": name,
                "raw_bytes": len(data),
                "raw_sha256": digest,
                "gzip": name + ".gz",
                "gzip_bytes": len(compressed),
                "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
                "roundtrip_equal": True,
            }
        )
        objects[name] = obj
    baseline, candidate = objects[inputs[0][0]], objects[inputs[1][0]]
    summary = {
        "source": baseline["source"],
        "total_http_requests": baseline["total_http_requests"],
        "setup_requests": baseline["setup_requests"],
        "network_or_mysql_attempts_blocked": baseline["network_or_mysql_attempts_blocked"],
        "profile_clock": baseline["clock"],
        "profiles": {},
        "formal_acceptance": False,
        "root_cause": "NOT_PROVEN",
    }
    for operation, profile in baseline["profiles"].items():
        measured = [r for r in baseline["rows"] if r["operation"] == operation and r["phase"] == "measured"]
        groups = Counter()
        for function in profile["functions"]:
            path, name = function["file"], function["function"]
            group = (
                "sqlalchemy_sql_expression"
                if "/sqlalchemy/sql/" in path
                else "sqlalchemy_other"
                if "/sqlalchemy/" in path
                else "jsonschema_referencing"
                if "/jsonschema/" in path or "/referencing/" in path or "attrs generated methods referencing" in path
                else "t44_wire"
                if path == "backend/t44/services/common.py" and name == "wire"
                else "other"
            )
            groups[group] += function["exclusive_cpu_seconds"]
        if abs(sum(groups.values()) - profile["total_profiled_cpu_seconds"]) > 1e-8:
            raise ValueError("EXCLUSIVE_PARTITION_MUST_EQUAL_TOTAL")
        summary["profiles"][operation] = {
            "unprofiled_samples": len(measured),
            "unprofiled_handler_cpu_median_ms": statistics.median(r["thread_cpu_ms"] for r in measured),
            "unprofiled_handler_wall_median_ms": statistics.median(r["handler_wall_ms"] for r in measured),
            "profile_samples": profile["samples"],
            "instrumented_profile_cpu_mean_ms": profile["total_profiled_cpu_seconds"] * 1000 / profile["samples"],
            "exclusive_groups_instrumented_ms_per_request": {
                k: v * 1000 / profile["samples"] for k, v in groups.items()
            },
            "top_exclusive": profile["functions"][:20],
            "top_inclusive_do_not_sum": sorted(
                profile["functions"], key=lambda r: r["inclusive_cpu_seconds"], reverse=True
            )[:20],
            "shape_observation": [r for r in baseline["rows"] if r["operation"] == operation and r["phase"] == "shape"],
        }
    phases = {r["phase"]: r["median_batch_mean_us_per_statement"] for r in candidate["timings"]}
    summary["pure_query_candidate"] = {
        "guards": candidate["guards"],
        "timings": candidate["timings"],
        "A1_over_B1": phases["A1"] / phases["B1"],
        "A2_over_B2": phases["A2"] / phases["B2"],
        "A1_to_B1_reduction_percent": (1 - phases["B1"] / phases["A1"]) * 100,
        "A2_to_B2_reduction_percent": (1 - phases["B2"] / phases["A2"]) * 100,
        "expected_net_effective_line_change": 0,
        "end_to_end_candidate_run": False,
    }
    with (folder / "summary.json").open("x") as output:
        json.dump(summary, output, indent=2)
        output.write("\n")
    with (folder / "raw-manifest.json").open("x") as output:
        json.dump(manifest, output, indent=2)
        output.write("\n")
    print(json.dumps({"raw_manifest": manifest, "candidate": summary["pure_query_candidate"]}, indent=2))


if __name__ == "__main__":
    main()
