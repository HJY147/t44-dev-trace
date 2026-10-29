"""Fixed APP staging and one chosen phase to idle; no sessions, QA grant or VM control."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD_PROOF = Path("/root/t44-r9/proof-v2-01/proof.jsonl")
OLD_SHA = "30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def stamp(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()  # noqa: FURB162 -- APP Python3.10


class Runner:
    def __init__(self, args):
        self.args, self.steps, self.armed, self.phase = args, [], False, None
        if args.output.exists() or not args.output.is_absolute() or args.output.parent.resolve() != args.output.parent:
            raise ValueError("NEW_CANONICAL_APP_ATTEMPT_REQUIRED")
        args.output.mkdir(mode=0o700)
        (args.output / "commands").mkdir(mode=0o700)
        approval_raw=args.cost_approval.read_bytes()
        if hashlib.sha256(approval_raw).hexdigest()!=args.cost_approval_sha256:
            raise ValueError("EXACT_NEW_COST_APPROVAL_REQUIRED")
        self.cost_cutoff=stamp(json.loads(approval_raw)["absolute_cost_cutoff_utc"])
        self.end = self.cost_cutoff - 600

    def command(self, label, argv, cap=240, *, stopping=False):
        prefix = self.args.output / "commands" / (f"{len(self.steps)+1:02d}-" + label)
        out, err = Path(str(prefix) + ".stdout.private"), Path(str(prefix) + ".stderr.private")
        timeout = min(cap, (self.cost_cutoff - 30 if stopping else self.end) - time.time())
        if timeout < 1:
            raise TimeoutError("APP_STAGE_OR_PHASE_DEADLINE")
        rc = None
        try:
            with out.open("xb") as stdout, err.open("xb") as stderr:
                out.chmod(0o600)
                err.chmod(0o600)
                rc = subprocess.run(list(map(str, argv)), check=False, stdout=stdout, stderr=stderr, timeout=timeout,
                    env={k:v for k,v in os.environ.items() if k in {"PATH", "HOME", "LANG"}}).returncode
        finally:
            self.steps.append({"label":label,"returncode":rc,"stdout":{"path":str(out),"sha256":sha(out)},"stderr":{"path":str(err),"sha256":sha(err)}})
        if rc:
            raise RuntimeError("APP_CHILD_FAILED_PREFIX_PRESERVED")
        return json.loads(out.read_bytes())

    def execute(self):
        a, package, tool = self.args, self.args.package, HERE / "final-image-bundle.py"
        if OLD_PROOF.stat().st_size != 50297 or sha(OLD_PROOF) != OLD_SHA:
            raise ValueError("ORIGINAL_PUBLIC_CACHE_PROOF_REQUIRED_NO_SEARCH")
        self.command("verify", [sys.executable, tool, "verify", "--package", package, "--manifest-sha256", a.bundle_sha256])
        if a.action == "stage":
            result = self.command("import", [sys.executable, tool, "import", "--package", package,
                "--manifest-sha256", a.bundle_sha256, "--receipt", a.output / "backend-import-receipt.PUBLIC.json"], 480)
            self.command("cache", [sys.executable, tool, "verify-cache", "--original-proof", OLD_PROOF])
            return result
        if sha(a.source_profile) != a.source_profile_sha256:
            raise ValueError("ROOT_APPROVED_SOURCE_PROFILE_RAW_SHA_REQUIRED")
        source = json.loads(a.source_profile.read_bytes())
        if source.get("root_approved") is not True or source["backend_bundle_manifest_sha256"] != a.bundle_sha256:
            raise ValueError("BUSINESS_START_NEEDS_ROOT_APPROVED_SOURCE_PROFILE")
        if a.phase == "p":
            if not a.previous_f_phase_dir or not a.previous_f_binding_sha256:
                raise ValueError("P_REQUIRES_EXPLICIT_COMPLETED_F_OWNERSHIP")
            previous = json.loads((a.previous_f_phase_dir / "binding.json").read_bytes())
            if (sha(a.previous_f_phase_dir / "binding.json") != a.previous_f_binding_sha256
                    or previous["phase"] != "f" or previous["source_sha"] != source["source_sha"]
                    or sha(a.previous_f_phase_dir / "controller.py") != previous["file_hashes"]["controller.py"]):
                raise ValueError("EXACT_PREVIOUS_F_BINDING_REQUIRED")
            self.command("stop-F", [sys.executable, a.previous_f_phase_dir / "controller.py", "stop",
                "--phase-dir", a.previous_f_phase_dir, "--binding-sha256", a.previous_f_binding_sha256], stopping=True)
            remaining = subprocess.run(["docker","--context","default","ps","--quiet","--filter","label=com.docker.compose.project="+previous["project"]],
                check=True,capture_output=True,timeout=20).stdout.strip()
            if remaining:
                raise ValueError("NO_F_RUNNING_CONTAINERS_BEFORE_FIRST_P_T0")
            fd = os.open(a.previous_f_phase_dir / "F-CLOSED", os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
            os.close(fd)
        observation = self.command("prove-loaded", [sys.executable, tool, "prove-loaded", "--package", package,
            "--manifest-sha256", a.bundle_sha256, "--receipt", a.output / "backend-import-receipt.PUBLIC.json"])
        plan = self.command("freeze-time", [sys.executable, HERE / "final-timeplan-absolute.py", "freeze", "--phase", a.phase,
            "--run-id", a.run_id, "--actual-first-boot-utc", a.actual_first_boot_utc,
            "--cost-approval", a.cost_approval, "--cost-approval-sha256", a.cost_approval_sha256,
            "--source-profile", a.source_profile, "--source-profile-sha256", a.source_profile_sha256,
            "--import-receipt", observation["receipt"], "--import-receipt-sha256", observation["sha256"],
            "--output", a.output / "timeplan.PUBLIC.json"])
        self.end = stamp(plan["t0_utc"]) + 17.5 * 60
        self.command("derive", [sys.executable, tool, "derive", "--package", package, "--manifest-sha256", a.bundle_sha256,
            "--run-id", a.run_id, "--stop-utc", plan["stop_utc"], "--cost-stop-utc", plan["cost_stop_utc"], "--output", a.output / "profile"])
        self.command("derive-wrappers", [sys.executable,HERE/"final-runtime-profile.py","--source-profile",a.source_profile,
            "--source-profile-sha256",a.source_profile_sha256,"--source-manifest",package/"source-manifest.json",
            "--gen-profile",a.output/"profile","--gen-profile-sha256",sha(a.output/"profile/profile.json"),"--output",a.output/"runtime"])
        prepared = self.command("GEN-prepare", [sys.executable,a.output/"profile/generation.py","prepare",
            "--factory",a.output/"profile/factory.py","--source-package",package,"--upgrade-binding",package/"backend-bundle-manifest.json",
            "--upgrade-binding-sha256",a.bundle_sha256,"--source-manifest-sha256",source["source_manifest_sha256"],
            "--original-proof",OLD_PROOF,"--image-proof",a.output/"profile/image-proof.py","--run-id",a.run_id,
            "--app-ip",a.app_ip,"--stop-utc",plan["stop_utc"],"--f-tls-port","26443","--f-http-port","18580",
            "--p-tls-port","26445","--p-http-port","18581","--p-workers","64","--p-pool-size","5","--p-max-overflow","0","--output",a.output/"campaign"])
        self.phase = prepared["phases"][a.phase]
        gen = [sys.executable,a.output/"profile/generation.py"]
        common = ["--phase-dir",self.phase["phase_dir"],"--binding-sha256",self.phase["binding_sha256"]]
        probe = None
        for action in ("arm","config","infra","probe-budget","migrate","idle"):
            extra = ["--database", self.phase["database"]] if action == "migrate" else []
            result = self.command(action, [*gen,action,*common,*extra,*(["--budget-receipt",probe["budget_receipt"],"--budget-receipt-sha256",probe["budget_receipt_sha256"]] if action in {"migrate","idle"} else [])])
            if action == "arm":
                self.armed = True
            if action == "probe-budget":
                probe = result
        return {"status":"CHOSEN_PHASE_IDLE_NO_SESSIONS_OR_QA","phase":self.phase,"budget":probe,"timeplan":plan,"import":observation}

    def run(self):
        result = {"status":"FAILED_PREFIX_PRESERVED"}
        try:
            result = self.execute()
            return result
        except BaseException:
            if self.armed:
                try:
                    self.command("failure-owned-stop",[sys.executable,self.args.output/"profile/generation.py","stop","--phase-dir",self.phase["phase_dir"],"--binding-sha256",self.phase["binding_sha256"]],stopping=True)
                except Exception:  # noqa: BLE001 -- preserve failure prefix; never claim stopped
                    result["owned_stop_not_proven"] = True
            raise
        finally:
            (self.args.output/"preparation.PUBLIC.json").write_text(json.dumps({**result,"steps":self.steps},sort_keys=True,indent=2)+"\n")
            (self.args.output/"preparation.PUBLIC.json").chmod(0o600)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("stage","phase"))
    p.add_argument("--phase",choices=("f","p"))
    for key in ("package","output","source-profile","previous-f-phase-dir","cost-approval"):
        p.add_argument("--"+key,type=Path)
    for key in ("bundle-sha256","actual-first-boot-utc","source-profile-sha256","run-id","app-ip","previous-f-binding-sha256","cost-approval-sha256"):
        p.add_argument("--"+key)
    args=p.parse_args()
    os.umask(0o077)
    print(json.dumps(Runner(args).run()))


if __name__=="__main__":
    main()
