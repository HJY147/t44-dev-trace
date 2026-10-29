#!/usr/bin/env bash
# Read-only exact seven-image/archive diagnosis; no load, tag, pull, removal or installation.
set -euo pipefail
python3 - <<'T44_IMAGE_IDENTITY_PROBE'
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import tarfile
from pathlib import Path

BUNDLE = Path('/root/t44-r9/bundle-935')
EXPECTED = '3c599b31922d55822cb845abc768ea8c2db668d469d6d6bf330378bcb1ac7ec4'
HELPER = Path('/root/t44-r9/image-bundle.py')
HELPER_SHA = '0a1c2cd5bf57717ba5218ff6bb5086d6acbb60ff54713940a6da73f495a1cfcd'
DOCKER = ['docker', '--context', 'default']
ENV = {k:v for k,v in os.environ.items() if k not in {'DOCKER_HOST','DOCKER_CONTEXT','DOCKER_CONFIG'}}


def emit(kind, **values):
    print(json.dumps({'kind':kind, **values}), flush=True)


def run(argv):
    try:
        result = subprocess.run(argv, env=ENV, capture_output=True, timeout=15, check=False)
        return result.returncode, result.stdout.decode(errors='replace'), result.stderr.decode(errors='replace')[:512]
    except subprocess.TimeoutExpired:
        return None, '', 'timed_out'


raw = (BUNDLE/'bundle-manifest.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED, 'exact trusted manifest mismatch'
assert hashlib.sha256(HELPER.read_bytes()).hexdigest() == HELPER_SHA, 'exact uploaded helper mismatch'
manifest = json.loads(raw)
assert set(manifest['images']) == {'python','node','nginx','mysql','rabbitmq','backend','web'}
spec = importlib.util.spec_from_file_location('approved_bundle_readonly', HELPER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
emit('host', platform=platform.system(), architecture=platform.machine(), disk_free_bytes=shutil.disk_usage(BUNDLE).free,
     manifest_sha256=EXPECTED, source_sha=manifest['source_sha'], helper_sha256=HELPER_SHA,
     context=run(['docker','context','inspect','default','--format','{{json .Endpoints}}']),
     engine=run(DOCKER+['info','--format','{{json .ServerVersion}} {{json .Driver}} {{json .DriverStatus}} {{json .OSType}} {{json .Architecture}}']))
for role, declared in manifest['images'].items():
    code, stdout, stderr = run(DOCKER+['image','inspect',declared['alias']])
    projection = None
    if code == 0:
        rows = json.loads(stdout)
        if len(rows) == 1:
            value = rows[0]
            projection = {key:value.get(key) for key in ['Id','RepoTags','RepoDigests','Descriptor','RootFS','Os','Architecture','Variant','Size']}
            projection['Config.Labels'] = (value.get('Config') or {}).get('Labels')
    try:
        guard = {'success':True, 'observed':module.inspect_image(declared['alias'])}
    except (ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        guard = {'success':False, 'error_class':type(error).__name__, 'reason':str(error)}
    emit('exact_alias', role=role, declared=declared, inspect_exit=code, inspect_stderr=stderr,
         actual=projection, current_inspect_guard=guard)

# No extraction or member execution. Only bounded small JSON records are parsed; Env/Cmd are never emitted.
small = {}
total_members = 0
with tarfile.open(BUNDLE/'images.tar.gz', mode='r|gz') as archive:
    for member in archive:
        total_members += 1
        if not member.isfile() or member.size > 2*1024*1024:
            continue
        if member.name not in {'manifest.json','index.json','oci-layout'} and not (member.name.endswith('.json') or member.name.startswith('blobs/sha256/')):
            continue
        data = archive.extractfile(member).read()
        try:
            value = json.loads(data)
        except (ValueError, UnicodeError):
            continue
        if member.name in {'manifest.json','index.json','oci-layout'}:
            small[member.name] = {'sha256':hashlib.sha256(data).hexdigest(),'value':value}
            emit('archive_index', member=member.name, sha256=small[member.name]['sha256'], value=value)
        elif isinstance(value,dict) and ('rootfs' in value or 'config' in value or 'mediaType' in value):
            projection = {key:value.get(key) for key in ['architecture','os','rootfs','mediaType','schemaVersion','config','layers','manifests'] if key in value}
            if 'rootfs' in value:
                projection.pop('config',None)
                projection['Config.Labels'] = (value.get('config') or {}).get('Labels')
            record = {'sha256':hashlib.sha256(data).hexdigest(),'value':projection}
            small[member.name] = record
            emit('archive_config_or_descriptor', member=member.name, **record)
if 'manifest.json' in small:
    for row in small['manifest.json']['value']:
        config = small.get(row.get('Config',''))
        emit('archive_tag_config_binding', tags=row.get('RepoTags'), config_member=row.get('Config'),
             actual_config_sha256=config['sha256'] if config else None,
             declared_roles=[role for role,value in manifest['images'].items() if value['alias'] in (row.get('RepoTags') or [])])
emit('probe_complete', read_only=True, mutation_performed=False, credentials_or_environment_dumped=False,
     tar_members_seen=total_members, small_json_records=len(small), image_load_pass_claim=False)
T44_IMAGE_IDENTITY_PROBE
