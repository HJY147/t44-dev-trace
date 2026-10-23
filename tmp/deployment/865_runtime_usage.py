"""Synthetic neutral usage boundaries; never invokes Docker or samples a real workload."""

import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from deployment.acceptance import control  # noqa: E402

TOP = {'schema_version', 'observation_complete', 'started_at_utc', 'finished_at_utc', 'services', 'limitations'}
FIELDS = {'container_id', 'observed', 'sample_started_at_utc', 'sample_finished_at_utc', 'cpu_percent_cli',
          'memory_usage_cli', 'memory_percent_cli', 'network_io_cli', 'block_io_cli', 'pids_cli', 'error'}


def test_runtime_usage_cli_declares_and_delegates_single_json(capfd):
    value = {'observation_complete': True, 'synthetic': 'delegated without sampling'}
    with patch.object(control, 'usage', create=True) as usage, patch.object(control, 'Controls'), patch.object(
            sys, 'argv', ['control.py', 'runtime-usage']):
        usage.collect.return_value = value
        assert control.main() == 0
    assert json.loads(capfd.readouterr().out) == value


def fixture():
    usage = importlib.import_module('deployment.acceptance.usage')
    ids = {name: format(index + 1, '064x') for index, name in enumerate(usage.SERVICES)}
    rows = [{'ID': container_id, 'CPUPerc': '12.34%', 'MemUsage': '12.5MiB / 1GiB', 'MemPerc': '1.22%',
             'NetIO': '12kB / 0B', 'BlockIO': '0B / 3.4MB', 'PIDs': '7'} for container_id in ids.values()]
    controls = SimpleNamespace(values={'COMPOSE_PROJECT_NAME': 'synthetic', 'T44_DOCKER_CONTEXT': 'default'},
                               state={'env_file': 'synthetic.env', 'override_file': 'synthetic.yaml'})
    return usage, ids, rows, controls


def collect_synthetic(change=None, invalid=None):
    usage, ids, rows, controls = fixture()
    if change:
        change(rows)
    commands = []

    def compose(*args, **kwargs):
        assert args[-3:-1] == ('ps', '-q')
        service = args[-1]
        value = ids[service]
        if invalid == 'id' and service == 'api':
            value = 'a' * 12
        if invalid == 'duplicate-id' and service == 'api':
            value = ids['mysql']
        return subprocess.CompletedProcess([], 0, (value + '\n').encode(), b'synthetic-private-stderr')

    def run(command, **kwargs):
        commands.append(command)
        assert kwargs['capture_output'] and kwargs['timeout'] <= 15
        if 'stats' in command:
            if invalid == 'timeout':
                raise subprocess.TimeoutExpired(command, 15, output=b'synthetic-secret')
            return subprocess.CompletedProcess(command, 7 if invalid == 'nonzero' else 0,
                                               b'\n'.join(json.dumps(row).encode() for row in rows),
                                               b'synthetic-secret')
        container_id = command[-1]
        service = next(key for key, value in ids.items() if value == container_id)
        data = {'id': container_id, 'project': 'different' if invalid == 'project' else 'synthetic',
                'service': service, 'running': invalid != 'stopped', 'paused': False}
        return subprocess.CompletedProcess(command, 0, json.dumps(data).encode(), b'synthetic-secret')

    with patch.object(usage.ops, 'compose', side_effect=compose), patch.object(usage.subprocess, 'run', side_effect=run):
        result = usage.collect(controls)
    assert 'synthetic-secret' not in json.dumps(result)
    assert 'synthetic-private-stderr' not in json.dumps(result)
    return result, commands


def test_complete_snapshot_uses_six_verified_ids_one_field_scoped_stats():
    result, commands = collect_synthetic()
    assert set(result) == TOP and result['observation_complete']
    assert set(result['services']) == set(control.SERVICES)
    assert all(set(row) == FIELDS and row['observed'] and row['error'] is None for row in result['services'].values())
    stats = [command for command in commands if 'stats' in command]
    assert len(stats) == 1 and '--no-stream' in stats[0] and '--no-trunc' in stats[0]
    assert len(stats[0][-6:]) == 6 and all(len(value) == 64 for value in stats[0][-6:])
    assert '.Name' not in ' '.join(stats[0]) and '{{json .}}' not in ' '.join(stats[0])
    assert all('Config.Env' not in ' '.join(command) for command in commands)
    assert result['services']['api']['memory_usage_cli'] == '12.5MiB / 1GiB'


@pytest.mark.parametrize('invalid', ['id', 'project', 'duplicate-id', 'stopped'])
def test_scope_or_running_failure_never_calls_stats(invalid):
    result, commands = collect_synthetic(invalid=invalid)
    assert not result['observation_complete']
    assert not any('stats' in command for command in commands)
    assert all(row['cpu_percent_cli'] is None and not row['observed'] for row in result['services'].values())


@pytest.mark.parametrize('bad', ['missing', 'duplicate', 'foreign', 'format', 'extra'])
def test_batch_failures_are_null_not_zero_or_untrusted_rows(bad):
    def change(rows):
        if bad == 'missing':
            rows.pop()
        elif bad == 'duplicate':
            rows.append(rows[0])
        elif bad == 'foreign':
            rows[0]['ID'] = 'f' * 64
        elif bad == 'format':
            rows[0]['CPUPerc'] = 'synthetic-secret'
        else:
            rows[0]['Env'] = 'synthetic-secret'
    result, commands = collect_synthetic(change=change)
    assert len([c for c in commands if 'stats' in c]) == 1
    assert not result['observation_complete']
    assert all(row['cpu_percent_cli'] is None and row['pids_cli'] is None and row['error']
               for row in result['services'].values())


@pytest.mark.parametrize('invalid', ['timeout', 'nonzero'])
def test_command_failure_or_timeout_is_structured_redacted(invalid):
    result, _ = collect_synthetic(invalid=invalid)
    assert not result['observation_complete']
    assert all(not row['observed'] and row['error'] for row in result['services'].values())


def test_cli_bad_private_state_is_single_incomplete_json(capfd):
    with patch.object(control, 'Controls', side_effect=OSError('synthetic-secret')), patch.object(
            sys, 'argv', ['control.py', 'runtime-usage']):
        assert control.main() == 1
    output = capfd.readouterr()
    value = json.loads(output.out)
    assert set(value) == TOP and not value['observation_complete']
    assert all(set(row) == FIELDS and row['error'] for row in value['services'].values())
    assert 'synthetic-secret' not in output.out + output.err


def test_legacy_metadata_command_delegation_unchanged(capfd):
    value = {'observation_complete': False, 'old_contract_marker': True}
    with patch.object(control, 'Controls'), patch.object(control.metadata, 'collect', return_value=value), patch.object(
            sys, 'argv', ['control.py', 'runtime-metadata']):
        assert control.main() == 1
    assert json.loads(capfd.readouterr().out) == value
