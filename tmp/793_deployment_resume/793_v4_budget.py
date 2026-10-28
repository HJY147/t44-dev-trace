"""v4 local guards: real files/locks/pipes, explicit simulated Docker and MySQL observations."""

import ast
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "deployment/cloud-reuse/v4"
FIXTURES = ROOT / "tmp/793_deployment_resume"
FIXTURE_SOURCE = "2b79eb7f1becd3c1a63c137bed5a5aef2d16bf1d"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load("v4_budget_guard", V4 / "mysql-budget.py")
D = load("v4_derive_guard", V4 / "derive-profile.py")


@pytest.fixture
def phase():
    with tempfile.TemporaryDirectory(dir=FIXTURES) as folder:
        root = Path(folder).resolve()
        phase = root / "p"
        phase.mkdir(mode=0o700)
        (phase / "receipts").mkdir(mode=0o700)
        value = {
            "generation_kind": B.KIND,
            "phase": "p",
            "api_workers": 16,
            "v4_pool_plan": B.pool_plan("p", 16, 20, 0),
            "source_sha": FIXTURE_SOURCE,
            "stop_utc": "2099-01-01T00:00:00Z",
            "project": "t44-fixture-v4-p",
            "database": "t44_fixture_v4_p",
            "image_ids": {"mysql": "sha256:" + "1" * 64},
            "config_ids": {"mysql": "sha256:" + "2" * 64},
        }
        raw = json.dumps(value).encode()
        (phase / "binding.json").write_bytes(raw)
        (phase / "binding.json").chmod(0o600)
        yield phase, hashlib.sha256(raw).hexdigest(), value


def mysql(value):
    return {
        "role": "mysql",
        "container_id": "a" * 64,
        "image_id": value["image_ids"]["mysql"],
        "restart_count": 0,
        "state": {"Pid": 12345, "StartedAt": "2026-10-28T12:00:00Z", "Running": True},
    }


def sample(value, maximum=384):
    return {
        "max_connections": maximum,
        "database": value["database"],
        "server_uuid": "11111111-2222-3333-4444-555555555555",
        "connection_id": 17,
        "Connections": 100,
        "Threads_connected": 3,
        "Max_used_connections": 30,
        "Uptime": 50,
        "Threads_running": 1,
    }


def mock_mysql(monkeypatch, value, maximum=384):
    monkeypatch.setattr(B, "pid_start_ticks", lambda _: "1234567")
    monkeypatch.setattr(B, "query_once", lambda _: sample(value, maximum))
    return lambda _: mysql(value)


@pytest.mark.parametrize(
    "phase,workers,size,overflow,total",
    [
        ("f", 4, 5, 10, 124),
        ("p", 7, 5, 10, 169),
        ("p", 16, 5, 10, 304),
        ("p", 16, 15, 0, 304),
        ("p", 16, 20, 0, 384),
        ("p", 64, 5, 0, 384),
    ],
)
def test_explicit_capacity_and_all_role_reserve(phase, workers, size, overflow, total):
    plan = B.pool_plan(phase, workers, size, overflow)
    assert plan["required_max_connections"] == total
    assert sum(plan["reserve_breakdown"].values()) == 64
    assert plan["reserve_breakdown"]["one_serial_operation"] == 15
    assert plan["reserve_breakdown"]["health_probes"] == 4
    assert plan["reserve_breakdown"]["persistent_observer"] == 1


@pytest.mark.parametrize(
    "values",
    [
        ("p", 64, 5, 10),
        ("p", 64, 15, 0),
        ("p", 16, 5, 0),
        ("f", 4, 15, 0),
        ("p", 16, None, 0),
        ("p", True, 5, 10),
    ],
)
def test_unreviewed_or_absent_plan_is_not_assumed_safe(values):
    with pytest.raises(ValueError):
        B.pool_plan(*values)


