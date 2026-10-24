"""One bounded, field-scoped Docker CLI usage snapshot; no automatic sampling."""

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from deployment import ops
from deployment.acceptance.metadata import SERVICES

STATS_FIELDS = {'CPUPerc': 'cpu_percent_cli', 'MemUsage': 'memory_usage_cli', 'MemPerc': 'memory_percent_cli',
                'NetIO': 'network_io_cli', 'BlockIO': 'block_io_cli', 'PIDs': 'pids_cli'}
STATS_TEMPLATE = '{' + ','.join('"' + key + '":{{json .' + key + '}}' for key in ('ID', *STATS_FIELDS)) + '}'
INSPECT_TEMPLATE = ('{"id":{{json .Id}},"project":{{json (index .Config.Labels "com.docker.compose.project")}},'
                    '"service":{{json (index .Config.Labels "com.docker.compose.service")}},'
                    '"running":{{json .State.Running}},"paused":{{json .State.Paused}}}')
LIMITATIONS = [
    'Docker Linux CLI memory subtracts cache; memory_usage_cli is not RSS.',
    'PIDs includes processes and kernel threads, not just processes.',
    'Network/block IO are formatted cumulative quantities, not rates or physical device time.',
    'CPU percentage uses the Docker sampling window, not the whole 600-second load window.',
    'Timestamps enclose the call; six container samples are not atomic or whole-run peaks.',
    'Snapshot wall-clock duration and its workload overhead are real; no claim of zero impact.',
    'No physical-colocation or no-other-traffic conclusion; no past unknown observation is filled in.',
]
ERRORS = {'CONTROL_UNAVAILABLE', 'CONTAINER_ID_INVALID', 'CONTAINER_ID_DUPLICATE', 'CONTAINER_SCOPE_INVALID',
          'CONTAINER_NOT_RUNNING', 'VALIDATION_INCOMPLETE', 'COMMAND_FAILED', 'COMMAND_TIMEOUT',
          'STATS_MISSING', 'STATS_DUPLICATE_ID', 'STATS_FOREIGN_ID', 'STATS_FORMAT_INVALID'}


class ObservationFailure(ValueError):
    def __init__(self, code):
        super().__init__(code if code in ERRORS else 'CONTROL_UNAVAILABLE')
        self.code = str(self)


def now():
    return datetime.now(UTC).isoformat()


def new_report():
    return {'schema_version': 1, 'observation_complete': False, 'started_at_utc': now(), 'finished_at_utc': None,
            'services': {service: {'container_id': None, 'observed': False, 'sample_started_at_utc': None,
                                   'sample_finished_at_utc': None,
                                   **{field: None for field in STATS_FIELDS.values()}, 'error': 'CONTROL_UNAVAILABLE'}
                         for service in SERVICES}, 'limitations': list(LIMITATIONS)}


def fail(report, code):
    code = code if code in ERRORS else 'CONTROL_UNAVAILABLE'
    for row in report['services'].values():
        row.update(observed=False, **{field: None for field in STATS_FIELDS.values()}, error=code)
    report.update(observation_complete=False, finished_at_utc=now())
    return report


def capture(command):
    # No Controls.compose/event logger: raw streams stay in memory and are discarded.
    try:
        result = subprocess.run(command, capture_output=True, timeout=15, check=False)
    except subprocess.TimeoutExpired:
        raise ObservationFailure('COMMAND_TIMEOUT') from None
    if result.returncode:
        raise ObservationFailure('COMMAND_FAILED')
    if len(result.stdout) > 16384:
        raise ObservationFailure('STATS_FORMAT_INVALID')
    return result.stdout


