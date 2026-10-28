"""Narrow time/path derivation and actual outer-command replay; no SUT/network."""

import ast
import base64
import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = HERE.parent / "p64-f7-window1600"
BUILDER = ROOT / "agents/backend/contrast-20261028/build-p64-f7-2000.py"
UTC = timezone.utc  # noqa: UP017 -- host3.10.


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


builder = module(BUILDER, "owned_20z_builder")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def document(name):
    return json.loads((HERE / name).read_bytes())


def test_thirteen_runtime_files_only_exact_window_literals_changed():
    before = json.loads((OLD / "manifest.json").read_bytes())
    after = document("manifest.json")
    assert len(after["files"]) == 13
    same = 0
    for name, item in before["files"].items():
        old = (OLD / name).read_bytes()
        new = (HERE / name).read_bytes()
        assert sha(old) == item["sha256"]
        expected = old.decode()
        for first, second in builder.CHANGES.get(name, []):
            assert expected.count(first) == 1
            expected = expected.replace(first, second)
        assert new == expected.encode()
        assert sha(new) == after["files"][name]["sha256"]
        ast.parse(new, feature_version=(3, 10))
        same += old == new
    assert same == 9
    permitted = {
        "files",
        "window_utc",
        "supersedes_manifest_sha256",
        "phase_GEN_sha256",
    }
    assert {k: v for k, v in before.items() if k not in permitted} == {
        k: v for k, v in after.items() if k not in permitted
    }
    assert after["window_utc"] == "2026-10-28T20:00:00Z"
    assert after["supersedes_manifest_sha256"] == builder.OLD_MANIFEST
    assert after["phase_GEN_sha256"] == builder.GEN_SHA


def test_templates_only_window_path_and_manifest_pins_change_and_stay_unadmitted():
    manifest_sha = sha((HERE / "manifest.json").read_bytes())
    for side in ("APP", "LOAD"):
        name = f"{side}-configuration.template.PUBLIC.json"
        expected = json.loads((OLD / name).read_bytes())
        expected.update(tools_dir=builder.DEST, manifest_sha256=manifest_sha)
        assert document(name) == expected
        assert (
            expected["root_grant_sha256"] is None and expected["binding_sha256"] is None
        )
    for mode in ("prep", "pressure"):
        name = f"{mode}-grant.template.PUBLIC.json"
        expected = json.loads((OLD / name).read_bytes())
        expected.update(
            stop_utc="2026-10-28T20:00:00Z", expires_at="2026-10-28T20:00:00Z"
        )
        assert document(name) == expected
        assert expected["admitted"] is False and expected["session_nonce"] is None


def test_actual_deployment_generator_is_only_new_stop_not_new_algorithm():
    old = (OLD / "fixtures/generation-f7.PUBLIC.py").read_bytes()
    new = (HERE / "fixtures/generation-f7-2000.PUBLIC.py").read_bytes()
    assert old.count(b"2026-10-28T16:00:00Z") == 1
    assert new == old.replace(b"2026-10-28T16:00:00Z", b"2026-10-28T20:00:00Z")
    assert sha(new) == builder.GEN_SHA
    ast.parse(new, feature_version=(3, 10))


def test_old_packages_original46_and_failure_records_remain_exact_git_bytes():
    directories = (OLD, HERE.parent / "p64-f7-ui-encoded-v2")
    for folder in directories:
        relative = folder.relative_to(ROOT).as_posix()
        names = (
            subprocess.check_output(
                ["git", "ls-tree", "-r", "--name-only", "20eb4ae3", relative], cwd=ROOT
            )
            .decode()
            .splitlines()
        )
        assert names
        for name in names:
            expected = subprocess.check_output(
                ["git", "show", "20eb4ae3:" + name], cwd=ROOT
            )
            assert (ROOT / name).read_bytes() == expected


def decode(ui):
    source = ui.decode().split("python3 - <<'PY'\n", 1)[1].rsplit("\nPY\n", 1)[0]
    call = next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "b64decode"
    )
    return base64.b64decode(ast.literal_eval(call.args[0]), validate=True)


