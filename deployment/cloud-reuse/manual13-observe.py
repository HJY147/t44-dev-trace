"""Bounded, read-only host-side Docker observations; never sends SUT HTTP or starts load."""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROLES = ('api', 'mysql', 'rabbitmq', 'consumer', 'scheduler', 'web', 'tls-gateway')
DOCKER = ['docker', '--context', 'default']
DEADLINE = None
FORMAT = '{{json .Id}}\n{{json .Image}}\n{{json .State.Running}}\n{{json .HostConfig}}'
CGROUP = '''for f in cpu.stat cpu.max cpuset.cpus.effective memory.current memory.max memory.events pids.current pids.max io.stat io.pressure; do
printf '%s\\n' "FILE:$f"; cat "/sys/fs/cgroup/$f" 2>/dev/null || true; done'''
PROCESS = r'''import json,os
from pathlib import Path
rows=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal(): continue
 try:
  args=(p/'cmdline').read_bytes().split(b'\0')
  worker=len(args)>3 and args[1]==b'-c' and args[2].startswith(b'from multiprocessing.spawn import spawn_main;') and b'--multiprocessing-fork' in args
  supervisor=args[1:4]==[b'-m',b'uvicorn',b't44.api:app']
  kind='worker' if worker else 'supervisor' if supervisor else None
  if kind is None: continue
  raw=(p/'stat').read_text(); s=raw[raw.rfind(')')+2:].split()
  workers=int(args[args.index(b'--workers')+1]) if supervisor and b'--workers' in args else None
  rows.append(dict(pid=int(p.name),kind=kind,configured_workers=workers,ppid=int(s[1]),user_ticks=int(s[11]),system_ticks=int(s[12]),threads=int(s[17]),start_ticks=int(s[19]),rss_bytes=int(s[21])*os.sysconf('SC_PAGE_SIZE')))
 except (FileNotFoundError,PermissionError,ProcessLookupError): pass
print(json.dumps(dict(clock_ticks=os.sysconf('SC_CLK_TCK'),processes=rows,pool={k:os.getenv(k) for k in ('T44_DB_POOL_SIZE','T44_DB_MAX_OVERFLOW')})))'''
STATUS = ('Threads_connected', 'Threads_running', 'Max_used_connections', 'Connections', 'Uptime',
          'Innodb_row_lock_current_waits', 'Innodb_row_lock_waits', 'Innodb_row_lock_time',
          'Innodb_buffer_pool_reads', 'Innodb_buffer_pool_read_requests', 'Innodb_data_reads',
          'Innodb_data_writes', 'Innodb_data_read', 'Innodb_data_written', 'Innodb_log_waits',
          'Com_commit', 'Com_rollback', 'Handler_commit', 'Binlog_commits', 'Binlog_group_commits',
          'Innodb_os_log_fsyncs', 'Innodb_data_fsyncs', 'Innodb_os_log_written', 'Innodb_log_writes',
          'Innodb_buffer_pool_pages_total', 'Innodb_buffer_pool_pages_data', 'Innodb_buffer_pool_pages_dirty',
          'Innodb_buffer_pool_pages_free', 'Innodb_buffer_pool_wait_free', 'Innodb_buffer_pool_bytes_data',
          'Innodb_buffer_pool_bytes_dirty', 'Innodb_buffer_pool_pages_flushed',
          'Innodb_lsn_current', 'Innodb_lsn_flushed', 'Innodb_lsn_last_checkpoint',
          'Innodb_redo_log_current_lsn', 'Innodb_redo_log_checkpoint_lsn',
          'Innodb_redo_log_flushed_to_disk_lsn', 'Innodb_redo_log_logical_size',
          'Innodb_redo_log_physical_size', 'Innodb_redo_log_capacity_resized')
