"""Actual POSIX sh wrapper replay with fixed PUBLIC input, never network/cloud."""

import base64
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "agents/backend/window-20261029"


class WrapperChecks(unittest.TestCase):
    def test_complete_embedded_source_and_outer_size(self):
        raw = (ART / "install-via-github-api.PUBLIC.sh").read_bytes()
        proof = json.loads((ART / "wrapper-proof.PUBLIC.json").read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), proof["wrapper_sha256"])
        embedded = raw.decode().split("<<'R29_VERIFY_INSTALL'\n", 1)[1].rsplit("\nR29_VERIFY_INSTALL\n", 1)[0]
        self.assertEqual(embedded.encode(), (ART / "install.py").read_bytes())
        self.assertLess(len(raw) + 300, 18000)
        self.assertLess(len(base64.b64encode(raw)) + 300, 18000)
        self.assertEqual(subprocess.run(["sh", "-n"], input=raw, capture_output=True, check=False).returncode, 0)

    def replay(self, response, valid):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder).resolve()
            target = base / "owned"
            target.mkdir()
            payload = base / "fixed-public-response"
            payload.write_bytes(response)
            executable = base / "bin"
            executable.mkdir()
            curl = executable / "curl"
            curl.write_text("#!/bin/sh\nset -eu\nwhile [ \"$#\" -gt 0 ]; do\n if [ \"$1\" = '--output' ]; then shift; target=\"$1\"; fi\n shift\ndone\ncp \"$R29_TEST_PAYLOAD\" \"$target\"\n")
            curl.chmod(0o755)
            command = (ART / "install-via-github-api.PUBLIC.sh").read_text()
            # Only explicit owned filesystem targets move for the local replay;
            # fixed PUBLIC manifest targets and every verification branch remain intact.
            self.assertEqual(command.count("base=Path(\"/root/t44-r9\")"), 1)
            command = command.replace("base=Path(\"/root/t44-r9\")", "base=Path(" + repr(str(target)) + ")")
            self.assertEqual(command.count("'/root/t44-r9/r29-public-code-XXXXXX'"), 1)
            command = command.replace("'/root/t44-r9/r29-public-code-XXXXXX'", repr(str(base / "staging-XXXXXX")))
            env = dict(os.environ, PATH=str(executable) + os.pathsep + os.environ["PATH"], R29_TEST_PAYLOAD=str(payload))
            result = subprocess.run(["sh"], input=command.encode(), capture_output=True, env=env, check=False, timeout=10)
            if valid:
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                output = json.loads(result.stdout)
                self.assertEqual(output["installed_files"], 20)
                for group in ("p64", "profile"):
                    for source in (ART / group).rglob("*"):
                        if source.is_file():
                            actual = Path(output["targets"][group]) / source.relative_to(ART / group)
                            self.assertEqual(actual.read_bytes(), source.read_bytes())
            else:
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(list(target.iterdir()), [])

    def test_actual_whole_sh_wrapper_raw_and_json(self):
        raw = (ART / "runtime-bundle.PUBLIC.tar.gz").read_bytes()
        self.replay(raw, True)
        response = json.dumps({"type": "file", "path": "agents/backend/window-20261029/runtime-bundle.PUBLIC.tar.gz", "size": len(raw), "encoding": "base64", "content": base64.b64encode(raw).decode()}).encode()
        self.replay(response, True)

    def test_actual_whole_wrapper_refuses_tamper_without_installation(self):
        raw = bytearray((ART / "runtime-bundle.PUBLIC.tar.gz").read_bytes())
        raw[-10] ^= 1
        self.replay(raw, False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
