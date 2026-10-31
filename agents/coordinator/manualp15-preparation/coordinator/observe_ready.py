"""Read host/container PUBLIC metadata only; never a benchmark or acceptance grant."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

LOAD_IMAGE = 'sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1'
FORMAT = '{"id":{{json .Id}},"project":{{json (index .Config.Labels "com.docker.compose.project")}},"role":{{json (index .Config.Labels "com.docker.compose.service")}},"image":{{json .Image}},"running":{{json .State.Running}},"nano_cpus":{{json .HostConfig.NanoCpus}},"memory":{{json .HostConfig.Memory}},"pids_limit":{{json .HostConfig.PidsLimit}}}'


def command(argv):
    result = subprocess.run(argv, capture_output=True, timeout=20, check=False)
    if result.returncode:
        raise ValueError('PUBLIC_OBSERVATION_COMMAND_FAILED')
    return result.stdout.decode()


def observe(role, workspace, run):
    if not re.fullmatch('[A-Za-z0-9_-]+', run) or not workspace.is_absolute():
        raise ValueError('VALID_RUN_AND_ABSOLUTE_WORKSPACE_REQUIRED')
    ids = command(['docker', 'ps', '-q']).split()
    containers = [json.loads(x) for x in command(['docker', 'inspect', '--format', FORMAT, *ids]).splitlines()] if ids else []
    info = {'kind': 'CURRENT_PUBLIC_HOST_METADATA_NOT_AUTHORIZATION', 'role': role,
            'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'cpus': os.cpu_count(), 'running_containers': containers,
            'host_memory_total_kib': next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemTotal:')),
            'free_disk_bytes': shutil.disk_usage(workspace).free,
            'QA_executed_by_observer': False, 'SUT_requests_by_observer': 0,
            'all_possible_external_writers_absent_proven': False}
    if role == 'app':
        info['other_running_container_projects'] = [x for x in containers if x['project'] != 't44-cloud-r30finalp09-p']
    else:
        info['runtime_image_id'] = command(['docker', 'image', 'inspect', '--format', '{{.Id}}', LOAD_IMAGE]).strip()
        info['new_output_exists'] = (workspace / 'results' / run).exists()
        info['new_phase_exists'] = (workspace / 'results' / (run + '.phase.json')).exists()
        info['grant_consumed_exists'] = (workspace / 'runs' / run / 'grant.consumed').exists()
        info['approved_grant_exists'] = (workspace / 'runs' / run / 'grant.json').exists()
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=['app', 'load'], required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--run', default='r30manualp15')
    args = parser.parse_args()
    print(json.dumps(observe(args.role, args.workspace, args.run), sort_keys=True))


if __name__ == '__main__':
    main()