def test_complete_outer_commands_and_encoded_payloads_fit_real_ceiling():
    value = document("delivery.PUBLIC.json")
    assert value["destination"] == builder.DEST and len(value["parts"]) == 7
    for row in value["parts"]:
        raw, ui = (
            (HERE / row["raw_file"]).read_bytes(),
            (HERE / row["ui_file"]).read_bytes(),
        )
        assert sha(raw) == row["raw_sha256"] and sha(ui) == row["ui_sha256"]
        assert len(raw) == row["raw_bytes"] <= 12000
        assert (
            len(base64.b64encode(raw)) + 300 == row["base64_plus_description"] < 18000
        )
        assert len(ui) + 300 == row["complete_ui_plus_description"] < 18000
        assert decode(ui) == raw


def test_actual_full_outer_installation_roundtrip_and_no_overwrite(tmp_path):
    value = document("delivery.PUBLIC.json")
    outer = builder.load_builder("build-p64-f7-ui-v2.py").outer
    target = tmp_path / "new20z"
    commands = []
    for row in value["parts"]:
        ui = (HERE / row["ui_file"]).read_bytes()
        raw = decode(ui)
        assert raw.count(repr(builder.DEST).encode()) == 1
        local = raw.replace(repr(builder.DEST).encode(), repr(str(target)).encode())
        command = outer(local)
        commands.append(command)
        result = subprocess.run(
            ["sh"], input=b"umask 077\n" + command, capture_output=True, check=False
        )
        assert result.returncode == 0, result.stderr.decode()
    assert (
        sha((target / "manifest.json").read_bytes()) == value["runtime_manifest_sha256"]
    )
    for name, row in document("manifest.json")["files"].items():
        assert (target / name).read_bytes() == (HERE / name).read_bytes()
        assert sha((target / name).read_bytes()) == row["sha256"]
        assert (target / name).stat().st_mode & 0o777 == 0o444
    before = {
        str(p.relative_to(target)): sha(p.read_bytes())
        for p in target.rglob("*")
        if p.is_file()
    }
    assert (
        subprocess.run(
            ["sh"], input=commands[0], capture_output=True, check=False
        ).returncode
        != 0
    )
    assert {
        str(p.relative_to(target)): sha(p.read_bytes())
        for p in target.rglob("*")
        if p.is_file()
    } == before


def test_new_window_guard_rejects_old16_and_expiry_without_any_network():
    authority = module(HERE / "edge/790_authority.py", "owned_20z_authority")
    fixture = module(OLD / "grant_fixture.py", "owned_old_grant_fixture")
    control = {
        "source_sha": authority.SOURCE,
        "run_id": "r28p64gen99",
        "binding_sha256": "a" * 64,
        "namespace": "t44-cloud-r28p64gen99-p",
        "database": "t44c_r28p64gen99_p",
        "api_workers": 64,
        "seed": 44,
        "anchor_at": authority.ANCHOR,
        "stop_utc": authority.STOP,
    }
    control = fixture.pressure(control)
    grant = json.loads(base64.b64decode(control["root_grant_b64"]))
    grant["expires_at"] = authority.STOP

    def attach(value, issued):
        raw = json.dumps(issued).encode()
        return {
            **value,
            "root_grant_b64": base64.b64encode(raw).decode(),
            "root_grant_sha256": sha(raw),
        }

    fresh = attach(control, grant)
    assert (
        authority.check_control(
            fresh, "pressure", datetime(2026, 10, 28, 19, tzinfo=UTC)
        )["session_ttl_seconds"]
        == 600
    )
    with pytest.raises(ValueError, match="FINITE_ROOT_GRANT"):
        authority.check_control(
            fresh, "pressure", datetime(2026, 10, 28, 20, tzinfo=UTC)
        )
    old = attach(
        {**control, "stop_utc": "2026-10-28T16:00:00Z"},
        {
            **grant,
            "stop_utc": "2026-10-28T16:00:00Z",
            "expires_at": "2026-10-28T16:00:00Z",
        },
    )
    with pytest.raises(ValueError, match="EXACT_20Z_WINDOW"):
        authority.check_control(old, "pressure", datetime(2026, 10, 28, 15, tzinfo=UTC))
    with pytest.raises(ValueError, match="WRONG_ROOT_GRANT_STAGE"):
        authority.check_control(fresh, "prep", datetime(2026, 10, 28, 19, tzinfo=UTC))
