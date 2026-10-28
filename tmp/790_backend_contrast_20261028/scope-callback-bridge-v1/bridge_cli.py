"""Three preinstalled root commands; no revocation ACK and no implicit retry."""

import argparse
import json
import os
import platform
from pathlib import Path

from bridge_app import provision
from bridge_backend import DockerBackend
from bridge_common import Clock, import_packet, parse, read, require
from bridge_load import DockerProcObserver, deliver, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "provision", "deliver"))
    parser.add_argument("--manifest-sha256", required=True)
    for name in (
        "configuration",
        "request",
        "state-dir",
        "packet",
        "reservation",
        "app-result",
        "owner-locator",
    ):
        parser.add_argument("--" + name, type=Path)
    for name in (
        "configuration-sha256",
        "request-sha256",
        "packet-sha256",
        "app-result-sha256",
        "owner-locator-sha256",
    ):
        parser.add_argument("--" + name)
    parser.add_argument("--owner-locator", type=Path)
    parser.add_argument("--owner-locator-sha256")
    args = parser.parse_args()
    require(os.geteuid() == 0 and platform.system() == "Linux", "ROOT_LINUX_HOST_REQUIRED")
    folder = Path(__file__).resolve().parent
    manifest = parse(read(folder / "manifest.PUBLIC.json", args.manifest_sha256))
    for name, value in manifest["files"].items():
        read(folder / name, value["sha256"])
    required = {
        "prepare": (
            args.configuration,
            args.configuration_sha256,
            args.request,
            args.request_sha256,
            args.state_dir,
        ),
        "provision": (args.packet, args.packet_sha256, args.state_dir),
        "deliver": (args.reservation, args.app_result, args.app_result_sha256),
    }
    require(
        all(value is not None for value in required[args.action]),
        "EXPLICIT_COMMAND_INPUTS_AND_SHA_REQUIRED",
    )
    clock = Clock()
    if args.action == "prepare":
        config = parse(read(args.configuration, args.configuration_sha256))
        if args.owner_locator is not None:
            require(args.owner_locator_sha256 is not None, "OWNER_LOCATOR_PIN_REQUIRED")
            config["owner"] = parse(read(args.owner_locator, args.owner_locator_sha256))["owner"]
        require(config["bridge_bundle_sha256"] == args.manifest_sha256, "BRIDGE_CONFIG_VERSION")
        result = prepare(
            config, args.request, args.request_sha256, args.state_dir, DockerProcObserver(), clock
        )
    elif args.action == "provision":
        authority = import_packet(read(args.packet), args.packet_sha256)
        backend = DockerBackend(authority["app_phase_dir"], folder, args.manifest_sha256, clock)
        result = provision(authority, args.state_dir, backend, clock, args.manifest_sha256)
    else:
        result = deliver(
            args.reservation,
            parse(read(args.app_result, args.app_result_sha256)),
            DockerProcObserver(),
            clock,
        )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- never echo private child/SQL values.
        print(
            json.dumps(
                {
                    "kind": "PUBLIC_SCOPE_BRIDGE_REFUSED",
                    "code": str(error)
                    if type(error).__name__ == "Refused"
                    else type(error).__name__,
                    "no_automatic_retry": True,
                    "private_output_printed": False,
                }
            ),
            flush=True,
        )
        raise SystemExit(1) from None
