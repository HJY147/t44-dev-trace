"""Detached original ENTRY runner. Explicit live --launch only; never retries a run."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

RUN = 'r30manualp13'
ENTRY_SHA = 'd15874c477fef0d92bc68ab77802a5354d15be237c853621b56467005c20d43e'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def put(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')
    path.chmod(0o600)


def validate(workspace, grant):
    if not workspace.is_absolute() or not grant.is_absolute() or grant.is_symlink():
        raise ValueError('CANONICAL_ABSOLUTE_INPUTS_REQUIRED')
    entry = workspace / 'public/ENTRY_MANUAL_753.sh'
    if entry.is_symlink() or hashlib.sha256(entry.read_bytes()).hexdigest() != ENTRY_SHA:
        raise ValueError('ORIGINAL_ENTRY_REQUIRED')
    original = json.loads((workspace / 'runs' / RUN / 'grant.default-false.json').read_bytes())
    approved = json.loads(grant.read_bytes())
    if original.get('allow') is not False or approved.get('allow') is not True:
        raise ValueError('INDEPENDENT_ONCE_GRANT_REQUIRED')
    expected = dict(original, allow=True)
    if approved != expected or approved.get('run_id') != RUN:
        raise ValueError('ONLY_ALLOW_MAY_CHANGE')
    for path in [workspace / 'results' / RUN, workspace / 'results' / (RUN + '.phase.json'),
                 workspace / 'runs' / RUN / 'grant.consumed', workspace / 'operator-channel' / RUN]:
        if path.exists():
            raise ValueError('DISPATCH_ALREADY_ATTEMPTED_OR_OUTPUT_EXISTS')
    return entry


def worker(workspace, grant, channel):
    # Only the original ENTRY touches the benchmark. Its unfiltered output stays private.
    with (channel / 'entry.stdout.private').open('xb') as out, (channel / 'entry.stderr.private').open('xb') as err:
        result = subprocess.run(['sh', str(workspace / 'public/ENTRY_MANUAL_753.sh'), 'execute',
                                 str(workspace), RUN, str(grant)], stdin=subprocess.DEVNULL, stdout=out, stderr=err)
    put(channel / 'dispatch-exit.PUBLIC.json', {'run_id': RUN, 'entry_exit_code': result.returncode,
                                               'entry_exited_utc': now(), 'performance_conclusion': False})


def launch(workspace, grant):
    validate(workspace, grant)
    channel = workspace / 'operator-channel' / RUN
    channel.mkdir(parents=True, mode=0o700)  # no exist_ok: an attempt is never retried
    put(channel / 'dispatch-requested.PUBLIC.json', {'run_id': RUN, 'requested_utc': now(),
                                                   'grant_sha256': hashlib.sha256(grant.read_bytes()).hexdigest(),
                                                   'actual_trigger_confirmed': False})
    process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--worker',
                                '--workspace', str(workspace), '--grant', str(grant)],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
    return {'status': 'DETACHED_ORIGINAL_ENTRY_REQUESTED', 'run_id': RUN, 'supervisor_pid': process.pid,
            'actual_trigger_confirmed': False, 'performance_conclusion': False}


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--launch', action='store_true')
    mode.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--grant', type=Path, required=True)
    args = parser.parse_args()
    if args.worker:
        worker(args.workspace, args.grant, args.workspace / 'operator-channel' / RUN)
    else:
        print(json.dumps(launch(args.workspace, args.grant), sort_keys=True))


if __name__ == '__main__':
    main()