TEXT_STATUS = {'Innodb_redo_log_resize_status': {'OK', 'Resizing down', 'Resizing up'}}
SQL = ("SELECT 'CAPACITY',@@GLOBAL.max_connections; SHOW GLOBAL STATUS WHERE Variable_name IN (" +
       ','.join("'" + k + "'" for k in (*STATUS, *TEXT_STATUS)) + "); SELECT 'LOCKS',COUNT(*) FROM performance_schema.data_lock_waits; "
       "SELECT 'DIGEST_TOTAL',COUNT(*),COALESCE(SUM(COUNT_STAR),0),COALESCE(SUM(SUM_TIMER_WAIT),0),"
       "COALESCE(SUM(SUM_LOCK_TIME),0),COALESCE(SUM(SUM_ROWS_EXAMINED),0) "
       "FROM performance_schema.events_statements_summary_by_digest; "
       "SELECT 'FILE_IO_TOTAL',COALESCE(SUM(COUNT_WRITE),0),COALESCE(SUM(SUM_TIMER_WRITE),0),"
       "COALESCE(SUM(SUM_NUMBER_OF_BYTES_WRITE),0),COALESCE(SUM(COUNT_READ),0),"
       "COALESCE(SUM(SUM_TIMER_READ),0),COALESCE(SUM(SUM_NUMBER_OF_BYTES_READ),0) "
       "FROM performance_schema.file_summary_by_event_name "
       "WHERE EVENT_NAME LIKE 'wait/io/file/innodb/%' OR EVENT_NAME='wait/io/file/sql/binlog';")
MYSQL = 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --user=root --database="$MYSQL_DATABASE" --batch --skip-column-names --execute "$1"'

CONFIG_FIELDS = ('innodb_buffer_pool_size', 'innodb_page_size', 'innodb_log_buffer_size',
                 'innodb_flush_log_at_trx_commit', 'sync_binlog', 'innodb_dedicated_server',
                 'innodb_buffer_pool_instances', 'innodb_redo_log_capacity',
                 'innodb_autoinc_lock_mode', 'innodb_io_capacity', 'innodb_io_capacity_max',
                 'innodb_flush_neighbors')
# SHOW reports the same effective global settings as @@GLOBAL, and allows absent
# version-specific fields to remain explicitly unavailable without aborting all fields.
CONFIG_SQL = ('SHOW GLOBAL VARIABLES WHERE Variable_name IN (' +
              ','.join("'" + name + "'" for name in CONFIG_FIELDS) + ');')

DIGEST_FIELDS = ('count_star', 'sum_timer_wait_ps', 'sum_rows_examined', 'sum_rows_sent', 'sum_lock_time_ps')
DIGEST_COLUMNS = 'DIGEST,COUNT_STAR,SUM_TIMER_WAIT,SUM_ROWS_EXAMINED,SUM_ROWS_SENT,SUM_LOCK_TIME'
DIGEST_TABLE = ' FROM performance_schema.events_statements_summary_by_digest '
DIGEST_SCOPE = 'WHERE SCHEMA_NAME=DATABASE() AND DIGEST IS NOT NULL '
DIGEST_CANDIDATE_SQL = ('SELECT ' + DIGEST_COLUMNS + DIGEST_TABLE + DIGEST_SCOPE +
    "AND LOWER(DIGEST_TEXT) LIKE '%outbox_events%' AND LOWER(DIGEST_TEXT) LIKE '%json_table%' "
    "AND LOWER(DIGEST_TEXT) LIKE '%confirmed_at%' ORDER BY COUNT_STAR DESC,DIGEST LIMIT 20;")
DIGEST_TOP_SQL = ('SELECT ' + DIGEST_COLUMNS + DIGEST_TABLE + DIGEST_SCOPE +
    'ORDER BY COUNT_STAR DESC,DIGEST LIMIT 20;')

# Optional global instrument counters only. No statement text, SQL parameters,
# user accounts or host names are selected. One bounded query per sample.
WAIT_SCOPE = ("(e.EVENT_NAME LIKE 'wait/io/file/innodb/%' OR "
              "e.EVENT_NAME='wait/io/file/sql/binlog' OR "
              "e.EVENT_NAME LIKE 'wait/synch/%/innodb/%')")
WAIT_JOIN = (' FROM performance_schema.events_waits_summary_global_by_event_name e '
             'JOIN performance_schema.setup_instruments i ON i.NAME=e.EVENT_NAME WHERE ' + WAIT_SCOPE)
