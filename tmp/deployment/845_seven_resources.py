"""Synthetic projection/deadline guards only; never run the collector or read host /proc."""

import json
import runpy
from pathlib import Path

import pytest

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[2] / "deployment/seven-resource-sampler.py"))


def fixtures():
    mapping = {name: f"{index:064x}" for index, name in enumerate(MODULE["SERVICES"], 1)}
    labels = [[identity, "t44", service, True] for service, identity in mapping.items()]
    rows = [{name: (identity if name == "ID" else "synthetic") for name in MODULE["FIELDS"]}
            for identity in mapping.values()]
    return mapping, labels, rows


def label_text(rows):
    return "\n".join("\t".join(json.dumps(value) for value in row) for row in rows)


def stats_text(rows):
    return "\n".join(json.dumps(row) for row in rows)


def test_seven_services_include_gateway_and_strict_projection():
    mapping, labels, rows = fixtures()
    MODULE["validate_labels"](label_text(labels), mapping)
    result = MODULE["stats_projection"](stats_text(rows), mapping)
    assert len(result) == 7 and "tls-gateway" in result
    assert set(result["api"]) == {"ID", "CPUPerc", "MemUsage", "MemPerc", "NetIO", "BlockIO", "PIDs"}
    assert ".Config.Env" not in MODULE["INSPECT_FORMAT"]


@pytest.mark.parametrize("case", ["foreign", "duplicate", "stopped"])
def test_bad_mapping_or_state_refused(case):
    mapping, labels, _ = fixtures()
    if case == "foreign":
        labels[0][1] = "other-project"
    elif case == "duplicate":
        labels[1] = labels[0]
    else:
        labels[0][3] = False
    with pytest.raises(ValueError):
        MODULE["validate_labels"](label_text(labels), mapping)


@pytest.mark.parametrize("case", ["missing", "secret", "foreign"])
def test_partial_or_extra_stats_refused(case):
    mapping, _, rows = fixtures()
    if case == "missing":
        rows.pop()
    elif case == "secret":
        rows[0]["Env"] = "synthetic-secret-must-not-be-projected"
    else:
        rows[0]["ID"] = "f" * 64
    with pytest.raises(ValueError):
        MODULE["stats_projection"](stats_text(rows), mapping)


def test_expired_absolute_deadline_never_starts_process(monkeypatch):
    function = MODULE["command"]
    monkeypatch.setitem(function.__globals__, "END_UTC", 0)
    monkeypatch.setattr(function.__globals__["subprocess"], "run",
                        lambda *a, **kw: pytest.fail("must not launch"))
    with pytest.raises(ValueError, match="DEADLINE"):
        function(["forbidden"], float("inf"))
