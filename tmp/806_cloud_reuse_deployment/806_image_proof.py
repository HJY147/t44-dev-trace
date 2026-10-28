"""Cryptographic source/config/layer/descriptor guards; synthetic OCI bytes, no Docker."""

import copy
import gzip
import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "image_proof", ROOT / "deployment/cloud-reuse/image-proof.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def encoded(value):
    return json.dumps(value, separators=(",", ":")).encode()


def tar_layer(text):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        info = tarfile.TarInfo("public.txt")
        info.size = len(text)
        archive.addfile(info, io.BytesIO(text))
    return buffer.getvalue()


def model(tmp_path, mode="oci", compressed=False, evil=None):
    m = module()
    source = "9" * 40
    archive_sha = "4" * 64
    tag = "t44-backend:src-" + source
    content = tar_layer(b"public original bytes")
    payload = gzip.compress(content, mtime=0) if compressed else content
    labels = {
        "org.opencontainers.image.revision": source,
        "io.t44.source-archive-sha256": archive_sha,
    }
    config = {
        "os": "linux",
        "architecture": "amd64",
        "rootfs": {"type": "layers", "diff_ids": [m.digest(content)]},
        "config": {"Labels": labels, "Env": ["SYNTHETIC_PUBLIC_DEFAULT=1"]},
    }
    config_bytes = encoded(config)
    config_id = m.digest(config_bytes)
    blobs = {config_id: config_bytes, m.digest(payload): payload}
    config_descriptor = {
        "mediaType": "application/vnd.oci.image.config.v1+json",
        "digest": config_id,
        "size": len(config_bytes),
    }
    layer_descriptor = {
        "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip"
        if compressed
        else "application/vnd.oci.image.layer.v1.tar",
        "digest": m.digest(payload),
        "size": len(payload),
    }
    if evil == "config":
        changed = copy.deepcopy(config)
        changed["config"]["Env"] = ["SYNTHETIC_PUBLIC_DEFAULT=2"]
        data = encoded(changed)
        blobs[m.digest(data)] = data
        config_descriptor.update(digest=m.digest(data), size=len(data))
    if evil == "layer":
        changed = tar_layer(b"tampered different layer")
        blobs[m.digest(changed)] = changed
        layer_descriptor.update(digest=m.digest(changed), size=len(changed))
    descriptor_body = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": config_descriptor,
        "layers": [layer_descriptor],
    }
    descriptor_bytes = encoded(descriptor_body)
    descriptor_id = m.digest(descriptor_bytes)
    blobs[descriptor_id] = descriptor_bytes
    docker_table = [
        {
            "Config": "blobs/sha256/" + config_id.split(":")[1],
            "RepoTags": [tag],
            "Layers": ["blobs/sha256/" + m.digest(payload).split(":")[1]],
        }
    ]
    path = tmp_path / "archive.tar.gz"
    with tarfile.open(path, mode="w:gz") as archive:
        files = {
            "manifest.json": encoded(docker_table),
            **{
                "blobs/sha256/" + key.split(":")[1]: value
                for key, value in blobs.items()
            },
        }
        for name, data in files.items():
            item = tarfile.TarInfo(name)
            item.size = len(data)
            archive.addfile(item, io.BytesIO(data))
    graph = m.scan_archive(path)
    declared = {
        "alias": tag,
        "image_id": config_id,
        "revision_label": source,
        "archive_label": archive_sha,
    }
    manifest = {"source_sha": source, "source_archive_sha256": archive_sha}
    actual = {
        "Id": config_id if mode == "classic" else descriptor_id,
        "Os": "linux",
        "Architecture": "amd64",
        "Variant": "",
        "RootFS": {"Type": "layers", "Layers": [m.digest(content)]},
        "Config": {"Labels": dict(labels)},
        "Descriptor": {
            "mediaType": descriptor_body["mediaType"],
            "digest": descriptor_id,
            "size": len(descriptor_bytes),
        },
    }
    return m, graph, declared, manifest, actual


@pytest.mark.parametrize(
    "mode,compressed", [("classic", False), ("oci", False), ("oci", True)]
)
def test_exact_classic_or_OCI_config_layers_proven(tmp_path, mode, compressed):
    m, g, d, manifest, a = model(tmp_path, mode, compressed)
    result = m.prove_role(g, "backend", d, manifest, a)
    assert result["success"] and result["config_id"] == d["image_id"]
    assert result["identity_kind"] == (
        "classic-config-id"
        if mode == "classic"
        else "oci-descriptor-to-original-config"
    )


@pytest.mark.parametrize(
    "evil,reason",
    [
        ("config", "OCI_MANIFEST_CONFIG_DIFFERS"),
        ("layer", "OCI_LAYER_ENCODING_OR_UNCOMPRESSED"),
    ],
)
def test_cryptographically_wellformed_but_different_config_or_layer_rejected(
    tmp_path, evil, reason
):
    m, g, d, manifest, a = model(tmp_path, evil=evil)
    with pytest.raises(ValueError, match=reason):
        m.prove_role(g, "backend", d, manifest, a)


@pytest.mark.parametrize(
    "change",
    [
        "labels",
        "rootfs",
        "architecture",
        "descriptor_hash",
        "unknown_media",
        "original_CI_id",
        "source_label",
    ],
)
def test_actual_or_trust_identity_changes_rejected(tmp_path, change):
    m, g, d, manifest, a = model(tmp_path)
    if change == "labels":
        a["Config"]["Labels"]["extra"] = "unauthorized"
    elif change == "rootfs":
        a["RootFS"]["Layers"] = ["sha256:" + "0" * 64]
    elif change == "architecture":
        a["Architecture"] = "arm64"
    elif change == "descriptor_hash":
        a["Id"] = a["Descriptor"]["digest"] = "sha256:" + "0" * 64
    elif change == "unknown_media":
        a["Descriptor"]["mediaType"] = "application/x-unknown"
    elif change == "original_CI_id":
        d["image_id"] = "sha256:" + "0" * 64
    elif change == "source_label":
        manifest["source_sha"] = "8" * 40
    with pytest.raises(ValueError):
        m.prove_role(g, "backend", d, manifest, a)


def test_changed_blob_bytes_cannot_keep_digest_filename(tmp_path):
    m = module()
    path = tmp_path / "corrupt.tar"
    data = b"changed"
    with tarfile.open(path, "w") as archive:
        item = tarfile.TarInfo("blobs/sha256/" + "0" * 64)
        item.size = len(data)
        archive.addfile(item, io.BytesIO(data))
    with pytest.raises(ValueError, match="FILENAME_DIGEST"):
        m.scan_archive(path)
