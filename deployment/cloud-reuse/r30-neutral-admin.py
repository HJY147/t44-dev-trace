"""Fixed R30 administrative children under the actual phase budget lock; no cloud lifecycle."""

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import secrets
import stat
import subprocess
import time
from pathlib import Path, PurePosixPath

SOURCE = "0bffe0c535e5897890aebf30879fdd3839dc52d6"
KIND = "r30-official-backend-production-entry-window-v1"
BUDGET_SHA = "9e98632fa1885bf4327b04a95daeba5cee4ad909b536e91ac8b11a1e58488a61"
ADAPTER_SHA = "7efee30a2e3ef9552c9e2a5b321cebe4ddbd3eb3d8e652484017fd45e5f8d70f"
CONFIG = "sha256:8e3e2a9d1f2d4706072eb0502b041d3db49d32b7a2fc48ac6b39fc2162336845"
MODES = ("init-accounts", "seed", "counts", "service")
ACCOUNT_ROLES = ("manager", "developer", "reviewer")
DOCKER = ["docker", "--context", "default"]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def raw(path, *, private=False, directory=False):
    s = path.lstat()
    if (not path.is_absolute() or path.resolve() != path or s.st_uid != os.geteuid()
            or not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))
            or (not directory and s.st_nlink != 1)
            or (private and stat.S_IMODE(s.st_mode) != (0o700 if directory else 0o600))):
        raise ValueError("CANONICAL_OWNED_REGULAR_OR_PRIVATE_OBJECT_REQUIRED")
    if directory:
        return None
    if s.st_size > 4 * 1024 * 1024:
        raise ValueError("ADMIN_INPUT_SIZE_BOUND")
    return path.read_bytes()


def pinned(path, expected, *, private=False):
    value = raw(path, private=private)
    if not re.fullmatch(r"[0-9a-f]{64}", expected or "") or digest(value) != expected:
        raise ValueError("ROOT_PINNED_INPUT_HASH_REQUIRED")
    return value


