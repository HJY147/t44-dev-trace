"""Archive only official T44 Actions bytes and metadata; never run product tests."""
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile

REPO = 'HJY147/t44-dev-trace'
RUNS = {
    40200930857: 'a16238b9eb3b47473c0332989d6b3dcc1d95d1f4',
    40200930957: 'a16238b9eb3b47473c0332989d6b3dcc1d95d1f4',
    40201584671: 'f4bd382d4668130793fc553df9ce6363c4656ea6',
    40201584699: 'f4bd382d4668130793fc553df9ce6363c4656ea6',
}


def acquire(endpoint, path):
    if not path.exists():
        with path.open('xb') as handle:
            completed = subprocess.run(['gh', 'api', endpoint], stdout=handle, stderr=subprocess.PIPE)
        if completed.returncode:
            partial = path.with_name(path.name + '.failed-attempt-next')
            assert not partial.exists()
            path.rename(partial)
            raise RuntimeError(f'Official API download failed, exit {completed.returncode}; partial retained as {partial}; redirect URL omitted')
    return path.read_bytes()


def validate_zip(path):
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None, path
        members = []
        seen = set()
        for item in archive.infolist():
            name = item.filename
            assert name not in seen, ('duplicate zip path', name)
            seen.add(name)
            assert not PurePosixPath(name).is_absolute(), name
            assert '..' not in PurePosixPath(name).parts, name
            assert '\\' not in name and '\x00' not in name, name
            assert not stat.S_ISLNK(item.external_attr >> 16), name
            members.append({
                'path': name, 'bytes': item.file_size,
                'crc32': f'{item.CRC:08x}',
                'sha256': hashlib.sha256(archive.read(item)).hexdigest(),
            })
    return {
        'file': path.name, 'bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(),
        'zip_crc_all_passed': True,
        'unsafe_paths_or_symlinks': False, 'members': members,
    }


def collect(run_id, expected_sha):
    root = Path('records/ci') / str(run_id)
    root.mkdir(parents=True, exist_ok=True)
    prefix = f'repos/{REPO}/actions'
    run = json.loads(acquire(f'{prefix}/runs/{run_id}', root / 'run-rest.json'))
    jobs = json.loads(acquire(f'{prefix}/runs/{run_id}/jobs?per_page=100', root / 'jobs.json'))
    artifacts = json.loads(acquire(f'{prefix}/runs/{run_id}/artifacts?per_page=100', root / 'artifacts-rest.json'))
    assert run['id'] == run_id and run['head_sha'] == expected_sha
    assert run['event'] == 'push' and run['head_branch'] == 'codex/integration'
    assert run['run_attempt'] == 1 and run['status'] == 'completed'
    assert jobs['total_count'] == len(jobs['jobs'])
    assert artifacts['total_count'] == len(artifacts['artifacts'])
    for job in jobs['jobs']:
        assert job['run_id'] == run_id and job['head_sha'] == expected_sha
        assert job['run_attempt'] == run['run_attempt']
    bound_artifacts = []
    for artifact in artifacts['artifacts']:
        assert artifact['workflow_run']['id'] == run_id
        assert artifact['workflow_run']['head_sha'] == expected_sha
        assert artifact['workflow_run']['head_branch'] == run['head_branch']
        assert artifact['name'].endswith('-' + expected_sha)
        assert not artifact['expired']
        path = root / (artifact['name'] + '.zip')
        acquire(f"{prefix}/artifacts/{artifact['id']}/zip", path)
        checked = validate_zip(path)
        assert checked['bytes'] == artifact['size_in_bytes']
        assert 'sha256:' + checked['sha256'] == artifact['digest']
        name = artifact['name'].removesuffix('-' + expected_sha)
        job = next(job for job in jobs['jobs'] if job['name'] == name)
        checked.update({
            'artifact_id': artifact['id'], 'artifact_name': artifact['name'],
            'official_size': artifact['size_in_bytes'],
            'official_digest': artifact['digest'],
            'official_size_digest_match': True,
            'artifact_run_head_binding': True,
            'job_id': job['id'], 'job_conclusion': job['conclusion'],
        })
        bound_artifacts.append(checked)
    logs_path = root / 'official-run-logs.zip'
    acquire(f'{prefix}/runs/{run_id}/logs', logs_path)
    logs = validate_zip(logs_path)
    logs['acquisition_endpoint'] = f'https://api.github.com/{prefix}/runs/{run_id}/logs'
    logs['official_digest_available'] = False
    binding = {
        'schema_version': 2,
        'collected_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'run_id': run_id, 'source_sha': expected_sha,
        'head_branch': run['head_branch'], 'event': run['event'],
        'run_attempt': run['run_attempt'], 'run_number': run['run_number'],
        'status': run['status'], 'conclusion': run['conclusion'],
        'jobs': [{key: job.get(key) for key in ['id', 'name', 'run_id', 'run_attempt', 'head_sha', 'status', 'conclusion', 'started_at', 'completed_at', 'html_url']} for job in jobs['jobs']],
        'artifacts': bound_artifacts, 'official_run_logs': logs,
        'metadata_pages_complete': True,
        'acquisition': 'Official gh REST GET JSON and original binary ZIP output; no extraction/repackaging used to infer ZIP integrity. Connector metadata retained separately.',
        'limits': ['API JSON representation is not original HTTP transport bytes', 'logs endpoint exposes no server digest; calculated local digest only', 'CI/Docker do not establish independent acceptance, formal performance, source-size compliance or final billing'],
    }
    (root / 'archive-binding.json').write_text(json.dumps(binding, ensure_ascii=False, indent=2) + '\n')
    return {'run_id': run_id, 'conclusion': run['conclusion'], 'artifacts': len(bound_artifacts), 'zip_bytes': sum(item['bytes'] for item in bound_artifacts), 'log_bytes': logs['bytes']}


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(collect, run, sha) for run, sha in RUNS.items()]
        for future in concurrent.futures.as_completed(futures):
            print(json.dumps(future.result()), flush=True)
