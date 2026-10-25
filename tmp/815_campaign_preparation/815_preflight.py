"""Neutral operator HTTPS/CLI/scheduler preflight; never an acceptance run."""
import argparse
import hashlib
import http.client
import json
import os
import ssl
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path('/Users/yang/Desktop/nothing/软件开发大作业')
PRIVATE = ROOT / '.agent-worktrees/.runtime/continuation-20261025'
SOURCE = '935ab5b93bea788672c2b4a088c79cfeed848954'


def load(p):
    return json.loads(p.read_text())


def write(p, d):
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(d, f, indent=2)
        f.write('\n')


def main(kind):
    cap = load(ROOT / '.agent-worktrees/deployment-continuation-20261025/agents/deployment/native-performance-20261025/round8' / (kind+'-running-capability.json'))
    run = Path(cap['run_dir'])
    assert cap['source_sha'] == SOURCE
    for path, digest in [('native_build_path', 'native_build_sha256'), ('ca_path', 'ca_sha256')]:
        assert hashlib.sha256(Path(cap[path]).read_bytes()).hexdigest() == cap[digest]
    binding = load(run/'application-binding.json')
    assert binding['source_commit'] == SOURCE
    folder = PRIVATE / ('functional-db-round8' if kind == 'functional' else 'performance-db-round8')
    env = os.environ.copy()
    env.update(load(folder/'application-env.json'))
    env['PYTHONPATH'] = str(Path(binding['application_root'])/'backend')
    dest = PRIVATE/'provisioned'/('round8-'+kind+'-p1')
    dest.mkdir(mode=0o700, exist_ok=False)
    count, project = 0, 1
    if kind == 'functional':
        account = load(folder/'accounts-private.json')['m']
        body = json.dumps({'name':'Coordinator neutral round8 preflight', 'description':'Retained environment preflight; not independent acceptance.'}).encode()
        connection = http.client.HTTPSConnection('127.0.0.1', 18098, context=ssl.create_default_context(cafile=cap['ca_path']), timeout=20)
        try:
            connection.request('POST', '/api/v1/projects', body, {'Authorization':'Bearer '+account['token'], 'Content-Type':'application/json', 'Idempotency-Key':'root-round8-preflight-1'})
            response = connection.getresponse()
            raw = response.read()
            assert response.status == 201, 'Neutral strict-TLS project preflight failed'
            project = json.loads(raw)['data']['project']['id']
            count = 1
        finally:
            connection.close()
    token = dest/'token.json'
    cli = subprocess.run([binding['python'], '-m', 't44.cli', 'service-token', '--name', 'round8-'+kind+'-p1', '--project-id', str(project), '--token-file', str(token)], env=env, cwd=binding['application_root'], capture_output=True, text=True, timeout=40)
    assert cli.returncode == 0, 'Neutral scoped credential CLI failed'
    credential = load(token)
    expiry = datetime.fromisoformat(credential['expires_at']).astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    controller = Path(cap['scope_control_path'])
    result = subprocess.run([binding['python'], str(controller), 'replace', '--run-dir', str(run), '--project-id', str(project), '--token-file', str(token), '--token-expires-utc', expiry], capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, 'Neutral scheduler scope application failed'
    receipt = {'source_sha':SOURCE, 'kind':kind, 'at_utc':datetime.now(UTC).isoformat(), 'root_actual_tls_http':count, 'project_id':project, 'session_id':credential['session_id'], 'expires_at':credential['expires_at'], 'scheduler_stdout':result.stdout, 'scheduler_stderr':result.stderr, 'not_independent_acceptance':True}
    write(dest/'preflight-receipt.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['functional', 'performance'])
    args = parser.parse_args()
    try:
        main(args.kind)
    except BaseException as error:
        raise RuntimeError('Preflight failed and retained; no automatic retry; exception='+type(error).__name__) from None
