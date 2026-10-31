"""Read-only container-side proof: recorded process group absent and same-DB lock free.

Never kills a PID, reads environment variables or emits a process command line.
Missing state or ambiguity is NOT an exit proof.
"""
import fcntl
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone


def audit(marker, expected_code, *, proc=Path('/proc'), temp=Path('/tmp')):
    if not re.fullmatch('[0-9a-f]{64}', marker):
        raise ValueError('EXACT_PROCESS_MARKER_REQUIRED')
    path = temp / ('t44-manual-material-' + marker + '.PUBLIC.json')
    result = {'marker': marker, 'captured_at': datetime.now(timezone.utc).isoformat(),
              'process_exit_proven': False, 'state_changed': False}
    if not path.is_file() or path.is_symlink():
        return {**result, 'status': 'JOB_STATE_MISSING_UNPROVEN'}
    state = json.loads(path.read_bytes())
    if state['marker'] != marker or state['code_sha256'] != expected_code:
        raise ValueError('JOB_STATE_MARKER_MISMATCH')
    result['recorded_job'] = state
    members = []
    for item in proc.iterdir():
        if not item.name.isdigit():
            continue
        try:
            fields = (item / 'stat').read_text().rsplit(')', 1)[1].split()
        except FileNotFoundError:
            continue
        except (OSError, ValueError, IndexError):
            return {**result, 'status': 'PROC_READ_UNCERTAIN'}
        if int(fields[2]) == state['pgid'] and fields[0] not in ['Z', 'X']:
            members.append({'pid': int(item.name), 'state': fields[0], 'start_ticks': fields[19]})
    result['active_group_members'] = members
    if members:
        return {**result, 'status': 'MATERIAL_GROUP_STILL_ACTIVE'}
    lock = Path(state['lock_path'])
    if not lock.is_file() or lock.is_symlink() or lock.parent != temp:
        return {**result, 'status': 'LOCK_SCOPE_UNCERTAIN'}
    descriptor = os.open(lock, os.O_RDWR)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {**result, 'status': 'ANOTHER_MATERIAL_REFRESH_ACTIVE'}
    finally:
        os.close(descriptor)
    return {**result, 'status': 'MATERIAL_PROCESS_GROUP_EXIT_PROVEN', 'process_exit_proven': True}


if __name__ == '__main__':
    print(json.dumps(audit(sys.argv[1], sys.argv[2]), sort_keys=True))
