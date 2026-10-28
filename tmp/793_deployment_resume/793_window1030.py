"""Final window transport: complete encoded-command size, real local reassembly, no cloud."""

import argparse
import ast
import base64
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
FOLDER = ROOT / "agents/deployment/resume-20261028/window1030"
SPEC = importlib.util.spec_from_file_location("window1030_install", FOLDER / "reassemble-install-code.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
MANIFEST = json.loads((FOLDER / "manifest.PUBLIC.json").read_bytes())


def fixture(root):
    root.mkdir(mode=0o700)
    (root / "parts").mkdir(mode=0o700)
    (root / "manifest.PUBLIC.json").write_bytes((FOLDER / "manifest.PUBLIC.json").read_bytes())
    for record in MANIFEST["parts"]:
        (root / "parts" / record["path"]).write_bytes((FOLDER / record["path"]).read_bytes())


def test_every_complete_command_including_description_fits_actual_encoded_limit():
    proof = json.loads((FOLDER / "delivery-size-proof.PUBLIC.json").read_bytes())
    for record in proof["commands"]:
        raw = (ROOT / record["file"]).read_bytes()
        assert len(raw) == record["raw_bytes"] <= 13000
        assert len(base64.b64encode(raw)) + 256 == record["encoded_plus_256_description"] < 18000
        assert hashlib.sha256(raw).hexdigest() == record["sha256"]
        body = raw.decode().split("\n", 1)[1].rsplit("\n", 2)[0]
        compile(body, record["file"], "exec")
    assert all(row["bytes"] <= 8500 for row in MANIFEST["parts"])


def test_real_local_reassembly_and_exclusive_install_have_exact_bytes():
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp/793_deployment_resume") as directory:
        root = Path(directory).resolve() / "new-root"
        fixture(root)
        files = M.reassemble(root)
        assert set(files) == {"profile.json", "generation.py", "resource-stream.py"}
        M.install(root / "resume-profile", files)
        for name, raw in files.items():
            assert raw == (FOLDER / "profile" / name).read_bytes()
            assert (root / "resume-profile" / name).stat().st_mode & 0o777 == 0o600
        with pytest.raises(FileExistsError):
            M.install(root / "resume-profile", files)


@pytest.mark.parametrize("change", ["missing", "extra", "tampered", "symlink", "manifest"])
def test_partial_or_changed_transport_refuses_without_installing(change):
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp/793_deployment_resume") as directory:
        root = Path(directory).resolve() / "new-root"
        fixture(root)
        piece = root / "parts" / MANIFEST["parts"][0]["path"]
        if change == "missing":
            piece.unlink()
        elif change == "extra":
            (root / "parts/extra.bin").write_bytes(b"extra")
        elif change == "tampered":
            piece.write_bytes(b"tampered")
        elif change == "symlink":
            piece.unlink()
            piece.symlink_to(FOLDER / MANIFEST["parts"][0]["path"])
        else:
            (root / "manifest.PUBLIC.json").write_bytes(b"{}")
        with pytest.raises((ValueError, OSError)):
            M.reassemble(root)
        assert not (root / "resume-profile").exists()


def test_old_published_windows_remain_distinct_and_source_chain_is_exact():
    profile = json.loads((FOLDER / "profile/profile.json").read_bytes())
    assert profile["source_sha"] == "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
    assert profile["source_file_count"] == 53 and profile["stop_utc"] == "2026-10-28T10:30:00Z"
    original = json.loads((ROOT / "agents/deployment/resume-20261028/functional-profile-0815/profile.json").read_bytes())
    assert original["stop_utc"] == "2026-10-28T08:15:00Z"
    assert hashlib.sha256((ROOT / "agents/deployment/resume-20261028/functional-profile-0815/profile.json").read_bytes()).hexdigest() == "b940549052f149f616ae5e943cd6f6571d74142c497df8afb9b99f4513e85270"
    for name in ("generation.py", "resource-stream.py"):
        assert hashlib.sha256((FOLDER / "profile" / name).read_bytes()).hexdigest() == profile["derived_files"][name]["sha256"]
        tree = ast.parse((FOLDER / "profile" / name).read_bytes())
        hardstop = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                        and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "HARDSTOP")
        assert hardstop == "2026-10-28T10:30:00Z"


@pytest.mark.parametrize("mode", ["p16", "functional"])
def test_new_namespace_argv_parse_with_exact_new_generator_before_dispatch(mode):
    plan = json.loads((FOLDER / "prepare-plan.PUBLIC.json").read_bytes())[mode]
    assert re.fullmatch(r"[a-z][a-z0-9]{5,15}", plan["run_id"])
    assert plan["argv"][plan["argv"].index("--stop-utc") + 1] == "2026-10-28T10:30:00Z"

    class ParsedOnly(Exception):
        pass

    parse = argparse.ArgumentParser.parse_args

    def parse_only(parser, args=None, namespace=None):
        value = parse(parser, args, namespace)
        assert value.run_id == plan["run_id"] and value.p_workers == plan["p_workers"]
        raise ParsedOnly

    path = FOLDER / "profile/generation.py"
    with patch.object(sys, "argv", [str(path), *plan["argv"][2:]]), patch.object(
        argparse.ArgumentParser, "parse_args", parse_only
    ), pytest.raises(ParsedOnly):
        runpy.run_path(str(path), run_name="__main__")
