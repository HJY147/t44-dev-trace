"""Five local guard groups: real files/FDs, explicit simulated systemd/proc observations."""

import hashlib
import importlib.util
import json
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


M = load(
    ROOT / "deployment/cloud-reuse/resource-operator-completion.py",
    "operator_completion",
)
FROZEN = (
    ROOT / "agents/deployment/resume-20261028/window1030/profile/resource-stream.py"
)
LIB = load(FROZEN, "frozen_resource_fixture")


def fixture(directory, monkeypatch, mirror=False):
    root = Path(directory).resolve()
    app, load_dir = root / "app", root / "mirror"
    selected = load_dir if mirror else app
    selected.mkdir(mode=0o700)
    units = root / "units"
    units.mkdir(mode=0o700)
    monkeypatch.setattr(M, "APP", app)
    monkeypatch.setattr(
        M,
        "SCOPES",
        {
            app: ("app-owned-resource-stream-v1", "t44-resource-"),
            load_dir: ("load-append-resource-mirror-v1", "t44-mirror-"),
        },
    )
    monkeypatch.setattr(M, "UNIT_ROOT", units)
    monkeypatch.setattr(
        M,
        "time",
        SimpleNamespace(
            time=lambda: 1793178000.0, monotonic=time.monotonic, sleep=time.sleep
        ),
    )

    def write(path, raw, mode=0o600):
        path.write_bytes(raw)
        path.chmod(mode)

    controller = FROZEN.read_bytes()
    assert hashlib.sha256(controller).hexdigest() == M.HELPER_SHA
    write(selected / "controller.py", controller)
    auxiliary = "private-handoff.json" if mirror else "nonce"
    write(selected / auxiliary, b"synthetic-not-a-real-secret")
    value = {
        "kind": M.SCOPES[selected][0],
        "source_sha": M.SOURCE,
        "unit": M.SCOPES[selected][1] + "r28example01.service",
        "serve_until": "2026-10-28T10:29:30Z",
        "file_hashes": {
            "controller.py": M.HELPER_SHA,
            auxiliary: hashlib.sha256((selected / auxiliary).read_bytes()).hexdigest(),
        },
    }
    binding = json.dumps(value).encode()
    expected = hashlib.sha256(binding).hexdigest()
    monkeypatch.setattr(M, "APP_BINDING", expected)
    write(selected / "binding.json", binding)
    failure = selected / M.APP_FAILURE
    write(
        failure,
        json.dumps(
            {
                "error_class": "ValueError",
                "reason": M.REASON,
                "partial_state_preserved": True,
            }
        ).encode(),
    )
    # Frozen generator intentionally accepts ASCII systemd paths. The real project path
    # is Unicode, so substitute only its dynamic directory slot in this local fixture.
    ascii_directory = Path("/root/t44-local-resource-fixture")
    unit, argv = LIB.unit_text(ascii_directory, value, expected)
    unit = unit.replace(str(ascii_directory), str(selected))
    argv = [part.replace(str(ascii_directory), str(selected)) for part in argv]
    write(units / value["unit"], unit.encode(), 0o644)
    write(
        selected / "start-plan.json",
        json.dumps(
            {
                "unit": value["unit"],
                "unit_path": str(units / value["unit"]),
                "unit_sha256": hashlib.sha256(unit.encode()).hexdigest(),
                "argv": argv,
                "binding_sha256": expected,
            }
        ).encode(),
    )
    observed = {
        "pid": 12345,
        "start_ticks": 9876,
        "cmdline": b"\0".join(x.encode() for x in argv) + b"\0",
        "unit": value["unit"],
        "cgroup": "/system.slice/" + value["unit"],
    }
    monkeypatch.setattr(M, "probe", lambda *_: observed.copy())
    monkeypatch.setattr(
        M,
        "run",
        lambda *_: json.dumps(
            {
                "action": "status",
                "unit": value["unit"],
                "observed_before_pid": 12345,
                "observed_after_pid": 12345,
            }
        ).encode(),
    )
    return SimpleNamespace(
        directory=selected, binding_sha256=expected, failure=failure
    ), observed


def test_positive_app_and_mirror_write_real_exclusive_late_receipt(monkeypatch):
    for mirror in (False, True):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "tmp/793_deployment_resume"
        ) as directory:
            args, _ = fixture(directory, monkeypatch, mirror)
            before = {p.name: p.read_bytes() for p in args.directory.iterdir()}
            result = M.complete(args)
            saved = json.loads((args.directory / "start-result.json").read_bytes())
            assert result["original_status_rechecked"] is True
            assert saved["late"] is saved["not_original_start_success"] is True
            assert saved["pid"] == 12345 and saved["start_ticks"] == 9876
            assert (
                args.directory / "start-result.json"
            ).stat().st_mode & 0o777 == 0o600
            assert all(
                (args.directory / name).read_bytes() == raw
                for name, raw in before.items()
            )
            with pytest.raises(ValueError, match="ALREADY_PRESENT"):
                M.complete(args)


