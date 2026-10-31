"""APP-local direct initialization. No SSH, image change, scan gate or benchmark."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

SOURCE = 'bcec3326b40814fdb1922bbfea7c29473b47ba47'
IDS = {
    'mysql': 'ecb591df0b96f4ab774225b478f26fbd6652d16ef57bc277b54600e8e830cc9e',
    'rabbitmq': '97918f928d25ae8ad235337bab3d9c547ac1836c92942e97d07fd510b60f711e',
    'tls': '855882b40173e31083a95e06eca62da94a57a8a765d17df3c74709ea21f010bf',
    'api': 'a92f1db5890ab8b2b0c8a2cb3104d1c96520ac18cbbe348125a4c7598f3c6f44',
    'web': '402ff7e0601826bfcbf8873f58e6034749827ac626e8f2251bf6b716f144c9cc',
    'consumer': '6147918a252aa31ffba89af4706960f020a7a12d568fceabb63961124bfe4e4f',
    'scheduler': 'd2ea97d46f7b9c0f482447598054cc70c654ae0e2085a1ec017adcebc9d2eb49',
}
P09 = Path('/root/t44-final-20261029/P09')
TOKEN = P09 / 'campaign/p/scheduler-secrets/scheduler-token.json'
PINS = {
    'bootstrap.py': 'ba0c8ab216dd643ed83a27d2ce4479b459ad998451c9530238f2134658dbd72d',
    'runtime_support.py': 'bec01e4038ef4ca5d6ba6d048e96fb8c7cb32933f705fd65a6995d24d9753170',
}


def need(ok, code):
    if not ok:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    need(path.is_absolute() and path.resolve() == path, 'CANONICAL_FILE_REQUIRED')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        st = os.fstat(f.fileno())
        need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_size <= 2000000,
             'BOUNDED_REGULAR_FILE_REQUIRED')
        raw = f.read(2000001)
        end = os.fstat(f.fileno())
    need((st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns) ==
         (end.st_dev, end.st_ino, end.st_size, end.st_mtime_ns) and len(raw) == st.st_size,
         'STABLE_FILE_REQUIRED')
    return raw, st


def syncdir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write(path, raw, uid=None, gid=None):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        if uid is not None:
            os.fchown(f.fileno(), uid, gid)
        os.fchmod(f.fileno(), 0o600)
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())


def public(path, value):
    write(path, (json.dumps(value, sort_keys=True) + '\n').encode())


def rotate(source, target, backup_dir):
    new, ns = read(source)
    need(stat.S_IMODE(ns.st_mode) == 0o600, 'PRIVATE_NEW_CREDENTIAL_REQUIRED')
    value = json.loads(new)
    need(isinstance(value.get('access_token'), str) and bool(value['access_token']), 'CLI_TOKEN_REQUIRED')
    old, st = read(target)
    need(stat.S_IMODE(st.st_mode) == 0o600, 'PRIVATE_EXISTING_CREDENTIAL_REQUIRED')
    backup_dir.mkdir(mode=0o700, exist_ok=False)
    write(backup_dir / 'scheduler-token.original.private.json', old, st.st_uid, st.st_gid)
    syncdir(backup_dir)
    syncdir(backup_dir.parent)
    fd, name = tempfile.mkstemp(prefix='.direct-token-', dir=target.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as f:
            os.fchown(f.fileno(), st.st_uid, st.st_gid)
            os.fchmod(f.fileno(), 0o600)
            f.write(new)
            f.flush()
            os.fsync(f.fileno())
        current, cs = read(target)
        need(current == old and (cs.st_dev, cs.st_ino, cs.st_uid, cs.st_gid) ==
             (st.st_dev, st.st_ino, st.st_uid, st.st_gid), 'TOKEN_CHANGED_NO_REPLACE')
        os.replace(tmp, target)
        syncdir(target.parent)
    finally:
        if tmp.exists():
            tmp.unlink()
    actual, after = read(target)
    need(actual == new and (after.st_uid, after.st_gid) == (st.st_uid, st.st_gid)
         and stat.S_IMODE(after.st_mode) == 0o600, 'ROTATION_READBACK_FAILED')
    result = {'status': 'DIRECT_TOKEN_ATOMIC_REPLACEMENT', 'original_bytes_preserved': True,
              'old_sha256': digest(old), 'new_sha256': digest(new),
              'backup': str(backup_dir / 'scheduler-token.original.private.json'),
              'uid': after.st_uid, 'gid': after.st_gid, 'mode': '0600'}
    public(backup_dir / 'rotation.PUBLIC.json', result)
    return result


def command(argv, output, label, runner):
    result = runner(argv, capture_output=True, check=False)
    write(output / (label + '.stdout.private'), result.stdout)
    write(output / (label + '.stderr.private'), result.stderr)
    need(result.returncode == 0, label.upper() + '_FAILED_NO_RETRY')


def execute(backend, run_id, output, runner=subprocess.run, target=TOKEN):
    need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,100}', run_id), 'SAFE_RUN_ID_REQUIRED')
    need(output.is_absolute() and output.parent.resolve() == output.parent,
         'CANONICAL_OUTPUT_REQUIRED')
    for name, expected in PINS.items():
        need(digest(read(backend / name)[0]) == expected, 'BACKEND_TOOL_SHA_MISMATCH')
    output.mkdir(mode=0o700, exist_ok=False)
    phase = 'infra'
    try:
        command(['docker', '--context', 'default', 'start'] +
                [IDS[k] for k in ('mysql', 'rabbitmq', 'tls', 'api', 'web')],
                output, 'infra-start', runner)
        phase = 'bootstrap'
        bootstrap = output / 'bootstrap'
        command([sys.executable, '-B', str(backend / 'bootstrap.py'),
                 '--old-packet', str(P09 / 'P-packet/output/packet/inputs/session.private.json'),
                 '--accounts', str(P09 / 'P-accounts/output/accounts.initialized.private.json'),
                 '--ca', str(P09 / 'P-packet/output/packet/inputs/ca.pem'),
                 '--runtime-support', str(backend / 'runtime_support.py'),
                 '--import-receipt', '/root/t44-p15-live-20261031/backend-import-receipt.json',
                 '--api-container', IDS['api'], '--gateway-dns', 'tls-gateway',
                 '--connect-port', '8443', '--run-id', run_id, '--output', str(bootstrap)],
                output, 'bootstrap', runner)
        receipt = json.loads(read(bootstrap / 'bootstrap.PUBLIC.json')[0])
        inputs = json.loads(read(bootstrap / 'current-inputs.private.json')[0])
        need(receipt.get('status') == 'DIRECT_INITIALIZATION_COMPLETE' and
             receipt.get('run_id') == run_id and receipt.get('source_expected') == SOURCE and
             inputs.get('schema') == 'DIRECT_INPUTS_V1' and inputs.get('run_id') == run_id,
             'DIRECT_BOOTSTRAP_RESULT_REQUIRED')
        phase = 'rotation'
        cli = json.loads(read(bootstrap / 'service-cli.original.private.json')[0])
        need(cli.get('access_token') == inputs.get('sessions', {}).get('service', {}).get('token')
             and bool(cli.get('access_token')), 'CURRENT_SERVICE_CREDENTIAL_MATCH_REQUIRED')
        rotate(bootstrap / 'service-cli.original.private.json', target, output / 'rotation')
        phase = 'workers'
        command(['docker', '--context', 'default', 'start', IDS['consumer'], IDS['scheduler']],
                output, 'workers-start', runner)
        result = {'status': 'INIT_DONE', 'mode': 'DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE',
                  'run_id': run_id, 'bootstrap_output': str(bootstrap),
                  'private_inputs': str(bootstrap / 'current-inputs.private.json'),
                  'source_expected': SOURCE, 'benchmark_started': False,
                  'fullscan_waited': False, 'automatic_retry': False}
        public(output / 'INIT_DONE.PUBLIC.json', result)
        return result
    except BaseException:
        public(output / 'FAILED.PUBLIC.json', {'status': 'FAILED_STOP_CHAIN', 'phase': phase,
               'automatic_retry': False, 'partial_changes_retained': True,
               'credentials_may_have_been_issued': phase != 'infra', 'benchmark_started': False})
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend-dir', type=Path, required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    os.umask(0o077)
    need(os.geteuid() == 0, 'APP_ROOT_REQUIRED')
    try:
        result = execute(a.backend_dir, a.run_id, a.output)
    except Exception as exc:
        print(json.dumps({'status': 'INIT_FAILED', 'error_type': type(exc).__name__,
                          'output': str(a.output), 'automatic_retry': False}))
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