WAITS_SQL = ("SELECT 'WAIT_COVERAGE',COUNT(*),SUM(i.ENABLED='YES'),SUM(i.TIMED='YES'),"
             'SUM(e.COUNT_STAR),SUM(e.SUM_TIMER_WAIT)' + WAIT_JOIN + '; '
             "SELECT e.EVENT_NAME,i.ENABLED,i.TIMED,e.COUNT_STAR,e.SUM_TIMER_WAIT,"
             'e.MIN_TIMER_WAIT,e.MAX_TIMER_WAIT' + WAIT_JOIN +
             ' ORDER BY e.SUM_TIMER_WAIT DESC,e.EVENT_NAME LIMIT 20;')

DISK_COUNTER_FIELDS = ('reads_completed', 'reads_merged', 'sectors_read_512b', 'read_milliseconds',
                       'writes_completed', 'writes_merged', 'sectors_written_512b', 'write_milliseconds',
                       'io_inflight', 'io_milliseconds', 'weighted_io_milliseconds')
DISK_CUMULATIVE_FIELDS = tuple(name for name in DISK_COUNTER_FIELDS if name != 'io_inflight')


def command(argv):
    remaining = 8 if DEADLINE is None else min(8, DEADLINE - time.monotonic())
    if remaining <= 0:
        raise ValueError('OBSERVER_120_SECOND_LIMIT')
    result = subprocess.run(argv, capture_output=True, timeout=remaining, check=False)
    if result.returncode or len(result.stdout) > 262144:
        # Raw stdout/stderr is deliberately never persisted; it may contain configuration.
        raise ValueError('READ_ONLY_COMMAND_UNAVAILABLE')
    return result.stdout.decode()


def identity(container):
    lines = command([*DOCKER, 'inspect', '--format', FORMAT, container]).splitlines()
    cid, image, running, host = map(json.loads, lines)
    if cid != container or not running or not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise ValueError('EXACT_RUNNING_IDENTITY_REQUIRED')
    keys = ('CpuPeriod', 'CpuQuota', 'NanoCpus', 'CpusetCpus', 'Memory', 'MemorySwap', 'PidsLimit')
    return {'container_id': cid, 'image_id': image, 'limits': {k: host.get(k) for k in keys}}


def cgroup(container):
    output = command([*DOCKER, 'exec', container, 'sh', '-c', CGROUP])
    fields, key = {}, None
    for line in output.splitlines():
        if line.startswith('FILE:'):
            key = line[5:]
            fields[key] = []
        elif key and re.fullmatch(r'[0-9a-zA-Z_: =,.-]+', line):
            fields[key].append(line)
        else:
            raise ValueError('CGROUP_PROJECTION_REJECTED')
    return fields


def io_pressure(lines):
    try:
        rows = {}
        for line in lines:
            fields = line.split()
            if len(fields) != 5 or fields[0] not in ('some', 'full') or fields[0] in rows:
                raise ValueError('PRESSURE_PROJECTION_REQUIRED')
            values = dict(field.split('=', 1) for field in fields[1:])
            if (set(values) != {'avg10', 'avg60', 'avg300', 'total'} or not values['total'].isdigit()
                    or any(not re.fullmatch(r'\d+(?:\.\d+)?', values[key]) for key in ('avg10', 'avg60', 'avg300'))):
                raise ValueError('PRESSURE_NUMERIC_REQUIRED')
            averages = {key: float(values[key]) for key in ('avg10', 'avg60', 'avg300')}
            if any(not 0 <= value <= 100 for value in averages.values()):
                raise ValueError('PRESSURE_PERCENT_RANGE_REQUIRED')
            rows[fields[0]] = {**averages, 'total_microseconds': int(values['total'])}
        if set(rows) != {'some', 'full'}:
            raise ValueError('PRESSURE_BOTH_SCOPES_REQUIRED')
        return {'available': True, 'scopes': rows,
                'units': 'avg10/60/300 are kernel PSI percentages; total is cumulative microseconds',
                'meaning': 'owned service cgroup IO stall pressure, not disk utilization or per-request latency'}
    except (ValueError, TypeError):
        return {'available': False, 'scopes': None, 'missing_reason': 'CGROUP_V2_IO_PRESSURE_UNAVAILABLE_OR_INVALID'}


