"""Measure application snapshots with the project's fixed classifier and cloc 2.10."""

import argparse
import hashlib
import importlib.util
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/cloc-2.10.pl')
EXPECTED = 'bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert hashlib.sha256(TOOL.read_bytes()).hexdigest() == EXPECTED
    spec = importlib.util.spec_from_file_location('fixed_metrics', ROOT / 'scripts/metrics/source_count.py')
    metrics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metrics)
    commit = subprocess.check_output(['git', 'rev-parse', args.ref], cwd=ROOT, text=True).strip()
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', commit], cwd=ROOT, text=True).splitlines()
    selected = [name for name in names if metrics.classify(name) == 'application']
    with tempfile.TemporaryDirectory(prefix='.measure-', dir=Path(__file__).parent) as temporary:
        base = Path(temporary)
        data = subprocess.check_output(['git', 'archive', '--format=tar', commit, '--', *selected], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(base, filter='data')
        listing, output = base / 'application.list', base / 'application.json'
        listing.write_text('\n'.join(str(base / name) for name in selected) + '\n')
        subprocess.run(['/usr/bin/perl', str(TOOL), '--quiet', '--json', '--by-file',
                        '--list-file=' + str(listing), '--report-file=' + str(output)], check=True)
        raw = json.loads(output.read_text())
        report = {'commit': commit, 'tool': 'cloc 2.10', 'tool_sha256': EXPECTED,
                  'classifier': 'unchanged scripts/metrics/source_count.py.classify',
                  'application': raw['SUM'],
                  'files': {str(Path(key).relative_to(base)): value for key, value in raw.items()
                            if key not in ('header', 'SUM')}}
    target = Path(__file__).parent / (args.label + '.json')
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    subset = {key: value['code'] for key, value in report['files'].items()
              if key.startswith(('backend/t44/messaging/', 'backend/t44/scheduling/'))}
    print(json.dumps({'commit': commit, 'application_code': report['application']['code'],
                      'message_scheduler_files': subset}, ensure_ascii=False))


if __name__ == '__main__':
    main()
