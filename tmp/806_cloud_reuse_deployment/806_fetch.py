"""Private public-object downloader guards with in-memory HTTP doubles only."""

import hashlib
import importlib.util
import io
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "public_fetch", ROOT / "deployment/cloud-reuse/public-bundle-fetch.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Response(io.BytesIO):
    status = 200


class Opener:
    def __init__(self, data):
        self.data = data

    def open(self, request, timeout):
        return Response(self.data[request.full_url.rsplit("/", 1)[1]])


def setup(tmp_path, m, monkeypatch, corrupt=False):
    value = b"public synthetic bytes"
    manifest = json.dumps(
        {
            "schema": 1,
            "parts": [
                {
                    "name": "payload.part0000",
                    "bytes": len(value),
                    "sha256": hashlib.sha256(value).hexdigest(),
                }
            ],
        }
    ).encode()
    data = {
        "parts-manifest.json": manifest,
        "payload.part0000": b"x" * len(value) if corrupt else value,
    }
    monkeypatch.setattr(m.urllib.request, "build_opener", lambda *a: Opener(data))
    return SimpleNamespace(
        server="http://10.1.1.1:18444",
        kind="parts",
        manifest_sha256=hashlib.sha256(manifest).hexdigest(),
        stop_utc=(datetime.now(UTC) + timedelta(seconds=300)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        output=tmp_path / "new",
    )


def test_valid_hash_bound_objects_fetched_without_credentials(tmp_path, monkeypatch):
    m = module()
    args = setup(tmp_path, m, monkeypatch)
    result = m.fetch(args)
    assert result["success"] and not result["credentials_or_tokens_sent"]
    assert (args.output / "payload.part0000").read_bytes() == b"public synthetic bytes"


def test_corrupt_bytes_rejected_and_partial_retained(tmp_path, monkeypatch):
    m = module()
    args = setup(tmp_path, m, monkeypatch, True)
    with pytest.raises(ValueError, match="COMPLETE_OBJECT"):
        m.fetch(args)
    assert (args.output / "payload.part0000").exists()


@pytest.mark.parametrize(
    "server",
    ["http://8.8.8.8:18444", "http://synthetic-user:synthetic-pass@10.1.1.1:18444"],
)
def test_public_or_credential_URL_rejected_before_network(
    tmp_path, monkeypatch, server
):
    m = module()
    args = setup(tmp_path, m, monkeypatch)
    args.server = server
    monkeypatch.setattr(
        m.urllib.request,
        "build_opener",
        lambda *a: pytest.fail("forbiddenURL reached network"),
    )
    with pytest.raises(ValueError, match="WITHOUT_CREDENTIALS"):
        m.fetch(args)
    assert not args.output.exists()
