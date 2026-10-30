"""New factual packet from existing task IDs; no product, clock or token rewriting."""
import copy
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

SOURCE = '90b734f65ce6ee9f5c217e885bc7ea4857e32b48'
ROLES = {'manager', 'developer', 'reviewer', 'service'}
OPERATIONS = ['login', 'service-token', 'readonly-inventory', 'readonly-counts', 'assemble-neutral']


def require(value, code):
    if not value:
        raise ValueError(code)


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def timestamp(value):
    at = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(at.utcoffset() == timedelta(0), 'UTC_REQUIRED')
    return at


def stamp(value):
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def authorization(auth, old_raw):
    old = json.loads(old_raw)
    require(auth.get('schema') == 'manual-material-preparation-v1'
            and auth.get('root_approved') is True
            and auth.get('benchmark_grant_allow') is False
            and auth.get('operations') == OPERATIONS, 'EXPLICIT_MATERIAL_AUTHORIZATION_REQUIRED')
    require(auth.get('source_sha') == SOURCE == old['identity']['git_commit']
            and auth.get('old_packet_sha256') == sha(old_raw), 'SAME_SOURCE_AND_OLD_PACKET_REQUIRED')
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', auth['new_packet_run_id'])
            and auth['new_packet_run_id'] != old['run_id'], 'NEW_MATERIAL_RUN_REQUIRED')
    require(re.fullmatch('[0-9a-f]{64}', auth['packet_nonce']), 'FRESH_PACKET_NONCE_REQUIRED')
    require(sha(canonical({k: v for k, v in old.items() if k != 'binding_sha256'}))
            == old['binding_sha256'], 'ORIGINAL_PACKET_BINDING_REQUIRED')
    scope = old['additional_neutral_snapshots']
    require(auth['database'] == scope['database']
            and auth['namespace'] == scope['namespace'], 'ORIGINAL_DATABASE_SCOPE_REQUIRED')
    return old


def build_packet(old, auth, sessions, inventory, counts, manifests, now, session_attestations):
    """All supplied sessions/inventory/counts must be actual provider readbacks."""
    require(set(sessions) == ROLES == set(session_attestations), 'EXACT_FOUR_ACTUAL_SESSIONS')
    end = now + timedelta(seconds=900)
    project_ids = sorted({x['project_id'] for x in inventory['clients']})
    require(len(project_ids) >= 35 and len(inventory['clients']) == 400
            and {x['client_id'] for x in inventory['clients']} == set(range(400)), '400_CURRENT_CLIENTS')
    require(timestamp(inventory['captured_at']) <= now, 'REAL_CAPTURE_TIME_REQUIRED')
    identifiers = []
    old_pairs = {(x['client_id'], x['transition_task']['id'], x['escalation_task']['id'])
                 for x in old['inventory']['clients']}
    new_pairs = {(x['client_id'], x['transition_task']['id'], x['escalation_task']['id'])
                 for x in inventory['clients']}
    require(new_pairs == old_pairs, 'SAME_EXISTING_800_TASK_IDS_REQUIRED')
    for role, session in sessions.items():
        att = session_attestations[role]
        require(isinstance(session['token'], str) and len(session['token']) >= 16
                and timestamp(session['expires_at']) > end, 'ACTUAL_SESSION_LIFETIME_' + role)
        require(sha(session['token'].encode()) == att['token_sha256']
                and all(session[k] == att[k] for k in ['user_id', 'expires_at', 'project_ids', 'scopes']),
                'SESSION_READBACK_BINDING_' + role)
        require(set(project_ids) <= set(session['project_ids']), 'ACTUAL_PROJECT_SCOPE_' + role)
    require('escalation:write' in sessions['service']['scopes'], 'SERVICE_SCOPE')
    for item in inventory['clients']:
        pid, task, escalation, event = (item[k] for k in
                                        ['project_id', 'transition_task', 'escalation_task', 'escalation_event'])
        require(task['project_id'] == escalation['project_id'] == event['project_id'] == pid,
                'CURRENT_TASK_PROJECT_BINDING')
        require(task['state'] == 2 and task['owner_id'] == sessions['developer']['user_id']
                and timestamp(task['plan']['planned_end']) > end + timedelta(days=1),
                'EXISTING_TRANSITION_TASK_NOT_ELIGIBLE')
        require(escalation['state'] not in [6, 7] and event['task_id'] == escalation['id']
                and event['schedule_version'] == escalation['schedule_version']
                and event['rule_version'] == inventory['rule_version'], 'CURRENT_ESCALATION_NOT_ELIGIBLE')
        identifiers += [task['id'], escalation['id']]
    require(len(set(identifiers)) == 800, '800_DISTINCT_TASKS')
    require(counts['counts'] == old['counts'], 'DATA_COUNTS_CHANGED_NO_RESEED_OR_HIDE')
    require(re.fullmatch('[0-9a-f]{64}', counts['actual_fixture_sha256']), 'ACTUAL_FIXTURE_SHA_REQUIRED')
    for name, key in [('source-manifest.json', 'source_manifest_sha256'),
                      ('backend-bundle-manifest.json', 'backend_bundle_manifest_sha256')]:
        require(sha(manifests[name]) == old['identity'][key], 'EXACT_SOURCE_FILE_' + name)
    require(sha(manifests['ca.pem']) == old['environment']['ca_sha256'], 'EXACT_CA')
    require(sha(manifests['backend-import-receipt.json']) == old['loaded_receipt_sha256'], 'EXACT_IMPORT')
    value = copy.deepcopy(old)
    value.update(run_id=auth['new_packet_run_id'], created_at=stamp(now),
                 packet_nonce=auth['packet_nonce'], sessions=sessions, inventory=inventory,
                 counts=counts['counts'], fixture_sha256=counts['actual_fixture_sha256'])
    # This materialization interval is provenance only; it does not schedule the benchmark.
    value['window'] = {'start_utc': stamp(now), 'end_utc': stamp(end), 'cost_stop_utc': stamp(end)}
    value['additional_neutral_snapshots'] = {
        'run_id': auth['new_packet_run_id'], 'namespace': auth['namespace'], 'database': auth['database'],
        'materialized_at': stamp(now), 'inventory': inventory, 'session_attestations': session_attestations,
        'counts_readback': counts, 'original_packet_sha256': auth['old_packet_sha256'],
        'original_packet_run_id': old['run_id'], 'original_packet_window': old['window'],
        'benchmark_grant_allow': False, 'external_writer_absence_proven': False,
        'note': 'Current APP/LOAD ownership and writer evidence is supplied separately by coordinator.'}
    value.pop('binding_sha256', None)
    value['binding_sha256'] = sha(canonical(value))
    return value
