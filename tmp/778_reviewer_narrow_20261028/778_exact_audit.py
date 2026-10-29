"""Review exact Git objects and byte chains; no cloud, HTTP or private evidence."""

import ast
import base64
import copy
import gzip
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
CANDIDATE = "5cd0ad43d93bb9066e67bda04337815e6f6fa1b1"
P_OLD = "20eb4ae340375a0b687324df15dacf11e2a73c0b"
P_NEW = "7779681010de99cbb4d5946ded9c4bcd5f8ae132"
D_OLD = "e1bfc9e7beaab0b17991a139854e31d8937c7f41"
D_NEW = "d7b65303f67075c2239584d61c18ace65e4addfa"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def source(commit, name):
    return git("show", f"{commit}:{name}")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def tree(node):
    return ast.dump(node, include_attributes=False)


class Substitute(ast.NodeTransformer):
    def __init__(self, names):
        self.names = names

    def visit_Name(self, node):
        return copy.deepcopy(self.names.get(node.id, node))


def product_proof(filename, helper):
    before = ast.parse(source(BASE, filename))
    after = ast.parse(source(CANDIDATE, filename))
    cls = next(n for n in after.body if isinstance(n, ast.ClassDef))
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == helper)
    cls.body.remove(method)
    calls = []

    class Inline(ast.NodeTransformer):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and node.func.attr == helper:
                assert helper == "_assessment_versions" and len(node.args) == 2
                assert isinstance(method.body[0], ast.Return) and len(method.body) == 1
                calls.append(node.func.attr)
                return Substitute(dict(zip([a.arg for a in method.args.args[1:]], node.args))).visit(
                    copy.deepcopy(method.body[0].value)
                )
            return self.generic_visit(node)

        def visit_Assign(self, node):
            call = node.value
            if helper == "_editable_task" and isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == helper:
                assert helper == "_editable_task" and len(call.args) == 3
                assert tree(node.targets[0]) == tree(ast.Name(id="row", ctx=ast.Store()))
                assert isinstance(method.body[-1], ast.Return)
                assert tree(method.body[-1].value) == tree(ast.Name(id="row", ctx=ast.Load()))
                calls.append(call.func.attr)
                substitution = Substitute(dict(zip([a.arg for a in method.args.args[1:]], call.args)))
                return [substitution.visit(copy.deepcopy(n)) for n in method.body[:-1]]
            return self.generic_visit(node)

    after = Inline().visit(after)
    assert tree(before) == tree(after), filename
    return {"file": filename, "helper": helper, "inlined_calls": len(calls), "whole_module_AST_equal_after_exact_inlining": True}


