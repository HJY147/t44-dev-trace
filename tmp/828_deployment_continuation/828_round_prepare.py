"""New-round preparation checks only; never run a generated main or contact services."""

import ast
import importlib.util
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("round_preparation_test", ROOT / "deployment/round-prepare.py")
ROUND = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROUND)
NOW = datetime(2026, 10, 25, 6, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def originals():
    return {
        name: subprocess.run(
            ["git", "show", ROUND.BASE + ":deployment/" + name], cwd=ROOT, check=True, capture_output=True
        ).stdout
        for name in ROUND.PINS
    }


@pytest.fixture
def plan():
    return {
        "round_id": "r20261025a1",
        "source_sha": ROUND.BASE,
        "issued_utc": "2026-10-25T06:00:00Z",
        "operation_deadline_utc": "2026-10-25T07:30:00Z",
        "sample_end_utc": "2026-10-25T08:00:00Z",
        "evidence_deadline_utc": "2026-10-25T08:20:00Z",
        "release_utc": "2026-10-25T08:40:00Z",
        "api_workers": 32,
        "mysql_max_connections": 640,
        "sample_max_seconds": 5400,
        "run_budget_cny": 40,
    }


def test_new_round_preserves_templates_and_source_boundaries(plan, originals):
    before = {name: ROUND.digest(data) for name, data in originals.items()}
    files, receipt = ROUND.render(plan, originals, NOW)
    assert before == ROUND.PINS
    assert {name: ROUND.digest(data) for name, data in originals.items()} == before
    assert set(files) == set(ROUND.PINS)
    for name, data in files.items():
        assert ROUND.OLD_SOURCE.encode() not in data
        assert b"2026-10-24" not in data
        assert b"/run/t44-relay852" not in data
        assert b"/run/t44-delivery" not in data
        if name.endswith(".py"):
            ast.parse(data)
    subprocess.run(["bash", "-n"], input=files["ubuntu24-bootstrap.sh"], check=True, capture_output=True)
    assert receipt["generated_files_executed"] is False
    assert receipt["old_templates_modified_or_executed"] is False
    assert receipt["plan"]["minimum_connections"] == 540
    assert receipt["performance_verdict"] is None
    assert "fixture-launcher-cloud.py" in receipt["not_generated"]


def test_runtime_overlay_has_explicit_workers_connections_and_security(plan, originals):
    files, _ = ROUND.render(plan, originals, NOW)
    namespace = {"__name__": "round_overlay_pure_test"}
    exec(compile(files["tls-delivery-extended.py"], "synthetic-derived-tls", "exec"), namespace)
    overlay = namespace["render_overlay"](Path("/run/synthetic-round/app/tls"), "10.1.2.3")
    command = overlay["services"]["api"]["command"]
    assert command[command.index("--workers") + 1] == "32"
    assert "--max-connections=640" in overlay["services"]["mysql"]["command"]
    gateway = overlay["services"]["tls-gateway"]
    assert gateway["read_only"] is True and gateway["cap_drop"] == ["ALL"]
    assert gateway["security_opt"] == ["no-new-privileges:true"]
    assert all(m["read_only"] and m["bind"]["create_host_path"] is False for m in gateway["volumes"])
    assert b'"-verify_ip"' in files["tls-delivery-extended.py"]
    assert b"--require-hashes" in files["api-pypi-delivery.py"]
    assert b"https://mirrors.aliyun.com/pypi/simple/" in files["api-pypi-delivery.py"]
    assert b"clock_anchor" in files["seven-resource-sampler-v3.py"]
    assert b"clock_anchor" in files["host-resource-sampler.py"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("round_id", "../old-round"),
        ("source_sha", "not-a-sha"),
        ("api_workers", True),
        ("api_workers", 65),
        ("mysql_max_connections", 539),
        ("sample_max_seconds", 10801),
        ("run_budget_cny", 101),
        ("issued_utc", "2026-10-25T05:58:59Z"),
        ("operation_deadline_utc", "2026-10-25T05:59:59Z"),
        ("evidence_deadline_utc", "2026-10-25T08:05:00Z"),
        ("release_utc", "2026-10-25T10:00:01Z"),
    ],
)
def test_invalid_or_unbounded_plan_rejected(plan, originals, field, value):
    plan[field] = value
    with pytest.raises(ValueError):
        ROUND.render(plan, originals, NOW)


def test_old_template_byte_change_refused(plan, originals):
    changed = dict(originals)
    changed["ubuntu24-bootstrap.sh"] += b"# changed\n"
    with pytest.raises(ValueError, match="HASH"):
        ROUND.render(plan, changed, NOW)


def test_sixty_four_worker_budget_explicit(plan, originals):
    plan.update(api_workers=64, mysql_max_connections=990)
    with pytest.raises(ValueError, match="CONNECTION"):
        ROUND.render(plan, originals, NOW)
    plan["mysql_max_connections"] = 1280
    _, result = ROUND.render(plan, originals, NOW)
    assert result["plan"]["minimum_connections"] == 1020
    assert result["runtime_values_observed"] is False


def test_private_new_bundle_exclusive_and_complete(tmp_path, plan, originals):
    tmp_path.chmod(0o700)
    files, result = ROUND.render(plan, originals, NOW)
    output = tmp_path / "new-round"
    ROUND.write_bundle(output, files, result)
    assert output.stat().st_mode & 0o777 == 0o700
    for name, data in files.items():
        assert (output / name).read_bytes() == data
        assert (output / name).stat().st_mode & 0o777 == 0o600
    assert json.loads((output / "derivation.json").read_text())["files"] == result["files"]
    with pytest.raises(FileExistsError):
        ROUND.write_bundle(output, files, result)
    assert all((output / name).read_bytes() == data for name, data in files.items())


def test_non_private_parent_refused(tmp_path, plan, originals):
    tmp_path.chmod(0o755)
    files, result = ROUND.render(plan, originals, NOW)
    with pytest.raises(ValueError, match="PRIVATE_OUTPUT"):
        ROUND.write_bundle(tmp_path / "new-round", files, result)


def test_private_plan_rejects_links_public_mode_and_parent(tmp_path):
    tmp_path.chmod(0o700)
    path = tmp_path / "plan.json"
    path.write_text("{}")
    path.chmod(0o600)
    assert ROUND.private_bytes(path) == b"{}"
    link = tmp_path / "plan-link.json"
    link.symlink_to(path)
    with pytest.raises(OSError):
        ROUND.private_bytes(link)
    path.chmod(0o644)
    with pytest.raises(ValueError):
        ROUND.private_bytes(path)
    path.chmod(0o600)
    tmp_path.chmod(0o755)
    with pytest.raises(ValueError, match="PRIVATE_INPUT"):
        ROUND.private_bytes(path)


def test_source_assumptions_preserve_declared_pool_basis():
    data = {name: name.encode() for name in ROUND.ASSUMPTIONS}
    result = ROUND.source_assumptions(Path("/synthetic"), "a" * 40, lambda revision, name: data[name])
    assert result == {name: ROUND.digest(value) for name, value in data.items()}


@pytest.mark.parametrize("changed", ROUND.ASSUMPTIONS)
def test_source_assumptions_reject_changed_pool_settings_or_compose(changed):
    def read(revision, name):
        return b"changed" if revision != ROUND.BASE and name == changed else name.encode()

    with pytest.raises(ValueError, match="ASSUMPTION_CHANGED"):
        ROUND.source_assumptions(Path("/synthetic"), "a" * 40, read)