def test_actual_max_is_required_and_same_identity_rechecked(phase, monkeypatch):
    directory, sha, value = phase
    live = mock_mysql(monkeypatch, value, 383)
    with pytest.raises(ValueError, match="INSUFFICIENT"):
        B.probe(directory, sha, value, live)
    assert list((directory / "receipts").iterdir()) == []
    live = mock_mysql(monkeypatch, value)
    result = B.probe(directory, sha, value, live)
    saved = Path(result["budget_receipt"])
    admitted = B.admit(
        directory, sha, value, live, saved, result["budget_receipt_sha256"]
    )
    assert admitted["actual_max_connections"] == 384
    with pytest.raises(ValueError, match="EXPLICIT_CURRENT"):
        B.admit(directory, sha, value, live, None, None)
    changed = copy.deepcopy(value)
    changed["source_sha"] = "c" * 40
    with pytest.raises(ValueError, match="SAME_ACTUAL"):
        B.admit(directory, sha, changed, live, saved, result["budget_receipt_sha256"])
    monkeypatch.setattr(B, "pid_start_ticks", lambda _: "7654321")
    with pytest.raises(ValueError, match="SAME_ACTUAL"):
        B.admit(directory, sha, value, live, saved, result["budget_receipt_sha256"])
    assert saved.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    "change",
    ["restarted", "wrong-image", "pid-during-query", "wrong-db", "bad-counter"],
)
def test_actual_mysql_observation_guards(phase, monkeypatch, change):
    directory, sha, value = phase
    live = mock_mysql(monkeypatch, value)
    observed = mysql(value)
    if change == "restarted":
        observed["restart_count"] = 1
    elif change == "wrong-image":
        observed["image_id"] = "sha256:" + "9" * 64
    elif change == "pid-during-query":
        values = iter(["123", "124"])
        monkeypatch.setattr(B, "pid_start_ticks", lambda _: next(values))
    else:
        row = sample(value)
        row["database" if change == "wrong-db" else "Connections"] = "wrong"
        monkeypatch.setattr(B, "query_once", lambda _: row)
    if change in {"restarted", "wrong-image"}:

        def live(_):
            return observed

    with pytest.raises(ValueError):
        B.probe(directory, sha, value, live)
    assert list((directory / "receipts").iterdir()) == []


def test_mutex_uses_same_file_across_processes_and_releases(phase):
    directory, sha, _ = phase
    program = (
        "import importlib.util,sys;from pathlib import Path;"
        "s=importlib.util.spec_from_file_location('budget',sys.argv[1]);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "ctx=m.operation_lock(Path(sys.argv[2]),sys.argv[3],timeout_seconds=0);"
        "ctx.__enter__();print('acquired');ctx.__exit__(None,None,None)"
    )
    argv = [
        sys.executable,
        "-c",
        program,
        str(V4 / "mysql-budget.py"),
        str(directory),
        sha,
    ]
    with B.operation_lock(directory, sha, timeout_seconds=0) as fd:
        assert not os.get_inheritable(fd)
        denied = subprocess.run(argv, capture_output=True, check=False)
        assert (
            denied.returncode != 0 and b"PHASE_OPERATION_MUTEX_TIMEOUT" in denied.stderr
        )
    accepted = subprocess.run(argv, capture_output=True, check=False)
    assert accepted.returncode == 0 and b"acquired" in accepted.stdout


@pytest.mark.parametrize("change", ["symlink", "hardlink", "mode", "old-kind"])
def test_mutex_does_not_adopt_unsafe_files(phase, change):
    directory, sha, value = phase
    target = directory / "outside"
    target.write_bytes(b"untouched")
    target.chmod(0o600)
    lock = directory / ".v4-operation.lock"
    if change == "symlink":
        lock.symlink_to(target)
    elif change == "hardlink":
        os.link(target, lock)
    elif change == "mode":
        lock.write_bytes(b"")
        lock.chmod(0o644)
    else:
        value["generation_kind"] = "old-v3"
        raw = json.dumps(value).encode()
        (directory / "binding.json").write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest()
    with pytest.raises((OSError, ValueError)):
        with B.operation_lock(directory, sha, timeout_seconds=0):
            pytest.fail("must not enter")
    assert target.read_bytes() == b"untouched"


def app_role(role):
    return {
        "role": role,
        "container_id": {"api": "1", "consumer": "2", "scheduler": "3"}[role] * 64,
        "image_id": "sha256:" + "b" * 64,
        "restart_count": 0,
        "state": {"Pid": 100, "StartedAt": "fixture", "Running": True},
    }


