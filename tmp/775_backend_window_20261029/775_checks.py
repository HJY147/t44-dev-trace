"""Narrow offline date/pin/install and distinct deadline-condition checks."""

import ast
import base64
import copy
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import tarfile
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "agents/backend/window-20261029"
OLD = ROOT / "tmp/790_backend_contrast_20261028/p64-f7-window2000"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


installer = module(ART / "install.py", "r29_owned_installer")
builder = module(ART / "build.py", "r29_owned_builder")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Checks(unittest.TestCase):
    def test_exact_derivation_and_all_file_pins(self):
        parent = json.loads((OLD / "manifest.json").read_bytes())
        new = json.loads((ART / "p64/manifest.json").read_bytes())
        same = 0
        for name, row in parent["files"].items():
            before = (OLD / name).read_bytes()
            after = (ART / "p64" / name).read_bytes()
            self.assertEqual(sha(before), row["sha256"])
            self.assertEqual(after, builder.replace_once(before, builder.DATE_CHANGES.get(name, [])))
            self.assertEqual(sha(after), new["files"][name]["sha256"])
            ast.parse(after, feature_version=(3, 10))
            same += before == after
        self.assertEqual(same, 9)
        self.assertEqual(new["anchor_at"], "2026-10-28T04:00:00Z")
        self.assertEqual(new["session_ttl_seconds"], 600)
        self.assertEqual(new["cohorts"], parent["cohorts"])
        self.assertEqual(new["request_totals"], [80, 800, 8000])
        self.assertEqual(new["phase_GEN_sha256"], sha((ART / "profile/generation.py").read_bytes()))

    def test_profile_only_stop_and_generator_hash_chain(self):
        parent = builder.OLD_PROFILE
        old_gen = (parent / "generation.py").read_bytes()
        new_gen = (ART / "profile/generation.py").read_bytes()
        self.assertEqual(new_gen, builder.replace_once(old_gen, [(builder.OLD_STOP, builder.STOP)]))
        for name in ("backend-upgrade.py", "mysql-budget.py", "source-artifact-receive.py"):
            self.assertEqual((parent / name).read_bytes(), (ART / "profile" / name).read_bytes())
        self.assertEqual((ART / "profile/resource-stream.py").read_bytes(), builder.replace_once((parent / "resource-stream.py").read_bytes(), [(builder.OLD_STOP, builder.STOP), (sha(old_gen), sha(new_gen))]))
        for path in (ART / "profile").glob("*.py"):
            ast.parse(path.read_bytes(), feature_version=(3, 10))

    def test_templates_generate_current_pins_and_do_not_grant(self):
        manifest_raw = (ART / "p64/manifest.json").read_bytes()
        manifest = json.loads(manifest_raw)
        for side in ("APP", "LOAD"):
            value = json.loads((ART / "templates" / (side + "-configuration.template.PUBLIC.json")).read_bytes())
            self.assertEqual(value["transfer_sha256"], manifest["files"]["transport/790_transfer.py"]["sha256"])
            self.assertEqual(value["manifest_sha256"], sha(manifest_raw))
            self.assertEqual(value["tools_dir"], builder.P64_DEST)
            self.assertIsNone(value["root_grant_sha256"])
        for mode in ("prep", "pressure"):
            value = json.loads((ART / "templates" / (mode + "-grant.template.PUBLIC.json")).read_bytes())
            self.assertFalse(value["admitted"])
            self.assertIsNone(value["session_nonce"])
            self.assertEqual(value["stop_utc"], builder.STOP)

    def test_builder_is_source_only_not_stop_bound(self):
        raw = (ART / "profile/backend-upgrade.py").read_bytes()
        self.assertEqual(sha(raw), "d2fc28b2f0c19b19a81c2ac10c0712767c6182d8b3e2b5e7f2346da62bf2bbf5")
        tree = ast.parse(raw)
        options = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument" and n.args and isinstance(n.args[0], ast.Constant)]
        self.assertFalse(any("stop" in x or "deadline" in x for x in options))
        binding = next(n for n in ast.walk(tree) if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "builder_sha256" for k in n.keys))
        keys = [k.value for k in binding.keys if isinstance(k, ast.Constant)]
        self.assertNotIn("stop_utc", keys)
        self.assertNotIn("expires_at", keys)

    def test_original_old_packages_tests_and_product_unchanged(self):
        paths = ["backend", "frontend", "tmp/790_backend_contrast_20261028/p64-f7-window1600", "tmp/790_backend_contrast_20261028/p64-f7-ui-encoded-v2"]
        result = subprocess.run(["git", "diff", "--exit-code", "fcc847f3", "--", *paths], cwd=ROOT, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout.decode())

    def test_true_330_global_window_and_600_packet_age_are_distinct(self):
        now = datetime(2026, 10, 29, 5, tzinfo=timezone.utc)

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return now

        code = ast.parse((ART / "p64/edge/790_http.py").read_bytes())
        node = next(n for n in code.body if isinstance(n, ast.FunctionDef) and n.name == "check_packet")
        original = next(n for n in ast.parse((OLD / "edge/790_http.py").read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name == "check_packet")
        self.assertEqual(ast.dump(node), ast.dump(original))
        ns = {"datetime": Clock, "timedelta": timedelta, "UTC": timezone.utc, "KIND": "case", "PRODUCT": "product", "DATABASE": "db", "require_context": lambda packet: None, "target": lambda url: None, "InvalidDiagnostic": ValueError}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "unchanged-check-packet", "exec"), ns)
        packet = {"kind": "case", "product": "product", "database": "db", "resumable": True, "created_at": (now - timedelta(seconds=280)).isoformat(), "url": "https://example.invalid", "sessions": {role: {"expires_at": (now + timedelta(seconds=10)).isoformat()} for role in ("manager", "developer", "reviewer", "service")}, "slots": [{"transition": {"id": 1}, "escalation": {"id": 2}}]}
        ns["check_packet"](packet)  # 320 seconds of fixture age left is not the 330s global gate.
        for age, accepted in ((599, True), (600, False)):
            candidate = copy.deepcopy(packet)
            candidate["created_at"] = (now - timedelta(seconds=age)).isoformat()
            if accepted:
                ns["check_packet"](candidate)
            else:
                with self.assertRaisesRegex(ValueError, "window expired"):
                    ns["check_packet"](candidate)
        load_tree = ast.parse((ART / "p64/790_load.py").read_bytes())
        gate = next(n.test for n in ast.walk(load_tree) if isinstance(n, ast.If) and "330" in ast.unparse(n.test))
        scope = {"datetime": Clock, "UTC": timezone.utc, "bootstrap": SimpleNamespace(SOURCE="source", ANCHOR="anchor", stamp=datetime.fromisoformat)}
        for remaining, refused in ((329, True), (331, False)):
            scope["control"] = {"kind": "t44-contrast-development-v1", "source_sha": "source", "anchor_at": "anchor", "seed": 44, "stop_utc": (now + timedelta(seconds=remaining)).isoformat()}
            self.assertEqual(eval(compile(ast.Expression(gate), "unchanged-global-gate", "eval"), scope), refused)

    def test_each_real_session_expiry_stays_independent(self):
        tree = ast.parse((ART / "p64/edge/790_http.py").read_bytes())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "check_packet")
        now = datetime(2026, 10, 29, 5, tzinfo=timezone.utc)

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return now

        ns = {"datetime": Clock, "timedelta": timedelta, "UTC": timezone.utc, "KIND": "case", "PRODUCT": "product", "DATABASE": "db", "require_context": lambda packet: None, "target": lambda url: None, "InvalidDiagnostic": ValueError}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "unchanged-session-gates", "exec"), ns)
        packet = {"kind": "case", "product": "product", "database": "db", "resumable": True, "created_at": now.isoformat(), "url": "https://example.invalid", "sessions": {role: {"expires_at": (now + timedelta(seconds=10)).isoformat()} for role in ("manager", "developer", "reviewer", "service")}, "slots": [{"transition": {"id": 1}, "escalation": {"id": 2}}]}
        for role in packet["sessions"]:
            with self.subTest(role=role):
                changed = copy.deepcopy(packet)
                changed["sessions"][role]["expires_at"] = now.isoformat()
                with self.assertRaisesRegex(ValueError, "Session expired"):
                    ns["check_packet"](changed)

    def test_actual_archive_install_roundtrip_raw_and_github_json(self):
        archive = (ART / "runtime-bundle.PUBLIC.tar.gz").read_bytes()
        response = json.dumps({"type": "file", "path": installer.REPO_PATH, "size": len(archive), "encoding": "base64", "content": base64.b64encode(archive).decode()}).encode()
        for raw in (archive, response):
            with self.subTest(raw_response=raw is archive), tempfile.TemporaryDirectory() as folder:
                base = Path(folder).resolve()
                result = installer.install(raw, base)
                self.assertEqual(result["installed_files"], 20)
                self.assertFalse(result["SUT_or_sessions_or_services_started"])
                for group in ("profile", "p64"):
                    for path in (ART / group).rglob("*"):
                        if path.is_file():
                            actual = Path(result["targets"][group]) / path.relative_to(ART / group)
                            self.assertEqual(actual.read_bytes(), path.read_bytes())
                            self.assertEqual(stat.S_IMODE(actual.stat().st_mode), 0o444)
                before = {str(path): sha(path.read_bytes()) for path in base.rglob("*") if path.is_file()}
                with self.assertRaisesRegex(ValueError, "ALL_NEW_TARGETS"):
                    installer.install(raw, base)
                self.assertEqual(before, {str(path): sha(path.read_bytes()) for path in base.rglob("*") if path.is_file()})

    def test_tampered_bundle_refused_before_any_install_mutation(self):
        raw = bytearray((ART / "runtime-bundle.PUBLIC.tar.gz").read_bytes())
        raw[-10] ^= 1
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder).resolve()
            with self.assertRaisesRegex(ValueError, "EXACT_PUBLIC_BUNDLE"):
                installer.install(bytes(raw), base)
            self.assertEqual(list(base.iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
