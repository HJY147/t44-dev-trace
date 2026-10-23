"""Deployment environment boundaries only; no independent acceptance cases or product oracles."""

import importlib.util
import json
import os
import stat
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "deployment/acceptance/run.py"
spec = importlib.util.spec_from_file_location("acceptance_environment", SOURCE)
environment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(environment)
control = sys.modules["control"]
COMMIT = "a" * 40


def request(**changes):
    return {"version": 1, "mode": "harness", "product_source_sha": COMMIT, "harness_ref": "b" * 40,
            "harness_path": "tmp/independent/frozen.py", "recipient_certificate_path": "tmp/independent/recipient.pem",
            **changes}


@pytest.mark.parametrize("commit", ["main", "abc123", "a" * 39, "a" * 40 + "\n", "$(id)"])
def test_only_exact_commits(commit):
    with pytest.raises(ValueError):
        environment.validate_request(request(product_source_sha=commit))


@pytest.mark.parametrize("path", ["/tmp/independent/a.py", "tmp/independent/../a.py", "tmp/independentx/a.py",
                                  "tmp/independent/a.py\n", "tmp/independent/a\\b.py"])
def test_entry_cannot_escape_frozen_directory(path):
    with pytest.raises(ValueError):
        environment.harness_path(path)


def test_modes_and_timeout_are_explicit():
    assert environment.validate_request(request())["harness_timeout_seconds"] == 900
    for changes in [{"mode": "environment-check"}, {"harness_timeout_seconds": True},
                    {"harness_timeout_seconds": 1201}, {"request_revision": 0}, {"unexpected": "input"}]:
        with pytest.raises(ValueError):
            environment.validate_request(request(**changes))
    assert environment.validate_request({"version": 1, "mode": "environment-check",
                                          "product_source_sha": COMMIT})["mode"] == "environment-check"


def test_frozen_entry_rejects_symlink(tmp_path):
    root = tmp_path / "harness"
    (root / "tmp/independent").mkdir(parents=True)
    outside = tmp_path / "outside.py"
    outside.write_text("not a harness case")
    (root / "tmp/independent/frozen.py").symlink_to(outside)
    with pytest.raises(ValueError):
        environment.frozen_file(root, "tmp/independent/frozen.py")


def test_archive_whitelist_does_not_collect_workspace_or_credentials(tmp_path):
    for name in ["report.md", "results.json", ".env", "coverage.json", "credentials.json", "private-case.py"]:
        (tmp_path / name).write_text("synthetic sentinel")
    assert {p.name for p in environment.archive_members(tmp_path)} == {"report.md", "results.json"}


def test_archive_rejects_links_and_oversize_output(tmp_path):
    target = tmp_path / "unlisted.txt"
    target.write_text("synthetic")
    selected = tmp_path / "report.md"
    selected.symlink_to(target)
    with pytest.raises(ValueError):
        environment.archive_members(tmp_path)
    selected.unlink()
    with selected.open("wb") as stream:
        stream.truncate(20 * 1024 * 1024 + 1)
    with pytest.raises(ValueError):
        environment.archive_members(tmp_path)