def bounded_text(path, cap):
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        raise ValueError('OBSERVER_120_SECOND_LIMIT')
    with Path(path).open() as stream:
        value = stream.read(cap + 1)
    if len(value) > cap:
        raise ValueError('HOST_COUNTER_FILE_LIMIT')
    return value


def parse_diskstats(raw, device):
    matches = []
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) < 2 or not fields[0].isdigit() or not fields[1].isdigit():
            continue
        if fields[0] + ':' + fields[1] == device:
            matches.append(fields)
    if len(matches) != 1:
        raise ValueError('DISKSTATS_DEVICE_MISSING_OR_AMBIGUOUS')
    fields = matches[0]
    if (len(fields) < 14 or not re.fullmatch(r'[A-Za-z0-9_.!+-]{1,128}', fields[2])
            or any(not value.isdigit() for value in fields[3:14])):
        raise ValueError('DISKSTATS_FIELDS_UNAVAILABLE_OR_INVALID')
    return fields[2], dict(zip(DISK_COUNTER_FIELDS, map(int, fields[3:14]), strict=True))


def parse_device_mapping(raw, device, diskstats_name):
    fields = {}
    for line in raw.splitlines():
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        if key in ('MAJOR', 'MINOR', 'DEVNAME', 'DEVTYPE'):
            if key in fields:
                raise ValueError('SYSFS_DEVICE_MAPPING_AMBIGUOUS')
            fields[key] = value
    if (set(fields) != {'MAJOR', 'MINOR', 'DEVNAME', 'DEVTYPE'}
            or fields['MAJOR'] + ':' + fields['MINOR'] != device
            or fields['DEVNAME'] != diskstats_name or fields['DEVTYPE'] not in ('disk', 'partition')):
        raise ValueError('SYSFS_DISKSTATS_MAPPING_UNCONFIRMED')
    return {'device_name': diskstats_name, 'device_type': fields['DEVTYPE']}


def disk_delta(previous, current, elapsed):
    if elapsed <= 0 or any(key not in previous or key not in current for key in DISK_CUMULATIVE_FIELDS):
        return {'available': False, 'counts': None, 'missing_reason': 'PREVIOUS_SAMPLE_OR_INTERVAL_UNAVAILABLE'}
    if any(current[key] < previous[key] for key in DISK_CUMULATIVE_FIELDS):
        return {'available': False, 'counts': None, 'missing_reason': 'COUNTER_RESET_WRAP_OR_DEVICE_REPLACEMENT'}
    return {'available': True, 'elapsed_seconds': elapsed,
            'counts': {key: current[key] - previous[key] for key in DISK_CUMULATIVE_FIELDS},
            'io_inflight_current': current['io_inflight'],
            'await_utilization_queue_depth_or_quota_calculated': False}


