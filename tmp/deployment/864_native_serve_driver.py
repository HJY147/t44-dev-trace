"""Single admitted native360 retest, outside unchanged reviewed controller."""
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

os.umask(0o077)
PROJECT = Path('/Users/yang/Desktop/nothing/软件开发大作业')
WORK = PROJECT / '.agent-worktrees/deployment-bounded-demo'
AUDIT = PROJECT / '.agent-worktrees/.runtime/native-demo-20261023/bounded-retest-20261023'
EXPECTED = '08461886f631e070b206d1533be8be320a90eeea27a0f813795d970f7d9a1e25'
IMPLEMENTATION = '62ac2f327e7523ffed69a2bd9f98c87ba2372931'
PORTS = (5173, 18080, 5175, 18084, 5176, 18089, 13306, 5177, 18086)
SPEC = importlib.util.spec_from_file_location('bounded_retest_app', WORK / 'deployment/native/application.py')
appmod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(appmod)

def now():
    return datetime.now(UTC).isoformat()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(name, value):
    appmod.private_write(AUDIT / name, appmod.json_bytes(value))

def listener_snapshot():
    ports = {}
    for port in PORTS:
        result = subprocess.run(['/usr/sbin/lsof', '-nP', '-a', f'-iTCP:{port}', '-sTCP:LISTEN', '-Fpn'],
                                capture_output=True, text=True, check=False)
        if result.returncode not in (0, 1) or result.stderr:
            raise RuntimeError('PROTECTED_LISTENER_OBSERVATION_FAILED')
        pids = sorted({int(line[1:]) for line in result.stdout.splitlines() if line.startswith('p')})
        identities = []
        for pid in pids:
            identity = appmod.process_identity(pid)
            if identity is None:
                raise RuntimeError('PROTECTED_LISTENER_IDENTITY_UNAVAILABLE')
            identities.append({key: identity[key] for key in ('pid', 'uid', 'started', 'pgid', 'command_sha256')})
        ports[str(port)] = {'listeners': identities,
                            'addresses': sorted({line[1:] for line in result.stdout.splitlines() if line.startswith('n')})}
    if not ports['5177']['listeners'] or not ports['18086']['listeners']:
        raise RuntimeError('CURRENT_PROTECTED_V3_LISTENER_REQUIRED')
    return {'at_utc': now(), 'ports': ports}

assert sha((WORK / 'deployment/native/application.py').read_bytes()) == EXPECTED
assert sha((WORK / 'deployment/native/runtime.py').read_bytes()) == 'a251989f589943bf513fa506015a7bba356fbb167a525a7fd79a29306689fa6b'
before_prepare = listener_snapshot()
save('protected-before-prepare.json', before_prepare)
old = json.loads((PROJECT / '.agent-worktrees/.runtime/native-demo-20261023/bounded-validation-20261023/prepare-receipt.json').read_text())
argv = old['argv']
start = now()
prepared = subprocess.run(argv, cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
for suffix, raw in (('stdout', prepared.stdout), ('stderr', prepared.stderr)):
    appmod.private_write(AUDIT / ('prepare.' + suffix), raw)
save('prepare-receipt.json', {'started_at_utc': start, 'ended_at_utc': now(), 'argv': argv,
                            'exit_code': prepared.returncode, 'stdout_sha256': sha(prepared.stdout),
                            'stderr_sha256': sha(prepared.stderr), 'controller_sha256': EXPECTED})
if prepared.returncode != 0:
    raise RuntimeError('FRESH_PREPARE_FAILED')
run = Path(json.loads(prepared.stdout)['run_dir'])
app = appmod.Application(PROJECT, run)
assert app.manifest['controller_sha256'] == EXPECTED
assert app.manifest['source_commit'] == appmod.NATIVE_DEMO_SOURCE
appmod.assert_app_ports_free()
before_serve = listener_snapshot()
save('protected-before-serve.json', before_serve)
assert before_prepare['ports'] == before_serve['ports'], 'PROTECTED_BASELINE_CHANGED_BEFORE_SERVE'
save('run.json', {'run_dir': str(run), 'controller_implementation': IMPLEMENTATION,
                  'controller_sha256': EXPECTED, 'source_commit': appmod.NATIVE_DEMO_SOURCE,
                  'broker_run': str(app.broker.run), 'source_files_verified': len(app.binding['source_files']),
                  'protected9_before_prepare_equals_before_serve': True})
argv = [str(app.python), 'deployment/native/application.py', '--project-root', str(PROJECT),
        'serve', '--run-dir', str(run), '--duration', '360']
start = now()
with (AUDIT / 'serve.stdout').open('xb') as stdout, (AUDIT / 'serve.stderr').open('xb') as stderr:
    process = subprocess.Popen(argv, cwd=WORK, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                               start_new_session=True)
    save('serve-launch.json', {'started_at_utc': start, 'argv': argv, 'pid': process.pid,
                               'duration_requested': 360, 'source_implementation': IMPLEMENTATION})
    print(json.dumps({'phase': 'started', 'run': run.name, 'controller_sha256': EXPECTED,
                      'protected9_baseline_match': True, 'at_utc': now()}), flush=True)
    deadline = time.monotonic() + 600
    previous = None
    while process.poll() is None and time.monotonic() < deadline:
        status = run / 'state/serve-status.json'
        if status.exists():
            data = json.loads(status.read_text())
            current = data['phase'], data['additional_rotations']
            if current != previous:
                print(json.dumps({key: data.get(key) for key in ('phase', 'at_utc', 'started_at_utc',
                      'deadline_at_utc', 'capability_ready', 'additional_rotations', 'stop_reason')}), flush=True)
                previous = current
        time.sleep(1)
    unconfirmed = process.poll() is None
    code = None if unconfirmed else process.wait()
    save('serve-driver-receipt.json', {'started_at_utc': start, 'ended_at_utc': now(), 'argv': argv,
         'actual_exit_code': code, 'wait600_unconfirmed': unconfirmed,
         'stdout_sha256': sha((AUDIT / 'serve.stdout').read_bytes()),
         'stderr_sha256': sha((AUDIT / 'serve.stderr').read_bytes()),
         'external_driver_wait_confirmed_runner_exit': not unconfirmed})
    if unconfirmed:
        print(json.dumps({'phase': 'runner_wait_unconfirmed', 'actual_exit_code': None}), flush=True)
        raise SystemExit(2)
after = listener_snapshot()
save('protected-after-finish.json', after)
matches = {port: before_prepare['ports'][port] == before_serve['ports'][port] == after['ports'][port]
           for port in before_prepare['ports']}
save('protected-comparison.json', {'at_utc': now(), 'ports': matches, 'all9_exact_match': all(matches.values()),
                                  'covers_only_this_retest': True, 'old7_snapshot_not_rewritten': True})
print(json.dumps({'phase': 'external_runner_exited', 'actual_exit_code': code,
                  'protected9_exact_match': all(matches.values()), 'at_utc': now()}), flush=True)
raise SystemExit(code if all(matches.values()) else 3)
