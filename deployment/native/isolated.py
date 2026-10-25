"""Exact ade5 native isolation; explicit new inputs, owned lifecycle, fixed hard stop."""

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import signal
import socket
import stat
import subprocess
import sys
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

SOURCE = "ade5e4c1998b4c2f014afde8c011645c6c5a7412"
BROKER_SHA = "a251989f589943bf513fa506015a7bba356fbb167a525a7fd79a29306689fa6b"
PROJECT = Path("/Users/yang/Desktop/nothing/软件开发大作业")
BASE = PROJECT / ".agent-worktrees/.runtime/native-isolated-20261025"
DEPENDENCY = (
    PROJECT
    / ".agent-worktrees/.runtime/native-demo-20261023/dependencies/3b15a7bdf9302475_461a4f3c05a314b2_attempt_c53026c6"
)
LAYOUT = PROJECT / ".agent-worktrees/.runtime/native-mq-20261023/layout.json"
PORTS = {"api": 18096, "amqp": 25696, "epmd": 24396, "distribution": 35696}
CLI_PORTS = (45696, 45705)
STOP = datetime(2026, 10, 25, 8, 47, tzinfo=UTC).timestamp()
HARD_STOP = datetime(2026, 10, 25, 8, 50, tzinfo=UTC).timestamp()
SUBSET = ("backend/t44", "backend/requirements.lock", "backend/pyproject.toml")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stamp():
    return datetime.now(UTC).isoformat()


def private(path, directory=False):
    info = path.lstat()
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if not kind(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("PRIVATE_PATH_REQUIRED")
    if path.resolve() != path.absolute():
        raise ValueError("CANONICAL_PATH_REQUIRED")


def write(path, data):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())


def save(path, value, replace=False):
    data = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    if not replace:
        write(path, data)
        return
    if path.exists():
        private(path)
    temporary = path.with_name(path.name + "." + uuid4().hex)
    write(temporary, data)
    os.replace(temporary, path)


def read(path):
    private(path)
    return json.loads(path.read_text())


def admitted(now=None):
    if (time.time() if now is None else now) >= STOP - 120:
        raise ValueError("NEW_START_WINDOW_CLOSED")


def git(repository, *args):
    return subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True, timeout=20).stdout


def ports_free(ports):
    for port in ports:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", port))


def derive_broker(data):
    if sha(data) != BROKER_SHA:
        raise ValueError("BROKER_TEMPLATE_DIFFERS")
    text, changes = data.decode(), []
    for old, new, count in (
        (
            'PORTS = {"amqp": 25674, "epmd": 24369, "distribution": 35674}',
            'PORTS = {"amqp": 25696, "epmd": 24396, "distribution": 35696}',
            1,
        ),
        ("CLI_PORTS = (45674, 45683)", "CLI_PORTS = (45696, 45705)", 1),
        (
            ".agent-worktrees/.runtime/t44-native-broker",
            ".agent-worktrees/.runtime/native-isolated-20261025/brokers",
            2,
        ),
    ):
        if text.count(old) != count:
            raise ValueError("BROKER_PATCH_POSITION_DIFFERS")
        text = text.replace(old, new)
        changes.append({"old": old, "new": new, "occurrences": count})
    return text.encode(), changes


def environment(extra=None):
    value = {key: os.environ[key] for key in ("HOME", "home", "CODEX_HOME") if key in os.environ}
    value.update(
        PATH="/usr/bin:/bin:/usr/sbin:/sbin",
        LANG="en_US.UTF-8",
        LC_ALL="en_US.UTF-8",
        PYTHONUNBUFFERED="1",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
    )
    value.update(extra or {})
    return value