@pytest.mark.parametrize(
    "failure", [None, "consumer-override", "api-missing", "duplicate", "image-change"]
)
def test_actual_role_env_projects_only_capacity_and_preserves_defaults(
    phase, monkeypatch, failure
):
    _, _, value = phase
    calls = {}

    def live(role):
        row = app_role(role)
        calls[role] = calls.get(role, 0) + 1
        if failure == "image-change" and calls[role] > 1:
            row["image_id"] = "sha256:" + "c" * 64
        return row

    def inspect(argv, **_):
        data = [
            "DATABASE_URL=mysql+pymysql://secret:must-not-leak@mysql/db",
            "ANOTHER_SECRET=private",
        ]
        if argv[-1] == "1" * 64 and failure != "api-missing":
            data += ["T44_DB_POOL_SIZE=20", "T44_DB_MAX_OVERFLOW=0"]
            if failure == "duplicate":
                data.append("T44_DB_POOL_SIZE=20")
        if argv[-1] == "2" * 64 and failure == "consumer-override":
            data += ["T44_DB_POOL_SIZE=20", "T44_DB_MAX_OVERFLOW=0"]
        return SimpleNamespace(returncode=0, stdout=json.dumps(data).encode())

    monkeypatch.setattr(B.subprocess, "run", inspect)
    if failure:
        with pytest.raises(ValueError):
            B.verify_runtime_environment(value, live)
    else:
        result = B.verify_runtime_environment(value, live)
        assert result[0]["effective_pool"] == {"size": 20, "max_overflow": 0}
        assert (
            result[1]["effective_pool"]
            == result[2]["effective_pool"]
            == {"size": 5, "max_overflow": 10}
        )
        assert "secret" not in json.dumps(result) and "DATABASE_URL" not in json.dumps(
            result
        )


def generated(folder):
    texts = D.derive_texts(D.parent(), FIXTURE_SOURCE, "2099-01-01T00:00:00Z", 53)
    for name, text in texts.items():
        (folder / name).write_text(text)
    return load("v4_generated_guard", folder / "generation.py"), texts


def test_new_source_hash_chain_and_frozen_originals_remain_distinct():
    legacy = D.parent()
    originals = legacy.checked_templates()
    before = {name: legacy.digest(text.encode()) for name, text in originals.items()}
    texts = D.derive_texts(legacy, FIXTURE_SOURCE, "2099-01-01T00:00:00Z", 53)
    trees = {name: ast.parse(text) for name, text in texts.items()}
    constants = {
        name: {
            n.targets[0].id: ast.literal_eval(n.value)
            for n in tree.body
            if isinstance(n, ast.Assign)
            and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id in {"SOURCE", "BUDGET_SHA", "GENERATOR_SHA", "HARDSTOP"}
        }
        for name, tree in trees.items()
    }
    assert constants["generation.py"]["BUDGET_SHA"] == legacy.digest(
        texts["mysql-budget.py"].encode()
    )
    assert constants["resource-stream.py"]["GENERATOR_SHA"] == legacy.digest(
        texts["generation.py"].encode()
    )
    assert constants["generation.py"]["SOURCE"] == FIXTURE_SOURCE
    assert {
        name: legacy.digest(text.encode())
        for name, text in legacy.checked_templates().items()
    } == before
    with pytest.raises(ValueError, match="OLD_A12"):
        D.derive_texts(
            legacy,
            "a12e9e70b963bacafda3242bb6d82e53ee912ff1",
            "2099-01-01T00:00:00Z",
            53,
        )


@pytest.mark.parametrize(
    "action",
    ["migrate", "idle", "scheduler-token", "scheduler-rotate", "scheduler-start"],
)
def test_no_business_dispatch_without_actual_budget(phase, monkeypatch, action):
    directory, sha, value = phase
    gen, _ = generated(directory.parent)
    events = []

    @contextmanager
    def lock(*_, **__):
        events.append("lock")
        yield

    def refuse(*_, **__):
        events.append("budget")
        raise ValueError("missing actual receipt")

    budget = SimpleNamespace(
        operation_lock=lock,
        admit=refuse,
        verify_runtime_environment=lambda *_: events.append("env"),
    )
    monkeypatch.setattr(gen, "phase_binding", lambda *_: (SimpleNamespace(), value))
    monkeypatch.setattr(gen, "valid_window", lambda *_: None)
    monkeypatch.setattr(gen, "budget_module", lambda *_: budget)
    monkeypatch.setattr(
        gen, "_operate_without_mutex", lambda _: pytest.fail("business dispatched")
    )
    args = SimpleNamespace(
        action=action,
        phase_dir=directory,
        binding_sha256=sha,
        budget_receipt=None,
        budget_receipt_sha256=None,
    )
    with pytest.raises(ValueError, match="missing actual"):
        gen.operate(args)
    assert events == ["lock", "env", "budget"]


@pytest.mark.parametrize("action", ["stop", "status"])
def test_owned_cleanup_and_status_do_not_require_budget_or_mutex(
    phase, monkeypatch, action
):
    directory, _, _ = phase
    gen, _ = generated(directory.parent)
    monkeypatch.setattr(
        gen, "budget_module", lambda *_: pytest.fail("cleanup must not load budget")
    )
    monkeypatch.setattr(gen, "_operate_without_mutex", lambda args: args.action)
    assert gen.operate(SimpleNamespace(action=action)) == action


