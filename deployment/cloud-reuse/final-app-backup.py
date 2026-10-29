"""APP-only offline-recipient encrypted backup; release authority is always outside this tool."""

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import signal
import stat
import subprocess
import tarfile
import threading
import time
from datetime import datetime
from pathlib import Path, PurePosixPath


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def regular(path, expected, private=False):
    row = path.lstat()
    if (path.resolve() != path or not path.is_absolute() or not stat.S_ISREG(row.st_mode)
            or row.st_nlink != 1 or row.st_uid != os.geteuid()
            or (private and stat.S_IMODE(row.st_mode) != 0o600)
            or not re.fullmatch(r"[0-9a-f]{64}", expected or "") or sha(path) != expected):
        raise ValueError("CANONICAL_OWNED_ORIGINAL_PINNED_FILE_REQUIRED")


def save(path, value):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def inspect(argv):
    return json.loads(subprocess.run(["docker", "--context", "default", *argv], check=True,
        capture_output=True, timeout=20, env={k: v for k, v in os.environ.items() if k in {"PATH", "HOME"}}).stdout)


def checked_inventory(value):
    if (os.geteuid() != 0 or value.get("kind") != "root-approved-APP-backup-selection-v1"
            or value.get("role") != "APP" or value.get("root_approved") is not True
            or not value.get("directories") or not value.get("volumes") or not value.get("restore_required_files")):
        raise ValueError("ROOT_APPROVED_APP_SETTINGS_AND_DATA_SELECTION_REQUIRED")
    paths = []
    for text in value["directories"]:
        path = Path(text)
        if (not re.fullmatch(r"/root/t44-[A-Za-z0-9_./-]+", text) or path.resolve() != path
                or not path.is_dir() or any(p.lower() in {"qa-private", "qa_private"} for p in path.parts)):
            raise ValueError("EXPLICIT_CANONICAL_APP_DIRECTORY_ONLY_NO_QA_PRIVATE")
        paths.append(path)
    for wanted in value["volumes"]:
        rows = inspect(["volume", "inspect", wanted["name"]])
        if (len(rows) != 1 or rows[0]["Name"] != wanted["name"]
                or rows[0]["Labels"].get("com.docker.compose.project") != wanted["project"]
                or not re.fullmatch(r"t44-cloud-[a-z][a-z0-9]{5,17}-[fp]", wanted["project"])):
            raise ValueError("EXACT_OWNED_APP_VOLUME_REQUIRED")
        ids = subprocess.run(["docker", "--context", "default", "ps", "--all", "--quiet", "--filter", "volume=" + wanted["name"]],
                             check=True, capture_output=True, timeout=20).stdout.decode().split()
        for cid in ids:
            row = inspect(["inspect", cid])[0]
            if row["State"]["Running"]:
                raise ValueError("ALL_VOLUME_USERS_MUST_EXIT_BEFORE_COLD_DATA_BACKUP")
        path = Path(rows[0]["Mountpoint"])
        if (not str(path).startswith("/var/lib/docker/volumes/") or path.resolve() != path
                or path.name != "_data" or not path.is_dir()):
            raise ValueError("ACTUAL_CANONICAL_DOCKER_DATA_MOUNTPOINT_REQUIRED")
        paths.append(path)
    return paths


def checked_output(output, paths):
    if (not output.is_absolute() or output.exists() or output.parent.resolve() != output.parent
            or any(output == p or output.is_relative_to(p) or p.is_relative_to(output) for p in paths)):
        raise ValueError("NEW_BACKUP_REQUIRED")


def tar_command(paths):
    return ["tar", "--create", "--gzip", "--file", "-", "--one-file-system", "--directory", "/", "--",
            *(str(path).lstrip("/") for path in paths)]