def host_block_io(services, previous=None, reader=bounded_text, platform=None, clock=None):
    platform = sys.platform if platform is None else platform
    if platform != 'linux':
        return {'available': False, 'devices': None, 'missing_reason': 'LINUX_HOST_COUNTERS_REQUIRED'}
    sources = {}
    try:
        for role, service in services.items():
            for line in service['cgroup'].get('io.stat', []):
                device = line.split()[0]
                if not re.fullmatch(r'\d{1,10}:\d{1,10}', device):
                    raise ValueError('CGROUP_IO_DEVICE_PROJECTION_INVALID')
                sources.setdefault(device, set()).add(role)
        if not sources or len(sources) > 32:
            raise ValueError('CGROUP_DEVICE_SET_EMPTY_OR_OUT_OF_BOUND')
        raw = reader('/proc/diskstats', 1024 * 1024)
    except (ValueError, OSError, KeyError, IndexError, TypeError):
        return {'available': False, 'devices': None, 'missing_reason': 'HOST_DISKSTATS_OR_CGROUP_DEVICE_SET_UNAVAILABLE'}
    observed = time.monotonic() if clock is None else clock()
    devices = {}
    for device, roles in sorted(sources.items()):
        try:
            name, counters = parse_diskstats(raw, device)
            mapping = parse_device_mapping(reader('/sys/dev/block/' + device + '/uevent', 4096), device, name)
            row = {'available': True, **mapping, 'source_owned_roles': sorted(roles), 'counters': counters}
            old = None if previous is None else (previous.get('devices') or {}).get(device)
            if (old and old.get('available') is True and old.get('device_name') == name
                    and old.get('device_type') == mapping['device_type'] and 'observed_monotonic' in previous):
                row['delta'] = disk_delta(old['counters'], counters, observed - previous['observed_monotonic'])
            else:
                row['delta'] = {'available': False, 'counts': None, 'missing_reason': 'NO_PREVIOUS_CONFIRMED_SAME_DEVICE_SAMPLE'}
            devices[device] = row
        except (ValueError, OSError):
            devices[device] = {'available': False, 'counters': None, 'source_owned_roles': sorted(roles),
                               'missing_reason': 'DISKSTATS_FIELDS_OR_SYSFS_DEVICE_MAPPING_UNAVAILABLE_OR_AMBIGUOUS'}
    return {'available': all(row['available'] for row in devices.values()), 'devices': devices,
            'observed_monotonic': observed, 'observed_utc': datetime.now(timezone.utc).isoformat(),
            'units': 'completion/merge counts, kernel512-byte sectors, milliseconds, instantaneous io_inflight count',
            'scope': 'host-wide device counters only for major:minor observed in owned cgroup io.stat; no device-layer aggregation',
            'meaning': 'cumulative counters and reset-aware deltas; not request latency, true device utilization, queue depth or provisioned limits',
            'serial_numbers_paths_or_user_data_collected': False}


def mysql(container):
    lines = command([*DOCKER, 'exec', container, 'sh', '-c', MYSQL, 'observer', SQL]).splitlines()
    rows, aggregates, text_status = {}, {}, {}
    shapes = {'CAPACITY': ('max_connections',), 'LOCKS': ('data_lock_waits_count',),
              'DIGEST_TOTAL': ('digest_rows', 'count_star', 'sum_timer_wait_ps', 'sum_lock_time_ps', 'sum_rows_examined'),
              'FILE_IO_TOTAL': ('count_write', 'sum_timer_write_ps', 'bytes_write', 'count_read', 'sum_timer_read_ps', 'bytes_read')}
    for line in lines:
        parts = line.split('\t')
        key, values = parts[0], parts[1:]
        if key in TEXT_STATUS:
            if len(values) != 1 or values[0] not in TEXT_STATUS[key] or key in text_status:
                raise ValueError('MYSQL_REDO_RESIZE_STATE_WHITELIST_REQUIRED')
            text_status[key] = values[0]
            continue
        if any(not value.isdigit() for value in values):
            raise ValueError('MYSQL_NUMERIC_PROJECTION_REQUIRED')
        if key in STATUS and len(values) == 1 and key not in rows:
            rows[key] = int(values[0])
        elif key in shapes and len(values) == len(shapes[key]) and key not in aggregates:
            aggregates[key] = dict(zip(shapes[key], map(int, values), strict=True))
        else:
            raise ValueError('MYSQL_STATUS_WHITELIST_REQUIRED')
    if set(aggregates) != set(shapes):
        raise ValueError('MYSQL_AGGREGATES_REQUIRED')
    return {'status': rows, 'unavailable_status_fields': sorted(set(STATUS) - set(rows)),
            'redo_resize_status': text_status,
            'unavailable_text_status_fields': sorted(set(TEXT_STATUS) - set(text_status)),
            'checkpoint_age': checkpoint_age(rows),
            'aggregates': aggregates, 'sql_text_or_digest_text_collected': False,
            'scope': 'global cumulative counters; reset/restart and observer contribution must be considered'}


def checkpoint_age(rows):
    pairs = [('Innodb_redo_log_current_lsn', 'Innodb_redo_log_checkpoint_lsn'),
             ('Innodb_lsn_current', 'Innodb_lsn_last_checkpoint')]
    for current, checkpoint in pairs:
        if current in rows and checkpoint in rows:
            if rows[current] < rows[checkpoint]:
                return {'available': False, 'bytes': None,
                        'missing_reason': 'LSN_SAMPLE_INCONSISTENT_OR_RESET',
                        'source_fields': [current, checkpoint]}
            return {'available': True, 'bytes': rows[current] - rows[checkpoint],
                    'source_fields': [current, checkpoint],
                    'meaning': 'point-in-time current_lsn minus checkpoint_lsn, not request latency'}
    return {'available': False, 'bytes': None, 'missing_reason': 'CURRENT_OR_CHECKPOINT_LSN_UNAVAILABLE'}


