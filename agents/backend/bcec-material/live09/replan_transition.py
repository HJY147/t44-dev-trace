"""One authorized existing-cohort plan shift through the frozen manager HTTP API."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import time
from datetime import datetime, timedelta
from uuid import uuid4


def main():
    p = argparse.ArgumentParser()
    for name in ('helper', 'backend-tools', 'old-packet', 'accounts', 'authorization',
                 'new-authorization', 'before-journal', 'ca', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--api-container', required=True)
    p.add_argument('--expected-api-image-id', required=True)
    p.add_argument('--root-admit-existing400-plan-shift', action='store_true')
    args = p.parse_args()
    os.umask(0o077)
    spec = importlib.util.spec_from_file_location('maintenance', args.helper)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    h.need(os.geteuid() == 0 and args.root_admit_existing400_plan_shift,
           'EXPLICIT_ROOT_PLAN_SHIFT_REQUIRED')
    old_raw = h.read(args.old_packet)
    old = json.loads(old_raw)
    accounts = json.loads(h.read(args.accounts))
    auth = json.loads(h.read(args.authorization))
    items, ids = h.authorization(old, old_raw, auth, accounts)
    current = json.loads(h.read(args.new_authorization))
    core = h.load_module('refresh_core', args.backend_tools / 'refresh_core.py')
    h.need(h.sha(h.read(args.backend_tools / 'refresh_core.py')) == h.NEW_CORE_SHA,
           'CURRENT_CORE_PIN_REQUIRED')
    core.authorization(current, old_raw)
    events = [json.loads(line) for line in h.read(args.before_journal).splitlines()]
    before = next(e['tasks'] for e in events if e['event'] == 'BEFORE800_SNAPSHOT')
    receipt = {'operation': 'r30replantransition09', 'status': 'INCOMPLETE',
               'old_packet_sha256': h.sha(old_raw), 'shift_seconds': 172800,
               'planned': 400, 'confirmed': 0, 'new_tasks': 0,
               'automatic_retry': False, 'benchmark_started': False}
    evidence = h.Evidence(args.output, receipt['operation'])
    api = None
    try:
        host = h.load_module('host_runner', args.backend_tools / 'host_runner.py')
        runtime = h.load_module('runtime_support', args.backend_tools / 'runtime_support.py')
        for name, expected in h.OWNER_MODULE_HASHES.items():
            h.need(h.sha(h.read(args.backend_tools / name)) == expected, 'OWNER_PIN_REQUIRED')
        for unit in (auth['namespace'] + '-stop.service', 't44-final-p09-continuous.service'):
            h.controller_idle(unit)
        host.inspect_api(args.api_container, auth['namespace'], args.expected_api_image_id)
        endpoint = host.maintenance_endpoint(argparse.Namespace(
            api_container=args.api_container, discover_maintenance_gateway=True,
            maintenance_gateway_container=None, maintenance_connect_ip=None,
            maintenance_connect_port=None), auth, old)
        api = h.API(runtime, old, args.ca, endpoint, evidence, time.monotonic() + 300)
        token = h.login(api, 'manager', accounts['manager'], evidence)
        expected = {}
        for pid, tid, _ in items:
            task = api.request(f'/projects/{pid}/tasks/{tid}', token)
            h.need(task == before[str(tid)], 'CONCURRENT_CHANGE_SINCE_SAVED800')
            h.check_task(task, pid, tid, accounts['developer']['user_id'], True)
            plan = copy.deepcopy(task['plan'])
            for key in ('planned_start', 'planned_end'):
                plan[key] = (datetime.fromisoformat(plan[key].replace('Z', '+00:00'))
                             + timedelta(days=2)).isoformat().replace('+00:00', 'Z')
            body = {'expected_version': task['version'], 'plan': plan,
                    'reason': 'Existing isolated cohort stable horizon expired; shift unchanged duration by two days',
                    'evidence': [{'kind': 2, 'locator': f'maintenance/r30replantransition09/{tid}',
                                  'description': 'Root-authorized existing task plan shift; preserve original task identity'}]}
            key = str(uuid4())
            evidence.event('PLAN_PATCH_PREPARED', {'task_id': tid, 'project_id': pid,
                'expected_version': task['version'], 'idempotency_key': key, 'body': body})
            h.need(time.monotonic() < api.deadline, 'PLAN_DEADLINE_PREFIX_PRESERVED')
            api.calls += 1
            api.connection.request('PATCH', f'/api/v1/projects/{pid}/tasks/{tid}/plan',
                h.canonical(body), {'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json', 'Accept': 'application/json',
                'Idempotency-Key': key, 'X-Request-ID': key})
            response = api.connection.getresponse()
            raw = response.read(2 * 1024 * 1024 + 1)
            evidence.response(api.calls, raw)
            h.need(response.status == 200 and len(raw) <= 2 * 1024 * 1024,
                   'PLAN_RESPONSE_NOT_CONFIRMED_NO_RETRY')
            data = json.loads(raw)['data']
            after = data['task']
            h.need(type(data.get('audit_id')) is int and data['audit_id'] > 0
                   and after['version'] == task['version'] + 1
                   and after['schedule_version'] == task['schedule_version'] + 1,
                   'PLAN_VERSION_AUDIT_MISMATCH')
            for field in plan:
                if field in ('planned_start', 'planned_end'):
                    h.need(datetime.fromisoformat(after['plan'][field].replace('Z', '+00:00'))
                           == datetime.fromisoformat(plan[field].replace('Z', '+00:00')),
                           'PLAN_TIME_MISMATCH')
                else:
                    h.need(after['plan'][field] == plan[field], 'PLAN_WORKLOAD_CHANGED')
            for field in ('id', 'project_id', 'owner_id', 'iteration_id', 'state', 'blocked_from_state'):
                h.need(after[field] == task[field], 'PLAN_UNRELATED_IDENTITY_CHANGED')
            expected[tid] = after
            receipt['confirmed'] += 1
            evidence.event('PLAN_PATCH_CONFIRMED', {'task_id': tid, 'version': after['version'],
                'schedule_version': after['schedule_version'], 'audit_id': data['audit_id']}, public=True)
        totals, final = h.project_snapshot(api, items, token)
        original_totals = next(e['project_totals'] for e in events if e['event'] == 'BEFORE800_SNAPSHOT')
        h.need(totals == original_totals and len(final) == 800 and set(final) == set(ids),
               'ORIGINAL800_TOTALS_CHANGED')
        for _, tid, eid in items:
            h.need(final[tid] == expected[tid] and final[eid] == before[str(eid)],
                   'FINAL800_READBACK_MISMATCH')
        h.guard_transition_horizon(expected.values())
        receipt.update(status='COMPLETE_EXISTING400_PLAN_SHIFT_ORIGINAL800_PRESERVED',
                       original800_after=800, escalation400_unchanged=True)
    except Exception:
        receipt['error'] = 'FAILED_PREFIX_PRESERVED_COORDINATOR_INSPECTION_REQUIRED'
        raise
    finally:
        if api:
            api.close()
            receipt['http_requests'] = api.calls
        h.put(args.output / 'receipt.PUBLIC.json', h.canonical(receipt))
        print(json.dumps(receipt))


if __name__ == '__main__':
    main()
