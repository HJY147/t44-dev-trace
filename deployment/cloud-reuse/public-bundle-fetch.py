"""Fetch only a root-hash-verified public bundle from an explicit private IPv4 HTTP endpoint."""

import argparse
import hashlib
import ipaddress
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("REDIRECTS_NOT_ALLOWED")


def fetch(args):
    url = urllib.parse.urlsplit(args.server)
    ip = ipaddress.IPv4Address(url.hostname)
    if (
        url.scheme != "http"
        or url.path not in {"", "/"}
        or url.query
        or url.fragment
        or url.username
        or url.password
        or not url.port
        or not 1024 <= url.port <= 65535
        or not any(
            ip in ipaddress.IPv4Network(net)
            for net in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
        )
    ):
        raise ValueError("EXPLICIT_PRIVATE_HTTP_IP_PORT_WITHOUT_CREDENTIALS_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{64}", args.manifest_sha256) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", args.stop_utc
    ):
        raise ValueError("ROOT_MANIFEST_HASH_AND_UTC_DEADLINE_REQUIRED")
    deadline = datetime.fromisoformat(args.stop_utc.replace("Z", "+00:00")).timestamp()  # noqa: FURB162 - Python3.10
    left = deadline - time.time()
    if not 30 <= left <= 3600:
        raise ValueError("THIRTY_SECONDS_TO_ONE_HOUR_FETCH_WINDOW_REQUIRED")
    end = time.monotonic() + left
    if (
        not args.output.is_absolute()
        or args.output.parent.resolve() != args.output.parent
    ):
        raise ValueError("NEW_CANONICAL_ABSOLUTE_OUTPUT_REQUIRED")
    args.output.mkdir(mode=0o700)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def download(name, expected, size=None):
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("OBJECT_HASH_REQUIRED")
        path = args.output / name
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        total, value = 0, hashlib.sha256()
        with os.fdopen(fd, "wb") as output:
            request = urllib.request.Request(
                args.server.rstrip("/") + "/" + name,
                headers={"Cache-Control": "no-store"},
            )
            with opener.open(
                request, timeout=min(10, max(1, deadline - time.time()))
            ) as incoming:
                if incoming.status != 200:
                    raise ValueError("EXACT_HTTP200_REQUIRED")
                while True:
                    if time.monotonic() >= end or time.time() >= deadline:
                        raise ValueError("FETCH_DEADLINE_REACHED")
                    block = incoming.read(1024 * 1024)
                    if not block:
                        break
                    total += len(block)
                    if total > (size if size is not None else 131072):
                        raise ValueError("OBJECT_BYTE_LIMIT_EXCEEDED")
                    value.update(block)
                    output.write(block)
        if (size is not None and total != size) or value.hexdigest() != expected:
            raise ValueError("COMPLETE_OBJECT_BYTES_OR_HASH_MISMATCH")
        return {"name": name, "bytes": total, "sha256": value.hexdigest()}

    manifest_name = (
        "parts-manifest.json" if args.kind == "parts" else "bundle-manifest.json"
    )
    receipts = [download(manifest_name, args.manifest_sha256)]
    manifest = json.loads((args.output / manifest_name).read_text())
    if manifest["schema"] != 1:
        raise ValueError("EXACT_PUBLIC_MANIFEST_SCHEMA_REQUIRED")
    if args.kind == "parts":
        objects = {}
        for index, row in enumerate(manifest["parts"]):
            if row["name"] != "payload.part" + str(index).zfill(4):
                raise ValueError("EXACT_SEQUENTIAL_PART_NAMES_REQUIRED")
            objects[row["name"]] = row
        maximum = 256 * 1024 * 1024
    else:
        objects = manifest["files"]
        if set(objects) != {"images.tar.gz", "source-runtime-context.tar.gz"}:
            raise ValueError("EXACT_PUBLIC_BUNDLE_OBJECTS_REQUIRED")
        maximum = 10 * 1024**3
    if not objects:
        raise ValueError("NONEMPTY_OBJECTS_REQUIRED")
    for name, row in objects.items():
        if type(row["bytes"]) is not int or not 0 < row["bytes"] <= maximum:
            raise ValueError("DECLARED_OBJECT_SIZE_REQUIRED")
        receipts.append(download(name, row["sha256"], row["bytes"]))
    return {
        "success": True,
        "output": str(args.output),
        "objects": receipts,
        "credentials_or_tokens_sent": False,
        "images_loaded_or_services_started": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True)
    parser.add_argument("--kind", choices=("parts", "bundle"), required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--stop-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(fetch(args)))
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError):
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "PRIVATE_PUBLIC_BUNDLE_FETCH_REFUSED",
                    "partial_files_preserved_no_retry": True,
                }
            )
        )
        raise SystemExit(1) from None
