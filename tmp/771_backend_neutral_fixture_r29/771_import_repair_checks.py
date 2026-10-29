import ast
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'agents/backend/neutral-fixture-20261029'

class ImportRepairChecks(unittest.TestCase):
    def test_actual_python_isolated_path_behavior(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'only_neutral_synthetic_module.py').write_text('value=729\n')
            env={**os.environ,'PYTHONPATH':str(p)}
            command='import only_neutral_synthetic_module as x;print(x.value)'
            bad=subprocess.run([sys.executable,'-I','-B','-c',command],env=env,capture_output=True)
            good=subprocess.run([sys.executable,'-B','-c',command],env=env,capture_output=True)
            self.assertNotEqual(bad.returncode,0);self.assertIn(b'ModuleNotFoundError',bad.stderr)
            self.assertEqual(good.returncode,0);self.assertEqual(good.stdout.strip(),b'729')

    def test_admin_only_I_removed_edge_unchanged(self):
        old=ast.parse((D/'host.py').read_text());new=ast.parse((D/'resume-import-01.py').read_text())
        def admin(tree):return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='admin')
        before=admin(old);after=admin(new)
        before_strings=[n.value for n in ast.walk(before) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        after_strings=[n.value for n in ast.walk(after) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        self.assertEqual(before_strings.count('-I'),1);self.assertEqual(after_strings.count('-I'),0)
        for node in ast.walk(before):
            if isinstance(node,ast.List):node.elts=[v for v in node.elts if not (isinstance(v,ast.Constant) and v.value=='-I')]
        self.assertEqual(ast.dump(before),ast.dump(after))
        def edge_argv(tree):
            return next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='argv' for t in n.targets))
        self.assertEqual(ast.dump(edge_argv(old)),ast.dump(edge_argv(new)))
        text=(D/'resume-import-01.py').read_text()
        self.assertNotIn('output.mkdir(',text);self.assertNotIn('inputs.mkdir(',text)
        self.assertIn("'e860274a73bdba7e1e6978dfca7044da789f456f5faa8ead8eea00fdbae159a3'",text)
        self.assertIn("admin('01b-service','service')",text)
        self.assertIn("raise ValueError('FIRST_SERVICE_WAS_NEVER_CALLED_AND_EDGE_UNSTARTED_REQUIRED')",text)

    def test_complete_launcher_exact_bytes(self):
        script=(D/'resume-import-launch.PUBLIC.sh').read_text()
        self.assertLess(len(script.encode())+300,16500)
        b64=ast.literal_eval(re.search(r'raw=zlib.decompress\(base64.b64decode\((.+),validate=True\)\)',script).group(1))
        decoded=zlib.decompress(base64.b64decode(b64,validate=True))
        self.assertEqual(decoded,(D/'resume-import-01.py').read_bytes())
        self.assertIn(repr(hashlib.sha256(decoded).hexdigest()),script)
        self.assertIn('--unit=t44-r29-neutral-import-repair-01',script)
        self.assertIn('O_EXCL',script)

    def test_original_four_manifest_files_unchanged(self):
        manifest=json.loads((D/'code-manifest.PUBLIC.json').read_bytes())
        for name,wanted in manifest['files'].items():self.assertEqual(hashlib.sha256((D/name).read_bytes()).hexdigest(),wanted)
        diff=subprocess.run(['git','diff','--exit-code','6abc991c','--','backend','frontend','agents/backend/window-20261029/p64'],cwd=ROOT,capture_output=True)
        self.assertEqual(diff.returncode,0,diff.stdout)

if __name__=='__main__':unittest.main(verbosity=2)
