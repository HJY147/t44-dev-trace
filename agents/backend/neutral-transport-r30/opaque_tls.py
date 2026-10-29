"""One opaque file, one exact private peer, ordinary CA/IP TLS, and an absolute C."""

import argparse
import http.client
import http.server
import ipaddress
import json
import os
import re
import signal
import ssl
from datetime import timedelta
from pathlib import Path

from five_files import CAP, SOURCE, bounded, canonical, need, remaining, sha, stamp, write


def validate(config, mode):
    need(config.get("root_admit_transport") is True, "EXPLICIT_ROOT_TRANSPORT_ADMISSION_REQUIRED")
    need(
        config["schema"] == "r30-neutral-opaque-relay-v1" and config["source_sha"] == SOURCE,
        "EXACT_NEW_TRANSPORT_CONFIG_REQUIRED",
    )
    remaining(config["cost_stop_utc"])
    networks = tuple(
        ipaddress.IPv4Network(value) for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
    )
    for name in ("app_ip", "load_ip"):
        address = ipaddress.IPv4Address(config[name])
        need(any(address in network for network in networks), "EXACT_PRIVATE_IPV4_REQUIRED")
    need(
        config["app_ip"] != config["load_ip"]
        and type(config["port"]) is int
        and 1024 <= config["port"] <= 65535
        and type(config["bytes"]) is int
        and 0 < config["bytes"] <= CAP
        and re.fullmatch(r"[0-9a-f]{64}", config["sha256"]),
        "EXPLICIT_FINITE_TRANSFER_REQUIRED",
    )
    need(Path(config["attempt_marker"]).is_absolute(), "NEW_ABSOLUTE_ATTEMPT_MARKER_REQUIRED")
    if mode == "serve":
        raw = bounded(config["binding_file"])
        need(sha(raw) == config["binding_sha256"], "ORIGINAL_GEN_BINDING_SHA_REQUIRED")
        binding = json.loads(raw)
        need(
            binding["source_sha"] == SOURCE
            and binding["app_private_ip"] == config["app_ip"]
            and stamp(config["cost_stop_utc"]) == stamp(binding["stop_utc"]) + timedelta(minutes=5),
            "SAME_NEW_SOURCE_BINDING_AND_C40_REQUIRED",
        )
        need(
            sha(bounded(config["certificate_file"], 65536)) == config["certificate_sha256"],
            "PINNED_TLS_LEAF_REQUIRED",
        )
    else:
        need(
            sha(bounded(config["ca_file"], 65536)) == config["ca_sha256"],
            "PINNED_ORIGINAL_CA_REQUIRED",
        )
        need(not Path(config["output_file"]).exists(), "EXCLUSIVE_NEW_FETCH_OUTPUT_REQUIRED")


def opaque_shape(raw):
    records = [json.loads(line) for line in raw.splitlines()]
    need(
        records
        and records[0]["kind"] == "PUBLIC-790-TRANSFER"
        and all(row["kind"] == "OPAQUE" for row in records[1:]),
        "ONLY_ORIGINAL_OPAQUE_STREAM_ALLOWED",
    )


def mark(config, role):
    write(
        Path(config["attempt_marker"]),
        canonical(
            {
                "role": role,
                "bytes": config["bytes"],
                "sha256": config["sha256"],
                "cost_stop_utc": config["cost_stop_utc"],
                "retry": False,
            }
        ),
    )


def serve(config):
    payload = bounded(config["source_file"])
    need(
        len(payload) == config["bytes"] and sha(payload) == config["sha256"],
        "EXACT_SOURCE_SIZE_SHA_REQUIRED",
    )
    opaque_shape(payload)
    mark(config, "serve-one-attempt")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    key = Path(config["private_key_file"])
    need(
        key.resolve() == key and not key.is_symlink() and key.stat().st_mode & 0o077 == 0,
        "OWNED_PRIVATE_TLS_KEY_REQUIRED",
    )
    context.load_cert_chain(config["certificate_file"], str(key))

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.server.attempted = True
            if self.path != "/opaque" or remaining(config["cost_stop_utc"]) <= 0:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-T44-SHA256", sha(payload))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)
            self.wfile.flush()
            self.server.delivered = True

    class Server(http.server.HTTPServer):
        attempted = False
        delivered = False

        def get_request(self):
            connection, peer = super().get_request()
            self.attempted = True
            try:
                need(peer[0] == config["load_ip"], "ONLY_EXACT_LOAD_PEER_ALLOWED")
                connection.settimeout(min(5, remaining(config["cost_stop_utc"])))
                return context.wrap_socket(connection, server_side=True), peer
            except BaseException:
                connection.close()
                raise OSError("TLS_OR_EXACT_PEER_REFUSED") from None

    server = Server((config["app_ip"], config["port"]), Handler)
    server.timeout = 0.2
    print(
        json.dumps(
            {
                "kind": "R30_OPAQUE_LISTENING",
                "pid": os.getpid(),
                "bytes": len(payload),
                "sha256": sha(payload),
                "cost_stop_utc": config["cost_stop_utc"],
            }
        ),
        flush=True,
    )
    try:
        while not server.attempted:
            remaining(config["cost_stop_utc"])
            server.handle_request()
    finally:
        server.server_close()
    need(server.delivered, "SINGLE_OPAQUE_ATTEMPT_NOT_DELIVERED_NO_RETRY")
    return {"kind": "R30_OPAQUE_SENT_ONCE", "bytes": len(payload), "sha256": sha(payload)}


def fetch(config):
    need(not Path(config["output_file"]).exists(), "EXCLUSIVE_NEW_FETCH_OUTPUT_REQUIRED")
    mark(config, "fetch-one-attempt")
    context = ssl.create_default_context(cafile=config["ca_file"])
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    connection = http.client.HTTPSConnection(
        config["app_ip"],
        config["port"],
        source_address=(config["load_ip"], 0),
        timeout=min(30, remaining(config["cost_stop_utc"])),
        context=context,
    )
    try:
        connection.request("GET", "/opaque", headers={"Connection": "close"})
        response = connection.getresponse()
        need(
            response.status == 200
            and response.getheader("Content-Length") == str(config["bytes"])
            and response.getheader("X-T44-SHA256") == config["sha256"],
            "EXACT_OPAQUE_HEADERS_REQUIRED",
        )
        raw = response.read(CAP + 1)
    finally:
        connection.close()
    remaining(config["cost_stop_utc"])
    need(
        len(raw) == config["bytes"] and sha(raw) == config["sha256"],
        "EXACT_RECEIVED_SIZE_SHA_REQUIRED",
    )
    opaque_shape(raw)
    write(Path(config["output_file"]), raw)
    return {"kind": "R30_OPAQUE_FETCHED_ONCE", "bytes": len(raw), "sha256": sha(raw)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("serve", "fetch"))
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    config = json.loads(bounded(args.config))
    validate(config, args.mode)

    def expire(signum, frame):
        raise TimeoutError("ABSOLUTE_C_HARD_STOP")

    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, remaining(config["cost_stop_utc"]))
    try:
        print(json.dumps((serve if args.mode == "serve" else fetch)(config), sort_keys=True))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    main()
