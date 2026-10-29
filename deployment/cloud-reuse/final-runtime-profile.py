"""Derive new exact-source admin/HTTP wrappers from reviewed templates; never run them."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = {"r30-neutral-admin.py": "8e9d024b7aa38692a633b620a23a27380d155ed7a8725f45c9ee25dac0fe4d9a",
             "r30-http-prepare.py": "c2c322bd0c932928fcd811d49a4c92f2b45188d2f32b2669fab79a27df9e4e2e"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(path, expected):
    if path.is_symlink() or sha(path.read_bytes()) != expected:
        raise ValueError("EXACT_ROOT_PINNED_ORIGINAL_REQUIRED")
    return path.read_bytes()


def replace(text, before, after, count=1):
    if text.count(before) != count:
        raise ValueError("EXACT_RUNTIME_TEMPLATE_PREIMAGE_REQUIRED:" + before)
    return text.replace(before, after)


def constant(text, name, value):
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.Assign)
             and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name]
    if len(nodes) != 1:
        raise ValueError("EXACT_SINGLE_CONSTANT_REQUIRED:" + name)
    node = nodes[0]
    lines = text.splitlines(keepends=True)
    return "".join(lines[:node.lineno - 1]) + name + " = " + repr(value) + "\n" + "".join(lines[node.end_lineno:])


def derive(args):
    source_raw = pinned(args.source_profile, args.source_profile_sha256)
    source = json.loads(source_raw)
    gen_raw = pinned(args.gen_profile / "profile.json", args.gen_profile_sha256)
    gen = json.loads(gen_raw)
    if (source.get("schema") != "t44-final-source-profile-v1" or source.get("root_approved") is not True
            or source["source_sha"] != gen["source_sha"]
            or source["backend_bundle_manifest_sha256"] != gen["backend_bundle_manifest_sha256"]
            or not source["runtime_files"] or source["runtime_file_count"] != len(source["runtime_files"])
            or gen["derived_budget_sha256"] != source["budget_helper_sha256"]):
        raise ValueError("ROOT_APPROVED_ACTUAL_BUILD_PROFILE_AND_NEW_GEN_REQUIRED")
    adapter_sha = gen["derived_files"]["final-image-bundle.py"]["sha256"]
    texts = {n: pinned(HERE / n, h).decode() for n, h in TEMPLATES.items()}
    admin = constant(constant(constant(texts["r30-neutral-admin.py"], "SOURCE", source["source_sha"]),
                             "CONFIG", source["backend_config_id"]), "ADAPTER_SHA", adapter_sha)
    admin = replace(admin, 'profile["derived_files"]["r30-window.py"]', 'profile["derived_files"]["final-image-bundle.py"]')
    admin = replace(admin, "generation.R30_ADAPTER_SHA", "generation.FINAL_ADAPTER_SHA")
    helper = '''
EXPECTED_SOURCE_PROFILE_SHA = __ROOT_SHA__
def _source_profile(args, pin, plan):
    raw = pin(args.source_profile, EXPECTED_SOURCE_PROFILE_SHA)
    value = json.loads(raw)
    if (value.get("root_approved") is not True or value["source_sha"] != SOURCE
            or value["backend_config_id"] != CONFIG
            or plan.get("source_profile") != {"path":"/neutral-input/source-profile.PUBLIC.json", "sha256":EXPECTED_SOURCE_PROFILE_SHA}):
        raise ValueError("ORIGINAL_ROOT_APPROVED_SOURCE_PROFILE_REQUIRED")
    return raw
'''.replace("__ROOT_SHA__", repr(args.source_profile_sha256))
    admin = replace(admin, "def checked(args):", helper + "\n\ndef checked(args):")
    admin = replace(admin, '    plan, intent = json.loads(inputs["plan.json"]), json.loads(inputs["intent.json"])',
        '    plan, intent = json.loads(inputs["plan.json"]), json.loads(inputs["intent.json"])\n    inputs["source-profile.PUBLIC.json"] = _source_profile(args, pinned, plan)')
    # Both old templates expose Path in argparse; add only the fixed source-profile file input.
    admin = replace(admin, '    args = p.parse_args()', '    p.add_argument("--source-profile", type=Path, required=True)\n    args = p.parse_args()')
    f_init = constant(admin, "ACCOUNT_ROLES", ("manager", "developer_a", "developer_b", "reviewer_a", "reviewer_b", "outsider", "login_only"))
    f_init = constant(f_init, "MODES", ("init-accounts",))
    f_init = replace(f_init, '    lib, value = generation.phase_binding(args.phase_dir, args.binding_sha256)',
                     '    lib, value = generation.phase_binding(args.phase_dir, args.binding_sha256)\n    if value["phase"] != "f":\n        raise ValueError("F_ONLY_ACCOUNT_INITIALIZATION_REQUIRED")')
    account_function = '''def accounts_for_init(args):
    value = json.loads(raw(args.accounts, private=True))
    plan = json.loads(raw(args.plan, private=True))
    if (value.get("schema") != "final-f-account-init-v1" or value.get("synthetic") is not True
            or value.get("phase") != "f" or value.get("binding_sha256") != args.binding_sha256
            or value.get("source_profile_sha256") != EXPECTED_SOURCE_PROFILE_SHA
            or set(value["accounts"]) != set(ACCOUNT_ROLES)):
        raise ValueError("EXACT_NEW_F_ACCOUNT_BINDING_AND_LABELS_REQUIRED")
    accounts = value["accounts"]
    for role in ACCOUNT_ROLES:
        account = accounts[role]
        if (account["username"] != "synthetic-" + plan["run_id"] + "-f-" + role
                or account.get("user_id") is not None
                or account["display_name"] != "[synthetic] " + role):
            raise ValueError("FIXED_F_SYNTHETIC_NEW_USERNAME_AND_DISPLAY_REQUIRED")
        if account["password"] is None:
            account["password"] = secrets.token_urlsafe(32)
        if (not isinstance(account["password"], str) or not 1 <= len(account["password"]) <= 128
                or "\\n" in account["password"] or "\\r" in account["password"]):
            raise ValueError("PRIVATE_SINGLE_LINE_PASSWORD_REQUIRED")
    return accounts
'''
    node = next(n for n in ast.parse(f_init).body if isinstance(n, ast.FunctionDef) and n.name == "accounts_for_init")
    lines = f_init.splitlines(keepends=True)
    f_init = "".join(lines[:node.lineno - 1]) + account_function + "\n\n" + "".join(lines[node.end_lineno:])
    f_init = replace(f_init, '"--username", "synthetic-" + step,\n                         "--display-name", "synthetic-" + step,',
                     '"--username", accounts[step]["username"],\n                         "--display-name", accounts[step]["display_name"],')
    f_init = replace(f_init, '            output = args.output_dir / "output/accounts.initialized.private.json"',
                     '            if len({accounts[r]["user_id"] for r in ACCOUNT_ROLES}) != len(ACCOUNT_ROLES):\n                raise ValueError("DISTINCT_ACTUAL_F_USER_IDS_REQUIRED")\n            output = args.output_dir / "output/accounts.initialized.private.json"')
    http = texts["r30-http-prepare.py"]
    for key, value in {"SOURCE": source["source_sha"], "CONFIG": source["backend_config_id"],
                       "ALIAS": "t44-backend:src-" + source["source_sha"],
                       "SOURCE_MANIFEST": source["source_manifest_sha256"],
                       "BUNDLE": source["backend_bundle_manifest_sha256"], "ADMIN_SHA": sha(admin.encode())}.items():
        http = constant(http, key, value)
    http = replace(http, "generation.R30_ADAPTER_SHA", "generation.FINAL_ADAPTER_SHA")
    http = replace(http, '["-B", "/neutral-code/escalation_readback.py", "--check-runtime-only"]',
                   '["-B", "/neutral-code/escalation_readback.py", "--check-runtime-only", "--plan", "/neutral-input/plan.json"]')
    http = replace(http, '"r30-backend-import-receipt-v1"', '"final-backend-web-import-v1"')
    http = replace(http, 'manifest.get("purpose") != "FUTURE_NEW_WINDOW_ONLY_NOT_R30WINDOW01_REPLAY"',
        'manifest.get("kind") != "r30-neutral-producer-code-manifest-v1"\n'
        '            or manifest.get("status") != "BUILD_FACTS_BOUND_ROOT_APPROVAL_AND_ACTUAL_IMPORT_PENDING"')
    http = replace(http, 'receipt.get("full_runtime_files") != 60', 'receipt.get("full_runtime_files") != ' + str(source["runtime_file_count"]))
    http = replace(http, 'len(observed.get("files", [])) != 60', 'len(observed.get("files", [])) != ' + str(source["runtime_file_count"]))
    # The original archive source binding is obtained from its actual source-manifest bytes, not an old constant.
    source_manifest = json.loads(pinned(args.source_manifest, source["source_manifest_sha256"]))
    http = replace(http, '"275970aa18117751e3a4fc8c404d0750cb9698310a70146d64061a634c37bf09"', repr(source_manifest["source_archive_sha256"]))
    http = replace(http, "def checked(args, a):", helper + "\n\ndef checked(args, a):")
    http = replace(http, '    plan = json.loads(plan_raw)', '    plan = json.loads(plan_raw)\n    profile_raw = _source_profile(args, a.pinned, plan)')
    http = replace(http, '"ca.pem": a.raw(args.ca)}', '"ca.pem": a.raw(args.ca), "source-profile.PUBLIC.json": profile_raw}')
    http = replace(http, '    args = p.parse_args()', '    p.add_argument("--source-profile", type=Path, required=True)\n    args = p.parse_args()')
    f_http = http
    begin = f_http.index("    t0, start, end, stop, cutoff =", f_http.index("def checked(args, a):"))
    end = f_http.index('    inputs = {"plan.json":', begin)
    f_http = f_http[:begin] + '''    t0, stop, cost = (deadline(plan["lifecycle"]["t0_utc"]), deadline(binding["stop_utc"]), deadline(plan["lifecycle"]["cost_stop_utc"]))
    if binding["phase"] != "f" or stop != t0 + 2100 or cost != t0 + 2400 or not t0 <= now < stop - 600:
        raise ValueError("FINITE_SEPARATE_F_PREPARATION_AND_RESERVE_REQUIRED")
    timeout = min(180, stop - now - 600)
''' + f_http[end:]
    begin = f_http.index('        timeout = min(timeout, deadline(plan["lifecycle"]["packet_cutoff_utc"])')
    end = f_http.index('        if timeout < 1:',begin)
    f_http = f_http[:begin] + '        timeout = min(timeout, deadline(value["stop_utc"]) - time.time() - 600)\n' + f_http[end:]
    extra_raw = (HERE / "final-f-project.py").read_bytes()
    f_http = replace(f_http, '"-B", "/neutral-code/prepare_http.py",', '"-B", "/neutral-extra/f-fixture.py",')
    f_http = replace(f_http, '    a.stage(args, inputs, code)', '    a.stage(args, inputs, code)\n'
        '    extra = args.output_dir / "extra"\n    extra.mkdir(mode=0o755)\n    extra.chmod(0o755)\n'
        '    extra_raw = Path(__file__).with_name("final-f-project.py").read_bytes()\n'
        '    if a.digest(extra_raw) != ' + repr(sha(extra_raw)) + ':\n        raise ValueError("EXACT_FIXED_F_EXTRA_CODE_REQUIRED")\n'
        '    a.write(extra / "f-fixture.py", extra_raw)\n    (extra / "f-fixture.py").chmod(0o644)\n'
        '    a.save(args.output_dir / "extra-code.PUBLIC.json", {"files":{"f-fixture.py":{"sha256":a.digest(extra_raw),"bytes":len(extra_raw)}}})')
    f_http = replace(f_http, '"--volume", str(args.output_dir / "code") + ":/neutral-code:ro",',
        '"--volume", str(args.output_dir / "extra") + ":/neutral-extra:ro",\n            "--volume", str(args.output_dir / "code") + ":/neutral-code:ro",')
    if args.output.exists() or not args.output.is_absolute() or args.output.parent.resolve() != args.output.parent:
        raise ValueError("NEW_CANONICAL_RUNTIME_OUTPUT_REQUIRED")
    args.output.mkdir(mode=0o700)
    output = {"r30-neutral-admin.py": admin.encode(), "http-prepare.py": http.encode(),
              "f-init-accounts.py": f_init.encode(), "f-http-prepare.py": f_http.encode(), "final-f-project.py": extra_raw,
              "source-profile.PUBLIC.json": source_raw}
    for name, raw in output.items():
        if name.endswith(".py"):
            compile(raw, name, "exec")
        fd = os.open(args.output / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
    manifest = {"kind": "final-exact-source-runtime-wrappers-v1", "source_sha": source["source_sha"],
                "source_profile_sha256": args.source_profile_sha256, "gen_profile_sha256": args.gen_profile_sha256,
                "files": {n: {"sha256": sha(raw), "bytes": len(raw)} for n, raw in output.items()},
                "templates": TEMPLATES, "executed": False, "authority": "new root run approval remains external"}
    (args.output / "runtime-manifest.PUBLIC.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    (args.output / "runtime-manifest.PUBLIC.json").chmod(0o600)
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("source-profile", "source-manifest", "gen-profile", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    p.add_argument("--source-profile-sha256", required=True)
    p.add_argument("--gen-profile-sha256", required=True)
    args = p.parse_args()
    os.umask(0o077)
    print(json.dumps(derive(args)))


if __name__ == "__main__":
    main()