def test_observer_one_real_pipe_connection_and_own_overhead(phase, monkeypatch):
    directory, sha, value = phase
    live = mock_mysql(monkeypatch, value)
    receipt = B.probe(directory, sha, value, live)
    row = sample(value)
    server = "import sys,json\nrow=json.loads(sys.argv[1])\nfor line in sys.stdin:\n print(json.dumps(row),flush=True)\n row['Connections']+=2\n row['Uptime']+=1\n"
    monkeypatch.setattr(
        B, "mysql_argv", lambda _: [sys.executable, "-u", "-c", server, json.dumps(row)]
    )
    args = SimpleNamespace(
        until_utc=(datetime.now(UTC) + timedelta(seconds=5.2)).isoformat(),
        interval_seconds=1,
        output=directory / "receipts/observer.jsonl",
        budget_receipt=Path(receipt["budget_receipt"]),
        budget_receipt_sha256=receipt["budget_receipt_sha256"],
    )
    result = B.observe(directory, sha, value, live, args)
    raw = args.output.read_bytes()
    assert result["sha256"] == hashlib.sha256(raw).hexdigest()
    rows = [json.loads(line) for line in raw.splitlines()]
    samples = [row for row in rows if row["kind"] == "mysql-observer-sample-v4"]
    assert len(samples) >= 3
    assert {row["observer_connection_id"] for row in samples} == {17}
    assert samples[0]["connections_delta"] is None
    assert all(row["connections_delta"] == 2 for row in samples[1:])
    assert samples[0]["threads_connected_minus_this_observer_only"] == 2
    assert rows[0]["self_persistent_connections"] == 1
    assert rows[-1]["own_client_exit_code"] == 0


def test_observer_sql_and_argv_are_read_only_and_do_not_copy_credentials():
    assert B.SQL.startswith("SELECT ") and B.SQL.count(";") == 1
    assert not any(
        word in B.SQL.upper()
        for word in ("UPDATE ", "ALTER ", "SET ", "RESET ", "DELETE ", "INSERT ")
    )
    argv = " ".join(B.mysql_argv({"container_id": "a" * 64}))
    assert 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD"' in argv and "--skip-reconnect" in argv
    assert "must-not-leak" not in argv