def encrypt_stream(tar_argv, cert, cipher, log, timeout):
    """No plaintext archive on APP disk; recipient private key never leaves the local machine."""
    end = time.monotonic() + timeout
    plain = hashlib.sha256()
    count = 0
    with log.open("xb") as err, cipher.open("xb") as encrypted:
        log.chmod(0o600)
        cipher.chmod(0o600)
        archive = subprocess.Popen(tar_argv, stdout=subprocess.PIPE, stderr=err, start_new_session=True)
        crypto = subprocess.Popen(["openssl", "cms", "-encrypt", "-binary", "-aes-256-cbc", "-outform", "DER",
                                   "-recip", str(cert)], stdin=subprocess.PIPE, stdout=encrypted, stderr=err, start_new_session=True)
        def bounded_kill():
            for proc in (archive, crypto):
                if proc.poll() is None:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
        watchdog = threading.Timer(timeout, bounded_kill)
        watchdog.start()
        try:
            for block in iter(lambda: archive.stdout.read(1024 * 1024), b""):
                if time.monotonic() >= end:
                    raise TimeoutError("BACKUP_COST_RESERVE_DEADLINE")
                plain.update(block)
                count += len(block)
                crypto.stdin.write(block)
            crypto.stdin.close()
            archive.stdout.close()
            if archive.wait(timeout=max(1, end - time.monotonic())) != 0 or crypto.wait(timeout=max(1, end - time.monotonic())) != 0:
                raise ValueError("ARCHIVE_OR_ENCRYPT_FAILED_PREFIX_PRESERVED")
        finally:
            watchdog.cancel()
            for proc in (archive, crypto):
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=10)
    return {"plaintext_stream_sha256": plain.hexdigest(), "plaintext_stream_bytes": count,
            "encrypted_sha256": sha(cipher), "encrypted_bytes": cipher.stat().st_size}


