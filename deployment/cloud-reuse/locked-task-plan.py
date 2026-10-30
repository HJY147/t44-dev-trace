"""Read-only exact-seven Compose plan; never load images or mutate containers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

PROJECT = 't44-cloud-r30finalp09-p'
ROLES = {'mysql', 'rabbitmq', 'api', 'consumer', 'scheduler', 'web', 'tls-gateway'}
TARGETS = ['api', 'consumer', 'scheduler', 'web']
SOURCE = '13acb43a804e717e7485091895378511fe3d9b76'
MANIFEST = '414e3069bddc03adedea3671cb5de7c9382f46f9f44bb77799c5cc7112856bd7'
IMAGES = {'api': 'sha256:766701c81ee873258930346b1fa30986035dd341810ad170a2bcca271ee088fc',
          'consumer': 'sha256:766701c81ee873258930346b1fa30986035dd341810ad170a2bcca271ee088fc',
          'scheduler': 'sha256:766701c81ee873258930346b1fa30986035dd341810ad170a2bcca271ee088fc',
          'web': 'sha256:2fe34a6c88d86017eac8e566c7648b9da8e11c6c4eaf4b89357e8d8f50cf42f4'}
LIMITS = ['CpuPeriod', 'CpuQuota', 'Memory', 'MemorySwap', 'NanoCpus', 'PidsLimit', 'Ulimits']

def need(value, code):
    if not value:
        raise ValueError(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def run(argv):
    p = subprocess.run(argv, capture_output=True, timeout=40, check=False)
    need(p.returncode == 0, 'READONLY_COMMAND_FAILED_PRIVATE_ERROR_WITHHELD')
    return p.stdout

def plan(a):
    need(a.output.is_absolute() and not a.output.exists(), 'NEW_ABSOLUTE_OUTPUT_REQUIRED')
    need(a.manifest_sha256 == MANIFEST and sha((a.package / 'backend-bundle-manifest.json').read_bytes()) == MANIFEST,
         'EXACT_DOWNLOADED_BUNDLE_REQUIRED')
    bundle = json.loads((a.package / 'backend-bundle-manifest.json').read_bytes())
    need(bundle['source_sha'] == SOURCE, 'EXACT_SOURCE_REQUIRED')
    expected = json.loads(a.expected.read_bytes())['containers']
    need(len(expected) == 7 and {r['role'] for r in expected} == ROLES, 'EXPECTED_SEVEN_REQUIRED')
    docker = ['docker', '--context', 'default']
    ids = run(docker + ['ps', '-aq', '--no-trunc', '--filter', 'label=com.docker.compose.project=' + PROJECT]).decode().split()
    need(set(ids) == {r['id'] for r in expected} and len(ids) == 7, 'CURRENT_SEVEN_IDENTITY_REQUIRED')
    actual = json.loads(run(docker + ['inspect', *ids]))
    by_role = {r['Config']['Labels']['com.docker.compose.service']: r for r in actual}
    need(set(by_role) == ROLES, 'CURRENT_SEVEN_ROLES_REQUIRED')
    for e in expected:
        r = by_role[e['role']]
        need(r['Id'] == e['id'] and r['Image'] == e['image_id'] and r['Name'] == e['name']
             and r['Config']['User'] == e['user'] and {k: r['HostConfig'][k] for k in LIMITS} == e['limits'],
             'CURRENT_ID_IMAGE_USER_RESOURCES_CHANGED')
        need(r['Config']['Labels']['com.docker.compose.project'] == PROJECT, 'PROJECT_REQUIRED')
    compose = docker + ['compose', '--project-directory', str(a.directory), '-p', PROJECT]
    for file in a.config:
        need(file.is_absolute() and file.is_file() and not file.is_symlink(), 'EXPLICIT_ORIGINAL_CONFIG_REQUIRED')
        compose += ['-f', str(file)]
    raw = run(compose + ['config', '--format', 'json'])
    need(sha(raw) == a.rendered_config_sha256, 'ROOT_REVIEWED_CURRENT_CONFIG_REQUIRED')
    config = json.loads(raw)
    need(set(config['services']) == ROLES, 'ONLY_ORIGINAL_SEVEN_SERVICES_REQUIRED')
    for role in ROLES:
        need(config['services'][role]['image'] in {by_role[role]['Config']['Image'], by_role[role]['Image']},
             'CURRENT_CONFIG_IMAGE_MISMATCH')
    # Full rendered current config is the baseline. The overlay changes only image/pull_policy.
    new = {'services': {r: {'image': IMAGES[r], 'pull_policy': 'never'} for r in TARGETS}}
    rollback = {'services': {r: {'image': by_role[r]['Image'], 'pull_policy': 'never'} for r in TARGETS}}
    a.output.mkdir(mode=0o700)
    def save(name, value):
        p = a.output / name
        p.write_text(json.dumps(value, indent=2) + '\n'); p.chmod(0o600)
    save('new-images.json', new); save('rollback-images.json', rollback)
    save('before.PRIVATE.json', actual)
    def command(overlay):
        return shlex.join(compose + ['-f', str(a.output / overlay), 'up', '-d', '--no-deps', '--no-build', '--pull', 'never', *TARGETS])
    save('PLAN.PUBLIC.json', {'status': 'PLAN_ONLY_NOT_IMPORTED_OR_APPLIED', 'source': SOURCE,
         'before_ids': ids, 'manifest_sha256': MANIFEST, 'rendered_config_sha256': sha(raw),
         'config_files': {str(f): sha(f.read_bytes()) for f in a.config},
         'apply_after_import_and_root_preflight': command('new-images.json'),
         'rollback_same_original_configuration': command('rollback-images.json'),
         'postcheck_required': 'New seven-role snapshot; unchanged infra IDs/volumes/resources and app Env/Cmd/worker/pool/TLS/health; new image IDs/runtime source; refreshed scheduler credential and new independent admission.',
         'cloud_or_container_mutation_executed': False})
    print(json.dumps({'status': 'PLAN_ONLY_NOT_APPLIED', 'output': str(a.output)}))

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected', type=Path, required=True)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--manifest-sha256', required=True)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--config', type=Path, action='append', required=True)
    p.add_argument('--rendered-config-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    try:
        plan(p.parse_args())
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired):
        raise SystemExit('PLAN_REFUSED_NO_MUTATION; inspect approved inputs privately') from None
