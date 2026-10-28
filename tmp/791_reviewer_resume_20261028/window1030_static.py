"""Static reviewer window delta/package checks; no cloud, DB, private input or load."""

import ast
import base64
import gzip
import hashlib
import io
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

COMMIT = "a8c1f7a26892f845d9d415076107aa77f17ac2ac"
DEPLOY = "4de69da8db08577762586a5ee28cfc2d0cf398f8"
BASE = "tmp/790_backend_contrast_20261028/"
V3 = BASE + "v3-window1030/"
OWNED = Path("/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/backend-resume-20261028")


def raw(path, commit=COMMIT):
    return subprocess.check_output(["git", "show", commit + ":" + path])


def sha(value):
    return hashlib.sha256(value).hexdigest()


old_manifest_raw, manifest_raw = raw(BASE + "manifest.json"), raw(V3 + "manifest.json")
old_manifest, manifest = json.loads(old_manifest_raw), json.loads(manifest_raw)
assert sha(old_manifest_raw) == "640b3d386a756547d940b638ef6ccfc9bc49adaa2c071a2794aca8464b2edd84"
assert sha(manifest_raw) == "0ef08aab3e14887b703c9a2fa5e5265d60fbbcb4172d1d6deb20b5f746df048a"
assert manifest["tool_version"] == 3 and manifest["window_utc"] == "2026-10-28T10:30:00Z"
assert manifest["supersedes_manifest_sha256"] == sha(old_manifest_raw)
assert set(manifest["files"]) == set(old_manifest["files"]) and len(manifest["files"]) == 7
deltas = {}
for name, info in manifest["files"].items():
    before, after = raw(BASE + name), raw(V3 + name)
    old = b"HARDSTOP = datetime(2026, 10, 28, 7, 30, tzinfo=UTC)"
    new = b"HARDSTOP = datetime(2026, 10, 28, 10, 30, tzinfo=UTC)"
    changes = int(name in ("790_bootstrap.py", "edge/790_http.py"))
    assert before.count(old) == changes
    assert after == (before.replace(old, new, 1) if changes else before)
    assert info == {"bytes": len(after), "sha256": sha(after)}
    deltas[name] = {"only_authorized_hardstop_change": bool(changes), "otherwise_byte_identical": True, "sha256": sha(after)}
    ast.parse(after, feature_version=(3, 10) if name in ("790_bootstrap.py", "790_host.py", "790_load.py") else None)
before, after = raw(BASE + "transport/790_transfer.py"), raw(V3 + "transport/790_transfer.py")
old = b"STOP = datetime(2026, 10, 28, 7, 30, tzinfo=UTC)"
new = b"STOP = datetime(2026, 10, 28, 10, 30, tzinfo=UTC)"
assert before.count(old) == 1 and after == before.replace(old, new, 1)
assert sha(after) == "7e2dfb5b4c4fd3766769d4c5f15ac65fa8b61e7286e09ee402ff10fa650816f3"
ast.parse(after, feature_version=(3, 10))

installer_sizes = []
installed = {}
for number in (1, 2, 3):
    command = raw(f"agents/backend/contrast-20261028/split-v3-window1030-install-{number}.txt")
    code = command.decode().split("\n", 1)[1].rsplit("\n", 2)[0]
    tree = ast.parse(code)
    record = next(node.value for node in tree.body if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "record")
    record = json.loads(ast.literal_eval(record.args[0]))
    assert record["part"] == number and record["manifest_sha256"] == sha(manifest_raw)
    for item in record["files"]:
        with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(item["data"], validate=True))) as stream:
            content = stream.read(item["bytes"] + 1)
        assert len(content) == item["bytes"] and sha(content) == item["sha256"]
        assert content == raw(V3 + item["name"])
        assert item["name"] not in installed
        installed[item["name"]] = sha(content)
    installer_sizes.append({"part": number, "raw_bytes": len(command), "base64_bytes": len(base64.b64encode(command)), "plus_256_description": len(base64.b64encode(command)) + 256})
assert set(installed) == set(manifest["files"]) | {"manifest.json"}

dp = "agents/deployment/resume-20261028/window1030/"
profile = json.loads(raw(dp + "profile/profile.json", DEPLOY))
expected = {"generation.py": "4672a5838879ab1fde599c45d464906600373fdb38da654e21879881204d11a8", "profile.json": "222c97a1a3711aafcb583f8683009411702f8d91a4cd65a601de631572da0b80", "resource-stream.py": "e5b0324e1576f901cbacb1ba9b973096c6b575318cc9f336a6f7183ce94ca115"}
for name, digest in expected.items():
    assert sha(raw(dp + "profile/" + name, DEPLOY)) == digest
assert profile["source_sha"] == manifest["product"] and profile["stop_utc"] == manifest["window_utc"]
plan = json.loads(raw(dp + "prepare-plan.PUBLIC.json", DEPLOY))["p16"]
assert plan["run_id"] == "r28p16gen02" and plan["output"] == "/root/t44-r9/campaign-r28p16-02"
assert plan["p_workers"] == 16 and plan["stop_utc"] == "2026-10-28T10:30:00Z"
assert plan["argv"][1].startswith("/root/t44-r9/resume-20261028-02/")

proofs = {}
for name in ("verification.json", "allowlist-proof.json", "installer-verification.json", "local-final.xml"):
    value = (OWNED / V3 / name).read_bytes()
    proofs[name] = sha(value)
local = ET.fromstring((OWNED / V3 / "local-final.xml").read_bytes())
cases = list(local.iter("testcase"))
transport = [c for c in cases if ".transport." in c.attrib.get("classname", "")]
assert len(cases) == 46 and len(transport) == 13
assert not any(c.find(kind) is not None for c in cases for kind in ("failure", "error", "skipped"))
checks = json.loads((OWNED / V3 / "installer-verification.json").read_bytes())["six_local_subprocess_checks"]
assert len(checks) == 6
print(json.dumps({"tool_commit": COMMIT, "deployment_commit": DEPLOY, "manifest_sha256": sha(manifest_raw), "seven_file_deltas": deltas, "transport_only_stop_replacement": True, "600s_TTL_abort_thresholds_cohorts_unchanged": True, "installer_payloads_match_all_seven_and_manifest": True, "installer_command_sizes": installer_sizes, "profile_hashes_verified": expected, "new_namespace_plan": plan["run_id"], "owner_local_case_counts": {"diagnostic": 33, "transport": 13, "installer_records": 6}, "owner_local_proof_snapshot_sha256": proofs, "scope": "static/raw/package proof only; no new tests, cloud, network or SUT execution"}, indent=2))
