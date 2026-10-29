"""Parse proposed argv against the exact reconstructed public tools; never execute actions."""

import argparse
import hashlib
import importlib.util
import json
import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLAN = json.loads(
    (
        ROOT / "agents/deployment/resume-20261028/p7-p16-command-plan.PUBLIC.json"
    ).read_bytes()
)
SPEC = importlib.util.spec_from_file_location(
    "derive_command_plan", ROOT / "deployment/cloud-reuse/derive-resume-profile.py"
)
DERIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DERIVE)


def tools():
    return DERIVE.derive_texts(
        DERIVE.checked_templates(), PLAN["source_sha"], PLAN["stop_utc"], 53
    )


def test_reconstructed_tools_match_exact_cloud_public_sha_and_bytes():
    result = tools()
    assert (
        hashlib.sha256(result["generation.py"].encode()).hexdigest()
        == PLAN["generation_sha256"]
    )
    assert len(result["generation.py"].encode()) == 27199
    assert (
        hashlib.sha256(result["resource-stream.py"].encode()).hexdigest()
        == PLAN["resource_helper_sha256"]
    )
    assert len(result["resource-stream.py"].encode()) == 44079


@pytest.mark.parametrize("name", list(PLAN["actions"]))
def test_every_proposed_action_parses_with_real_tool_without_execution(name):
    entry = PLAN["actions"][name]
    is_generation = (
        name == "p16-generation-prepare"
        or name.endswith("owned-stop")
        or name
        in {
            "p16-arm",
            "p16-config",
            "p16-infra",
            "p16-migrate",
            "p16-idle",
            "p16-status",
        }
    )
    text = tools()["generation.py" if is_generation else "resource-stream.py"]

    class ParsedOnly(Exception):
        pass

    parse = argparse.ArgumentParser.parse_args

    def stop_after_parse(parser, args=None, namespace=None):
        parsed = parse(parser, args, namespace)
        raise ParsedOnly(parsed)

    # Canonical fixture lives only in this project's tmp793. No action reaches its dispatch.
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp/793_deployment_resume") as folder:
        path = Path(folder) / "tool.py"
        path.write_text(text)
        with (
            patch.object(sys, "argv", [str(path), *entry["argv"][2:]]),
            patch.object(argparse.ArgumentParser, "parse_args", stop_after_parse),
            pytest.raises(ParsedOnly),
        ):
            runpy.run_path(str(path), run_name="__main__")


def test_cleanup_is_not_blocked_by_expired_start_window():
    for name, entry in PLAN["actions"].items():
        if name.endswith(("-stop", "-status", "-seal")):
            assert entry["minimum_remaining_seconds"] is None
        assert entry["execute_automatically"] is False


def test_two_arm_namespaces_ports_and_ids_are_distinct_and_nonmysql():
    prepare = PLAN["actions"]["p16-generation-prepare"]["argv"]
    ports = [
        int(prepare[prepare.index(flag) + 1])
        for flag in ["--f-tls-port", "--f-http-port", "--p-tls-port", "--p-http-port"]
    ]
    assert len(set(ports)) == 4 and 13306 not in ports
    assert prepare[prepare.index("--run-id") + 1] == "r28p16gen01"
    assert prepare[prepare.index("--p-workers") + 1] == "16"
    assert prepare[prepare.index("--output") + 1].endswith("campaign-r28p16-01")
    for workers in (7, 16):
        args = PLAN["actions"][f"p{workers}-resource-prepare"]["argv"]
        assert args[args.index("--phase-dir") + 1].endswith(
            f"campaign-r28p{workers}-01/p"
        )
        assert args[args.index("--run-id") + 1] == f"r28p{workers}metrics01"
        assert "ROOT_LOAD_PRIVATE_IP" in args and "ROOT_APP_PRIVATE_IP" in args


def test_deadlines_leave_final_tail_and_new_sut_guard_at_ten_minutes():
    for workers in (7, 16):
        args = PLAN["actions"][f"p{workers}-resource-prepare"]["argv"]
        assert args[args.index("--sample-until") + 1] == "2026-10-28T07:28:30Z"
        assert args[args.index("--serve-until") + 1] == "2026-10-28T07:29:30Z"
        assert (
            PLAN["actions"][f"p{workers}-resource-prepare"]["minimum_remaining_seconds"]
            >= 210
        )
    for state in ("config", "infra", "migrate", "idle"):
        assert PLAN["actions"]["p16-" + state]["minimum_remaining_seconds"] == 600
