"""Public functional profile parsing and transport guards, without any cloud action."""

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import re
import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "agents/deployment/resume-20261028"
PROFILE = FOLDER / "functional-profile-0815"
TRANSPORT = FOLDER / "functional-transport.PUBLIC.json"
SPEC = importlib.util.spec_from_file_location(
    "functional_install_guard", FOLDER / "functional-transport-install-code.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def constants(path):
    return {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse(path.read_bytes()).body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id
        in {
            "SOURCE",
            "HARDSTOP",
            "SOURCE_COUNT",
            "BUILDER_SHA",
            "GENERATOR_SHA",
            "FACTORY_SHA",
        }
    }


def test_new_source_deadline_chain_and_old_factory_pin():
    profile = json.loads((PROFILE / "profile.json").read_bytes())
    generation = constants(PROFILE / "generation.py")
    resource = constants(PROFILE / "resource-stream.py")
    assert (
        generation["SOURCE"]
        == resource["SOURCE"]
        == profile["source_sha"]
        == M.EXPECTED_SOURCE
    )
    assert (
        generation["HARDSTOP"]
        == resource["HARDSTOP"]
        == profile["stop_utc"]
        == M.EXPECTED_STOP
    )
    assert generation["SOURCE_COUNT"] == profile["source_file_count"] == 53
    assert (
        generation["BUILDER_SHA"]
        == "ebc91ce54ee73a418b9df11c3878ae75e348198b64c25060aeff8462de3949d1"
    )
    assert (
        generation["FACTORY_SHA"]
        == "daaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea"
    )
    assert (
        resource["GENERATOR_SHA"]
        == hashlib.sha256((PROFILE / "generation.py").read_bytes()).hexdigest()
    )


def test_public_transport_exact_three_files_without_writing_cloud():
    files = M.unpack(TRANSPORT.read_bytes())
    assert set(files) == {"profile.json", "generation.py", "resource-stream.py"}
    for name, raw in files.items():
        assert raw == (PROFILE / name).read_bytes()
    assert len((FOLDER / "functional-install-once.sh").read_bytes()) < 32768


def test_outer_transport_tampering_refused():
    with pytest.raises(ValueError, match="TRANSPORT_SHA"):
        M.unpack(TRANSPORT.read_bytes() + b" ")


@pytest.mark.parametrize(
    "change", ["source", "stop", "path", "duplicate", "compressed", "size"]
)
def test_inner_manifest_guards_still_refuse_changed_transport(change):
    value = json.loads(TRANSPORT.read_bytes())
    if change == "source":
        value["source_sha"] = "0" * 40
    elif change == "stop":
        value["stop_utc"] = "2026-10-28T09:00:00Z"
    elif change == "path":
        value["files"][0]["path"] = "../profile.json"
    elif change == "duplicate":
        value["files"][1] = copy.deepcopy(value["files"][0])
    elif change == "compressed":
        value["files"][1]["gzip_sha256"] = "0" * 64
    else:
        value["files"][1]["bytes"] = 1000000000
    raw = json.dumps(value).encode()
    with (
        patch.object(M, "TRANSPORT_SHA", hashlib.sha256(raw).hexdigest()),
        pytest.raises(ValueError),
    ):
        M.unpack(raw)


def test_real_local_install_is_exclusive_and_preserves_bytes():
    files = M.unpack(TRANSPORT.read_bytes())
    with tempfile.TemporaryDirectory(
        dir=ROOT / "tmp/793_deployment_resume"
    ) as directory:
        destination = Path(directory).resolve() / "fresh"
        M.install(destination, files)
        assert destination.stat().st_mode & 0o777 == 0o700
        for name, raw in files.items():
            assert (destination / name).read_bytes() == raw
            assert (destination / name).stat().st_mode & 0o777 == 0o600
        with pytest.raises(FileExistsError):
            M.install(destination, files)


def test_runid_ports_and_generation_cli_parse_without_dispatch():
    run_id = "r28funcgen01"
    assert re.fullmatch(r"[a-z][a-z0-9]{5,15}", run_id)
    assert len(run_id) == 12
    assert len({22443, 18480, 22445, 18481}) == 4
    args = [
        "prepare",
        "--factory",
        "/root/t44-r9/campaign-935/p/controller.py",
        "--upgrade-binding",
        "/root/t44-r9/resume-20261028-01/build-01/upgrade-binding.json",
        "--upgrade-binding-sha256",
        "31fc1c8a9cd2162656c8cfc9a42e830e228494d1e644f143921bbb718834cbd8",
        "--source-package",
        "/root/t44-r9/resume-20261028-01/source-checked-01",
        "--source-manifest-sha256",
        "68f9db715b4a9d33d1cc70c5f7d08a50fcd51c97dfd4276dceba71e93d9ade00",
        "--original-proof",
        "/root/t44-r9/proof-v2-01/proof.jsonl",
        "--image-proof",
        "/root/t44-r9/image-proof.py",
        "--output",
        "/root/t44-r9/campaign-r28functional-01",
        "--run-id",
        run_id,
        "--app-ip",
        "ROOT_APP_PRIVATE_IP",
        "--f-tls-port",
        "22443",
        "--f-http-port",
        "18480",
        "--p-tls-port",
        "22445",
        "--p-http-port",
        "18481",
        "--p-workers",
        "7",
        "--stop-utc",
        M.EXPECTED_STOP,
    ]

    class ParsedOnly(Exception):
        pass

    parse = argparse.ArgumentParser.parse_args

    def stop_before_dispatch(parser, args=None, namespace=None):
        value = parse(parser, args, namespace)
        assert value.run_id == run_id and value.p_workers == 7
        assert value.stop_utc == M.EXPECTED_STOP
        raise ParsedOnly

    path = PROFILE / "generation.py"
    with (
        patch.object(sys, "argv", [str(path), *args]),
        patch.object(argparse.ArgumentParser, "parse_args", stop_before_dispatch),
        pytest.raises(ParsedOnly),
    ):
        runpy.run_path(str(path), run_name="__main__")
