"""Offline upgrade rejection guards; no Docker, DB, application imports or cloud access."""

import copy
import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "backend_upgrade", ROOT / "deployment/cloud-reuse/backend-upgrade.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def frozen(m):
    return [
        {
            "path": "backend/requirements.lock",
            "bytes": 12,
            "sha256": m.LOCK_SHA,
            "mode": 0o644,
        },
        {
            "path": "specs/database/schema.sql",
            "bytes": 9,
            "sha256": "a" * 64,
            "mode": 0o644,
        },
        {
            "path": "specs/contracts/openapi.json",
            "bytes": 9,
            "sha256": "b" * 64,
            "mode": 0o644,
        },
        {"path": "frontend/src/main.ts", "bytes": 9, "sha256": "c" * 64, "mode": 0o644},
    ]


@pytest.mark.parametrize("index", range(4))
def test_changed_dependency_ddl_rest_or_frontend_disallows_reuse(index):
    m = module()
    before = frozen(m)
    after = copy.deepcopy(before)
    after[index]["sha256"] = "d" * 64
    with pytest.raises(ValueError, match="DEPENDENCIES_REST_DDL_FRONTEND"):
        m.compare_frozen(before, after)


def test_nondefault_lock_cannot_be_relabelled_as_unchanged():
    m = module()
    rows = frozen(m)
    rows[0]["sha256"] = "e" * 64
    with pytest.raises(ValueError, match="EXACT_EXISTING_HASH_LOCK"):
        m.compare_frozen(rows, rows)


def archive(extra=None):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as writer:
        info = tarfile.TarInfo("backend/t44/__init__.py")
        info.mode = 0o644
        info.size = 1
        writer.addfile(info, io.BytesIO(b"#"))
        if extra:
            info = tarfile.TarInfo(extra)
            info.size = 1
            if extra.endswith("symlink"):
                info.type = tarfile.SYMTYPE
                info.linkname = "/etc/passwd"
            writer.addfile(info, io.BytesIO(b"x"))
    return output.getvalue()


@pytest.mark.parametrize(
    "extra",
    [
        "backend/t44/__init__.py",
        "backend/t44/symlink",
        "backend/t44/../../../escape",
        "private/env",
    ],
)
def test_unsafe_duplicate_link_or_unapproved_archive_file_rejected(extra):
    with pytest.raises(ValueError):
        module().archive_files(archive(extra))


def test_container_exact_file_proof_detects_deleted_old_module_surviving():
    m = module()
    rows, _ = m.archive_files(archive())
    observed = {"uid": 10001, "database_env_absent": True, "files": copy.deepcopy(rows)}
    assert m.verify_product_files(observed, rows)["complete_exact_file_set"]
    observed["files"].append(
        {
            "path": "backend/t44/domain/commands.py",
            "sha256": "f" * 64,
            "bytes": 1,
            "mode": 0o644,
        }
    )
    with pytest.raises(ValueError, match="CONTAINER_PRODUCT_FILE_SET"):
        m.verify_product_files(observed, rows)


@pytest.mark.parametrize("change", ["missing", "bytes", "mode", "uid", "business-env"])
def test_incomplete_modified_or_unreadable_actual_product_rejected(change):
    m = module()
    rows, _ = m.archive_files(archive())
    seen = {"uid": 10001, "database_env_absent": True, "files": copy.deepcopy(rows)}
    if change == "missing":
        seen["files"] = []
    elif change in {"bytes", "mode"}:
        seen["files"][0][change] = 0
    elif change == "uid":
        seen["uid"] = 0
    else:
        seen["database_env_absent"] = False
    with pytest.raises(ValueError, match="CONTAINER_PRODUCT_FILE_SET"):
        m.verify_product_files(seen, rows)


def test_build_rejects_untrusted_package_before_docker(tmp_path, monkeypatch):
    m = module()
    tmp_path.chmod(0o700)
    p = tmp_path / "source-manifest.json"
    p.write_text("{}")
    p.chmod(0o600)
    monkeypatch.setattr(
        m, "command", lambda *a: pytest.fail("untrusted source reached Docker")
    )
    with pytest.raises(ValueError, match="PINNED_SOURCE_MANIFEST"):
        m.source_package(tmp_path, "0" * 64)


@pytest.mark.parametrize("field", ["User", "Cmd", "Labels", "Env"])
def test_new_image_cannot_change_runtime_or_smuggle_business_configuration(
    field, monkeypatch
):
    m = module()
    original = {
        "User": "10001:10001",
        "WorkingDir": "/app",
        "Cmd": ["python", "-m", "uvicorn"],
        "Env": ["PYTHONPATH=/app/backend"],
        "Labels": {"revision": "new"},
    }
    altered = copy.deepcopy(original)
    if field == "User":
        altered[field] = "0:0"
    elif field == "Cmd":
        altered[field] = ["python", "diagnostic.py"]
    elif field == "Env":
        altered[field].append("DATABASE_URL=must-never-be-in-image")
    else:
        altered[field] = {"revision": "old"}
    result = {"Os": "linux", "Architecture": "amd64", "Config": altered}
    monkeypatch.setattr(m, "command", lambda *a: json.dumps([result]).encode())
    with pytest.raises(ValueError):
        m.inspect_configuration("new:never-accessed", original["Labels"], original)


def test_offline_replacement_deletes_old_tree_before_full_copy_and_restores_user():
    text = module().dockerfile().decode().splitlines()
    assert text[1:4] == [
        "USER 0:0",
        "RUN rm -rf /app/backend/t44",
        "COPY backend/t44/ /app/backend/t44/",
    ]
    assert text[-1] == "USER 10001:10001"
    assert not any("pip" in line or "curl" in line or "apt" in line for line in text)
    assert not any(line.startswith(("ARG ", "CMD ", "ENTRYPOINT ")) for line in text)
