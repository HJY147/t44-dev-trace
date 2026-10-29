"""Reproduce new public-behavior properties against the untouched baseline package."""

import io
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = '396b646adb87de183929ac6fc46bbe7e88074c8a'
PYTHON = '/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/backend/.venv/bin/python'


def main():
    with tempfile.TemporaryDirectory(prefix='.baseline-', dir=Path(__file__).parent) as temporary:
        data = subprocess.check_output(['git', 'archive', BASE, 'backend/t44'], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(temporary, filter='data')
        backend = str(Path(temporary) / 'backend')
        args = ['-c', str(ROOT / 'backend/pyproject.toml'), '-o', 'pythonpath=' + backend,
                str(ROOT / 'tmp/backend/messaging/806_newscope.py'), '-q', '-m',
                'not integration', '--tb=short']
        command = (
            'import pathlib, t44.messaging.broker as broker, pytest; '
            f'assert pathlib.Path(broker.__file__).is_relative_to(pathlib.Path({backend!r})); '
            'print("Baseline module:", broker.__file__); '
            f'raise SystemExit(pytest.main({args!r}))'
        )
        return subprocess.call([PYTHON, '-c', command], cwd=ROOT,
                               env=dict(os.environ, PYTHONPATH=backend))


if __name__ == '__main__':
    raise SystemExit(main())
