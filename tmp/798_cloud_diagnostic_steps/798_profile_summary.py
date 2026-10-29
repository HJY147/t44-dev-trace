"""Summarize only root-approved source935 timing records; inclusive spans never added."""

import base64
import gzip
import hashlib
import json
import math
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path('/root/t44-r9/diag-profile-935-01/output')
WINDOWS = {
    'baseline1': ('2026-10-25T15:26:04.235353+00:00', '2026-10-25T15:26:08.611567+00:00', 80),
    'clients20': ('2026-10-25T15:34:29.880470+00:00', '2026-10-25T15:34:31.704157+00:00', 400),
    'clients40': ('2026-10-25T15:34:32.302250+00:00', '2026-10-25T15:34:34.264715+00:00', 800),
    'clients400': ('2026-10-25T15:34:34.831477+00:00', '2026-10-25T15:34:57.425886+00:00', 8000),
}


def distribution(values):
    values = sorted(values)
    return None if not values else {'n': len(values), 'mean': sum(values) / len(values),
                                   'p50': values[math.ceil(len(values) * .5) - 1],
                                   'p95': values[math.ceil(len(values) * .95) - 1], 'max': values[-1]}


def main():
    files, requests, final_rows = [], [], []
    for path in sorted(ROOT.glob('stage-*.jsonl')):
        assert not path.is_symlink()
        raw = path.read_bytes()
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        rows = [json.loads(line) for line in raw.splitlines()]
        final = [row for row in rows if row.get('kind') == 'probe_final']
        source = [row for row in rows if row.get('kind') == 'source_binding']
        files.append({'name': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                      'final_count': len(final), 'source_binding': source})
        requests.extend(row for row in rows if row.get('kind') == 'request')
        final_rows.extend(final)
    report = {'kind': 'source935-developer-observer-summary-not-acceptance', 'files': files,
              'all_seven_final_valid': len(files) == len(final_rows) == 7 and all(
                  row['diagnostic_valid'] and row['selected'] == row['written'] and not row['cap_skips']
                  for row in final_rows),
              'finals': final_rows, 'total_requests': len(requests), 'cohorts': {},
              'scope': 'UTC windows use NTP clocks, not request-ID join; spans overlap and cannot be added'}
    boundaries = {'ingress_to_body': ('ingress_ns', 'body_consumed_ns'),
                  'body_to_handler': ('body_consumed_ns', 'handler_start_ns'),
                  'handler': ('handler_start_ns', 'handler_end_ns'),
                  'handler_end_to_send_end': ('handler_end_ns', 'send_end_ns'),
                  'ingress_to_send_end': ('ingress_ns', 'send_end_ns')}
    for name, (start, end, expected) in WINDOWS.items():
        start, end = datetime.fromisoformat(start), datetime.fromisoformat(end)
        selected = [row for row in requests if start <= datetime.fromisoformat(row['utc_start']) <= end]
        cohort = {'rows': len(selected), 'client_completed': expected,
                  'window_count_match': len(selected) == expected, 'operations': {}}
        for operation in sorted({row.get('operation', 'unrouted') for row in selected}):
            group = [row for row in selected if row.get('operation', 'unrouted') == operation]
            entry = {'rows': len(group), 'statuses': dict(Counter(str(row.get('status')) for row in group)),
                     'request_id_mismatches': sum(bool(row.get('request_id_mismatch')) for row in group),
                     'boundaries_ms': {}, 'phases_inclusive_ms': {},
                     'peak_checkedout': max((row.get('pool_peak_checkedout', 0) for row in group), default=0)}
            for label, (a, b) in boundaries.items():
                entry['boundaries_ms'][label] = distribution([(row[b] - row[a]) / 1e6 for row in group if a in row and b in row])
            phases = {label for row in group for label in row['phases']}
            for label in sorted(phases):
                spans = [row['phases'][label] for row in group if label in row['phases']]
                entry['phases_inclusive_ms'][label] = {
                    'wall': distribution([span['wall_ns'] / 1e6 for span in spans]),
                    'thread_cpu': distribution([span['thread_cpu_ns'] / 1e6 for span in spans]),
                    'calls': distribution([span['calls'] for span in spans])}
            cohort['operations'][operation] = entry
        report['cohorts'][name] = cohort
    raw = json.dumps(report, separators=(',', ':')).encode()
    descriptor = os.open('/root/t44-r9/diag-summary-01.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    compressed = base64.b64encode(gzip.compress(raw, mtime=0)).decode()
    assert len(compressed) < 18000
    print(json.dumps({'kind': 'observer-public-metadata-transport', 'raw_bytes': len(raw),
                      'raw_sha256': hashlib.sha256(raw).hexdigest(), 'gzip_base64': compressed}))


if __name__ == '__main__':
    main()
