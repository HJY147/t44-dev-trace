"""Real cross-owner PUBLIC bytes; no QA cases/private code or cloud operations."""

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "agents/backend/neutral-final-20261029"
PUBLIC = Path(
    "/Users/yang/Desktop/nothing/软件开发大作业/tmp/753_independent_final_20261029/PUBLIC"
)


def test_packet_legacy_load_field_matches_public_adapter_target_and_original_cloud_identity():
    build_path = CODE / "source-profile.BUILD_UNAPPROVED.PUBLIC.json"
    build_raw = build_path.read_bytes()
    assert (
        hashlib.sha256(build_raw).hexdigest()
        == "c394542e393879b25042de9deee9c2263ec2ab003db8c916e21425d03f9c2f44"
    )
    profile = json.loads(build_raw)
    projection = (
        ROOT / "agents/deployment/cloud-reuse-20261025/image-proof-root-summary-projection.json"
    ).read_bytes()
    assert (
        hashlib.sha256(projection).hexdigest()
        == "ce562c117428face0b421e06b33c361b291cab26d8d3a51d24484dbd0841da2a"
    )
    python = json.loads(projection)["load"]["roles"]["python"]
    adapter = (PUBLIC / "ADAPTER_753.py").read_bytes()
    assert (
        hashlib.sha256(adapter).hexdigest()
        == "15b91449627218b011fff0768b1f84fe2e9274ec06c0486fd28f2ae9dce03f5d"
    )
    constant = next(
        ast.literal_eval(n.value)
        for n in ast.parse(adapter).body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "LOAD" for t in n.targets)
    )
    target = json.loads((PUBLIC / "TARGET_PROFILE_753.template.json").read_bytes())
    assert profile["load_python_config_id"] == python["config_id"]
    assert python["actual_id"] == constant == target["load_runtime_image_config_digest"]
    assert python["actual_id"] != python["config_id"]
    # Add only the proposed new target field to a copy; keep actual build/root flags false.
    profile["load_python_expected_runtime_id"] = python["actual_id"]
    tree = ast.parse((CODE / "assemble.py").read_text())
    identity = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Dict)
        and {k.value for k in n.keys if isinstance(k, ast.Constant)}
        >= {"sut_image_config_digest", "load_runtime_image_config_digest"}
    )
    template = json.loads((CODE / "NEUTRAL_753.template.json").read_bytes())
    result = eval(
        compile(ast.Expression(identity), "real-assemble-identity-expression", "eval"),
        {"profile": profile, "template": template},
    )
    assert result["load_runtime_image_config_digest"] == constant
    assert profile["load_python_config_id"] != result["load_runtime_image_config_digest"]
    assert profile["root_approved"] is False and profile["actual_loaded"] is False