def command(run, argv, *, cwd=None, timeout=30, env_extra=None):
    tag = uuid4().hex
    result = subprocess.run(
        list(map(str, argv)),
        cwd=cwd or run,
        env=environment(env_extra),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    for suffix, data in (("stdout", result.stdout), ("stderr", result.stderr)):
        write(run / "logs" / (tag + "." + suffix), data)
    save(
        run / "receipts" / (tag + ".json"),
        {
            "at_utc": stamp(),
            "argv": list(map(str, argv)),
            "exit_code": result.returncode,
            "stdout_sha256": sha(result.stdout),
            "stderr_sha256": sha(result.stderr),
        },
    )
    if result.returncode:
        raise RuntimeError("LOCAL_COMMAND_FAILED")
    return result.stdout


def broker_module(run):
    manifest = read(run / "manifest.json")
    path = run / "broker-controller.py"
    private(path)
    if sha(path.read_bytes()) != manifest["broker_controller_sha256"]:
        raise ValueError("BROKER_CONTROLLER_CHANGED")
    spec = importlib.util.spec_from_file_location("isolated_native_broker", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(run):
    run = run.absolute()
    private(run, True)
    if run.parent != BASE / "runs" or not re.fullmatch(r"[a-z0-9_]{8,48}", run.name):
        raise ValueError("OWNED_RUN_REQUIRED")
    manifest = read(run / "manifest.json")
    if manifest["source_commit"] != SOURCE or manifest["ports"] != PORTS:
        raise ValueError("EXACT_BASELINE_REQUIRED")
    if sha((run / "controller.py").read_bytes()) != manifest["controller_sha256"]:
        raise ValueError("CONTROLLER_CHANGED")
    for name, expected in manifest["source_files"].items():
        path = run / "source" / name
        if path.is_symlink() or sha(path.read_bytes()) != expected:
            raise ValueError("SOURCE_CHANGED")
    return manifest


def receipt(run, action, **fields):
    value = {"at_utc": stamp(), "receipt_id": uuid4().hex, "action": action, **fields}
    save(run / "receipts" / (value["receipt_id"] + ".json"), value)
    return value


def certificates(run, openssl):
    tls = run / "tls"
    write(tls / "openssl.cnf", b"[req]\ndistinguished_name=dn\n[dn]\n")

    def tls_command(argv):
        return command(run, argv, env_extra={"OPENSSL_CONF": str(tls / "openssl.cnf")})

    tls_command(
        [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "2",
            "-keyout",
            tls / "ca.key",
            "-out",
            tls / "ca.pem",
            "-subj",
            "/CN=T44 isolated native CA",
            "-addext",
            "basicConstraints=critical,CA:TRUE",
            "-addext",
            "keyUsage=critical,keyCertSign,cRLSign",
        ],
    )
    tls_command(
        [
            openssl,
            "req",
            "-new",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            tls / "server.key",
            "-out",
            tls / "server.csr",
            "-subj",
            "/CN=localhost",
        ],
    )
    write(
        tls / "server.ext",
        b"basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:localhost,IP:127.0.0.1\n",
    )
    tls_command(
        [
            openssl,
            "x509",
            "-req",
            "-in",
            tls / "server.csr",
            "-CA",
            tls / "ca.pem",
            "-CAkey",
            tls / "ca.key",
            "-CAcreateserial",
            "-days",
            "2",
            "-extfile",
            tls / "server.ext",
            "-out",
            tls / "server.pem",
        ],
    )
    tls_command(
        [
            openssl,
            "verify",
            "-CAfile",
            tls / "ca.pem",
            "-purpose",
            "sslserver",
            "-verify_hostname",
            "localhost",
            "-verify_ip",
            "127.0.0.1",
            tls / "server.pem",
        ],
    )
    key = tls_command([openssl, "pkey", "-in", tls / "server.key", "-pubout"])
    cert = tls_command([openssl, "x509", "-in", tls / "server.pem", "-pubkey", "-noout"])
    if key != cert:
        raise ValueError("TLS_KEYPAIR_DIFFERS")
    for path in tls.iterdir():
        private(path)


def prepare(repository):
    admitted()
    ports_free([*PORTS.values(), *range(CLI_PORTS[0], CLI_PORTS[1] + 1)])
    os.umask(0o077)
    BASE.mkdir(mode=0o700, exist_ok=True)
    private(BASE, True)
    for name in ("runs", "brokers"):
        (BASE / name).mkdir(mode=0o700, exist_ok=True)
        private(BASE / name, True)
    run = BASE / "runs" / ("isolated_20261025_" + uuid4().hex[:16])
    run.mkdir(mode=0o700)
    for name in ("logs", "state", "receipts", "tls", "source", "secrets"):
        (run / name).mkdir(mode=0o700)
    write(run / "state/control.lock", b"")
    raw = git(repository, "archive", SOURCE, *SUBSET)
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for item in archive:
            path = Path(item.name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or not any(item.name == p or item.name.startswith(p + "/") for p in SUBSET)
            ):
                if item.isdir() and item.name == "backend":
                    continue
                raise ValueError("UNEXPECTED_SOURCE_ARCHIVE_ENTRY")
            if item.isdir():
                (run / "source" / path).mkdir(mode=0o700, parents=True, exist_ok=True)
            elif item.isfile():
                data = archive.extractfile(item).read()
                target = run / "source" / path
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                write(target, data)
                files[item.name] = sha(data)
            else:
                raise ValueError("NONREGULAR_SOURCE_ENTRY")
    ready = read(DEPENDENCY / "ready.json")
    if ready["backend_lock_sha256"] != files["backend/requirements.lock"]:
        raise ValueError("EXISTING_DEPENDENCY_LOCK_DIFFERS")
    python = DEPENDENCY / "venv/bin/python"
    inventory = command(
        run,
        [
            python,
            "-c",
            "import importlib.metadata as m,json,sys;print(json.dumps({'python':sys.version,'executable':sys.executable,'prefix':sys.prefix,'distributions':sorted((d.metadata['Name'],d.version) for d in m.distributions())}))",
        ],
    )
    command(run, ["/Users/yang/Library/Application Support/MinerU/tools/uv", "pip", "check", "--python", python])
    broker_raw = git(repository, "show", SOURCE + ":deployment/native/runtime.py")
    derived, changes = derive_broker(broker_raw)
    write(run / "broker-controller.py", derived)
    write(run / "controller.py", Path(__file__).read_bytes())
    layout = json.loads(LAYOUT.read_text())
    certificates(run, Path(layout["openssl_prefix"]) / "bin/openssl")
    # Publish identity before preparing the broker, whose loader needs this hash.
    manifest = {
        "source_commit": SOURCE,
        "repository_tree_oid": git(repository, "rev-parse", SOURCE + "^{tree}").decode().strip(),
        "backend_tree_oid": git(repository, "rev-parse", SOURCE + ":backend/t44").decode().strip(),
        "source_subset": list(SUBSET),
        "source_files": files,
        "source_archive_sha256": sha(raw),
        "created_at_utc": stamp(),
        "controller_sha256": sha(Path(__file__).read_bytes()),
        "broker_template_sha256": BROKER_SHA,
        "broker_controller_sha256": sha(derived),
        "broker_changes": changes,
        "dependency_lock_sha256": files["backend/requirements.lock"],
        "dependency_reused": str(DEPENDENCY),
        "python": str(python),
        "python_executable_realpath": str(python.resolve()),
        "python_executable_sha256": sha(python.resolve().read_bytes()),
        "python_inventory": json.loads(inventory),
        "wheel_hashes_revalidated_this_stage": False,
        "ports": PORTS,
        "cli_ports": CLI_PORTS,
        "planned_stop_utc": "2026-10-25T08:47:00Z",
        "hard_stop_utc": "2026-10-25T08:50:00Z",
        "ca_sha256": sha((run / "tls/ca.pem").read_bytes()),
        "server_certificate_sha256": sha((run / "tls/server.pem").read_bytes()),
        "native_build": "selected exact baseline Python runtime source;no Docker image",
        "cloud_performance_verdict": None,
    }
    save(run / "manifest.json", manifest)
    module = broker_module(run)
    broker = module.NativeBroker.prepare(PROJECT, LAYOUT, run.name)
    save(run / "broker-binding.json", {"run_dir": str(broker.run)})
    return receipt(
        run,
        "prepare",
        success=True,
        run_dir=str(run),
        source_commit=SOURCE,
        amqp_credentials_path=str(broker.credentials),
        manifest=str(run / "manifest.json"),
    )


def owned(run, role):
    path = run / "state" / (role + ".json")
    if not path.exists():
        return None, None
    record = read(path)
    module = broker_module(run)
    actual = module.process_identity(record["pid"])
    if actual is not None and not module.same_owner(record, actual):
        raise ValueError("PROCESS_IDENTITY_CHANGED")
    return record, actual


def spawn(run, role, argv, env):
    _record, actual = owned(run, role)
    if actual is not None:
        raise ValueError("ROLE_ALREADY_RUNNING")
    handles = []
    for suffix in ("stdout", "stderr"):
        path = run / "logs" / (role + "-" + uuid4().hex + "." + suffix)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        handles.append(os.fdopen(fd, "wb"))
    try:
        child = subprocess.Popen(
            list(map(str, argv)),
            cwd=run / "source",
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=handles[0],
            stderr=handles[1],
            start_new_session=True,
        )
    finally:
        for handle in handles:
            handle.close()
    time.sleep(0.15)
    identity = broker_module(run).process_identity(child.pid)
    if identity is None or identity["uid"] != os.getuid() or identity["pid"] != identity["pgid"]:
        raise RuntimeError("SPAWN_IDENTITY_UNCONFIRMED")
    record = {k: v for k, v in identity.items() if k != "command"}
    record.update(role=role, argv=list(map(str, argv)), at_utc=stamp())
    save(run / "state" / (role + "-" + uuid4().hex + ".history.json"), record)
    save(run / "state" / (role + ".json"), record, replace=True)
    return record


def broker_for(run):
    return broker_module(run).NativeBroker(PROJECT, Path(read(run / "broker-binding.json")["run_dir"]))


def stop_app(run, role):
    record, actual = owned(run, role)
    if actual is None:
        return {"role": role, "absent": True, "success": True}
    os.killpg(record["pgid"], signal.SIGTERM)
    end = time.monotonic() + 8
    while time.monotonic() < end and owned(run, role)[1] is not None:
        time.sleep(0.1)
    _record, actual = owned(run, role)
    forced = actual is not None
    if forced:
        os.killpg(record["pgid"], signal.SIGKILL)
        time.sleep(0.2)
    return {"role": role, "forced": forced, "success": owned(run, role)[1] is None}


def stop(run):
    steps = [stop_app(run, role) for role in ("scheduler", "consumer", "api")]
    broker = broker_for(run)
    try:
        value = broker.stop()
        steps.append({"role": "broker", "success": value["success"], "receipt_id": value["receipt_id"]})
    except (RuntimeError, ValueError, OSError):
        steps.append({"role": "broker", "success": False, "error": "NORMAL_STOP_FAILED"})
    for role in ("rabbit", "epmd"):
        record, actual = broker.owner(role)
        if actual is not None:
            if role == "epmd":
                if broker.owner("rabbit")[1] is not None:
                    steps.append({"role": role, "success": False, "error": "RABBIT_STILL_PRESENT"})
                    continue
                names = subprocess.run(
                    [str(Path(broker.layout["prefix"]) / "bin/epmd"), "-port", str(PORTS["epmd"]), "-names"],
                    env=broker.env(),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if names.returncode or any(line.startswith("name ") for line in names.stdout.splitlines()):
                    steps.append({"role": role, "success": False, "error": "EPMD_NOT_PROVEN_EMPTY"})
                    continue
            broker.signal_owned(role)
            if not broker.wait_stopped(role, timeout=5):
                record, actual = broker.owner(role)
                if actual is not None:
                    os.killpg(record["pgid"], signal.SIGKILL)
                    broker.wait_stopped(role, timeout=3)
        steps.append({"role": role, "success": broker.owner(role)[1] is None})
    return receipt(run, "stop", success=all(v["success"] for v in steps), steps=steps)


def collect_sample(run):
    sample = {"at_utc": stamp(), "monotonic_ns": time.monotonic_ns(), "realtime_ns": time.time_ns(), "roles": {}}
    broker = broker_for(run)
    for role in ("api", "consumer", "scheduler", "rabbit", "epmd"):
        _record, actual = broker.owner(role) if role in ("rabbit", "epmd") else owned(run, role)
        if actual:
            raw = subprocess.run(
                ["/bin/ps", "-p", str(actual["pid"]), "-o", "pid=,uid=,%cpu=,rss=,etime="],
                capture_output=True,
                text=True,
                timeout=3,
            )
            sample["roles"][role] = {"pid": actual["pid"], "ps": raw.stdout.strip(), "exit_code": raw.returncode}
    return sample


def guardian(run):
    # Independent UTC+monotonic deadline; wall-clock rollback cannot extend it.
    stop_mono = time.monotonic() + max(0, STOP - time.time())
    path = run / "state" / ("resources-" + uuid4().hex + ".ndjson")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    requested = []

    def request(signum, _frame):
        requested.append(signum)

    signal.signal(signal.SIGTERM, request)
    signal.signal(signal.SIGINT, request)
    failed = False
    try:
        with os.fdopen(descriptor, "w") as output:
            while not requested and time.monotonic() < stop_mono and time.time() < STOP:
                output.write(json.dumps(collect_sample(run)) + "\n")
                output.flush()
                for _ in range(10):
                    if requested or time.monotonic() >= stop_mono or time.time() >= STOP:
                        break
                    time.sleep(1)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        failed = True
        receipt(run, "resource_sampling", success=False, error="OWNED_SAMPLING_FAILED")
    finally:
        cleanup = stop(run)
    return receipt(run, "guardian", success=not failed and cleanup["success"], cleanup_receipt=cleanup["receipt_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "broker-start", "guardian", "stop"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == "prepare":
            result = prepare(args.repository)
        else:
            run = args.run_dir
            load(run)
            if args.command == "guardian":
                result = guardian(run)
            elif args.command == "stop":
                result = stop(run)
            else:
                admitted()
                record = spawn(
                    run,
                    "guardian",
                    [sys.executable, run / "controller.py", "guardian", "--run-dir", run],
                    environment(),
                )
                started = broker_for(run).start()
                result = receipt(
                    run,
                    "broker_start",
                    success=started["success"],
                    guardian_pid=record["pid"],
                    broker_receipt=started["receipt_id"],
                )
        print(json.dumps(result))
        return 0 if result["success"] else 1
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyError):
        print(json.dumps({"success": False, "error": "ISOLATED_NATIVE_STEP_FAILED", "at_utc": stamp()}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