def local_verify(args):
    regular(args.backup, args.backup_sha256)
    regular(args.receipt, args.receipt_sha256)
    receipt = json.loads(args.receipt.read_bytes())
    if receipt["encrypted_sha256"] != args.backup_sha256:
        raise ValueError("ORIGINAL_BACKUP_RECEIPT_REQUIRED")
    h, count, members, selections = hashlib.sha256(), 0, [], []
    with args.output.open("xb") as private_log:
        args.output.chmod(0o600)
        proc = subprocess.Popen(["openssl", "cms", "-decrypt", "-binary", "-inform", "DER", "-in", str(args.backup),
             "-recip", str(args.recipient_cert), "-inkey", str(args.private_key)], stdout=subprocess.PIPE, stderr=private_log)
        try:
            class HashedReader(io.RawIOBase):
                def read(self, size=-1):
                    nonlocal count
                    data = proc.stdout.read(size)
                    h.update(data)
                    count += len(data)
                    return data
            reader = HashedReader()
            seen = set()
            with gzip.GzipFile(fileobj=reader, mode="rb") as zipped:
                with tarfile.open(fileobj=zipped, mode="r|") as archive:
                    for member in archive:
                        name = member.name.rstrip("/")
                        path = PurePosixPath(name)
                        if (not name or path.is_absolute() or ".." in path.parts or str(path) != name
                                or name in seen or not (member.isfile() or member.isdir() or member.issym() or member.islnk())):
                            raise ValueError("INVALID_OR_DUPLICATE_RESTORE_MEMBER")
                        seen.add(name)
                        row = {"path": name, "mode": member.mode, "bytes": member.size, "type": member.type.decode()}
                        if member.isfile():
                            stream = archive.extractfile(member)
                            file_hash, file_bytes = hashlib.sha256(), 0
                            private_selection = bytearray() if path.name == "backup-selection.private.json" else None
                            if private_selection is not None and member.size > 4 * 1024 * 1024:
                                raise ValueError("PRIVATE_RESTORE_SELECTION_SIZE_BOUND")
                            for block in iter(lambda stream=stream: stream.read(1024 * 1024), b""):
                                file_hash.update(block)
                                file_bytes += len(block)
                                if private_selection is not None:
                                    private_selection.extend(block)
                            stream.close()
                            if file_bytes != member.size:
                                raise ValueError("TRUNCATED_RESTORE_FILE")
                            row["sha256"] = file_hash.hexdigest()
                            if private_selection is not None:
                                selections.append(bytes(private_selection))
                        if member.issym() or member.islnk():
                            link = PurePosixPath(member.linkname)
                            if link.is_absolute() or ".." in link.parts:
                                raise ValueError("UNSAFE_RESTORE_LINK")
                            row["linkname"] = member.linkname
                        members.append(row)
                while zipped.read(1024 * 1024):
                    pass  # Consume gzip trailer and verify CRC/length.
            while reader.read(1024 * 1024):
                pass
            if proc.wait(timeout=30) != 0 or h.hexdigest() != receipt["plaintext_stream_sha256"] or count != receipt["plaintext_stream_bytes"]:
                raise ValueError("FULL_LOCAL_DECRYPT_STREAM_BYTES_HASH_MISMATCH")
        finally:
            proc.stdout.close()
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
    if len(selections) != 1 or hashlib.sha256(selections[0]).hexdigest() != receipt["inventory_sha256"]:
        raise ValueError("ORIGINAL_PRIVATE_RESTORE_SELECTION_NOT_PROVEN")
    selected = json.loads(selections[0])
    required = {p.lstrip("/") for p in selected["restore_required_files"]}
    if not required or not required <= {r["path"] for r in members if "sha256" in r}:
        raise ValueError("REQUIRED_APP_SETTINGS_OR_DATA_FILE_MISSING")
    manifest = args.output.with_name(args.output.name + ".restore-manifest.private.json")
    save(manifest, {"members": members, "required_files": sorted(required), "plaintext_stream_sha256": h.hexdigest()})
    return {"status": "FULL_LOCAL_DECRYPT_TAR_VERIFIED_NOT_RESTORE_TEST_OR_RELEASE_AUTHORITY", "encrypted_sha256": args.backup_sha256,
            "regular_files": sum("sha256" in r for r in members), "members": len(members), "private_manifest_sha256": sha(manifest)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("backup", "verify-local"))
    for key in ("inventory", "recipient-cert", "output", "backup", "receipt", "private-key"):
        p.add_argument("--" + key, type=Path)
    for key in ("inventory-sha256", "recipient-cert-sha256", "backup-sha256", "receipt-sha256"):
        p.add_argument("--" + key)
    args = p.parse_args()
    os.umask(0o077)
    if args.action == "verify-local":
        print(json.dumps(local_verify(args)))
        return
    regular(args.inventory, args.inventory_sha256, private=True)
    regular(args.recipient_cert, args.recipient_cert_sha256)
    selected = json.loads(args.inventory.read_bytes())
    paths = checked_inventory(selected)
    checked_output(args.output, paths)
    end = datetime.fromisoformat(selected["absolute_cost_cutoff_utc"].replace("Z", "+00:00")).timestamp()  # noqa: FURB162 -- APP Python3.10
    timeout = min(600, end - time.time() - 60)
    if timeout < 30 or args.output.exists() or args.output.parent.resolve() != args.output.parent:
        raise ValueError("NEW_BACKUP_AND_FINAL_COST_STOP_RESERVE_REQUIRED")
    args.output.mkdir(mode=0o700)
    cipher = args.output / "APP-data-settings.cms"
    selection = args.output / "backup-selection.private.json"
    fd = os.open(selection, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(args.inventory.read_bytes())
    argv = tar_command([*paths, selection])
    result = encrypt_stream(argv, args.recipient_cert, cipher, args.output / "backup.stderr.private", timeout)
    result.update(status="ENCRYPTED_ON_APP_NOT_YET_LOCAL_VERIFIED", inventory_sha256=args.inventory_sha256,
                  recipient_cert_sha256=args.recipient_cert_sha256)
    save(args.output / "backup.PUBLIC.json", result)
    print(json.dumps({"status": result["status"], "backup": str(cipher), "sha256": result["encrypted_sha256"],
                      "receipt": str(args.output / "backup.PUBLIC.json")}))


if __name__ == "__main__":
    main()