def write(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(value)
        f.flush()
        os.fsync(f.fileno())


def save(path, value):
    write(path, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode())


def module(path, expected):
    pinned(path, expected)
    spec = importlib.util.spec_from_file_location("r30_admin_" + path.stem.replace("-", "_"), path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def require_host():
    if os.geteuid() != 0 or platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        raise ValueError("ROOT_LINUX_AMD64_ADMIN_HOST_REQUIRED")


def container_owner(path):
    os.chown(path, 10001, 10001)


def check_scope(profile, value, plan, intent, binding_hash, probe_hash):
    run = profile["run_id"]
    phase = value["phase"]
    if (not re.fullmatch(r"r30[a-z0-9]{5,12}", run) or phase not in {"f", "p"}
            or value["generation_kind"] != KIND or value["source_sha"] != SOURCE
            or value["project"] != "t44-cloud-" + run + "-" + phase
            or value["database"] != "t44c_" + run + "_" + phase
            or value["stop_utc"] != profile["stop_utc"]
            or value["config_ids"]["backend"] != CONFIG):
        raise ValueError("EXACT_R30_SOURCE_RUN_PROJECT_DATABASE_STOP_REQUIRED")
    target = plan["target"]
    if (plan.get("schema") != "t44-neutral-r30-plan-v1" or plan.get("synthetic") is not True
            or plan.get("root_admit_preparation") is not True or plan.get("benchmark_grant_allow") is not False
            or plan["run_id"] != run or plan["source"]["git_commit"] != SOURCE or plan["namespace"] != value["project"]
            or target["compose_project"] != value["project"] or target["database"] != value["database"]
            or target["binding_sha256"] != binding_hash or target["mysql_host"] != "mysql"
            or target["mysql_port"] != 3306 or target["mysql_user"] != value["database"] + "_app"
            or plan["window"]["stop_utc"] != value["stop_utc"]
            or plan["budget"]["helper_sha256"] != BUDGET_SHA
            or plan["budget"]["actual_admission_receipt_sha256"] != probe_hash
            or intent["namespace"] != value["project"] or intent["database"] != value["database"]
            or intent["run_id"] != plan["run_id"]):
        raise ValueError("EXACT_ORIGINAL_PLAN_INTENT_BINDING_AND_PROBE_REQUIRED")


def checked(args):
    if args.mode not in MODES:
        raise ValueError("FIXED_ADMIN_MODE_ONLY")
    profile = json.loads(pinned(args.profile_json, args.profile_sha256))
    if (profile["kind"] != KIND or profile["source_sha"] != SOURCE
            or profile["derived_budget_sha256"] != BUDGET_SHA
            or profile["derived_files"]["mysql-budget.py"]["sha256"] != BUDGET_SHA
            or profile["derived_files"]["r30-window.py"]["sha256"] != ADAPTER_SHA):
        raise ValueError("REVIEWED_R30_PROFILE_GEN_AND_BUDGET_PINS_REQUIRED")
    generation = module(args.phase_dir / "controller.py", profile["derived_files"]["generation.py"]["sha256"])
    if generation.BUDGET_SHA != BUDGET_SHA or generation.R30_ADAPTER_SHA != ADAPTER_SHA:
        raise ValueError("EXACT_REVIEWED_GEN_HELPER_PINS_REQUIRED")
    lib, value = generation.phase_binding(args.phase_dir, args.binding_sha256)
    budget = generation.budget_module(args.phase_dir)
    if budget.KIND != KIND or digest(raw(args.phase_dir / "mysql-budget.py")) != BUDGET_SHA:
        raise ValueError("EXACT_9E_BUDGET_REQUIRED")
    generation.valid_window(lib, value["stop_utc"], 600)
    inputs = {"plan.json": raw(args.plan, private=True), "intent.json": raw(args.intent, private=True),
              "binding.json": pinned(args.phase_dir / "binding.json", args.binding_sha256, private=True),
              "budget.PUBLIC.json": pinned(args.budget_receipt, args.budget_receipt_sha256, private=True),
              "backend-import-receipt.json": raw(args.import_receipt, private=True)}
    plan, intent = json.loads(inputs["plan.json"]), json.loads(inputs["intent.json"])
    check_scope(profile, value, plan, intent, args.binding_sha256, args.budget_receipt_sha256)
    if digest(inputs["backend-import-receipt.json"]) != plan["source"]["actual_loaded_receipt_sha256"]:
        raise ValueError("ORIGINAL_IMPORT_RECEIPT_BYTES_REQUIRED")
    composition = json.loads(raw(args.phase_dir / "compose.json", private=True))
    service = composition["services"]["credential-admin"]
    if (service["image"] != value["images"]["backend"]["alias"]
            or set(service["networks"]) != {"data"} or service["pull_policy"] != "never"):
        raise ValueError("ORIGINAL_CREDENTIAL_ADMIN_DATA_ONLY_IMAGE_REQUIRED")
    return generation, lib, budget, value, inputs


def producer_files(args):
    manifest_raw = pinned(args.code_manifest, args.code_manifest_sha256)
    table = json.loads(manifest_raw)["files"]
    if isinstance(table, list):
        records = table
    elif isinstance(table, dict):
        records = [{"path": key, **value} for key, value in table.items()]
    else:
        raise ValueError("EXPLICIT_PRODUCER_FILE_TABLE_REQUIRED")
    raw(args.code_dir, directory=True)
    contents = {}
    for record in records:
        name = record["path"]
        p = PurePosixPath(name)
        if (not name or p.is_absolute() or ".." in p.parts or str(p) != name or "\\" in name
                or p.suffix not in {".py", ".json"} or name in contents):
            raise ValueError("UNIQUE_SAFE_PRODUCER_CODE_PATH_REQUIRED")
        content = raw(args.code_dir / name)
        if len(content) != record["bytes"] or digest(content) != record["sha256"]:
            raise ValueError("PRODUCER_CODE_BYTES_OR_HASH_CHANGED")
        contents[name] = content
    actual_py = set()
    for path in args.code_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError("PRODUCER_LINK_REFUSED")
        if path.is_file() and path.suffix == ".py":
            actual_py.add(path.relative_to(args.code_dir).as_posix())
    if ("admin.py" not in contents or actual_py != {n for n in contents if n.endswith(".py")}
            or sum(map(len, contents.values())) > 10 * 1024 * 1024):
        raise ValueError("COMPLETE_ACTUAL_PYTHON_PRODUCER_SET_REQUIRED")
    contents["producer-manifest.PUBLIC.json"] = manifest_raw
    return contents


def stage(args, inputs, code):
    raw(args.output_dir.parent, private=True, directory=True)
    args.output_dir.mkdir(mode=0o700)
    for name in ("inputs", "output", "logs", "code"):
        path = args.output_dir / name
        path.mkdir(mode=0o755 if name == "code" else 0o700)
        if name == "code":
            path.chmod(0o755)
        if name in {"inputs", "output"}:
            container_owner(path)
    for name, data in inputs.items():
        path = args.output_dir / "inputs" / name
        write(path, data)
        container_owner(path)
    for name, data in code.items():
        path = args.output_dir / "code" / name
        path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        write(path, data)
        path.chmod(0o644)
    for path in (args.output_dir / "code").rglob("*"):
        if path.is_dir():
            path.chmod(0o755)


def docker_prefix(args, value, name):
    return [*DOCKER, "compose", "--env-file", str(args.phase_dir / "application.env"),
            "--file", str(args.phase_dir / "compose.json"), "--project-name", value["project"],
            "--profile", "operations", "run", "--rm", "--no-deps", "-T", "--pull", "never",
            "--user", "10001:10001", "--name", name,
            "--label", "io.t44.r30.admin.owner=" + value["project"], "--entrypoint", "python",
            "--volume", str(args.output_dir / "code") + ":/neutral-code:ro",
            "--volume", str(args.output_dir / "inputs") + ":/neutral-input:ro",
            "--volume", str(args.output_dir / "output") + ":/neutral-output",
            "credential-admin"]


def owned_finished(lib, value, name, *, stop=False):
    def inspect():
        try:
            return json.loads(lib.command([*DOCKER, "inspect", name]))[0]
        except subprocess.CalledProcessError as error:
            if b"no such" in (error.stderr or b"").lower():
                return None
            raise

    row = inspect()
    if row is None:
        return
    labels = row["Config"]["Labels"]
    if (row["Image"] not in {value["image_ids"]["backend"], value["config_ids"]["backend"]}
            or labels.get("com.docker.compose.project") != value["project"]
            or labels.get("com.docker.compose.service") != "credential-admin"
            or labels.get("io.t44.r30.admin.owner") != value["project"]):
        raise ValueError("OWNED_ADMIN_CHILD_IDENTITY_REQUIRED")
    if row["State"]["Running"] and stop:
        lib.command([*DOCKER, "stop", "--time", "15", name])
        row = inspect()
    if row is not None and row["State"]["Running"]:
        raise ValueError("ADMIN_CHILD_EXIT_NOT_PROVEN")


def run_child(argv, stdout, stderr, stdin, timeout, env, cleanup):
    with stdout.open("xb") as out, stderr.open("xb") as err:
        stdout.chmod(0o600)
        stderr.chmod(0o600)
        process = subprocess.Popen(argv, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                   stdout=out, stderr=err, env=env)
        try:
            process.communicate(input=stdin, timeout=timeout)
        except BaseException:
            try:
                cleanup(stop=True)  # Still inside the actual phase operation_lock.
            finally:
                try:
                    process.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
            raise
        cleanup(stop=False)
        return process.returncode


def accounts_for_init(args):
    value = json.loads(raw(args.accounts, private=True))
    if set(value) != set(ACCOUNT_ROLES):
        raise ValueError("EXACT_THREE_SYNTHETIC_ACCOUNTS_REQUIRED")
    for role in ACCOUNT_ROLES:
        account = value[role]
        if account["username"] != "synthetic-" + role or account["user_id"] is not None:
            raise ValueError("FRESH_FIXED_USERNAME_WITHOUT_PRIOR_USER_ID_REQUIRED")
        if account["password"] is None:
            account["password"] = secrets.token_urlsafe(32)
        password = account["password"]
        if not isinstance(password, str) or not 1 <= len(password) <= 128 or "\n" in password or "\r" in password:
            raise ValueError("PRIVATE_SINGLE_LINE_PASSWORD_REQUIRED")
    return value


def private_result(path):
    info = path.lstat()
    if (path.resolve() != path or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or info.st_uid != 10001 or stat.S_IMODE(info.st_mode) != 0o600):
        raise ValueError("ACTUAL_PRIVATE_ADMIN_RESULT_REQUIRED")


def run_admin(args, *, runner=None):
    require_host()
    generation, lib, budget, value, inputs = checked(args)
    code = producer_files(args)
    accounts = accounts_for_init(args) if args.mode == "init-accounts" else None
    stage(args, inputs, code)
    runner = run_child if runner is None else runner
    with budget.operation_lock(args.phase_dir, args.binding_sha256):
        # Recheck immutable raw identity inside the lock, then actually re-measure/admit.
        lib2, current = generation.phase_binding(args.phase_dir, args.binding_sha256)
        if current != value:
            raise ValueError("PHASE_CHANGED_DURING_ADMIN_LOCK_ENTRY")
        generation.valid_window(lib2, value["stop_utc"], 600)
        lib.command(["systemctl", "is-active", "--quiet", value["timer_unit"]])
        actual_backend = lib.command([*DOCKER, "image", "inspect", "--format", "{{.Id}}", value["images"]["backend"]["alias"]]).decode().strip()
        if actual_backend not in {value["image_ids"]["backend"], value["config_ids"]["backend"]}:
            raise ValueError("BOUND_BACKEND_IMAGE_ALIAS_CHANGED")
        budget.verify_runtime_environment(value, lambda role: generation.live(lib, value, role))
        admitted = budget.admit(args.phase_dir, args.binding_sha256, value,
                                lambda role: generation.live(lib, value, role),
                                args.budget_receipt, args.budget_receipt_sha256)
        save(args.output_dir / "admission.PUBLIC.json", {
            "kind": "r30-lock-held-live-readmission-v1", "source_sha": SOURCE,
            "binding_sha256": args.binding_sha256, "probe_receipt_sha256": args.budget_receipt_sha256,
            "probe_role": "original GEN probe evidence, not this readmission result",
            "actual_admit_return": admitted})
        if accounts is not None:
            save(args.output_dir / "output/accounts.generated.private.json", accounts)
        steps = ACCOUNT_ROLES if accounts is not None else (args.mode,)
        for step in steps:
            name = value["project"] + "-neutral-" + step + "-" + secrets.token_hex(4)
            argv = docker_prefix(args, value, name)
            if accounts is not None:
                argv += ["-B", "-m", "t44.cli", "init-user", "--username", "synthetic-" + step,
                         "--display-name", "synthetic-" + step, "--password-stdin"]
                password = (accounts[step]["password"] + "\n").encode()
            else:
                argv += ["-B", "/neutral-code/admin.py", args.mode,
                         "--plan", "/neutral-input/plan.json", "--intent", "/neutral-input/intent.json",
                         "--budget-proof", "/neutral-input/budget.PUBLIC.json",
                         "--import-receipt", "/neutral-input/backend-import-receipt.json",
                         "--binding", "/neutral-input/binding.json", "--output", "/neutral-output/result",
                         "--root-budget-admitted"]
                password = None
            timeout = min(180, lib.expiry(value["stop_utc"]) - time.time() - 600)
            if timeout <= 0:
                raise ValueError("SIX_HUNDRED_SECOND_CLEANUP_RESERVE_REQUIRED")
            out, err = (args.output_dir / "logs" / (step + suffix) for suffix in (".stdout.private", ".stderr.private"))
            status = runner(argv, out, err, password, timeout, budget.clean_environment(),
                            lambda stop=False, child=name: owned_finished(lib, value, child, stop=stop))
            save(args.output_dir / (step + "-exit.PUBLIC.json"), {"mode": args.mode, "step": step, "returncode": status})
            if status:
                raise RuntimeError("ADMIN_CHILD_FAILED_NO_RETRY_PREFIX_PRESERVED")
            if accounts is not None:
                result = json.loads(raw(out, private=True))
                if set(result) != {"user_id"} or type(result["user_id"]) is not int or not 1 <= result["user_id"] <= 4294967295:
                    raise ValueError("ORIGINAL_INIT_USER_CLI_JSON_REQUIRED")
                accounts[step]["user_id"] = result["user_id"]
                save(args.output_dir / (step + "-account.private.json"), accounts[step])
        if accounts is not None:
            output = args.output_dir / "output/accounts.initialized.private.json"
            save(output, accounts)
        else:
            filename = {"seed": "seed-result.json", "counts": "counts.json", "service": "service.json"}[args.mode]
            output = args.output_dir / "output/result" / filename
            private_result(output)
        generation.valid_window(lib, value["stop_utc"], 600)
    receipt = {"kind": "r30-locked-admin-completion-v1", "mode": args.mode, "source_sha": SOURCE,
               "project": value["project"], "database": value["database"], "binding_sha256": args.binding_sha256,
               "output": str(output), "private_log_directory": str(args.output_dir / "logs"),
               "admission_receipt": str(args.output_dir / "admission.PUBLIC.json"), "credentials_disclosed": False}
    save(args.output_dir / "completion.PUBLIC.json", receipt)
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=MODES)
    for name in ("phase-dir", "profile-json", "code-dir", "code-manifest", "plan", "intent", "import-receipt", "budget-receipt", "output-dir"):
        p.add_argument("--" + name, type=Path, required=True)
    for name in ("binding-sha256", "profile-sha256", "code-manifest-sha256", "budget-receipt-sha256"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--accounts", type=Path)
    args = p.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(run_admin(args)))
    except Exception as error:  # noqa: BLE001 -- private child prefixes never printed.
        if args.output_dir.is_dir() and not (args.output_dir / "failure.PUBLIC.json").exists():
            save(args.output_dir / "failure.PUBLIC.json", {"kind": "r30-admin-failure-v1", "error_class": type(error).__name__,
                                                         "prefix_preserved": True, "automatic_retry": False})
        print(json.dumps({"success": False, "error_class": type(error).__name__, "prefix_preserved": True}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
