import argparse,json,os,subprocess,time,secrets,hashlib
from pathlib import Path
from datetime import datetime,timezone
def need(value, code):
    if not value:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def put(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return value


def command(argv, timeout=20, allow_not_found=False):
    result = subprocess.run(list(map(str, argv)), capture_output=True, timeout=timeout, check=False)
    missing_unit = allow_not_found and result.returncode == 1 and b'LoadState=not-found' in result.stdout.splitlines()
    need(result.returncode == 0 or missing_unit, 'CHILD_FAILED_NO_PRIVATE_OUTPUT')
    return result.stdout


SCAN_CODE = """from t44.persistence import SqlAlchemyUnitOfWorkFactory,create_mysql_engine
from t44.settings import Settings
from t44.services.common import wire
import json
settings=Settings.from_env().mysql_settings()
assert settings.database == 't44c_r30finalp09_p'
f=SqlAlchemyUnitOfWorkFactory(create_mysql_engine(settings))
with f() as u:
 rows=u.gateway.rows('scan_runs',{},order_by=('-id',),limit=4)
print(json.dumps(wire([{k:r.get(k) for k in ['id','status','started_at','heartbeat_at','finished_at','error_code','scanned_count','created_count','duplicate_count']} for r in rows])))
"""


def scan_after_rotation(api, completed, output, seconds=150):
    deadline = time.monotonic() + seconds
    threshold = datetime.fromisoformat(completed.replace('Z', '+00:00'))
    while True:
        remaining = deadline - time.monotonic()
        need(remaining > 0, 'NO_SUCCESSFUL_POST_ROTATION_SCAN_WITHIN_BOUND')
        rows = json.loads(command(['docker', '--context', 'default', 'exec', api, 'python', '-B', '-c', SCAN_CODE],
                                  timeout=min(10, remaining)))
        receipt = {'rotation_completed_utc': completed, 'rows': rows,
                   'observed_utc': datetime.now(timezone.utc).isoformat(),
                   'new_scanner_started': False, 'business_event_manually_created': False,
                   'proof_kind': 'existing_persistent_scanner_native_authenticated_runtime_not_HTTP_probe'}
        # Keep every original observation, including failures, without rewriting it.
        put(output / ('scan-' + secrets.token_hex(6) + '.PUBLIC.json'), receipt)
        fresh = [r for r in rows if r.get('started_at') and r.get('finished_at') and
                 datetime.fromisoformat(r['started_at'].replace('Z', '+00:00')) >= threshold and
                 datetime.fromisoformat(r['finished_at'].replace('Z', '+00:00')) >= threshold]
        need(not any(r['status'] == 3 or r.get('error_code') is not None for r in fresh),
             'POST_ROTATION_SCAN_REPORTED_FAILURE')
        success = [r for r in fresh if r['status'] == 2 and r.get('error_code') is None and r.get('scanned_count', 0) > 0]
        if success:
            receipt['successful_new_scan_ids'] = [r['id'] for r in success]
            return put(output / 'scanner.PUBLIC.json', receipt)
        time.sleep(min(5, max(0, deadline - time.monotonic())))

def verify_current_api(api):
 import rotate_current
 snapshot=json.loads((Path(__file__).parent/'P09-existing-containers.PUBLIC.json').read_bytes())
 rotate_current.validate_snapshot(snapshot)
 expected=next(r for r in snapshot['containers'] if r['role']=='api')
 need(api==expected['id'],'CURRENT_API_ID_REQUIRED')
 row=json.loads(command(['docker','--context','default','inspect','--format','{{json .Image}}',api]))
 need(row==rotate_current.IMAGE,'CURRENT_API_IMAGE_REQUIRED')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--api',required=True);p.add_argument('--rotation',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();v=json.loads(a.rotation.read_bytes());need(v['status']=='SCHEDULER_TOKEN_FILE_ATOMICALLY_REPLACED_NOT_SCANNER_USE_PROOF','ROTATION_RECEIPT_REQUIRED');verify_current_api(a.api);a.output.mkdir(mode=0o700);scan_after_rotation(a.api,v['rotation_completed_utc'],a.output,seconds=900)
