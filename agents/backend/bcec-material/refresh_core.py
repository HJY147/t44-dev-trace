"""New factual packet from existing task IDs; no product, clock or token rewriting."""
import copy
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

SOURCE = 'bcec3326b40814fdb1922bbfea7c29473b47ba47'
HISTORY_SOURCE = '90b734f65ce6ee9f5c217e885bc7ea4857e32b48'
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
    require(auth.get('schema') == 'manual-material-new-source-v2'
            and auth.get('root_approved') is True
            and auth.get('benchmark_grant_allow') is False
            and auth.get('operations') == OPERATIONS, 'EXPLICIT_MATERIAL_AUTHORIZATION_REQUIRED')
    require(auth.get('source_sha') == SOURCE and old['identity']['git_commit'] == HISTORY_SOURCE
            and auth.get('old_packet_sha256') == sha(old_raw), 'SAME_SOURCE_AND_OLD_PACKET_REQUIRED')
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', auth['new_packet_run_id'])
            and auth['new_packet_run_id'] == 'r30materialresume09' and auth['qa_run_id'] == 'r30manualp15'
            and auth['maintenance_id'] == 'r30restoretransition09'
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
    validate_new_source(auth, old, manifests)
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
        'qa_run_id': auth['qa_run_id'], 'maintenance_id': auth['maintenance_id'],
        'benchmark_grant_allow': False, 'external_writer_absence_proven': False,
        'note': 'Current APP/LOAD ownership and writer evidence is supplied separately by coordinator.'}
    value['schema'] = 'NEUTRAL_753_INPUTS_V1'
    value['identity'] = copy.deepcopy(auth['new_identity'])
    value['loaded_receipt_sha256'] = sha(manifests['backend-import-receipt.json'])
    value['loaded_receipt_reference'] = copy.deepcopy(auth['loaded_receipt_reference'])
    value['additional_neutral_snapshots']['historical_identity'] = copy.deepcopy(old['identity'])
    value.pop('binding_sha256', None)
    value['binding_sha256'] = sha(canonical(value))
    return value


def validate_new_source(auth, old, manifests):
    identity = auth['new_identity']
    require(identity['source_manifest_sha256'] == '__SOURCE_MANIFEST_SHA256__', 'FROZEN_CANDIDATE_SOURCE_BYTES_REQUIRED')
    require(identity['backend_bundle_manifest_sha256'] == '__BUNDLE_MANIFEST_SHA256__', 'FROZEN_CANDIDATE_BUNDLE_BYTES_REQUIRED')
    require(identity['runtime_sha256'] == '81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf', 'LEGACY_PACKET_TRANSPORT_RUNTIME_REQUIRED')
    require(set(identity) == set(old['identity']), 'FULL_EXPLICIT_NEW_IDENTITY_REQUIRED')
    require(identity['git_commit'] == SOURCE, 'NEW_SOURCE_REQUIRED')
    for name,key in [('source-manifest.json','source_manifest_sha256'), ('backend-bundle-manifest.json','backend_bundle_manifest_sha256')]:
        require(sha(manifests[name]) == identity[key], 'NEW_MANIFEST_RAW_SHA_REQUIRED')
    source = json.loads(manifests['source-manifest.json'])
    bundle = json.loads(manifests['backend-bundle-manifest.json'])
    receipt = json.loads(manifests['backend-import-receipt.json'])
    require(source['source_sha'] == bundle['source_sha'] == receipt['source_sha'] == SOURCE, 'DUAL_CHAIN_SOURCE_MISMATCH')
    require(bundle['kind'] == 'final-backend-web-bundle-v1' and receipt['kind'] == 'final-backend-web-import-v1', 'NEW_PRODUCER_SCHEMA_REQUIRED')
    require(bundle['source_manifest_sha256'] == receipt['source_manifest_sha256'] == identity['source_manifest_sha256'], 'NEW_SOURCE_BINDING_REQUIRED')
    require(receipt['bundle_manifest_sha256'] == identity['backend_bundle_manifest_sha256'], 'NEW_IMPORT_BUNDLE_BINDING_REQUIRED')
    config = bundle['images']['backend']['image_id']
    require(config == identity['sut_image_config_digest'] == auth['expected_api_image_id'], 'NEW_ACTUAL_CONFIG_REQUIRED')
    require(receipt['identity']['config_id'] == config and receipt['identity']['actual_id'] == config and receipt['identity']['success'] is True, 'ACTUAL_IMPORT_CONFIG_PROOF_REQUIRED')
    require(timestamp(receipt['observed_utc']) <= datetime.now(timezone.utc), 'NONFUTURE_UTC_IMPORT_OBSERVATION_REQUIRED')
    ref=auth['loaded_receipt_reference']
    require(ref['original_path'] != old.get('loaded_receipt_reference', {}).get('original_path'), 'NEW_IMPORT_PATH_NOT_HISTORY_REQUIRED')
    require(ref['sha256'] == sha(manifests['backend-import-receipt.json']) and ref['observed_at'] == receipt['observed_utc'] and ref['original_path'].startswith('/root/'), 'ACTUAL_NEW_RECEIPT_REFERENCE_REQUIRED')
    require(sha(manifests['ca.pem']) == old['environment']['ca_sha256'], 'EXACT_CA')
    require(identity['openapi_sha256'] == old['identity']['openapi_sha256'], 'FROZEN_OPENAPI_UNCHANGED')
    for key in ('runtime_sha256','load_runtime_image_config_digest'):
        require(isinstance(identity[key],str) and re.fullmatch(r'(?:sha256:)?[0-9a-f]{64}',identity[key]), 'CURRENT_QA_LOAD_IDENTITY_REQUIRED')
    require(identity['load_runtime_image_config_digest'] == 'sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1', 'FROZEN_LOAD_IDENTITY_REQUIRED')
    return source
