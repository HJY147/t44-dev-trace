"""Compare new repository helper with the exact historical cloud factory, no cloud execution."""

import hashlib
import importlib.util
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
OLD_SHA = "daaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea"
OLD_COMMIT = "fb0a433494ff8c23124e9901386ee1e991059c45"
FACTORY = ROOT / "deployment/cloud-reuse/app-campaign.py"
ROLES = ["backend", "web", "mysql", "rabbitmq", "nginx"]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def factories():
    raw = subprocess.check_output([
        "git", "-C", str(ROOT), "show", OLD_COMMIT + ":deployment/cloud-reuse/app-campaign.py"
    ])
    assert hashlib.sha256(raw).hexdigest() == OLD_SHA
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp/793_deployment_resume") as directory:
        original = Path(directory) / "historical_factory.py"
        original.write_bytes(raw)
        yield load(original, "old_factory_equivalence"), load(FACTORY, "new_factory_equivalence")


def images():
    return {role: {"alias": "synthetic-" + role + ":checked"} for role in ROLES}


@pytest.mark.parametrize("workers", [4, 7, 16])
def test_full_compose_and_tls_profile_outputs_equal(factories, workers):
    old, new = factories
    args = (Path("/root/t44-r9/example-new-phase"), "172.20.1.2", 19445, 18181, workers)
    assert old.compose_profile(images(), *args) == new.compose_profile(images(), *args)
    assert old.nginx() == new.nginx()


def test_alias_lookup_order_and_dynamic_mapping_capture_equal(factories):
    class ChangingAliases(dict):
        def __init__(self):
            super().__init__(images())
            self.calls = []

        def __getitem__(self, role):
            self.calls.append(role)
            value = super().__getitem__(role)
            return {"alias": value["alias"] + "-lookup" + str(len(self.calls))}

    old, new = factories
    old_images, new_images = ChangingAliases(), ChangingAliases()
    args = (Path("/root/t44-r9/example-new-phase"), "172.20.1.2", 19445, 18181, 7)
    assert old.compose_profile(old_images, *args) == new.compose_profile(new_images, *args)
    assert old_images.calls == new_images.calls
    assert old_images.calls == ["backend", "mysql", "rabbitmq", "web", "nginx"]


@pytest.mark.parametrize("role", ["backend", "nginx"])
def test_missing_alias_exception_unchanged(factories, role):
    args = (Path("/root/t44-r9/example-new-phase"), "172.20.1.2", 19445, 18181, 7)
    errors = []
    for factory in factories:
        value = images()
        del value[role]
        with pytest.raises(KeyError) as error:
            factory.compose_profile(value, *args)
        errors.append((type(error.value), error.value.args))
    assert errors[0] == errors[1]


def test_repository_factory_is_new_identity_while_old_templates_remain_pinned():
    assert hashlib.sha256(FACTORY.read_bytes()).hexdigest() != OLD_SHA
    text = (ROOT / "deployment/cloud-reuse/generation-f4.py").read_text()
    assert 'FACTORY_SHA = "' + OLD_SHA + '"' in text
    module = load(ROOT / "deployment/cloud-reuse/derive-resume-profile.py", "profile_template_check")
    assert len(module.checked_templates()) == 4
