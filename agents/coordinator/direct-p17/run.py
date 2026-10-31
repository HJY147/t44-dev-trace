"""One Mac command: start retained deployment, initialize, transport, run and recover."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
import time

RUN = "r30posttools17"
W = "/root/t44-final-20261101/QA753_POSTTOOLS_V12_P17"
REMOTE = "/root/t44-direct-p17"
KIT = REMOTE + "/kit"
CMS = KIT + "/transport/cms_five_transport.py"
RSA = "/root/t44-r9/r29-load-key-01/load-only-private.pem"
IDS = {
    "api": "a92f1db5890ab8b2b0c8a2cb3104d1c96520ac18cbbe348125a4c7598f3c6f44",
    "consumer": "6147918a252aa31ffba89af4706960f020a7a12d568fceabb63961124bfe4e4f",
    "scheduler": "d2ea97d46f7b9c0f482447598054cc70c654ae0e2085a1ec017adcebc9d2eb49",
    "web": "402ff7e0601826bfcbf8873f58e6034749827ac626e8f2251bf6b716f144c9cc",
    "tls-gateway": "855882b40173e31083a95e06eca62da94a57a8a765d17df3c74709ea21f010bf",
    "rabbitmq": "97918f928d25ae8ad235337bab3d9c547ac1836c92942e97d07fd510b60f711e",
    "mysql": "ecb591df0b96f4ab774225b478f26fbd6652d16ef57bc277b54600e8e830cc9e",
}

INSTALL = r'''import hashlib,io,json,os,tarfile
from pathlib import Path
root=Path('/root/t44-direct-p17');root.mkdir(mode=0o700)
raw=__import__('sys').stdin.buffer.read(16*1024*1024+1)
assert len(raw)<=16*1024*1024
assert hashlib.sha256(raw).hexdigest()==__import__('sys').argv[1]
out=root/'kit';out.mkdir(mode=0o700)
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
 m=json.load(t.extractfile('MANIFEST.PUBLIC.json'))
 members=t.getmembers();assert len({x.name for x in members})==len(members)
 assert {x.name for x in members}==set(m['files'])|{'MANIFEST.PUBLIC.json'}
 for x in members:
  assert x.isfile() and not Path(x.name).is_absolute() and '..'not in Path(x.name).parts
  b=t.extractfile(x).read()
  if x.name!='MANIFEST.PUBLIC.json':
   v=m['files'][x.name];assert hashlib.sha256(b).hexdigest()==v['sha256'] and len(b)==v['bytes']
  p=out/x.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);p.chmod(0o600)
print(json.dumps({'status':'DIRECT_PACKAGE_INSTALLED'}))
'''


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


class SSH:
    def __init__(self, configs, folder):
        self.configs, self.folder, self.sequence = configs, folder, 0

    def run(self, host, argv, data=None, timeout=180):
        # No shell interpolation on Mac; quote every remote argument as shell data.
        self.sequence += 1
        result = subprocess.run(["ssh", "-F", str(self.configs[host][0]),
                                 self.configs[host][1], shlex.join([str(x) for x in argv])],
                                input=data, capture_output=True, timeout=timeout)
        if result.returncode:
            path = self.folder / (host + "-error-" + str(self.sequence) + ".private")
            path.write_bytes(result.stderr)
            path.chmod(0o600)
            raise RuntimeError("REMOTE_COMMAND_FAILED_NO_RETRY:" + host)
        return result.stdout

    def get(self, host, remote, local, timeout=600):
        cfg, alias = self.configs[host]
        subprocess.run(["scp", "-F", str(cfg), alias + ":" + remote, str(local)],
                       check=True, capture_output=True, timeout=timeout)


def validate_contract(manifest, contract):
    if manifest.get("source") != "bcec3326b40814fdb1922bbfea7c29473b47ba47":
        raise ValueError("EXACT_TESTED_PRODUCT_SOURCE_REQUIRED")
    if manifest.get("run") != RUN or contract.get("run_id") != RUN or contract.get("workspace") != W:
        raise ValueError("EXACT_NEW_RUN_AND_WORKSPACE_REQUIRED")
    if contract.get("download_backup_even_on_nonzero_exit") is not True:
        raise ValueError("FAILURE_BACKUP_RECOVERY_REQUIRED")
    if not contract.get("backup_path", "").endswith("/" + RUN + ".753backup"):
        raise ValueError("EXACT_NEW_BACKUP_PATH_REQUIRED")
    if contract.get("backup_receipt_path") != contract["backup_path"] + ".receipt.json":
        raise ValueError("EXACT_NEW_BACKUP_RECEIPT_REQUIRED")


def template(argv, **values):
    return [part.format(**values) for part in argv]


def initialize(ssh, host, raw, archive_sha, contract):
    ssh.run(host, ["python3", "-c", INSTALL, archive_sha], data=raw)
    if host == "app":
        return json.loads(ssh.run("app", ["python3", "-B", KIT + "/deployment/start.py",
            "--backend-dir", KIT + "/backend", "--run-id", RUN,
            "--output", REMOTE + "/app-init"]))
    script = "from pathlib import Path;import shutil;w=Path(" + repr(W) + ");w.parent.mkdir(parents=True,exist_ok=True);w.mkdir(mode=0o700);shutil.copytree(" + repr(KIT + "/qa") + ",w/'public')"
    ssh.run("load", ["python3", "-c", script])
    ssh.run("load", template(contract["install_argv"], W=W))
    ssh.run("load", ["python3", CMS, "cert", "--key", RSA,
                     "--output", REMOTE + "/recipient.PUBLIC.pem"])
    return {"status": "LOAD_READY"}


def execute(ssh, raw, archive_sha, contract, local, notify=print, sleep=time.sleep):
    with ThreadPoolExecutor(max_workers=2) as pool:
        app = pool.submit(initialize, ssh, "app", raw, archive_sha, contract)
        load = pool.submit(initialize, ssh, "load", raw, archive_sha, contract)
        app_value = app.result()
        load.result()
    if app_value.get("status") != "INIT_DONE":
        raise RuntimeError("APP_INITIALIZATION_NOT_COMPLETE")
    bootstrap = app_value["bootstrap_output"]
    cert = local / "recipient.PUBLIC.pem"
    ssh.get("load", REMOTE + "/recipient.PUBLIC.pem", cert)
    digest = sha(cert)
    write_cert = "from pathlib import Path;import sys;p=Path(" + repr(REMOTE + "/recipient.PUBLIC.pem") + ");p.open('xb').write(sys.stdin.buffer.read())"
    ssh.run("app", ["python3", "-c", write_cert], data=cert.read_bytes())
    # Exact five-file CMS envelope; only ciphertext and the public cert reach Mac.
    stage = "from pathlib import Path;import shutil;d=Path(" + repr(REMOTE + "/five") + ");d.mkdir(mode=0o700);"
    sources = {
        "session.private.json": bootstrap + "/current-inputs.private.json",
        "ca.pem": "/root/t44-final-20261029/P09/P-packet/output/packet/inputs/ca.pem",
        "source-manifest.json": KIT + "/provenance/source-manifest.json",
        "backend-bundle-manifest.json": KIT + "/provenance/backend-bundle-manifest.json",
        "backend-import-receipt.json": "/root/t44-p15-live-20261031/backend-import-receipt.json",
    }
    for name, path in sources.items():
        stage += "shutil.copyfile(" + repr(path) + ",d/" + repr(name) + ");(d/" + repr(name) + ").chmod(0o600);"
    ssh.run("app", ["python3", "-c", stage])
    cipher = REMOTE + "/inputs.753cms"
    ssh.run("app", ["python3", CMS, "seal", "--inputs", REMOTE + "/five",
        "--cert", REMOTE + "/recipient.PUBLIC.pem", "--cert-sha256", digest, "--output", cipher])
    for suffix in ("", ".PUBLIC.json"):
        path = local / ("inputs.753cms" + suffix)
        ssh.get("app", cipher + suffix, path)
        code = "from pathlib import Path;import sys;p=Path(" + repr(cipher + suffix) + ");p.open('xb').write(sys.stdin.buffer.read())"
        ssh.run("load", ["python3", "-c", code], data=path.read_bytes())
    opened = REMOTE + "/opened"
    ssh.run("load", ["python3", CMS, "open", "--cipher", cipher,
        "--receipt", cipher + ".PUBLIC.json", "--cert", REMOTE + "/recipient.PUBLIC.pem",
        "--cert-sha256", digest, "--key", RSA, "--output", opened])
    direct_sha = contract["direct_shell_sha256"]
    channel = REMOTE + "/controller"
    ssh.run("load", ["python3", KIT + "/coordinator/launch.py", "--workspace", W,
        "--inputs", opened + "/inputs/session.private.json", "--channel", channel,
        "--shell-sha256", direct_sha])
    notify("DIRECT_RUNNER_DISPATCHED")
    deadline = time.monotonic() + 1200
    last_phase = None
    observers = ThreadPoolExecutor(max_workers=2)
    sampled = {}
    while time.monotonic() < deadline:
        probe = "from pathlib import Path;import json;p=Path(" + repr(channel + "/wrapper-exit.PUBLIC.json") + ");print(json.dumps({'done':p.is_file(),'value':json.loads(p.read_bytes())if p.is_file()else None}))"
        try:
            state = json.loads(ssh.run("load", ["python3", "-c", probe]))
        except Exception:
            # Retry only this read-only status read, never initialization or dispatch.
            notify({"status": "STATUS_UNAVAILABLE_RUN_NOT_REDISPATCHED"})
            sleep(15)
            continue
        if state["done"]:
            (local / "wrapper-exit.PUBLIC.json").write_text(json.dumps(state["value"]) + "\n")
            break
        try:
            phase = json.loads(ssh.run("load", template(contract["observe_argv"], W=W)))
        except Exception:
            phase = {"available": False, "missing_is_not_zero": True}
        elapsed = phase.get("seconds_since_public_RUNNING_marker")
        if isinstance(elapsed, (float, int)):
            for label, at in (("early", 70), ("late", 550)):
                if elapsed >= at and label not in sampled and not state["done"]:
                    argv = ["python3", KIT + "/coordinator/manual13-observe.py",
                            "--output", REMOTE + "/" + label + ".PUBLIC.jsonl"]
                    for role, identifier in IDS.items():
                        argv += ["--container", role + "=" + identifier]
                    sampled[label] = observers.submit(ssh.run, "app", argv, timeout=150)
        (local / "phase.PUBLIC.json").write_text(json.dumps(phase) + "\n")
        text = json.dumps(phase.get("phase"), sort_keys=True)
        if text != last_phase:
            notify(phase)
            last_phase = text
        sleep(15)
    else:
        raise RuntimeError("DIRECT_RUNNER_TIMEOUT_NO_AUTOMATIC_RETRY_OR_VM_SHUTDOWN")
    observers.shutdown(wait=True)
    for label, future in sampled.items():
        try:
            future.result()
        except Exception:
            (local / (label + "-observer-unavailable.PUBLIC.json")).write_text(
                json.dumps({"available": False, "missing_is_not_zero": True}) + "\n")
        try:
            ssh.get("app", REMOTE + "/" + label + ".PUBLIC.jsonl", local / (label + ".PUBLIC.jsonl"))
        except Exception:
            (local / (label + "-observer-unavailable.PUBLIC.json")).write_text(
                json.dumps({"available": False, "missing_is_not_zero": True}) + "\n")
    notify({"status": "APP_EVIDENCE_RECOVERED_CAN_STOP_APP",
            "load_must_stay_on_until_backup_download_verified": True,
            "automatic_vm_shutdown": False})
    # Recover even when the original measurement reports NP/nonzero.
    archive = local / (RUN + ".753backup")
    receipt = local / (RUN + ".753backup.receipt.json")
    ssh.get("load", contract["backup_receipt_path"], receipt)
    ssh.get("load", contract["backup_path"], archive, timeout=1800)
    value = json.loads(receipt.read_bytes())
    if archive.stat().st_size != value["cipher_bytes"] or sha(archive) != value["cipher_sha256"]:
        raise RuntimeError("BACKUP_BYTES_OR_SHA_MISMATCH")
    result = {"status": "EVIDENCE_RECOVERED_CAN_STOP_BOTH_SERVERS", "run_id": RUN,
              "classification": "DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE",
              "backup_bytes": archive.stat().st_size, "backup_sha256": sha(archive),
              "measurement_wrapper_exit_code": state["value"]["exit_code"],
              "automatic_vm_shutdown": False, "performance_pass_claimed": False}
    (local / "RECOVERY.PUBLIC.json").write_text(json.dumps(result, indent=2) + "\n")
    notify(result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app-ip", required=True)
    p.add_argument("--load-ip", required=True)
    p.add_argument("--kit", type=Path, required=True)
    p.add_argument("--kit-sha256", required=True)
    p.add_argument("--identity", type=Path, required=True)
    p.add_argument("--known-hosts", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    os.umask(0o077)
    for address in (a.app_ip, a.load_ip):
        if not ipaddress.IPv4Address(address).is_global:
            raise ValueError("PUBLIC_IPV4_REQUIRED")
    if sha(a.kit) != a.kit_sha256:
        raise ValueError("EXACT_OFFLINE_KIT_REQUIRED")
    a.output.mkdir(mode=0o700)
    helper = Path(__file__).resolve().parent / "ssh/update_ssh_addresses.py"
    if not helper.is_file():
        helper = Path(__file__).resolve().parents[1] / "manualp15-preparation/ssh/update_ssh_addresses.py"
    spec = importlib.util.spec_from_file_location("direct_ssh", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.prepare(a.known_hosts, a.identity, a.app_ip, a.load_ip, a.output / "ssh")
    configs = {"app": (a.output / "ssh/i-bp13uag4r4u9r2hge0mt.sshconfig", "t44-manual-app"),
               "load": (a.output / "ssh/i-bp13uag4r4u9r2hge0mu.sshconfig", "t44-manual-load")}
    ssh = SSH(configs, a.output)
    try:
        with tarfile.open(a.kit) as archive:
            manifest = json.load(archive.extractfile("MANIFEST.PUBLIC.json"))
            contract = json.load(archive.extractfile("qa/CLI_CONTRACT.PUBLIC.json"))
            validate_contract(manifest, contract)
            contract["direct_shell_sha256"] = manifest["files"]["qa/DIRECT_PRESSURE.sh"]["sha256"]
        recovered = execute(ssh, a.kit.read_bytes(), a.kit_sha256, contract, a.output,
                notify=lambda x: print(json.dumps(x) if isinstance(x, dict) else x, flush=True))
        return 0 if recovered["measurement_wrapper_exit_code"] == 0 else 2
    except Exception as error:
        value = {"status": "DIRECT_RUN_FAILED_NO_RETRY", "kind": type(error).__name__,
                 "automatic_vm_shutdown": False, "manual_stop_review_needed": True}
        (a.output / "FAILED.PUBLIC.json").write_text(json.dumps(value) + "\n")
        print(json.dumps(value), flush=True)
        raise SystemExit(1) from None


if __name__ == "__main__":
    raise SystemExit(main())