def verified_container(controls, docker, service):
    try:
        result = ops.compose(Path(controls.state['env_file']), controls.values,
                             '--file', controls.state['override_file'], 'ps', '-q', service,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    except subprocess.TimeoutExpired:
        raise ObservationFailure('COMMAND_TIMEOUT') from None
    except subprocess.CalledProcessError:
        raise ObservationFailure('COMMAND_FAILED') from None
    if result.returncode:
        raise ObservationFailure('COMMAND_FAILED')
    container_id = result.stdout.decode('ascii').strip()
    if not re.fullmatch(r'[0-9a-f]{64}', container_id):
        raise ObservationFailure('CONTAINER_ID_INVALID')
    raw = json.loads(capture([*docker, 'inspect', '--type', 'container', '--format', INSPECT_TEMPLATE, container_id]))
    if (raw.get('id') != container_id or raw.get('project') != controls.values['COMPOSE_PROJECT_NAME']
            or raw.get('service') != service):
        raise ObservationFailure('CONTAINER_SCOPE_INVALID')
    if raw.get('running') is not True or raw.get('paused') is not False:
        raise ObservationFailure('CONTAINER_NOT_RUNNING')
    return container_id


def parse_stats(raw, ids):
    try:
        rows = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    except (UnicodeError, ValueError):
        raise ObservationFailure('STATS_FORMAT_INVALID') from None
    expected = set(ids)
    mapped = {}
    quantity = r'[0-9]+(?:[.][0-9]+)?(?:[kKMGTPE]?i?B)'
    pair = quantity + r' / ' + quantity
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'ID', *STATS_FIELDS}
                or not isinstance(row['ID'], str)):
            raise ObservationFailure('STATS_FORMAT_INVALID')
        container_id = row['ID']
        if container_id not in expected:
            raise ObservationFailure('STATS_FOREIGN_ID')
        if container_id in mapped:
            raise ObservationFailure('STATS_DUPLICATE_ID')
        for key in STATS_FIELDS:
            value = row[key]
            pattern = (r'[0-9]+(?:[.][0-9]+)?%' if key in {'CPUPerc', 'MemPerc'} else
                       r'[0-9]+' if key == 'PIDs' else pair)
            if not isinstance(value, str) or not re.fullmatch(pattern, value):
                raise ObservationFailure('STATS_FORMAT_INVALID')
        mapped[container_id] = {target: row[source] for source, target in STATS_FIELDS.items()}
    if set(mapped) != expected:
        raise ObservationFailure('STATS_MISSING')
    return mapped


def collect(controls, report=None):
    report = new_report() if report is None else report
    try:
        docker = ['docker', '--context', controls.values['T44_DOCKER_CONTEXT']]
        valid = True
        for service, row in report['services'].items():
            try:
                row['container_id'] = verified_container(controls, docker, service)
                row['error'] = 'VALIDATION_INCOMPLETE'
            except ObservationFailure as error:
                row['error'] = error.code
                valid = False
            except Exception:  # noqa: BLE001 -- never expose raw driver errors, paths or streams
                row['error'] = 'CONTROL_UNAVAILABLE'
                valid = False
        ids = [row['container_id'] for row in report['services'].values()]
        if not valid:
            report['finished_at_utc'] = now()
            return report
        if len(set(ids)) != len(SERVICES):
            return fail(report, 'CONTAINER_ID_DUPLICATE')
        started = now()
        for row in report['services'].values():
            row['sample_started_at_utc'] = started
        try:
            raw = capture([*docker, 'stats', '--no-stream', '--no-trunc', '--format', STATS_TEMPLATE, *ids])
        finally:
            finished = now()
            for row in report['services'].values():
                row['sample_finished_at_utc'] = finished
        values = parse_stats(raw, ids)
        for row in report['services'].values():
            row.update(observed=True, **values[row['container_id']], error=None)
        report.update(observation_complete=True, finished_at_utc=now())
        return report
    except ObservationFailure as error:
        return fail(report, error.code)
    except Exception:  # noqa: BLE001 -- incomplete JSON, not raw exceptions/credentials
        return fail(report, 'CONTROL_UNAVAILABLE')
