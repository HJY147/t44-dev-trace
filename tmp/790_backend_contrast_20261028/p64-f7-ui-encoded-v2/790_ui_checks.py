"""Complete outer-encoded UI command checks and local end-to-end replay."""

import ast
import base64
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "p64-f7-window1600"
BUILDER = HERE.parents[2] / "agents/backend/contrast-20261028/build-p64-f7-ui-v2.py"
# The test is under tmp/790.../folder, so project is three parents above HERE.
BUILDER = HERE.parents[2] / "agents/backend/contrast-20261028/build-p64-f7-ui-v2.py"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def delivery():
    return json.loads((HERE / "delivery.PUBLIC.json").read_text())


def decoded(ui):
    source = ui.decode().split("python3 - <<'PY'\n", 1)[1].rsplit("\nPY\n", 1)[0]
    call = next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "b64decode"
    )
    return base64.b64decode(ast.literal_eval(call.args[0]), validate=True)


def replay(index, target):
    row = delivery()["parts"][index]
    ui = (HERE / row["ui_file"]).read_bytes()
    raw = (HERE / row["raw_file"]).read_bytes()
    assert sha(ui) == row["ui_sha256"] and decoded(ui) == raw
    old = repr(delivery()["destination"])
    assert raw.decode().count(old) == 1
    local = raw.decode().replace(old, repr(str(target))).encode()
    # Same complete outer launcher; only the original root destination is redirected locally.
    spec = importlib.util.spec_from_file_location("owned_ui_outer", BUILDER)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    command = builder.outer(local)
    assert len(command) + 300 < 18000
    return subprocess.run(["sh"], input=b"umask 077\n" + command, capture_output=True, check=False)


def test_every_complete_base64_and_outer_UI_command_plus_description_fits():
    for row in delivery()["parts"]:
        raw = (HERE / row["raw_file"]).read_bytes()
        ui = (HERE / row["ui_file"]).read_bytes()
        assert len(raw) <= 12000 and len(raw) == row["raw_bytes"]
        assert len(base64.b64encode(raw)) + 300 == row["base64_plus_description"] < 18000
        assert len(ui) + 300 == row["complete_ui_plus_description"] < 18000
        assert sha(raw) == row["raw_sha256"] and sha(ui) == row["ui_sha256"]


def test_production_ready_UI_bytes_decode_to_exact_raw_scripts():
    for row in delivery()["parts"]:
        assert (
            decoded((HERE / row["ui_file"]).read_bytes()) == (HERE / row["raw_file"]).read_bytes()
        )


def test_complete_outer_launcher_installs_original_thirteen_sources(tmp_path):
    target = tmp_path / "new"
    for index in range(len(delivery()["parts"])):
        result = replay(index, target)
        assert result.returncode == 0, result.stderr.decode()
        assert json.loads(result.stdout)["all_thirteen_verified"] is (
            index == len(delivery()["parts"]) - 1
        )
    manifest = json.loads((target / "manifest.json").read_bytes())
    assert sha((target / "manifest.json").read_bytes()) == delivery()["runtime_manifest_sha256"]
    assert len(manifest["files"]) == 13
    for name, row in manifest["files"].items():
        assert (target / name).read_bytes() == (OLD / name).read_bytes()
        assert sha((target / name).read_bytes()) == row["sha256"]
        assert (target / name).stat().st_mode & 0o777 == 0o444


@pytest.mark.parametrize("last", [False, True])
def test_duplicate_outer_install_preserves_existing_outputs(tmp_path, last):
    target = tmp_path / "once"
    index = len(delivery()["parts"]) - 1 if last else 0
    for current in range(index + 1):
        assert replay(current, target).returncode == 0
    before = {
        str(p.relative_to(target)): sha(p.read_bytes()) for p in target.rglob("*") if p.is_file()
    }
    assert replay(index, target).returncode != 0
    assert {
        str(p.relative_to(target)): sha(p.read_bytes()) for p in target.rglob("*") if p.is_file()
    } == before


def test_mixed_bundle_refused_before_next_outer_fragment(tmp_path):
    target = tmp_path / "mixed"
    assert replay(0, target).returncode == 0
    marker = target / "install-bundle.PUBLIC.json"
    marker.chmod(0o600)
    marker.write_text(json.dumps({"bundle_sha256": "0" * 64}))
    assert replay(1, target).returncode != 0
    assert not (target / "790_host.py").exists()


def test_old_runtime_grants_and_legacy_test_files_are_byte_unchanged():
    manifest_raw = (OLD / "manifest.json").read_bytes()
    assert sha(manifest_raw) == "1da8ff5eaede6d6349c04ee8c3208a85ea2628b6a7604351e9dcfe332feb1de8"
    for name, row in json.loads(manifest_raw)["files"].items():
        assert sha((OLD / name).read_bytes()) == row["sha256"]
    root = HERE.parents[2]
    for name in (
        "prep-grant.template.PUBLIC.json",
        "pressure-grant.template.PUBLIC.json",
        "790_checks.py",
        "790_deadline_abort_checks.py",
        "transport/test_790_transfer.py",
    ):
        path = OLD / name
        relative = path.relative_to(root).as_posix()
        expected = subprocess.check_output(["git", "show", "d17cf53c:" + relative], cwd=root)
        assert path.read_bytes() == expected