def mysql_waits(container):
    try:
        output = command([*DOCKER, 'exec', container, 'sh', '-c', MYSQL, 'observer', WAITS_SQL])
        rows, coverage, seen = [], None, set()
        for line in output.splitlines():
            fields = line.split('\t')
            if fields[0] == 'WAIT_COVERAGE':
                if coverage is not None or len(fields) != 6 or any(not value.isdigit() for value in fields[1:]):
                    raise ValueError('WAITS_COVERAGE_NUMERIC_REQUIRED')
                names = ('instruments', 'enabled_instruments', 'timed_instruments', 'count_star', 'sum_timer_wait_ps')
                coverage = dict(zip(names, map(int, fields[1:]), strict=True))
                if not coverage['instruments'] or max(coverage['enabled_instruments'], coverage['timed_instruments']) > coverage['instruments']:
                    raise ValueError('WAITS_INSTRUMENT_COVERAGE_UNAVAILABLE')
                continue
            if (len(fields) != 7 or not re.fullmatch(r'wait/(?:io/file|synch/(?:mutex|rwlock|sxlock|cond))/[A-Za-z0-9_./-]{1,160}', fields[0])
                    or fields[0] in seen or fields[1] not in ('YES', 'NO') or fields[2] not in ('YES', 'NO')
                    or any(not value.isdigit() for value in fields[3:])):
                raise ValueError('WAITS_EVENT_NUMERIC_PROJECTION_REQUIRED')
            seen.add(fields[0])
            names = ('count_star', 'sum_timer_wait_ps', 'min_timer_wait_ps', 'max_timer_wait_ps')
            rows.append({'event_name': fields[0], 'enabled': fields[1] == 'YES', 'timed': fields[2] == 'YES',
                         **dict(zip(names, map(int, fields[3:]), strict=True))})
        if coverage is None or not rows or len(rows) > 20 or len(rows) > coverage['instruments']:
            raise ValueError('WAITS_ROWS_OR_COVERAGE_REQUIRED')
        if not coverage['enabled_instruments'] or not coverage['timed_instruments']:
            return {'available': False, 'coverage': coverage, 'top20_by_cumulative_timer': None,
                    'missing_reason': 'WAIT_INSTRUMENTATION_DISABLED_OR_UNTIMED',
                    'sql_text_or_parameters_collected': False}
        return {'available': True, 'coverage': coverage, 'top20_by_cumulative_timer': rows,
                'scope': 'selected global cumulative instrument counters; disabled or untimed instrumentation is not zero waiting',
                'sql_text_or_parameters_collected': False}
    except (ValueError, subprocess.TimeoutExpired, OSError):
        return {'available': False, 'coverage': None, 'top20_by_cumulative_timer': None,
                'missing_reason': 'CAPABILITY_PERMISSION_TIMEOUT_OR_PROJECTION_UNAVAILABLE',
                'sql_text_or_parameters_collected': False}


def mysql_config(container):
    try:
        output = command([*DOCKER, 'exec', container, 'sh', '-c', MYSQL, 'observer', CONFIG_SQL])
        values = {}
        for line in output.splitlines():
            parts = line.split('\t')
            if len(parts) != 2 or parts[0] not in CONFIG_FIELDS or parts[0] in values:
                raise ValueError('CONFIG_WHITELIST_REQUIRED')
            key, value = parts
            if key == 'innodb_dedicated_server' and value in ('ON', 'OFF'):
                values[key] = int(value == 'ON')
            elif value.isdigit():
                values[key] = int(value)
            else:
                raise ValueError('NUMERIC_CONFIG_REQUIRED')
        return {'available': True, 'values': values,
                'unavailable_fields': sorted(set(CONFIG_FIELDS) - set(values))}
    except (ValueError, subprocess.TimeoutExpired, OSError):
        return {'available': False, 'values': None, 'unavailable_fields': list(CONFIG_FIELDS),
                'missing_reason': 'CAPABILITY_PERMISSION_TIMEOUT_OR_PROJECTION_UNAVAILABLE'}


