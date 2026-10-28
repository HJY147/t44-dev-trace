"""Owned local tool guards; no cloud operations or independent cases."""

import ast
import importlib.util
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

UTC = timezone.utc  # noqa: UP017 -- validate host Python 3.10 compatibility.
HERE = Path(__file__).parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bootstrap = load(HERE / "790_bootstrap.py", "owned_bootstrap790")


@pytest.fixture
def real_derived_binding(tmp_path):
    public = Path(os.environ["T44_CONTRAST_PUBLIC_DEPLOYMENT"])
    derive = load(public / "derive-resume-profile.py", "owned_public_profile790")
    texts = derive.derive_texts(
        derive.checked_templates(), bootstrap.SOURCE, "2026-10-28T07:30:00Z", 53
    )
    tree = ast.parse(texts["generation.py"])
    prepare = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "prepare")
    binding = next(
        n.value
        for n in ast.walk(prepare)
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "binding"
    )
    hashes = []

    def sha(path):
        hashes.append(path.name)
        return "c" * 64

    context = {
        "lib": SimpleNamespace(stamp=lambda: "2026-10-28T05:00:00Z"),
        "role": "p",
        "project": "t44-cloud-r28p7gen01-p",
        "database": "t44c_r28p7gen01_p",
        "SOURCE": bootstrap.SOURCE,
        "OLD_SOURCE": "935ab5b93bea788672c2b4a088c79cfeed848954",
        "SOURCE_COUNT": 53,
        "phase": tmp_path / "p",
        "sha": sha,
        "manifest": {"source_archive_sha256": "a" * 64},
        "args": SimpleNamespace(
            source_manifest_sha256="b" * 64,
            upgrade_binding_sha256="d" * 64,
            output=tmp_path,
            stop_utc="2026-10-28T07:30:00Z",
        ),
        "proofs": {
            "backend": {"actual_id": "sha256:" + "e" * 64, "config_id": "sha256:" + "f" * 64}
        },
        "images": {"backend": {"alias": "owned-backend"}, "web": {"alias": "owned-web"}},
        "upgrade": {"frozen_file_set_sha256": "a" * 64},
        "address": "172.21.182.245",
        "tls_port": 19445,
        "workers": 7,
        "tls": {"ca_sha256": "a" * 64},
    }
    result = eval(compile(ast.Expression(binding), "real-derived-binding", "eval"), context)
    assert "actual-source-files.json" in hashes and "actual53-source-files.json" not in hashes
    assert result["source_file_count"] == 53
    assert "source_actual_proof_sha256" in result and "source53_actual_proof_sha256" not in result
    return result


def test_real_derived_binding_shape_and_live_gate(real_derived_binding):
    assert (
        bootstrap.validate_binding(real_derived_binding, datetime(2026, 10, 28, 5, tzinfo=UTC))
        == "r28p7gen01"
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_sha", "935ab5b93bea788672c2b4a088c79cfeed848954"),
        ("generation_kind", "exact-f4-production-entry-generation"),
        ("phase", "f"),
        ("database", "t44c_old_p"),
        ("api_workers", 16),
        ("entrypoint", "810_stage:app_factory"),
        ("profiling", True),
        ("source_file_count", True),
        ("stop_utc", "2026-10-28T08:00:00Z"),
    ],
)
def test_wrong_binding_rejected(real_derived_binding, key, value):
    with pytest.raises(ValueError):
        bootstrap.validate_binding(
            {**real_derived_binding, key: value}, datetime(2026, 10, 28, 5, tzinfo=UTC)
        )


def test_expired_and_near_deadline_rejected(real_derived_binding):
    for hour, minute in [(7, 29), (8, 0)]:
        with pytest.raises(ValueError):
            bootstrap.validate_binding(
                real_derived_binding, datetime(2026, 10, 28, hour, minute, tzinfo=UTC)
            )


def test_host_310_syntax_and_utc_parser():
    raw = (HERE / "790_bootstrap.py").read_text()
    tree = ast.parse(raw, feature_version=(3, 10))
    assert not any(
        isinstance(n, ast.ImportFrom)
        and n.module == "datetime"
        and any(a.name == "UTC" for a in n.names)
        for n in ast.walk(tree)
    )
    assert bootstrap.stamp("2026-10-28T07:30:00Z") == datetime(2026, 10, 28, 7, 30, tzinfo=UTC)
    with pytest.raises(ValueError):
        bootstrap.stamp("2026-10-28T07:30:00")


def test_private_file_symlink_and_output_preservation(tmp_path):
    path = tmp_path / "owned.json"
    bootstrap.save(path, {"owned": True})
    with pytest.raises(FileExistsError):
        bootstrap.save(path, {"owned": False})
    assert bootstrap.raw(path, True) == b'{\n  "owned": true\n}\n'
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(OSError):
        bootstrap.raw(link, True)
    path.chmod(0o644)
    with pytest.raises(ValueError):
        bootstrap.raw(path, True)
