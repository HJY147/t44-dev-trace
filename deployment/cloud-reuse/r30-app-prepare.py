"""One bounded APP preparation: original verified package -> idle P only, no seed/session."""

import argparse
import hashlib
import ipaddress
import json
import os
import platform
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

RUN = "r30window01"
SOURCE = "0bffe0c535e5897890aebf30879fdd3839dc52d6"
PROFILE_SHA = "6d4b7bc4c4f77515da429df9cbf82554a3a0f5d379ef4fd3a638bf04eaf94584"
BUNDLE = "b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345"
PROOF = Path("/root/t44-r9/proof-v2-01/proof.jsonl")
PROOF_SHA = "30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0"
T0 = "2026-10-29T10:00:00Z"
G = "2026-10-29T10:35:00Z"
CUTOFF = "2026-10-29T10:17:30Z"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def epoch(value):
    from datetime import datetime

    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def save(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())


def regular(path):
    s = path.lstat()
    if (path.resolve() != path or not stat.S_ISREG(s.st_mode) or s.st_nlink != 1
            or s.st_uid != os.geteuid()):
        raise ValueError("OWNED_CANONICAL_REGULAR_FILE_REQUIRED")


def app_ip(explicit):
    if explicit:
        value = explicit
    else:
        # Kernel route lookup only: this does not send a packet or query a cloud API.
        rows = json.loads(subprocess.check_output(["ip", "-4", "-j", "route", "get", "1.1.1.1"], timeout=10))
        if len(rows) != 1:
            raise ValueError("ONE_ACTUAL_DEFAULT_ROUTE_REQUIRED")
        value = rows[0].get("prefsrc") or rows[0].get("src")
    address = ipaddress.IPv4Address(value)
    if not any(address in ipaddress.IPv4Network(net) for net in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
        raise ValueError("ACTUAL_RFC1918_APP_IP_REQUIRED")
    return str(address)


def require_host():
    if os.geteuid() != 0 or platform.system() != "Linux" or platform.machine() not in {"amd64", "x86_64"}:
        raise ValueError("ROOT_LINUX_AMD64_REQUIRED")


class Preparation:
    def __init__(self, args):
        self.args, self.steps, self.phase, self.armed = args, [], None, False
        self.root = args.run_root / "run"
        self.ops = args.ops

    def command(self, label, argv, cap=180, *, stopping=False):
        remaining = (epoch(G) if stopping else min(epoch(CUTOFF), epoch(G) - 600)) - time.time()
        if remaining <= 0:
            raise ValueError("NEW_PREPARATION_CUTOFF_OR_G_RESERVE_REACHED")
        index = len(self.steps) + 1
        prefix = self.root / "commands" / (f"{index:02d}-" + label)
        out, err = Path(str(prefix) + ".stdout.private"), Path(str(prefix) + ".stderr.private")
        result_code = None
        started = time.time()
        env = {k: v for k, v in os.environ.items() if not k.startswith(("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))}
        try:
            with out.open("xb") as stdout, err.open("xb") as stderr:
                out.chmod(0o600)
                err.chmod(0o600)
                p = subprocess.run(list(map(str, argv)), stdout=stdout, stderr=stderr, check=False,
                                   timeout=min(cap, remaining), env=env)
            result_code = p.returncode
        finally:
            step = {"step": label, "returncode": result_code, "started_epoch": started, "finished_epoch": time.time(),
                    "stdout": {"path": str(out), "bytes": out.stat().st_size, "sha256": sha(out)},
                    "stderr": {"path": str(err), "bytes": err.stat().st_size, "sha256": sha(err)}}
            self.steps.append(step)
            save(Path(str(prefix) + ".PUBLIC.json"), step)
        if result_code != 0:
            raise RuntimeError("PREPARATION_CHILD_FAILED_PREFIX_PRESERVED:" + label)
        return json.loads(out.read_bytes())

    def gen(self, action, *extra, cap=180, stopping=False):
        return self.command(action, [sys.executable, self.ops / "profile/generation.py", action,
                                     "--phase-dir", self.phase["phase_dir"], "--binding-sha256", self.phase["binding_sha256"], *extra],
                            cap, stopping=stopping)

    def execute(self):
        a = self.args
        require_host()
        if not epoch(T0) <= time.time() < epoch(CUTOFF):
            raise ValueError("EXPLICIT_T0_TO_PACKET_CUTOFF_REQUIRED")
        regular(a.package / "backend-bundle-manifest.json")
        regular(PROOF)
        if PROOF.stat().st_size != 50297 or sha(PROOF) != PROOF_SHA:
            raise ValueError("EXACT_ORIGINAL_PUBLIC_CACHE_PROOF_REQUIRED_NO_SEARCH")
        profile_file = self.ops / "profile/profile.json"
        regular(profile_file)
        if a.profile_sha256 != PROFILE_SHA or not re.fullmatch(r"[0-9a-f]{64}", a.profile_sha256) or sha(profile_file) != a.profile_sha256:
            raise ValueError("ROOT_FROZEN_PROFILE_SHA_REQUIRED")
        profile = json.loads(profile_file.read_bytes())
        if profile["source_sha"] != SOURCE or profile["run_id"] != RUN or profile["stop_utc"] != G:
            raise ValueError("EXACT_R30_SOURCE_RUN_G_REQUIRED")
        for name, expected in profile["derived_files"].items():
            regular(self.ops / "profile" / name)
            if sha(self.ops / "profile" / name) != expected["sha256"]:
                raise ValueError("FROZEN_PROFILE_CODE_CHANGED")
        self.root.mkdir(mode=0o700)
        (self.root / "commands").mkdir(mode=0o700)
        ip = app_ip(a.app_ip)
        self.command("verify-bundle", [sys.executable, self.ops / "profile/r30-backend-artifact.py", "verify-bundle",
                                      "--package", a.package, "--manifest-sha256", BUNDLE], 240)
        imported = self.root / "backend-import-receipt.PUBLIC.json"
        self.command("import-backend", [sys.executable, self.ops / "profile/r30-window.py", "import-backend", "--package", a.package,
                                       "--manifest-sha256", BUNDLE, "--receipt", imported], 480)
        self.command("verify-cache", [sys.executable, self.ops / "profile/r30-window.py", "verify-cache", "--original-proof", PROOF], 240)
        prepared = self.command("prepare", [sys.executable, self.ops / "profile/generation.py", "prepare",
            "--factory", self.ops / "profile/factory.py", "--source-package", a.package,
            "--upgrade-binding", a.package / "backend-bundle-manifest.json", "--upgrade-binding-sha256", BUNDLE,
            "--source-manifest-sha256", "0c5b0c0e027578b0f62711175beac4680aab8331bfbc4af2547f02398f38cc1b",
            "--original-proof", PROOF, "--image-proof", self.ops / "profile/image-proof.py", "--run-id", RUN,
            "--app-ip", ip, "--stop-utc", G, "--f-tls-port", "26443", "--f-http-port", "18580",
            "--p-tls-port", "26445", "--p-http-port", "18581", "--p-workers", "64", "--p-pool-size", "5", "--p-max-overflow", "0",
            "--output", self.root / "campaign"], 240)
        self.phase = prepared["phases"]["p"]
        binding = Path(self.phase["phase_dir"]) / "binding.json"
        if sha(binding) != self.phase["binding_sha256"]:
            raise ValueError("ACTUAL_PREPARED_BINDING_SHA_CHANGED")
        actual_binding = json.loads(binding.read_bytes())
        if actual_binding["project"] != "t44-cloud-r30window01-p" or actual_binding["database"] != "t44c_r30window01_p":
            raise ValueError("ACTUAL_NEW_P_NAMESPACE_REQUIRED")
        self.gen("arm", cap=90)
        self.armed = True
        self.gen("config", cap=120)
        self.gen("infra", cap=300)
        probe = self.gen("probe-budget", cap=180)
        budget_args = ["--budget-receipt", probe["budget_receipt"], "--budget-receipt-sha256", probe["budget_receipt_sha256"]]
        self.gen("migrate", "--database", actual_binding["database"], *budget_args, cap=180)
        idle = self.gen("idle", *budget_args, cap=300)
        actual_import = json.loads(imported.read_bytes())
        return {"kind": "r30-app-preparation-public-v1", "status": "IDLE_ONLY_NO_SEED_OR_SESSIONS", "success": True,
                "run_id": RUN, "source_sha": SOURCE, "app_private_ip": ip, "phase": self.phase,
                "binding": {"path": str(binding), "sha256": sha(binding), "bytes": binding.stat().st_size},
                "import_receipt": {"path": str(imported), "sha256": sha(imported), "bytes": imported.stat().st_size,
                                   "full_runtime_files": actual_import["full_runtime_files"]},
                "original_probe": probe, "resources": idle.get("resources", []), "steps": self.steps,
                "F_started": False, "scheduler_start_requested": False, "sessions_issued": False, "seed_requested": False}

    def finish(self):
        try:
            result = self.execute()
        except BaseException as error:
            if self.armed and self.phase:
                try:
                    self.gen("stop", cap=180, stopping=True)
                except BaseException:
                    pass  # All raw command prefixes remain; do not delay provider cost stop.
            result = {"kind": "r30-app-preparation-public-v1", "success": False, "error_class": type(error).__name__,
                      "phase": self.phase, "steps": self.steps, "prefix_preserved": True, "sessions_issued": False, "seed_requested": False}
            if self.root.is_dir():
                save(self.root / "failure.private.json", {"error_class": type(error).__name__, "reason": str(error)})
        raw = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if len(raw) > 22000:
            result = {"kind": "r30-app-preparation-public-v1", "success": False, "error": "PUBLIC_METADATA_LIMIT",
                      "raw_command_prefixes": str(self.root / "commands"), "sessions_issued": False, "seed_requested": False}
            raw = (json.dumps(result) + "\n").encode()
        if self.root.is_dir():
            save(self.root / "preparation.PUBLIC.json", result)
        sys.stdout.buffer.write(raw)
        return 0 if result.get("success") else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ops", type=Path, default=Path("/root/t44-r30/r30window01/ops"))
    p.add_argument("--package", type=Path, default=Path("/root/t44-r30/r30window01/package"))
    p.add_argument("--run-root", type=Path, default=Path("/root/t44-r30/r30window01"))
    p.add_argument("--profile-sha256", default=PROFILE_SHA)
    p.add_argument("--app-ip")
    args = p.parse_args()
    os.umask(0o077)
    raise SystemExit(Preparation(args).finish())


if __name__ == "__main__":
    main()
