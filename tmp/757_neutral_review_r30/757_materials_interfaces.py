"""Read-only exact coordinator CLI/permission seams; no Docker/service/HTTP invocation."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
import types
import unittest

ROOT = Path('/Users/yang/Desktop/nothing/软件开发大作业')
SOURCE = ROOT / '.agent-worktrees/resume-coordination-20261029/agents/coordinator/r30-bounded/materials.py'
PRODUCER = ROOT / '.agent-worktrees/backend-neutral-r30/agents/backend/neutral-r30'
WRAPPER = ROOT / '.agent-worktrees/deployment-preparation-r30/deployment/cloud-reuse/r30-neutral-admin.py'
EXPECTED = '8db05a89d7805054304900d2a10c05f1f07b906ac8712fc7b8d4561d61421ba6'
RAW = SOURCE.read_bytes()
TREE = ast.parse(RAW)
MAIN = next(x for x in TREE.body if isinstance(x, ast.ClassDef) and x.name == 'Run')
MAIN = next(x for x in MAIN.body if isinstance(x, ast.FunctionDef) and x.name == 'main')


def cli_parser(path):
    tree = ast.parse(path.read_bytes())
    main = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'main')
    prefix = []
    for node in main.body:
        if any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == 'parse_args' for x in ast.walk(node)):
            break
        prefix.append(node)
    scope = {'argparse': argparse, 'Path': Path, '__doc__': 'Exact producer parser only'}
    exec(compile(ast.Module(body=prefix, type_ignores=[]), str(path), 'exec'), scope)
    return scope['parser']


class Interfaces(unittest.TestCase):
    def test_exact_bytes_and_host_syntax(self):
        self.assertEqual(hashlib.sha256(RAW).hexdigest(), EXPECTED)
        ast.parse(RAW, feature_version=(3, 10))

    def test_all_four_container_argv_parse_actual_producer(self):
        calls = [x for x in ast.walk(MAIN) if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == 'container']
        self.assertEqual(len(calls), 4)
        for call in calls:
            script = ast.literal_eval(call.args[2])
            argv = eval(compile(ast.Expression(call.args[3]), '<coordinator options>', 'eval'))
            cli_parser(PRODUCER / script).parse_args(argv)
            if script == 'stage_scope.py':
                self.assertEqual(call.args[4].id, 'PYTHON')
                self.assertEqual(len(call.args), 5)  # default network none
            if script == 'assemble.py':
                self.assertNotIn('--binding', argv)

    def test_scope_raw_copy_accepted_by_actual_wrapper_private_input(self):
        module = types.ModuleType('exact_wrapper_private_read')
        exec(compile(WRAPPER.read_bytes(), str(WRAPPER), 'exec'), module.__dict__)
        start = next(i for i, x in enumerate(MAIN.body) if isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'material_path' for t in x.targets))
        end = next(i for i, x in enumerate(MAIN.body[start:], start) if isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'service' for t in x.targets))
        with tempfile.TemporaryDirectory(prefix='757-interface-') as directory:
            parent = Path(directory).resolve()
            scoped = parent / 'container-output'; scoped.mkdir()
            original = scoped / 'material-plan.json'
            original.write_bytes(b'{"pure_fake_fixture": true}\n'); original.chmod(0o600)
            out = parent / 'root-output'; out.mkdir(mode=0o700)
            values = {'self': types.SimpleNamespace(out=out), 'scoped': scoped, 'json': json}
            exec(compile(ast.Module(body=MAIN.body[start:end], type_ignores=[]), '<actual raw-copy block>', 'exec'), values)
            copied = values['material_path']
            self.assertNotEqual(copied, original)
            self.assertEqual(copied.stat().st_uid, os.geteuid())
            self.assertEqual(module.raw(copied, private=True), original.read_bytes())
            self.assertEqual(original.read_bytes(), b'{"pure_fake_fixture": true}\n')

    def test_manifest_declares_flat_public_files_and_permissions_precede_containers(self):
        manifest_raw = (PRODUCER / 'code-manifest.PUBLIC.json').read_bytes()
        self.assertEqual(hashlib.sha256(manifest_raw).hexdigest(), '66ab164258803a8a62edfc3dbc713837431ce8b649664ab8de4c5a48a2359606')
        manifest = json.loads(manifest_raw)
        self.assertEqual(len(manifest['files']), 17)
        for name, expected in manifest['files'].items():
            self.assertEqual(Path(name).name, name)
            raw = (PRODUCER / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
            self.assertEqual(len(raw), manifest['file_sizes'][name])
        self.assertIn('path.chmod(0o644)', RAW.decode())
        self.assertIn('self.code.chmod(0o755)', RAW.decode())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Interfaces)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {'materials_sha256': EXPECTED, 'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'actual_cloud_Docker_HTTP_sessions': False}
    Path(__file__).with_name('materials-interface-review.json').write_text(json.dumps(receipt, indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