def test_actual_preparation_code_changes_only_P_api_capacity_ENV(phase, monkeypatch):
    directory, _, _ = phase
    gen, _ = generated(directory.parent)
    frozen = subprocess.check_output(
        [
            "git",
            "show",
            "fb0a433494ff8c23124e9901386ee1e991059c45:deployment/cloud-reuse/app-campaign.py",
        ],
        cwd=ROOT,
    )
    assert hashlib.sha256(frozen).hexdigest() == gen.FACTORY_SHA
    factory = directory.parent / "factory-original.py"
    factory.write_bytes(frozen)
    lib = load("v4_original_factory_for_prepare", factory)
    monkeypatch.setattr(lib, "bind_free", lambda *_: None)
    monkeypatch.setattr(lib, "command", lambda *_: b"")
    monkeypatch.setattr(lib, "certificate", lambda *_: {"ca_sha256": "d" * 64})
    original_loader = gen.load
    monkeypatch.setattr(
        gen,
        "load",
        lambda path, expected, name: (
            lib
            if expected == gen.FACTORY_SHA
            else original_loader(path, expected, name)
        ),
    )
    monkeypatch.setattr(
        gen, "os", SimpleNamespace(geteuid=lambda: 0, chown=lambda *_: None)
    )
    monkeypatch.setattr(gen.platform, "system", lambda: "Linux")
    monkeypatch.setattr(gen.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(gen, "valid_window", lambda *_: None)
    roles = ["backend", "web", "python", "node", "nginx", "mysql", "rabbitmq"]
    images = {role: {"alias": "fixture-" + role} for role in roles}
    proofs = {
        role: {"actual_id": "sha256:" + "1" * 64, "config_id": "sha256:" + "2" * 64}
        for role in roles
    }
    monkeypatch.setattr(
        gen,
        "verified_images",
        lambda *_: (
            images,
            proofs,
            {"frozen_file_set_sha256": "3" * 64},
            {"source_archive_sha256": "4" * 64},
            {"fixture_only": True},
        ),
    )
    args = SimpleNamespace(
        factory=factory,
        run_id="v4fixture01",
        p_workers=64,
        p_pool_size=5,
        p_max_overflow=0,
        stop_utc="2099-01-01T00:00:00Z",
        app_ip="172.21.1.1",
        f_tls_port=24443,
        f_http_port=24444,
        p_tls_port=24445,
        p_http_port=24446,
        output=directory.parent / "new-campaign",
        source_manifest_sha256="5" * 64,
        upgrade_binding_sha256="6" * 64,
    )
    # Native project paths contain Chinese characters; only this cloud-path fixture
    # observation is mapped to a literal ASCII cloud path. The frozen guard stays intact.
    regex = gen.re
    monkeypatch.setattr(
        gen,
        "re",
        SimpleNamespace(
            fullmatch=lambda pattern, value: (
                regex.fullmatch(pattern, "/root/t44-v4-fixture")
                if pattern == r"/[A-Za-z0-9_./-]+" and value == str(args.output)
                else regex.fullmatch(pattern, value)
            )
        ),
    )
    result = gen.prepare(args)
    assert result["services_started"] is False
    for role, workers, tls_port, http_port in [
        ("f", 4, 24443, 24444),
        ("p", 64, 24445, 24446),
    ]:
        output = args.output / role
        compose = json.loads((output / "compose.json").read_bytes())
        expected = lib.compose_profile(
            images, output, args.app_ip, tls_port, http_port, workers
        )
        if role == "p":
            expected["services"]["api"]["environment"].update(
                T44_DB_POOL_SIZE="5", T44_DB_MAX_OVERFLOW="0"
            )
        assert compose == expected
        binding = json.loads((output / "binding.json").read_bytes())
        assert binding["generation_kind"] == B.KIND
        assert (
            binding["file_hashes"]["mysql-budget.py"]
            == hashlib.sha256((V4 / "mysql-budget.py").read_bytes()).hexdigest()
        )
        assert binding["v4_pool_plan"]["required_max_connections"] == (
            124 if role == "f" else 384
        )
        assert not any(
            k in compose["services"]["consumer"]["environment"] for k in B.POOL_KEYS
        )
        assert not any(
            k in compose["services"]["scheduler"]["environment"] for k in B.POOL_KEYS
        )
        for name in ("migrate", "admin", "credential-admin"):
            assert not any(
                k in compose["services"][name]["environment"] for k in B.POOL_KEYS
            )


def test_public_delivery_whole_encoded_limits_and_real_exclusive_install(phase):
    directory, _, _ = phase
    gen, texts = generated(directory.parent)
    del gen
    profile = {
        "kind": "explicit-new-source-time-pool-profile-v4",
        "source_sha": FIXTURE_SOURCE,
        "source_file_count": 53,
        "stop_utc": "2099-01-01T00:00:00Z",
        "derived_files": {
            name: {
                "bytes": len(text.encode()),
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
            for name, text in texts.items()
        },
    }
    raw = (json.dumps(profile, sort_keys=True) + "\n").encode()
    path = directory.parent / "profile.json"
    path.write_bytes(raw)
    maker = load("v4_delivery_guard", V4 / "make-delivery.py")
    args = SimpleNamespace(
        profile=path,
        profile_sha256=hashlib.sha256(raw).hexdigest(),
        remote_root="/root/t44-r9/v4-local-guard-only",
        output=directory.parent / "delivery",
    )
    result = maker.make(args)
    actual = directory.parent / "local-installed"
    scripts = []
    for row in result["commands"]:
        source = (args.output / row["name"]).read_text()
        assert row["raw_bytes"] <= 13000 and row["base64_plus_description_256"] < 18000
        code = source.split("\n", 1)[1].rsplit("PY\n", 1)[0]
        # Only the explicitly literal remote ROOT changes for this local installer fixture.
        code = code.replace(repr(args.remote_root), repr(str(actual)))
        scripts.append(code)
        exec(compile(code, row["name"], "exec"), {})
    assert set(p.name for p in (actual / "profile").iterdir()) == maker.ALLOWED
    for name in maker.ALLOWED:
        assert (actual / "profile" / name).read_bytes() == (
            directory.parent / name
        ).read_bytes()
        assert (actual / "profile" / name).stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        exec(compile(scripts[-1], "duplicate-final", "exec"), {})
    piece = actual / "parts/000.bin"
    piece.write_bytes(b"changed")
    with pytest.raises(ValueError, match="EXACT_BYTES_SHA"):
        exec(compile(scripts[-1], "tampered-final", "exec"), {})
