"""Accept an already imported set only after complete archive/config/OCI proof; never reload aliases."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

PROOF_SHA = "47b50d0111737d2b4ff7b47ce37c46bc5d7fc208d2f3933088b8a08dab326fc0"


def load_proof(path):
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != PROOF_SHA:
        raise ValueError("EXACT_REVIEWED_CRYPTO_PROOF_HELPER_REQUIRED")
    spec = importlib.util.spec_from_file_location("reviewed_image_proof", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def accept(args):
    module = load_proof(args.image_proof)
    result = module.observe(
        args.bundle, args.manifest_sha256, args.v1_helper, args.output
    )
    if not result["success"]:
        return {
            "success": False,
            "complete": result["complete"],
            "raw_path": result["raw_path"],
            "raw_sha256": result["raw_sha256"],
            "reason": "ALL_SEVEN_IMAGE_IDENTITIES_NOT_PROVEN",
            "Docker_load_or_alias_mutation_performed": False,
        }
    manifest = module.module_v1(args.v1_helper).verify(
        args.bundle, args.manifest_sha256
    )
    backend = manifest["images"]["backend"]["alias"]
    services = {
        name: {"image": backend, "pull_policy": "never"}
        for name in [
            "api",
            "consumer",
            "scheduler",
            "migrate",
            "admin",
            "credential-admin",
        ]
    }
    services.update(
        {
            name: {"image": manifest["images"][role]["alias"], "pull_policy": "never"}
            for name, role in [
                ("mysql", "mysql"),
                ("rabbitmq", "rabbitmq"),
                ("web", "web"),
            ]
        }
    )
    values = {
        "images-overlay-v2.json": {"services": services},
        "transport-acceptance-v2.json": {
            "success": True,
            "source_sha": manifest["source_sha"],
            "original_manifest_sha256": args.manifest_sha256,
            "original_CI_id_fields_unchanged": {
                role: row["image_id"] for role, row in manifest["images"].items()
            },
            "actual_daemon_id_and_original_config_proofs": result["roles"],
            "proof_raw_path": result["raw_path"],
            "proof_raw_sha256": result["raw_sha256"],
            "all_seven_crypto_proven": True,
            "Docker_load_or_alias_mutation_performed": False,
            "services_started_or_data_changed": False,
        },
    }
    for name, value in values.items():
        descriptor = os.open(
            args.output / name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
        )
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
    return {
        "success": True,
        "source_sha": manifest["source_sha"],
        "acceptance_path": str(args.output / "transport-acceptance-v2.json"),
        "proof_raw_path": result["raw_path"],
        "proof_raw_sha256": result["raw_sha256"],
        "Docker_load_or_alias_mutation_performed": False,
        "services_started_or_data_changed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--v1-helper", type=Path, required=True)
    parser.add_argument("--image-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        result = accept(args)
        print(json.dumps(result))
        raise SystemExit(0 if result["success"] else 1)
    except (OSError, ValueError, KeyError, TypeError):
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "IMAGE_TRANSPORT_V2_ACCEPTANCE_REFUSED",
                    "Docker_load_or_alias_mutation_performed": False,
                }
            )
        )
        raise SystemExit(1) from None
