"""APP adapter: original GEN only; protected Docker output stays in private prefix files."""

import os
import signal
import subprocess
import sys
import types
from contextlib import contextmanager
from pathlib import Path

from bridge_common import Refused, canonical, parse, read, require, reserve, sha, utc

DOCKER = ["docker", "--context", "default"]


def app_state_path(authority, state):
    phase = Path(authority["app_phase_dir"])
    require(
        phase.is_absolute()
        and phase.resolve() == phase
        and state == phase / ".scope-callback-state",
        "ONE_FIXED_APP_STATE_DIRECTORY_PER_PHASE",
    )
    return state


def clean_environment():
    return {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("MYSQL_", "RABBITMQ_", "COMPOSE_", "T44_", "DOCKER_"))
        and k not in {"DATABASE_URL", "AMQP_URL"}
    }


class Runner:
    def run(self, argv, deadline, prefix):
        deadline.remaining()
        process = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=clean_environment(),
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=deadline.remaining(30))
        except subprocess.TimeoutExpired as error:
            # This Popen is our unreaped child; never signal operator/scheduler groups.
            try:
                if process.poll() is None and os.getpgid(process.pid) == process.pid:
                    os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Own child exited between poll and metadata lookup; no other PID is signalled.
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired as cleanup:
                stdout = cleanup.stdout or error.stdout or b""
                stderr = cleanup.stderr or error.stderr or b""
                for pipe in (process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()
            reserve(prefix.with_suffix(".stdout.private"), stdout or error.stdout or b"")
            reserve(prefix.with_suffix(".stderr.private"), stderr or error.stderr or b"")
            raise Refused("OWNED_COMMAND_TIMEOUT_INFLIGHT_MAY_COMPLETE") from None
        reserve(prefix.with_suffix(".stdout.private"), stdout)
        reserve(prefix.with_suffix(".stderr.private"), stderr)
        require(process.returncode == 0, "COMMAND_FAILED_NO_RETRY_PRIVATE_PREFIX_PRESERVED")
        deadline.remaining()
        return stdout


class DockerBackend:
    def __init__(self, phase, bridge_dir, bridge_manifest_sha256, clock, runner=None):
        self.phase, self.bridge_dir = Path(phase), Path(bridge_dir)
        self.bundle_sha, self.clock = bridge_manifest_sha256, clock
        self.runner = runner or Runner()

    @contextmanager
    def phase_operation_lock(self, deadline):
        path = self.phase / "mysql-budget.py"
        raw = read(path, self.binding["file_hashes"]["mysql-budget.py"])
        module = types.ModuleType("t44_scope_mysql_budget_" + sha(raw))
        sys.modules[module.__name__] = module
        try:
            # Execute the exact hashed bytes, avoiding a second loader read of a changed path.
            exec(compile(raw, str(path), "exec"), module.__dict__)  # noqa: S102
            with module.operation_lock(
                self.phase,
                self.authority["documents"]["binding"]["sha256"],
                timeout_seconds=min(10, deadline.remaining()),
            ):
                deadline.remaining()
                yield
        finally:
            sys.modules.pop(module.__name__, None)

    def check_binding(self, facts, authority):
        phase = self.phase
        require(
            phase.is_absolute()
            and phase.resolve() == phase
            and str(phase) == authority["app_phase_dir"],
            "ACTUAL_APP_PHASE_REQUIRED",
        )
        read(phase / "binding.json", authority["documents"]["binding"]["sha256"])
        manifest = parse(read(self.bridge_dir / "manifest.PUBLIC.json", self.bundle_sha))
        for name, item in manifest["files"].items():
            read(self.bridge_dir / name, item["sha256"])
        binding = facts["binding"]
        require(
            binding["file_hashes"]["mysql-budget.py"]
            == manifest["phase_dependencies"]["mysql-budget.py"]["sha256"],
            "APP_PHASE_MUTEX_DEPENDENCY_VERSION",
        )
        for name in ("controller.py", "factory.py", "compose.json"):
            read(phase / name, binding["file_hashes"][name])
        composition = parse(read(phase / "compose.json"))
        require(
            set(composition["services"]["admin"]["networks"]) == {"data"}, "ADMIN_DATA_NETWORK_ONLY"
        )
        self.binding, self.authority = binding, authority
        proof_raw = read(
            phase.parent / "actual-source-files.json", binding["source_actual_proof_sha256"]
        )
        self.source_files = parse(proof_raw)["files"]
        require(len(self.source_files) == binding["source_file_count"], "FULL_SOURCE_PROOF_COUNT")

    def output(self, argv):
        self.deadline.remaining()
        value = subprocess.check_output(
            argv, timeout=self.deadline.remaining(5), env=clean_environment()
        )
        self.deadline.remaining()
        return value

    def inspect(self, identifier):
        return parse(self.output(DOCKER + ["inspect", "--format", "{{json .}}", identifier]))

    def scheduler_state(self, facts):
        ids = (
            self.output(
                DOCKER
                + [
                    "ps",
                    "--all",
                    "--quiet",
                    "--no-trunc",
                    "--filter",
                    "label=com.docker.compose.project=" + self.binding["project"],
                    "--filter",
                    "label=com.docker.compose.service=scheduler",
                ]
            )
            .decode()
            .split()
        )
        require(len(ids) <= 1, "ONE_OWNED_SCHEDULER_REQUIRED")
        credential = self.phase / "scheduler-secrets/scheduler-token.json"
        if not ids:
            return {"absent": True, "credential_exists": credential.exists()}
        info = self.inspect(ids[0])
        self._owned_scheduler(info)
        return {
            "absent": False,
            "credential_exists": credential.exists(),
            "healthy_owned": info["State"]["Running"] is True and info["RestartCount"] == 0,
        }

    def _owned_scheduler(self, info):
        require(
            info["Config"]["Labels"].get("com.docker.compose.project") == self.binding["project"]
            and info["Config"]["Labels"].get("com.docker.compose.service") == "scheduler",
            "SCHEDULER_OWNER_MISMATCH",
        )
        require(
            info["Image"]
            in {self.binding["image_ids"]["backend"], self.binding["config_ids"]["backend"]},
            "SCHEDULER_IMAGE_MISMATCH",
        )

    def generation(self, action, facts, folder, deadline):
        argv = [
            sys.executable,
            str(self.phase / "controller.py"),
            action,
            "--phase-dir",
            str(self.phase),
            "--binding-sha256",
            self.authority["documents"]["binding"]["sha256"],
        ]
        if action in {"scheduler-token", "scheduler-rotate"}:
            for identifier in facts["request"]["project_ids"]:
                argv += ["--project-id", str(identifier)]
        raw = self.runner.run(argv, deadline, folder / action)
        rows = [parse(line) for line in raw.splitlines() if line.strip()]
        receipt = rows[-1]
        require(
            receipt["success"] is True
            and receipt["action"] == action
            and receipt["source_sha"] == self.binding["source_sha"],
            "ORIGINAL_GEN_RECEIPT_MISMATCH",
        )
        return receipt

    def confirm_scheduler(self, facts, folder):
        state = self.scheduler_state(facts)
        require(not state["absent"] and state["healthy_owned"], "SCHEDULER_NOT_RUNNING")
        ids = (
            self.output(
                DOCKER
                + [
                    "ps",
                    "--quiet",
                    "--no-trunc",
                    "--filter",
                    "label=com.docker.compose.project=" + self.binding["project"],
                    "--filter",
                    "label=com.docker.compose.service=scheduler",
                ]
            )
            .decode()
            .split()
        )
        require(len(ids) == 1, "ONE_LIVE_SCHEDULER_REQUIRED")
        info = self.inspect(ids[0])
        self._owned_scheduler(info)
        require(
            any(
                m["Source"] == str(self.phase / "scheduler-secrets")
                and m["Destination"] == "/run/t44-secrets"
                and m["RW"] is False
                for m in info["Mounts"]
            ),
            "ACTUAL_SCHEDULER_PRIVATE_MOUNT_REQUIRED",
        )
        require(
            "T44_SCHEDULER_TOKEN_FILE=/run/t44-secrets/scheduler-token.json"
            in info["Config"]["Env"]
            and "t44.scheduling" in info["Config"]["Cmd"],
            "ACTUAL_SCHEDULER_CREDENTIAL_READER_REQUIRED",
        )
        token_path = self.phase / "scheduler-secrets/scheduler-token.json"
        metadata = token_path.lstat()
        require(
            metadata.st_uid == 10001 and (metadata.st_mode & 0o777) == 0o600,
            "ACTUAL_PRIVATE_CREDENTIAL_OWNER_MODE",
        )
        raw = read(token_path, private=True)
        proof = {
            "container_id": info["Id"],
            "image_id": info["Image"],
            "private_file_sha256": sha(raw),
            "observed_utc": utc(self.clock.now()),
            "same_file_mounted_readonly": True,
        }
        reserve(folder / "scheduler.PUBLIC.json", canonical(proof) + b"\n")
        return proof

    def _data(self, mode, facts, authority, folder, deadline, credential_sha=None):
        inputs = folder / (mode + "-inputs")
        inputs.mkdir(mode=0o755)
        inputs.chmod(0o755)  # CLI umask077 must not hide this PUBLIC mount from UID10001.
        output = folder / (mode + "-output")
        output.mkdir(mode=0o700)
        os.chown(output, 10001, 10001)
        control = {
            "request": facts["request"],
            "database": self.binding["database"],
            "source_files": self.source_files,
            "deadline_utc": utc(deadline.end),
        }
        if credential_sha:
            control["credential_file_sha256"] = credential_sha
        raw = canonical(control) + b"\n"
        reserve(inputs / "control.PUBLIC.json", raw, mode=0o444)
        alias = self.binding["images"]["backend"]["alias"]
        actual = (
            self.output(DOCKER + ["image", "inspect", "--format", "{{.Id}}", alias])
            .decode()
            .strip()
        )
        require(
            actual in {self.binding["image_ids"]["backend"], self.binding["config_ids"]["backend"]},
            "EXACT_BACKEND_IMAGE_REQUIRED",
        )
        name = self.binding["project"] + "-scope-" + authority["bridge_id"] + "-" + mode
        argv = DOCKER + [
            "compose",
            "--env-file",
            str(self.phase / "application.env"),
            "--file",
            str(self.phase / "compose.json"),
            "--project-name",
            self.binding["project"],
            "--profile",
            "operations",
            "run",
            "--rm",
            "--no-deps",
            "-T",
            "--name",
            name,
            "--user",
            "10001:10001",
            "--entrypoint",
            "python",
            "--volume",
            str(self.bridge_dir) + ":/opt/bridge:ro",
            "--volume",
            str(inputs) + ":/run/bridge:ro",
            "--volume",
            str(output) + ":/diag-output",
        ]
        if mode == "seal":
            argv += [
                "--volume",
                str(self.phase / "scheduler-secrets") + ":/run/scheduler-secrets:ro",
            ]
        argv += [
            "admin",
            "-B",
            "/opt/bridge/bridge_data.py",
            mode,
            "--control",
            "/run/bridge/control.PUBLIC.json",
            "--control-sha256",
            sha(raw),
            "--output",
            "/diag-output/result.PUBLIC.json",
        ]
        # Each SQL container owns this phase mutex independently. GEN above stays outside it.
        with self.phase_operation_lock(deadline):
            deadline.remaining()
            self.runner.run(argv, deadline, folder / (mode + "-container"))
            deadline.remaining()
            return read(output / "result.PUBLIC.json")

    def preflight(self, facts, authority, folder, deadline):
        result = parse(self._data("preflight", facts, authority, folder, deadline))
        require(result["kind"] == "PUBLIC_READONLY_SCOPE_PREFLIGHT", "READONLY_PREFLIGHT_REQUIRED")

    def seal(self, facts, authority, scheduler, folder, deadline):
        return self._data(
            "seal", facts, authority, folder, deadline, scheduler["private_file_sha256"]
        )
