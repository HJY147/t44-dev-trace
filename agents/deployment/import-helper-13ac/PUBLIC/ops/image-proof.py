"""Verify trusted save-archive config/layers against classic or containerd OCI identities."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tarfile
import zlib
from pathlib import Path

V1_SHA = "0a1c2cd5bf57717ba5218ff6bb5086d6acbb60ff54713940a6da73f495a1cfcd"
MANIFEST_TYPES = {
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
}
INDEX_TYPES = {
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
}
CONFIG_TYPES = {
    "application/vnd.oci.image.config.v1+json",
    "application/vnd.docker.container.image.v1+json",
}
RAW_LAYERS = {
    "application/vnd.oci.image.layer.v1.tar",
    "application/vnd.oci.image.layer.nondistributable.v1.tar",
    "application/vnd.docker.image.rootfs.diff.tar",
}
GZIP_LAYERS = {
    "application/vnd.oci.image.layer.v1.tar+gzip",
    "application/vnd.oci.image.layer.nondistributable.v1.tar+gzip",
    "application/vnd.docker.image.rootfs.diff.tar.gzip",
}
DOCKER = ["docker", "--context", "default"]


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def file_hash(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def scan_archive(path):
    """Hash all regular members, including original layer bytes and uncompressed DiffIDs; no extraction."""
    names, by_digest = {}, {}
    total = 0
    with tarfile.open(path, mode="r|*") as archive:
        for member in archive:
            relative = Path(member.name)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not (member.isdir() or member.isfile())
            ):
                raise ValueError("ARCHIVE_LINK_OR_UNSAFE_PATH")
            if member.isdir():
                continue
            if member.name in names or member.size > 8 * 1024**3:
                raise ValueError("DUPLICATE_OR_OVERSIZE_ARCHIVE_MEMBER")
            total += member.size
            if total > 20 * 1024**3:
                raise ValueError("ARCHIVE_SIZE_LIMIT")
            raw_hash, diff_hash = hashlib.sha256(), hashlib.sha256()
            buffer = bytearray() if member.size <= 2 * 1024 * 1024 else None
            decoder, gzip_member, first = None, False, True
            with archive.extractfile(member) as incoming:
                for block in iter(lambda: incoming.read(1024 * 1024), b""):
                    if first:
                        gzip_member = block.startswith(b"\x1f\x8b")
                        decoder = (
                            zlib.decompressobj(16 + zlib.MAX_WBITS)
                            if gzip_member
                            else None
                        )
                        first = False
                    raw_hash.update(block)
                    diff_hash.update(decoder.decompress(block) if decoder else block)
                    if buffer is not None:
                        buffer.extend(block)
            if decoder:
                diff_hash.update(decoder.flush())
                if not decoder.eof or decoder.unused_data:
                    raise ValueError("NONCANONICAL_OR_TRUNCATED_GZIP_LAYER")
            row = {
                "name": member.name,
                "bytes": member.size,
                "digest": "sha256:" + raw_hash.hexdigest(),
                "diff_id": "sha256:" + diff_hash.hexdigest(),
                "gzip": gzip_member,
                "json": None,
            }
            if buffer is not None:
                try:
                    row["json"] = json.loads(buffer)
                except (ValueError, UnicodeError):
                    pass
            if (
                member.name.startswith("blobs/sha256/")
                and member.name != "blobs/sha256/" + raw_hash.hexdigest()
            ):
                raise ValueError("OCI_BLOB_FILENAME_DIGEST_MISMATCH")
            names[member.name] = row
            by_digest[row["digest"]] = row
    return {"names": names, "digests": by_digest, "uncompressed_member_bytes": total}


def alias(value):
    return value.removeprefix("docker.io/library/")


def trusted_role(graph, role, declared, manifest):
    table = graph["names"].get("manifest.json", {}).get("json")
    if not isinstance(table, list):
        raise TypeError("TRUSTED_DOCKER_TAG_CONFIG_TABLE_REQUIRED")
    matches = [
        row
        for row in table
        if declared["alias"] in [alias(tag) for tag in row.get("RepoTags") or []]
    ]
    if len(matches) != 1:
        raise ValueError("EXACT_UNIQUE_ARCHIVE_TAG_REQUIRED")
    row = matches[0]
    config_blob = graph["names"].get(row["Config"])
    if (
        not config_blob
        or config_blob["digest"] != declared["image_id"]
        or not isinstance(config_blob["json"], dict)
    ):
        raise ValueError("ORIGINAL_CI_CONFIG_ID_NOT_PROVEN_BY_ARCHIVE_BYTES")
    config = config_blob["json"]
    rootfs = config.get("rootfs", {})
    if (
        config.get("os") != "linux"
        or config.get("architecture") != "amd64"
        or rootfs.get("type") != "layers"
    ):
        raise ValueError("TRUSTED_CONFIG_PLATFORM_ROOTFS_REQUIRED")
    diffs = rootfs.get("diff_ids")
    if (
        not isinstance(diffs, list)
        or any(not re.fullmatch(r"sha256:[0-9a-f]{64}", value) for value in diffs)
        or len(diffs) != len(row["Layers"])
    ):
        raise ValueError("EXACT_ORIGINAL_ORDERED_DIFF_IDS_REQUIRED")
    for path, expected in zip(row["Layers"], diffs, strict=True):
        layer = graph["names"].get(path)
        if not layer or layer["diff_id"] != expected:
            raise ValueError("ORIGINAL_ARCHIVE_LAYER_DIFF_ID_MISMATCH")
    labels = (config.get("config") or {}).get("Labels") or {}
    if (
        labels.get("org.opencontainers.image.revision") != declared["revision_label"]
        or labels.get("io.t44.source-archive-sha256") != declared["archive_label"]
    ):
        raise ValueError("ORIGINAL_CONFIG_LABELS_DIFFER_FROM_CI")
    if role in {"backend", "web"} and (
        declared["revision_label"] != manifest["source_sha"]
        or declared["archive_label"] != manifest["source_archive_sha256"]
    ):
        raise ValueError("BUILT_SOURCE_ARCHIVE_LABEL_BINDING_MISMATCH")
    return {
        "config_id": config_blob["digest"],
        "config_bytes": config_blob["bytes"],
        "labels": labels,
        "diff_ids": diffs,
        "os": config["os"],
        "architecture": config["architecture"],
        "variant": config.get("variant") or "",
    }


def descriptor_blob(graph, descriptor, media_types):
    if (
        not isinstance(descriptor, dict)
        or descriptor.get("mediaType") not in media_types
    ):
        raise ValueError("UNRECOGNIZED_OR_MISSING_OCI_MEDIA_TYPE")
    value = descriptor.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise ValueError("EXACT_DESCRIPTOR_SHA256_REQUIRED")
    row = graph["digests"].get(value)
    if (
        not row
        or type(descriptor.get("size")) is not int
        or row["bytes"] != descriptor["size"]
    ):
        raise ValueError("DESCRIPTOR_BLOB_BYTES_HASH_OR_SIZE_NOT_PROVEN")
    return row


def prove_role(graph, role, declared, manifest, actual):
    trusted = trusted_role(graph, role, declared, manifest)
    if (
        actual.get("Os") != trusted["os"]
        or actual.get("Architecture") != trusted["architecture"]
        or (actual.get("Variant") or "") != trusted["variant"]
        or (actual.get("Config", {}).get("Labels") or {}) != trusted["labels"]
        or actual.get("RootFS", {}).get("Type") != "layers"
        or actual.get("RootFS", {}).get("Layers") != trusted["diff_ids"]
    ):
        raise ValueError("ACTUAL_PLATFORM_LABELS_OR_ORDERED_ROOTFS_MISMATCH")
    if actual.get("Id") == trusted["config_id"]:
        return {
            "success": True,
            "identity_kind": "classic-config-id",
            "actual_id": actual["Id"],
            "config_id": trusted["config_id"],
            "ordered_layer_count": len(trusted["diff_ids"]),
            "labels_architecture_rootfs_checked": True,
        }
    descriptor = actual.get("Descriptor")
    if not isinstance(descriptor, dict) or descriptor.get("digest") != actual.get("Id"):
        raise ValueError("ACTUAL_ID_MUST_EQUAL_VERIFIED_DESCRIPTOR_DIGEST")
    blob = descriptor_blob(graph, descriptor, MANIFEST_TYPES | INDEX_TYPES)
    body = blob["json"]
    if (
        not isinstance(body, dict)
        or body.get("schemaVersion") != 2
        or body.get("artifactType")
    ):
        raise ValueError("EXACT_RUNNABLE_IMAGE_MANIFEST_REQUIRED")
    if body.get("mediaType", descriptor["mediaType"]) != descriptor["mediaType"]:
        raise ValueError("DESCRIPTOR_BODY_MEDIA_TYPE_MISMATCH")
    if descriptor["mediaType"] in INDEX_TYPES:
        children = body.get("manifests", [])
        if (
            len(children) != 1
            or children[0].get("platform", {}).get("os") != "linux"
            or children[0].get("platform", {}).get("architecture") != "amd64"
        ):
            raise ValueError("EXACT_SINGLE_AMD64_PLATFORM_INDEX_REQUIRED")
        descriptor = children[0]
        blob = descriptor_blob(graph, descriptor, MANIFEST_TYPES)
        body = blob["json"]
        if not isinstance(body, dict) or body.get("schemaVersion") != 2:
            raise ValueError("EXACT_PLATFORM_MANIFEST_REQUIRED")
    configuration = descriptor_blob(graph, body.get("config"), CONFIG_TYPES)
    if (
        configuration["digest"] != trusted["config_id"]
        or configuration["bytes"] != trusted["config_bytes"]
    ):
        raise ValueError("OCI_MANIFEST_CONFIG_DIFFERS_FROM_TRUSTED_CI_CONFIG")
    layers = body.get("layers")
    if not isinstance(layers, list) or len(layers) != len(trusted["diff_ids"]):
        raise ValueError("EXACT_OCI_LAYER_COUNT_REQUIRED")
    for layer, expected in zip(layers, trusted["diff_ids"], strict=True):
        physical = descriptor_blob(graph, layer, RAW_LAYERS | GZIP_LAYERS)
        if (
            physical["gzip"] != (layer["mediaType"] in GZIP_LAYERS)
            or physical["diff_id"] != expected
        ):
            raise ValueError("OCI_LAYER_ENCODING_OR_UNCOMPRESSED_DIFF_ID_MISMATCH")
    return {
        "success": True,
        "identity_kind": "oci-descriptor-to-original-config",
        "actual_id": actual["Id"],
        "config_id": trusted["config_id"],
        "actual_descriptor_sha256_recomputed_from_archive": True,
        "all_config_and_layer_descriptors_sha256_size_verified": True,
        "ordered_layer_count": len(layers),
        "labels_architecture_rootfs_checked": True,
    }


def module_v1(path):
    if file_hash(path) != V1_SHA:
        raise ValueError("UNCHANGED_V1_HELPER_REQUIRED")
    spec = importlib.util.spec_from_file_location("unchanged_v1_bundle", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def actual_image(alias_name):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG"}
    }
    result = subprocess.run(
        [*DOCKER, "image", "inspect", alias_name],
        capture_output=True,
        check=True,
        timeout=20,
        env=env,
    )
    rows = json.loads(result.stdout)
    if len(rows) != 1:
        raise ValueError("EXACT_ONE_RUNTIME_IMAGE_REQUIRED")
    raw = rows[0]
    return {
        key: raw.get(key)
        for key in [
            "Id",
            "RepoTags",
            "RepoDigests",
            "Descriptor",
            "RootFS",
            "Os",
            "Architecture",
            "Variant",
        ]
    } | {"Config": {"Labels": (raw.get("Config") or {}).get("Labels")}}


def observe(bundle, expected, v1_path, output):
    manifest = None
    if not output.is_absolute() or output.parent.resolve() != output.parent:
        raise ValueError("NEW_CANONICAL_PRIVATE_OUTPUT_REQUIRED")
    output.mkdir(mode=0o700)
    fd = os.open(
        output / "proof.jsonl",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    results, complete, graph = {}, False, None
    with os.fdopen(fd, "w") as raw:

        def emit(kind, **fields):
            raw.write(json.dumps({"kind": kind, **fields}) + "\n")
            raw.flush()

        emit("probe_reserved", manifest_sha256=expected, mutation_performed=False)
        try:
            v1 = module_v1(v1_path)
            manifest = v1.verify(bundle, expected)
            emit(
                "trust_anchor",
                manifest_sha256=expected,
                original_archive_gzip=manifest["files"]["images.tar.gz"],
                original_archive_tar_sha256=manifest[
                    "uncompressed_image_archive_sha256"
                ],
                source_sha=manifest["source_sha"],
                mutation_performed=False,
            )
            graph = scan_archive(bundle / "images.tar.gz")
            emit(
                "complete_archive_graph",
                members=len(graph["names"]),
                uncompressed_member_bytes=graph["uncompressed_member_bytes"],
                members_sha256_size_diff_id={
                    name: {k: row[k] for k in ["bytes", "digest", "diff_id", "gzip"]}
                    for name, row in graph["names"].items()
                },
            )
            for role, declared in manifest["images"].items():
                actual = None
                try:
                    actual = actual_image(declared["alias"])
                    proof = prove_role(graph, role, declared, manifest, actual)
                except (
                    ValueError,
                    KeyError,
                    TypeError,
                    subprocess.SubprocessError,
                ) as error:
                    proof = {
                        "success": False,
                        "reason": str(error),
                        "error_class": type(error).__name__,
                    }
                emit(
                    "role_proof",
                    role=role,
                    declared_CI=declared,
                    actual_projection_no_Env_or_Cmd=actual,
                    proof=proof,
                )
                results[role] = proof
            complete = True
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            zlib.error,
            tarfile.TarError,
        ) as error:
            emit(
                "archive_graph_failure",
                success=False,
                reason=str(error),
                error_class=type(error).__name__,
            )
        emit(
            "proof_final",
            complete=complete,
            all_seven_proven=complete
            and len(results) == 7
            and all(row["success"] for row in results.values()),
            mutation_performed=False,
        )
    summary = {
        "success": complete
        and len(results) == 7
        and all(row["success"] for row in results.values()),
        "complete": complete,
        "raw_path": str(output / "proof.jsonl"),
        "raw_sha256": file_hash(output / "proof.jsonl"),
        "raw_bytes": (output / "proof.jsonl").stat().st_size,
        "source_sha": manifest["source_sha"] if manifest else None,
        "manifest_sha256": expected,
        "roles": results,
        "truncated_stdout_raw_is_separate": True,
        "mutation_performed": False,
    }
    file = output / "summary.json"
    descriptor = os.open(
        file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "w") as stream:
        json.dump(summary, stream, indent=2)
    # Compact receipt, not the complete proof; callers must recover/hash raw before claiming reviewed full evidence.
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--v1-helper", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        result = observe(args.bundle, args.manifest_sha256, args.v1_helper, args.output)
        compact = {key: value for key, value in result.items() if key != "roles"}
        compact["roles"] = {
            role: {
                key: value
                for key, value in row.items()
                if key
                in {"success", "identity_kind", "reason", "config_id", "actual_id"}
            }
            for role, row in result["roles"].items()
        }
        wire = json.dumps(compact)
        if len(wire.encode()) >= 2900:
            compact["stdout_role_details_abbreviated_use_full_raw"] = True
            compact["roles"] = {
                role: {
                    "success": row["success"],
                    "identity_kind": row.get("identity_kind"),
                    "reason": row.get("reason", "")[:100],
                }
                for role, row in result["roles"].items()
            }
            wire = json.dumps(compact)
        print(wire)
        raise SystemExit(0 if result["success"] else 1)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print(
            json.dumps(
                {
                    "success": False,
                    "complete": False,
                    "error": "IMAGE_CONFIG_DESCRIPTOR_PROOF_REFUSED",
                    "partial_outputs_preserved": True,
                    "mutation_performed": False,
                }
            )
        )
        raise SystemExit(1) from None
