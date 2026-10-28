"""Resume tool provenance/time/source guards; no Docker, SUT or cloud execution."""

import ast
import copy
import importlib.util
import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "tmp/793_deployment_resume"
SPEC = importlib.util.spec_from_file_location(
    "resume_profile", ROOT / "deployment/cloud-reuse/derive-resume-profile.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
SOURCE = "22f666e25d2b7280224e58eb1c91cf6be0077ac7"
STOP = "2026-10-28T07:30:00Z"


def values(text):
    return {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse(text).body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id
        in {
            "SOURCE",
            "TARGET",
            "HARDSTOP",
            "SOURCE_COUNT",
            "BUILDER_SHA",
            "GENERATOR_SHA",
            "HELPER_SHA",
        }
    }


def test_exact_original_templates_and_sha_chain_not_modified():
    templates = M.checked_templates()
    before = {name: M.digest(text.encode()) for name, text in templates.items()}
    result = M.derive_texts(templates, SOURCE, STOP, 49)
    builder, generation, stream, receiver = [
        values(result[name])
        for name in (
            "backend-upgrade.py",
            "generation.py",
            "resource-stream.py",
            "source-artifact-receive.py",
        )
    ]
    assert builder["TARGET"] == generation["SOURCE"] == stream["SOURCE"] == SOURCE
    assert generation["HARDSTOP"] == stream["HARDSTOP"] == STOP
    assert generation["SOURCE_COUNT"] == 49
    assert (
        generation["BUILDER_SHA"]
        == receiver["HELPER_SHA"]
        == M.digest(result["backend-upgrade.py"].encode())
    )
    assert stream["GENERATOR_SHA"] == M.digest(result["generation.py"].encode())
    assert {
        name: M.digest(text.encode()) for name, text in M.checked_templates().items()
    } == before


@pytest.mark.parametrize("changed", ["TARGET", "HARDSTOP", "preimage-count"])
def test_changed_or_ambiguous_preimage_refused(changed):
    templates = copy.deepcopy(M.checked_templates())
    if changed == "TARGET":
        templates["backend-upgrade-v2.py"] = templates["backend-upgrade-v2.py"].replace(
            M.OLD_TARGET, "0" * 40
        )
    elif changed == "HARDSTOP":
        templates["generation-f4.py"] = templates["generation-f4.py"].replace(
            M.OLD_STOP, "changed"
        )
    else:
        templates["generation-f4.py"] += "\n# len(expected) != 53\n"
    with pytest.raises(ValueError, match="PREIMAGE_COUNT"):
        M.derive_texts(templates, SOURCE, STOP, 53)


@pytest.mark.parametrize(
    "value",
    ["2026-10-28T07:30:00+00:00", "2026-10-28T07:00:00Z", "2026-10-29T08:00:00Z"],
)
def test_ambiguous_past_or_unbounded_window_refused(value):
    now = datetime(2026, 10, 28, 7, 0, tzinfo=UTC)
    with pytest.raises(ValueError):
        M.deadline(value, now)


def test_explicit_bounded_future_window():
    now = datetime(2026, 10, 28, 7, 0, tzinfo=UTC)
    assert M.deadline("2026-10-28T07:30:00Z", now).hour == 7
    assert M.deadline("2026-10-28T19:00:00Z", now).hour == 19


@pytest.mark.parametrize(
    "source,count",
    [("codex/integration", 53), ("a" * 39, 53), (SOURCE, True), (SOURCE, 0)],
)
def test_moving_ref_or_fake_count_refused(source, count):
    with pytest.raises(ValueError):
        M.derive_texts(M.checked_templates(), source, STOP, count)


def test_source_identity_and_frozen_contract_comparison_preserved():
    builder = M.reviewed_builder()
    old = builder.tree(ROOT, builder.BASE, builder.FROZEN)
    new = builder.tree(ROOT, SOURCE, builder.FROZEN)
    assert builder.compare_frozen(old, new)["equal"]
    changed = copy.deepcopy(new)
    changed[0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="DEPENDENCIES_REST_DDL"):
        builder.compare_frozen(old, changed)


def test_real_git_source_package_and_five_file_receiver(tmp_path):
    # tmp_path can be outside project under a platform alias; use only a project-owned fixture.
    del tmp_path
    with tempfile.TemporaryDirectory(dir=FOLDER) as directory:
        root = Path(directory).resolve()
        stop = (datetime.now(UTC) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        args = SimpleNamespace(
            repository=ROOT, source=SOURCE, stop_utc=stop, output=root / "profile"
        )
        before = {name: M.digest((M.HERE / name).read_bytes()) for name in M.TEMPLATES}
        derived = M.derive(args)
        profile = root / "profile/profile.json"
        metadata = json.loads(profile.read_bytes())
        assert metadata["source_file_count"] == 53
        assert derived["cloud_or_SUT_executed"] is False
        packaged = M.package(
            SimpleNamespace(
                repository=ROOT,
                profile=profile,
                profile_sha256=derived["profile_sha256"],
                output=root / "package",
            )
        )
        receiver_spec = importlib.util.spec_from_file_location(
            "derived_receiver", root / "profile/source-artifact-receive.py"
        )
        receiver = importlib.util.module_from_spec(receiver_spec)
        receiver_spec.loader.exec_module(receiver)
        data = receiver.inspect_zip(
            Path(packaged["artifact"]), packaged["sha256"], packaged["manifest_sha256"]
        )
        assert len(data) == 5
        assert json.loads(data["source-manifest.json"])["source_sha"] == SOURCE
        assert {
            name: M.digest((M.HERE / name).read_bytes()) for name in M.TEMPLATES
        } == before
        with pytest.raises(FileExistsError):
            M.derive(args)
        bad_args = SimpleNamespace(
            repository=ROOT,
            profile=profile,
            profile_sha256="0" * 64,
            output=root / "bad",
        )
        with pytest.raises(ValueError, match="ROOT_PINNED"):
            M.package(bad_args)


def test_template_sha_change_refused_without_import():
    with (
        patch.object(M, "TEMPLATES", {"backend-upgrade-v2.py": "0" * 64}),
        pytest.raises(ValueError, match="EXACT_REVIEWED_TEMPLATE_SHA"),
    ):
        M.checked_templates()


def test_derived_generation_checks_the_complete_real_count_and_nonroot_boundary():
    texts = M.derive_texts(M.checked_templates(), SOURCE, STOP, 49)
    with tempfile.TemporaryDirectory(dir=FOLDER) as directory:
        path = Path(directory) / "generation.py"
        path.write_text(texts["generation.py"])
        spec = importlib.util.spec_from_file_location("derived_generation_check", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        expected = [
            {
                "path": f"backend/t44/example{i}.py",
                "bytes": i,
                "sha256": "a" * 64,
                "mode": 0o644,
            }
            for i in range(49)
        ]
        probe = {
            "files": copy.deepcopy(expected),
            "uid": 10001,
            "business_env_absent": True,
        }
        assert module.exact_files(probe, expected)["files"] == 49
        for field, value in (
            ("uid", 0),
            ("business_env_absent", False),
            ("files", expected[:-1]),
        ):
            bad = copy.deepcopy(probe)
            bad[field] = value
            with pytest.raises(ValueError, match="COMPLETE_SOURCE_FILES"):
                module.exact_files(bad, expected)
        bad = copy.deepcopy(probe)
        bad["files"][0]["mode"] = 0o600
        with pytest.raises(ValueError, match="COMPLETE_SOURCE_FILES"):
            module.exact_files(bad, expected)
