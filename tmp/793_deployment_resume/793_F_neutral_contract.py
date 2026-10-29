"""Adapter integration with the actual frozen status shape and permitted T15 public schema."""

import ast
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "agents/deployment/resume-20261028/finalize-functional/06-F-neutral-proof-only.sh"


def tree():
    text = SCRIPT.read_text().split("python3 - <<'PYFNEUTRAL'\n", 1)[1].rsplit("PYFNEUTRAL", 1)[0]
    return ast.parse(text)


def test_status_keys_match_actual_frozen_operate_status_contract(monkeypatch):
    path = ROOT / "agents/deployment/resume-20261028/window1030/profile/generation.py"
    spec = importlib.util.spec_from_file_location("F_status_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lib = SimpleNamespace(PERSISTENT=["api"], receipt=lambda _phase, action, **fields: {"action": action, **fields})
    monkeypatch.setattr(module, "phase_binding", lambda *_: (lib, {}))
    monkeypatch.setattr(module, "live", lambda *_: {"role": "api", "absent": True})
    status = module.operate(SimpleNamespace(action="status", phase_dir=Path("/synthetic"), binding_sha256="a" * 64))
    accessed = {ast.literal_eval(node.slice) for node in ast.walk(tree())
                if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "status"
                and isinstance(node.slice, ast.Constant)}
    assert "source_sha" not in status
    assert accessed <= set(status)


def test_exact_T15_identity_required_properties_no_unapproved_private_read():
    path = Path('/Users/yang/Desktop/nothing/软件开发大作业/tmp/792_independent_resume_20261028/PUBLIC/792-T15-new-F-private-input-schema.PUBLIC.json')
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "f8fe6a24b524ea7d9aa406ca9f7cbcd241c4cea602014cd778de173fcdfd187b"
    schema = json.loads(raw)["properties"]["sut_identity"]
    expression = next(node.value for node in tree().body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "identity" for target in node.targets))
    assert {ast.literal_eval(key) for key in expression.keys} == set(schema["required"]) == set(schema["properties"])


def test_original_start_bundle_unchanged_and_proves_all_five_real_actions():
    node = next(node for node in tree().body if isinstance(node, ast.Assign)
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "START_PAYLOAD")
    raw = gzip.decompress(base64.b64decode(ast.literal_eval(node.value), validate=True))
    assert len(raw) == 9786 and hashlib.sha256(raw).hexdigest() == "1297a0155bc9682685cc012129641181014084387f36a8fa37d16c436313404e"
    rows = [json.loads(line) for line in raw.splitlines()]
    actual = [row for row in rows if row.get("success") is True]
    assert [row["action"] for row in actual] == ["persistent_timer_armed", "config", "infra", "migrate", "idle"]
    assert actual[-1]["host_https"]["strict_CA_and_IP_verified"] is True