def mysql_digests(container, sql):
    # Optional P_S capability: absence/permissions/NULL fields are missing, never zero.
    # DIGEST_TEXT is used only inside the SQL predicate, never selected or persisted.
    try:
        output = command([*DOCKER, 'exec', container, 'sh', '-c', MYSQL, 'observer', sql])
        rows = []
        seen = set()
        for line in output.splitlines():
            values = line.split('\t')
            if (len(values) != 6 or not re.fullmatch(r'[0-9a-fA-F]{64}', values[0]) or
                    values[0].lower() in seen or any(not v.isdigit() for v in values[1:])):
                raise ValueError('DIGEST_HASH_NUMERIC_PROJECTION_REQUIRED')
            seen.add(values[0].lower())
            rows.append({'digest_hash': values[0].lower(), **dict(zip(DIGEST_FIELDS, map(int, values[1:]), strict=True))})
        if len(rows) > 20:
            raise ValueError('DIGEST_ROW_LIMIT_EXCEEDED')
        return {'available': True, 'rows': rows, 'sql_or_digest_text_exported': False}
    except (ValueError, subprocess.TimeoutExpired, OSError):
        return {'available': False, 'rows': None,
                'missing_reason': 'CAPABILITY_PERMISSION_TIMEOUT_OR_PROJECTION_UNAVAILABLE',
                'sql_or_digest_text_exported': False}


def observe(containers, previous_disks=None):
    row = {'utc': datetime.now(timezone.utc).isoformat(), 'monotonic': time.monotonic(), 'services': {}}  # noqa: UP017
    for role, container in containers.items():
        state = identity(container)
        state['cgroup'] = cgroup(container)
        state['io_pressure'] = io_pressure(state['cgroup'].get('io.pressure', []))
        if role == 'api':
            state['api_processes'] = json.loads(command([*DOCKER, 'exec', container, 'python', '-c', PROCESS]))
        if role == 'mysql':
            state['mysql'] = mysql(container)
            state['mysql']['effective_global_config'] = mysql_config(container)
            state['mysql']['confirmed_missing_digest_candidates'] = mysql_digests(container, DIGEST_CANDIDATE_SQL)
            state['mysql']['top20_digests_by_count'] = mysql_digests(container, DIGEST_TOP_SQL)
            state['mysql']['global_waits'] = mysql_waits(container)
        row['services'][role] = state
    row['host_block_io'] = host_block_io(row['services'], previous_disks)
    return row


def main():
    global DEADLINE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--container', action='append', required=True, help='role=full-64-hex-ID; all seven roles required')
    parser.add_argument('--samples', type=int, default=12)
    parser.add_argument('--interval', type=int, default=5)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    pairs = [value.split('=', 1) for value in args.container]
    if any(len(pair) != 2 for pair in pairs):
        parser.error('role=full-ID required')
    containers = dict(pairs)
    if (len(pairs) != 7 or set(containers) != set(ROLES) or len(set(containers.values())) != 7 or
            any(not re.fullmatch(r'[0-9a-f]{64}', value) for value in containers.values()) or
            not 1 <= args.interval <= 5 or not 1 <= args.samples <= 24 or args.samples * args.interval > 120):
        parser.error('seven unique exact IDs and <=120-second configured sample window required')
    # Slow or unavailable commands abort the sampler. No retry, service mutation or load spawn.
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    deadline = time.monotonic() + 120
    DEADLINE = deadline
    previous_disks = None
    with os.fdopen(fd, 'w') as stream:
        for index in range(args.samples):
            if time.monotonic() >= deadline:
                raise ValueError('OBSERVER_120_SECOND_LIMIT')
            row = observe(containers, previous_disks)
            previous_disks = row['host_block_io']
            stream.write(json.dumps(row, sort_keys=True) + '\n')
            stream.flush()
            if index + 1 < args.samples:
                time.sleep(min(args.interval, max(0, deadline-time.monotonic())))


if __name__ == '__main__':
    main()