def test_wrong_failure_external_directory_and_changed_unit_are_rejected(monkeypatch):
    for change in ("failure", "directory", "unit"):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "tmp/793_deployment_resume"
        ) as directory:
            args, _ = fixture(directory, monkeypatch)
            if change == "failure":
                args.failure.write_text(
                    json.dumps(
                        {
                            "error_class": "ValueError",
                            "reason": "OTHER_FAILURE",
                            "partial_state_preserved": True,
                        }
                    )
                )
            elif change == "directory":
                args.directory = args.directory.parent
            else:
                unit = next(M.UNIT_ROOT.iterdir())
                unit.write_text(unit.read_text().replace("User=root", "User=nobody"))
            with pytest.raises(ValueError):
                M.complete(args)
            assert not (args.directory / "start-result.json").exists()


def test_pid_switch_and_five_second_argv_mismatch_refuse_before_write(monkeypatch):
    for change in ("pid", "argv"):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "tmp/793_deployment_resume"
        ) as directory:
            args, snapshot = fixture(directory, monkeypatch)
            calls = []

            def probe(*_, snapshot=snapshot, calls=calls, change=change):
                row = snapshot.copy()
                calls.append(1)
                if change == "pid" and len(calls) > 1:
                    row["pid"] += 1
                if change == "argv":
                    row["cmdline"] = b"wrong\0"
                return row

            monkeypatch.setattr(M, "probe", probe)
            if change == "argv":
                count = iter(range(100))
                monkeypatch.setattr(
                    M,
                    "time",
                    SimpleNamespace(
                        time=lambda: 1793178000.0,
                        monotonic=lambda count=count: next(count),
                        sleep=lambda *_: None,
                    ),
                )
            with pytest.raises(ValueError):
                M.complete(args)
            assert not (args.directory / "start-result.json").exists()


def test_proc_uid_cgroup_and_membership_checks_use_real_fixture_files(monkeypatch):
    original_probe = load(
        ROOT / "deployment/cloud-reuse/resource-operator-completion.py",
        "real_probe_group",
    ).probe
    # Reloaded function has its own module namespace; patch that namespace explicitly.
    globals_ = original_probe.__globals__
    for change in ("ok", "uid", "cgroup", "membership"):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "tmp/793_deployment_resume"
        ) as directory:
            root = Path(directory).resolve()
            process = root / "proc/12345"
            process.mkdir(parents=True)
            unit = "t44-resource-r28example01.service"
            group = "/system.slice/" + unit
            control = root / "cgroup" / group.lstrip("/")
            control.mkdir(parents=True)
            fields = ["S"] + ["0"] * 18 + ["9876"] + ["0"] * 4
            (process / "stat").write_text("12345 (python3) " + " ".join(fields))
            (process / "status").write_text(
                "Uid:\t0\t0\t" + ("501" if change == "uid" else "0") + "\t0\n"
            )
            (process / "cmdline").write_bytes(b"synthetic\0")
            (process / "cgroup").write_text(
                "0::" + ("/wrong" if change == "cgroup" else group) + "\n"
            )
            (control / "cgroup.procs").write_text(
                "999\n" if change == "membership" else "12345\n"
            )
            globals_["PROC"], globals_["CGROUP"] = root / "proc", root / "cgroup"
            globals_["run"] = lambda *_, group=group: (
                "MainPID=12345\nActiveState=active\nSubState=running\nControlGroup="
                + group
                + "\n"
            ).encode()
            actual_stat = Path.stat

            def owner(path, *args, process=process, actual_stat=actual_stat, **kwargs):
                return (
                    SimpleNamespace(st_uid=0)
                    if path == process
                    else actual_stat(path, *args, **kwargs)
                )

            with monkeypatch.context() as context:
                context.setattr(Path, "stat", owner)
                if change == "ok":
                    assert (
                        original_probe(unit, time.monotonic() + 2)["start_ticks"]
                        == 9876
                    )
                else:
                    with pytest.raises(ValueError):
                        original_probe(unit, time.monotonic() + 2)


def test_status_failure_keeps_late_receipt_and_original_failure(monkeypatch):
    with tempfile.TemporaryDirectory(
        dir=ROOT / "tmp/793_deployment_resume"
    ) as directory:
        args, _ = fixture(directory, monkeypatch)
        original = args.failure.read_bytes()
        monkeypatch.setattr(
            M, "run", lambda *_: b'{"action":"status","observed_after_pid":999}'
        )
        with pytest.raises(ValueError, match="ORIGINAL_STATUS_NOT_PROVEN"):
            M.complete(args)
        assert args.failure.read_bytes() == original
        assert json.loads((args.directory / "start-result.json").read_bytes())[
            "not_original_start_success"
        ]
