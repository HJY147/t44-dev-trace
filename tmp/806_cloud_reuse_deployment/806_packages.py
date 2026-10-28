"""Actual large-output pipefail regression, with a synthetic fixture and no apt/cloud."""

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_policy(tmp_path, program):
    fixture = tmp_path / "policy.txt"
    fixture.write_text(
        "Candidate: 2.40.3\n"
        + "version source metadata\n" * 100000
        + "Candidate: ignored\n"
    )
    env = {**os.environ, "T44_POLICY_FIXTURE": str(fixture), "T44_AWK_PROGRAM": program}
    return subprocess.run(
        [
            "bash",
            "-o",
            "pipefail",
            "-c",
            'cat "$T44_POLICY_FIXTURE" | awk "$T44_AWK_PROGRAM"',
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_old_early_exit_reproduces_sigpipe141(tmp_path):
    result = run_policy(tmp_path, "/Candidate:/ {print $2;exit}")
    assert result.returncode == 141
    assert result.stdout == "2.40.3\n"


def test_actual_fixed_program_consumes_all_and_emits_only_first(tmp_path):
    script = (ROOT / "deployment/cloud-reuse/02-ubuntu-packages.sh").read_text()
    program = re.search(r"policy \"?[^\n]*?awk '([^']+)'", script)
    if program is None:
        program = re.search(r"awk '([^']+)'", script)
    result = run_policy(tmp_path, program.group(1))
    assert result.returncode == 0
    assert result.stdout == "2.40.3\n"
