"""Read immutable official Docker Hub metadata with normal CA verification."""

import hashlib
import json
import ssl
import urllib.request
from pathlib import Path

import certifi

context = ssl.create_default_context(cafile=certifi.where())
pin = "sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
with urllib.request.urlopen("https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/python:pull", context=context, timeout=20) as response:
    token = json.load(response)["token"]


def fetch(kind, digest):
    request = urllib.request.Request("https://registry-1.docker.io/v2/library/python/" + kind + "/" + digest,
                                     headers={"Authorization": "Bearer " + token,
                                              "Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"})
    with urllib.request.urlopen(request, context=context, timeout=20) as response:
        raw = response.read()
    assert "sha256:" + hashlib.sha256(raw).hexdigest() == digest
    return json.loads(raw)


index = fetch("manifests", pin)
child = next(value for value in index["manifests"] if value.get("platform", {}).get("os") == "linux" and value.get("platform", {}).get("architecture") == "amd64")
manifest = fetch("manifests", child["digest"])
config = fetch("blobs", manifest["config"]["digest"])
package = Path(__file__).resolve().parents[3] / "deployment-preparation-r30/tmp/761_deployment_preparation_r30/official-artifact-12880320744"
bundle = json.loads((package / "backend-bundle-manifest.json").read_text())
assert config["rootfs"]["diff_ids"] == bundle["official_python"]["diff_ids"] and len(config["rootfs"]["diff_ids"]) == 4
print(json.dumps(dict(registry="registry-1.docker.io/library/python", pinned_index_digest=pin,
                     linux_amd64_manifest_digest=child["digest"], config_digest=manifest["config"]["digest"],
                     official_diff_ids=config["rootfs"]["diff_ids"], bundle_ordered_base_prefix_equal=True,
                     token_saved_or_printed=False, TLS_CA_verification_disabled=False), indent=2))