def main():
    OUT.mkdir(exist_ok=True)
    report = {"operator": "AI reviewer", "cloud_or_SUT_or_independent_private_access": False}
    changed = git("diff", "--name-only", BASE, CANDIDATE, "--", "backend", "frontend").decode().splitlines()
    assert changed == ["backend/t44/services/reviews.py", "backend/t44/services/tasks.py"]
    report["product"] = [product_proof(changed[0], "_assessment_versions"), product_proof(changed[1], "_editable_task")]
    http = "tmp/backend/contracts/986_http.py"
    assert source(BASE, http) == source(CANDIDATE, http)
    report["unchanged_original_HTTP_test"] = {"sha256": sha(source(BASE, http)), "assert_AST_count": sum(isinstance(n, ast.Assert) for n in ast.walk(ast.parse(source(BASE, http))))}

    old = "tmp/790_backend_contrast_20261028/p64-f7-window1600/"
    new = "tmp/790_backend_contrast_20261028/p64-f7-window2000/"
    old_manifest = source(P_OLD, old + "manifest.json")
    new_manifest = source(P_NEW, new + "manifest.json")
    a, b = json.loads(old_manifest), json.loads(new_manifest)
    assert set(a["files"]) == set(b["files"]) and len(b["files"]) == 13
    identical, deadline_only = [], []
    for name, item in b["files"].items():
        raw = source(P_NEW, new + name)
        original = source(P_OLD, old + name)
        assert len(raw) == item["bytes"] and sha(raw) == item["sha256"]
        if raw == original:
            identical.append(name)
        else:
            expected = original.replace(b"datetime(2026, 10, 28, 16, 0, tzinfo=UTC)", b"datetime(2026, 10, 28, 20, 0, tzinfo=UTC)")
            expected = expected.replace(b"2026-10-28T16:00:00Z", b"2026-10-28T20:00:00Z").replace(b"EXACT_16Z_WINDOW", b"EXACT_20Z_WINDOW")
            assert raw == expected, name
            deadline_only.append(name)
    for key in set(a) - {"files", "window_utc", "phase_GEN_sha256", "supersedes_manifest_sha256"}:
        assert a[key] == b[key], key
    assert b["supersedes_manifest_sha256"] == sha(old_manifest)
    assert b["window_utc"] == "2026-10-28T20:00:00Z"
    assert b["formal600s_authorization"] is False and b["automatic_retry"] is False
    report["P64"] = {"manifest_sha256": sha(new_manifest), "identical_runtime_files": identical, "only_exact_deadline_or_label_changed": deadline_only, "business_algorithms_and_thresholds_unchanged": True}
    delivery = json.loads(source(P_NEW, new + "delivery.PUBLIC.json"))
    lengths, installed = [], {}
    for p in delivery["parts"]:
        raw, ui = source(P_NEW, new + p["raw_file"]), source(P_NEW, new + p["ui_file"])
        assert len(raw) == p["raw_bytes"] and len(ui) == p["ui_bytes"]
        assert sha(raw) == p["raw_sha256"] and sha(ui) == p["ui_sha256"]
        decoded = base64.b64decode(ui.split(b"base64.b64decode('", 1)[1].split(b"'", 1)[0], validate=True)
        assert decoded == raw
        assert len(base64.b64encode(raw)) + 300 == p["base64_plus_description"] < 18000
        assert len(ui) + 300 == p["complete_ui_plus_description"] < 18000
        encoded = raw.split(b"gzip.decompress(base64.b64decode('", 1)[1].split(b"'", 1)[0]
        payload = json.loads(gzip.decompress(base64.b64decode(encoded, validate=True)))
        for name, item in payload.items():
            assert name not in installed
            content = item["text"].encode()
            assert sha(content) == item["sha256"] and content == source(P_NEW, new + name)
            installed[name] = content
        lengths.append({"part": p["raw_file"], "raw_bytes": len(raw), "encoded_plus300": len(base64.b64encode(raw)) + 300, "whole_UI_plus300": len(ui) + 300})
    assert set(installed) == set(b["files"]) | {"manifest.json"}
    report["P64_delivery"] = {"delivery_sha256": sha(source(P_NEW, new + "delivery.PUBLIC.json")), "parts": lengths, "all14_installed_bytes_equal_exact_runtime_and_manifest": True, "executed_installer": False}

    oldd = "agents/deployment/v4-f7-20261028/profile-f7-1600/"
    newd = "agents/deployment/v4-f7-20z-20261028/profile-f7-2000/"
    profile = json.loads(source(D_NEW, newd + "profile.json"))
    same, changed_d = [], []
    for name in profile["derived_files"]:
        before, after = source(D_OLD, oldd + name), source(D_NEW, newd + name)
        item = profile["derived_files"][name]
        assert len(after) == item["bytes"] and sha(after) == item["sha256"]
        if before == after:
            same.append(name)
        else:
            expected = before.replace(b"2026-10-28T16:00:00Z", b"2026-10-28T20:00:00Z").replace(a["phase_GEN_sha256"].encode(), b["phase_GEN_sha256"].encode())
            assert after == expected, name
            changed_d.append(name)
    assert sha(source(D_NEW, newd + "generation.py")) == b["phase_GEN_sha256"]
    builder = source(D_NEW, newd + "backend-upgrade.py")
    parsed = ast.parse(builder)
    strings = [n.value.lower() for n in ast.walk(parsed) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert not any("stop_utc" in s or "deadline" in s or "hardstop" in s for s in strings)
    wrapper = source(D_NEW, "agents/deployment/v4-f7-20z-20261028/install-via-github-api.sh")
    assert len(base64.b64encode(wrapper)) + 256 == 3680 < 18000
    report["deployment"] = {"profile_sha256": sha(source(D_NEW, newd + "profile.json")), "identical_files": same, "only_deadline_and_GEN_hash_changed": changed_d, "builder_has_no_deadline_binding_strings": True, "whole_wrapper_bytes": len(wrapper), "whole_wrapper_encoded_plus256": len(base64.b64encode(wrapper)) + 256, "actual_image_reused_or_verified": False}

    local = ROOT / ".agent-worktrees/.runtime/reviewer-narrow-20261028"
    local.mkdir(parents=True, exist_ok=True)
    counts = {}
    cloc = Path("/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/cloc-2.10.pl")
    assert sha(cloc.read_bytes()) == "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83"
    for label, commit in [("baseline", BASE), ("candidate", CANDIDATE)]:
        dest = local / label
        dest.mkdir()
        archive = git("archive", "--format=tar", commit, "--", "backend/t44", "frontend/src", "frontend/index.html")
        with tarfile.open(fileobj=io.BytesIO(archive)) as t:
            t.extractall(dest, filter="data")
        paths = [str(p) for p in dest.rglob("*") if p.is_file() and p.suffix in {".py", ".ts", ".vue", ".css", ".html"}]
        listing = local / (label + ".list")
        listing.write_text("\n".join(sorted(paths)) + "\n")
        result = subprocess.run(["/usr/bin/perl", str(cloc), "--quiet", "--json", "--by-file", "--list-file=" + str(listing)], capture_output=True, check=False)
        assert result.returncode == 0
        (OUT / (label + "-cloc.json")).write_bytes(result.stdout)
        data = json.loads(result.stdout)
        counts[label] = {"commit": commit, "files": data["SUM"]["nFiles"], "code": data["SUM"]["code"]}
    assert counts["baseline"]["code"] == 5898 and counts["candidate"]["code"] == 5894
    report["own_fixed_cloc"] = counts
    report["size_range_passed"] = False
    report["full_CI_native_MySQL_cloud_or_formal_execution"] = False
    (OUT / "exact-audit.PUBLIC.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"checks": "passed", "counts": counts, "runtime_files": len(b["files"]), "UI_parts": len(lengths), "cloud": False}))


if __name__ == "__main__":
    main()