def test_failed_encryption_publishes_no_plaintext(tmp_path):
    folder = tmp_path / "outputs"
    folder.mkdir()
    (folder / "stdout.log").write_text("synthetic private output")
    certificate = tmp_path / "recipient.pem"
    certificate.write_text("public synthetic test marker")
    destination = tmp_path / "tester-output.cms"
    with patch.object(environment.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
        with pytest.raises(RuntimeError):
            environment.encrypt_archive(folder, certificate, destination)
    assert not (tmp_path / "tester-output.tar.gz").exists()
    assert not destination.exists()
    assert (folder / "stdout.log").read_text() == "synthetic private output"


def test_private_state_rejects_symlink_and_uses_0600(tmp_path):
    target = tmp_path / "state.json"
    control.write_private(target, {"synthetic": True})
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    alias = tmp_path / "alias.json"
    alias.symlink_to(target)
    with pytest.raises(ValueError):
        control.private_json(alias)
    with pytest.raises(OSError):
        control.write_private(alias, {})


@pytest.mark.parametrize("statement", ["UPDATE tasks SET name='x'", "SELECT 1; DELETE FROM tasks", "SELECT SLEEP(20)"])
def test_readonly_audit_rejects_write_or_unbounded_request(statement):
    with pytest.raises(ValueError):
        control.audit_statement(statement)


def test_readonly_audit_delivers_password_via_stdin_and_keeps_rows_out_of_ledger(tmp_path):
    controls = control.Controls.__new__(control.Controls)
    controls.runtime = tmp_path
    controls.state = {"env_file": "synthetic.env", "override_file": "synthetic.yaml"}
    controls.values = {}
    controls.event = Mock()
    control.write_private(tmp_path / "audit.json", {"password": "synthetic-not-a-secret"})
    with patch.object(control.ops, "compose", return_value=subprocess.CompletedProcess([], 0, b"private-row\n")) as call:
        assert controls.audit("SHOW CREATE TABLE tasks;") == b"private-row\n"
    assert "synthetic-not-a-secret" not in str(call.call_args.args)
    assert call.call_args.kwargs["input"].startswith(b"synthetic-not-a-secret\n")
    assert "TRANSACTION READ ONLY" in call.call_args.kwargs["input"].decode()
    assert controls.event.call_args.args == ("sql-audit",)
    assert not controls.event.call_args.kwargs


@pytest.mark.parametrize("service,action,lease", [("unrelated", "stop", 30), ("mysql", "rm", 30),
                                                  ("mysql", "pause", 121), ("mysql", "stop", 0)])
def test_fault_allowlist_precedes_docker(service, action, lease):
    controls = control.Controls.__new__(control.Controls)
    with pytest.raises(ValueError):
        controls.fault(service, action, lease)


def test_audit_accepts_bounded_select_and_show():
    assert control.audit_statement("SELECT COUNT(*) FROM tasks;") == "SELECT COUNT(*) FROM tasks"
    assert control.audit_statement("SHOW CREATE TABLE tasks") == "SHOW CREATE TABLE tasks"
    assert not os.getenv("T44_ACCEPTANCE_CONTEXT")  # guards have no tester runtime context


@pytest.mark.parametrize("reachable,networks,expected", [
    (True, {"own_data": True}, False),
    (False, {}, False),
    (False, {"own_data": True, "other": False}, False),
    (False, {"own_data": True}, True),
])
def test_client_network_repair_requires_observed_internal_only_unreachable_listener(reachable, networks, expected):
    assert environment.repairable_client_network({"tcp_listener_reachable": reachable,
                                                  "networks_internal": networks}) is expected


@pytest.mark.parametrize("projects,ttl,name", [([], 300, None), ([0], 300, None), ([1], 59, None),
                                              ([1], 901, None), ([1], True, None), ([1], 300, "../token.json")])
def test_service_credential_limits_are_checked_before_cli(projects, ttl, name):
    controls = control.Controls.__new__(control.Controls)
    with pytest.raises(ValueError):
        controls.service_credential(projects, ttl, name)


def service_controls(tmp_path):
    controls = control.Controls.__new__(control.Controls)
    controls.runtime = tmp_path
    controls.state = {"env_file": "synthetic.env", "override_file": "synthetic.yaml"}
    controls.values = {}
    controls.event = Mock()
    controls.compose = Mock(side_effect=AssertionError("bearer must not enter raw environment logging"))
    return controls


def test_service_bearer_is_real_output_to_private_file_and_not_public_metadata(tmp_path):
    controls = service_controls(tmp_path)
    credential = {"access_token": "synthetic-bearer-" + "x" * 32, "session_id": 11,
                  "expires_at": "2100-01-01T00:00:00Z", "scopes": ["escalation:write"],
                  "project_ids": [2], "ttl_seconds": 300}
    with patch.object(control.ops, "compose", return_value=subprocess.CompletedProcess([], 0, json.dumps(credential).encode())):
        metadata = controls.service_credential([2], 300, "service.json")
    saved = Path(metadata["credential_file"])
    assert json.loads(saved.read_text()) == credential
    assert stat.S_IMODE(saved.stat().st_mode) == 0o600
    assert "access_token" not in metadata
    assert credential["access_token"] not in str(controls.event.call_args)
    controls.compose.assert_not_called()


def test_existing_service_file_is_preserved_without_issuing_new_session(tmp_path):
    controls = service_controls(tmp_path)
    folder = tmp_path / "tester-secrets"
    folder.mkdir(mode=0o700)
    path = folder / "service.json"
    path.write_text("existing synthetic credential")
    with patch.object(control.ops, "compose") as command:
        with pytest.raises(FileExistsError):
            controls.service_credential([2], 300, "service.json")
    assert path.read_text() == "existing synthetic credential"
    command.assert_not_called()


def recovery_controls(tmp_path, *, paused=b"rabbitmq\n", failed_step=None, health="healthy"):
    controls = control.Controls.__new__(control.Controls)
    controls.runtime = tmp_path
    controls.locked = lambda: nullcontext()
    controls.event = Mock()
    control.write_private(tmp_path / "fault-leases.json", {"rabbitmq": 1})

    def compose(*args, **kwargs):
        if args[0] == "ps" and "--format" in args:
            name, output = "unpaused-health", json.dumps({"Service": "rabbitmq", "State": "running", "Health": health}).encode()
        elif args[0] == "ps":
            name, output = "inspect-paused", paused
        elif args[0] == "unpause":
            name, output = "unpause", b"private driver detail"
        else:
            assert "--wait" in args
            name = "infrastructure-ready" if args[-2:] == ("mysql", "rabbitmq") else "application-ready"
            output = b"private driver detail"
        assert kwargs["check"] is False
        return subprocess.CompletedProcess([], 17 if name == failed_step else 0, output)

    controls.compose = Mock(side_effect=compose)
    return controls


def test_recover_waits_for_all_required_commands_and_returns_correlated_receipt(tmp_path):
    controls = recovery_controls(tmp_path)
    receipt = controls.recover()
    assert receipt["recovery_completed"] is True
    assert receipt["restored_services"] == list(control.SERVICES)
    assert receipt["paused_services"] == ["rabbitmq"]
    assert all(step["exit_code"] == 0 for step in receipt["steps"])
    assert receipt["started_at"] and receipt["finished_at"] and receipt["recovery_id"]
    assert controls.event.call_args.kwargs["recovery_receipt"] == receipt
    assert control.private_json(tmp_path / "fault-leases.json") == {}
    assert "private driver detail" not in json.dumps(receipt)


def test_recover_has_distinct_calls_and_does_not_unpause_nonpaused_services(tmp_path):
    controls = recovery_controls(tmp_path, paused=b"")
    first, second = controls.recover(), controls.recover()
    assert first["recovery_id"] != second["recovery_id"]
    assert not any(call.args[0] == "unpause" for call in controls.compose.call_args_list)
    assert next(step for step in first["steps"] if step["name"] == "unpause")["needed"] is False


@pytest.mark.parametrize("failed_step", ["inspect-paused", "unpause", "infrastructure-ready", "application-ready"])
def test_recover_failure_is_false_keeps_leases_and_retains_actual_exit(tmp_path, failed_step):
    controls = recovery_controls(tmp_path, failed_step=failed_step)
    with pytest.raises(control.RecoveryFailure) as caught:
        controls.recover()
    receipt = caught.value.receipt
    assert receipt["recovery_completed"] is False
    assert receipt["error"] == "RECOVERY_FAILED"
    assert receipt["failed_step"] == failed_step
    assert next(step for step in receipt["steps"] if step["name"] == failed_step)["exit_code"] == 17
    assert control.private_json(tmp_path / "fault-leases.json") == {"rabbitmq": 1}
    assert receipt["restored_services"] == (["mysql", "rabbitmq"] if failed_step == "application-ready" else [])
    assert "private driver detail" not in json.dumps(receipt)


def test_recovery_does_not_expand_service_scope_from_inspection(tmp_path):
    controls = recovery_controls(tmp_path, paused=b"unrelated-service\n")
    with pytest.raises(control.RecoveryFailure):
        controls.recover()
    assert len(controls.compose.call_args_list) == 1


def test_lease_watchdog_keeps_existing_no_expiry_behavior(tmp_path):
    controls = recovery_controls(tmp_path)
    control.write_private(tmp_path / "fault-leases.json", {"rabbitmq": float("inf")})
    assert controls.recover(expired_only=True) is None
    controls.compose.assert_not_called()
    controls.event.assert_not_called()


def test_expired_lease_recovery_still_runs_with_the_same_service_scope(tmp_path):
    controls = recovery_controls(tmp_path)
    receipt = controls.recover(expired_only=True)
    assert receipt["recovery_completed"] is True
    assert controls.event.call_args.args == ("lease-recovery",)
    assert receipt["requested_services"] == list(control.SERVICES)


@pytest.mark.parametrize("success", [True, False])
def test_cli_recovery_emits_json_for_success_and_operational_failure(capfd, success):
    receipt = control.recovery_receipt()
    receipt["recovery_completed"] = success
    fake = Mock()
    if success:
        fake.recover.return_value = receipt
    else:
        receipt["error"] = "RECOVERY_FAILED"
        fake.recover.side_effect = control.RecoveryFailure(receipt)
    with patch.object(control, "Controls", return_value=fake), patch.object(sys, "argv", ["control.py", "recover"]):
        code = control.main()
    sys.stdout.flush()
    output = capfd.readouterr()
    assert code == (0 if success else 1)
    assert json.loads(output.out) == receipt
    assert not output.err


def test_cli_recovery_bad_private_state_is_structured_and_redacted(capfd):
    with patch.object(control, "Controls", side_effect=OSError("synthetic-private-value")), patch.object(
            sys, "argv", ["control.py", "recover"]):
        assert control.main() == 1
    output = capfd.readouterr()
    receipt = json.loads(output.out)
    assert receipt["recovery_completed"] is False
    assert receipt["error"] == "RECOVERY_CONTROL_UNAVAILABLE"
    assert "synthetic-private-value" not in output.out + output.err


def test_recovery_waits_for_observed_health_after_successful_unpause(tmp_path):
    controls = recovery_controls(tmp_path)
    original = controls.compose.side_effect
    health_calls = 0

    def compose(*args, **kwargs):
        nonlocal health_calls
        result = original(*args, **kwargs)
        if "--format" in args:
            health_calls += 1
            if health_calls == 1:
                result.stdout = json.dumps({"Service": "rabbitmq", "State": "running", "Health": "unhealthy"}).encode()
        return result

    controls.compose.side_effect = compose
    with patch.object(control.time, "sleep") as sleep:
        receipt = controls.recover()
    assert receipt["recovery_completed"] is True
    observations = [step for step in receipt["steps"] if step["name"] == "unpaused-health"]
    assert [step["observed_health"][0]["health"] for step in observations] == ["unhealthy", "healthy"]
    sleep.assert_called_once_with(1)


def test_recovery_health_timeout_is_false_without_starting_later_phases(tmp_path):
    controls = recovery_controls(tmp_path, health="unhealthy")
    with patch.object(control.time, "monotonic", side_effect=[0, 61]), pytest.raises(control.RecoveryFailure) as caught:
        controls.recover()
    assert caught.value.receipt["failed_step"] == "unpaused-health-timeout"
    assert caught.value.receipt["recovery_completed"] is False
    assert not any(call.args[0] == "up" for call in controls.compose.call_args_list)
    assert control.private_json(tmp_path / "fault-leases.json") == {"rabbitmq": 1}
