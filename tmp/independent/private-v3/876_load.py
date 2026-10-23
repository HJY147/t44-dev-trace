"""Separate formal 400 active VU / 600 second entries. No load is run at design time."""
import base64
import concurrent.futures as cf
import copy
import gzip
import hashlib
import http.client
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import resource
import threading
import time
import urllib.parse
import uuid

def run(mode):
    spec = importlib.util.spec_from_file_location('iv3_load_support', Path(__file__).with_name('881_support.py'))
    S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
    h = S.Harness('formal-' + mode)
    h.setup_users()
    # Scope scanner to the actual neutral bootstrap project, leaving formal fixtures deterministic.
    h.control('scheduler-scope', '--project-id', h.c['bootstrap_project_id'])
    origin = urllib.parse.urlsplit(h.base)
    if origin.scheme not in ('http', 'https'):
        raise S.Blocked('Formal endpoint must be supplied by exact coordinator context')
    seeded = []
    def seed_project(project_index):
        f = h.fixture(title='Independent formal ' + str(project_index) + ' ' + S.key())
        tasks = []
        for i in range(150):
            deps = [tasks[0]['id']] if i == 1 else [tasks[0]['id'], tasks[1]['id']] if 2 <= i <= 113 else []
            t = h.task(f, deps=deps, timing=S.plan(start=-259200, end=-3600) if mode == 'escalation' else S.plan())
            tasks.append(t)
        # Last 25 have no dependencies. Fifteen immutable reviews each gives 15,000
        # total evidence records across 40 projects; no direct SQL writes or fabricated rows.
        for i in range(125, 150):
            t = h.to_review(f, tasks[i])
            for _ in range(15):
                d = h.data('createTaskReview', actor='r', ids=h.ids(f, t), body=h.review_body(t), expected=201)
                t = d['task']
            tasks[i] = t
        return f, tasks
    h.rec.event({'kind': 'formal_fixture_preparation_start', 'mode': mode,
                 'not_timed_load': True, 'public_http_only': True})
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        seeded = list(ex.map(seed_project, range(40)))
    pids = [f['p'] for f, _ in seeded]
    project_sql = ','.join(str(x) for x in pids)
    counts = {
        'projects': h.sql('SELECT COUNT(*) AS n FROM projects WHERE id IN (' + project_sql + ')')[0]['n'],
        'tasks': h.sql('SELECT COUNT(*) AS n FROM tasks WHERE project_id IN (' + project_sql + ')')[0]['n'],
        'dependencies': h.sql('SELECT COUNT(*) AS n FROM task_dependencies WHERE project_id IN (' + project_sql + ')')[0]['n'],
        'reviews_and_decisions': h.sql('SELECT (SELECT COUNT(*) FROM reviews WHERE project_id IN (' + project_sql +
            '))+(SELECT COUNT(*) FROM decisions WHERE project_id IN (' + project_sql + ')) AS n')[0]['n']}
    S.check(counts == {'projects': 40, 'tasks': 6000, 'dependencies': 9000, 'reviews_and_decisions': 15000},
            'Formal scope has independently observed full representative dataset')
    h.rec.event({'kind': 'formal_dataset_census', 'counts': counts, 'project_ids': pids})
    service_labels = {}
    if mode == 'escalation':
        for f, _ in seeded:
            service_labels[f['p']] = h.service(f['p'], label='s' + str(f['p']))
    # Each worker owns a separate task. Pending block/unblock is a real allowed transition;
    # cached replay, expected rejection and fixed-success stubs do not count as writes.
    fixture_tasks = [(f, ts[i]) for f, ts in seeded for i in range(10)]
    S.check(len(fixture_tasks) == 400, 'Formal workers have 400 independent mutable task contexts')
    target_op = {'transition': 'transitionTask', 'contract': 'validateContractPayload',
                 'escalation': 'createEscalation'}[mode]
    lock = threading.Lock(); raw_buffer = []; metrics = []; samples = []
    active = set(); inflight = set(); phase = {}; validator_cache = {}
    trace = h.rec.directory / 'trace.log'
    columns = ['vu', 'start_ms', 'finish_ms', 'operation', 'http_status', 'latency_ms',
               'schema_ok', 'business_ok', 'effective_write', 'replayed', 'phase']
    def flush():
        if not raw_buffer: return
        content = ('\n'.join(raw_buffer) + '\n').encode(); raw_buffer.clear()
        frame = {'encoding': 'gzip-base64-csv-v1', 'columns': columns,
                 'uncompressed_sha256': hashlib.sha256(content).hexdigest(),
                 'payload': base64.b64encode(gzip.compress(content, compresslevel=6, mtime=0)).decode()}
        with trace.open('a') as f: f.write(json.dumps(frame, separators=(',', ':')) + '\n')
    def request(connection, op_id, pid, tid, body=None, actor='m'):
        method, path, op = S.OPS[op_id]
        path = path.replace('{project_id}', str(pid)).replace('{task_id}', str(tid))
        path = origin.path.rstrip('/') + path
        headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + h.tokens[actor],
                   'X-Request-ID': S.key(), 'Content-Type': 'application/json'}
        if op_id != 'validateContractPayload' and method != 'GET': headers['Idempotency-Key'] = S.key()
        payload = json.dumps(body, separators=(',', ':')).encode() if body is not None else None
        start = time.perf_counter()
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse(); status = response.status; data = response.read()
        finish = time.perf_counter()
        value = json.loads(data)
        cachekey = (op_id, status)
        if cachekey not in validator_cache:
            schema = op['responses'].get(str(status), {}).get('content', {}).get('application/json', {}).get('schema')
            if schema is None: return start, finish, status, value, False
            root = {'components': S.CONTRACT['components'], **schema}
            validator_cache[cachekey] = h.validator_cls(root, format_checker=h.formats)
        ok = not any(validator_cache[cachekey].iter_errors(value))
        return start, finish, status, value, ok
    def worker(vu):
        f, current = fixture_tasks[vu]
        cls = http.client.HTTPSConnection if origin.scheme == 'https' else http.client.HTTPConnection
        connection = cls(origin.hostname, origin.port, timeout=30)
        operation_index = 0; mutation_index = 0
        with lock: active.add(vu)
        barrier.wait()
        try:
            while time.perf_counter() < phase['end']:
                op_id = target_op; body = None; actor = 'm'; mutation_index += 1
                if mode == 'transition':
                    if operation_index % 5 == 4:
                        op_id = 'getTask'
                    else:
                        body = {'expected_version': current['version'], 'action': 2 if current['state'] == 1 else 3}
                        if body['action'] == 2:
                            body.update(reason='Synthetic formal blocker', responsibility_stage=1, evidence=S.EVIDENCE)
                        else:
                            body.update(basis='Synthetic formal resolved blocker', evidence=S.EVIDENCE)
                elif mode == 'contract':
                    category = operation_index % 3 + 1
                    if category == 1:
                        body = {'category': 1, 'payload': {'title': 'Synthetic contract load', 'iteration_id': f['i'],
                            'owner_id': h.users['a'], 'plan': S.plan(), 'dependency_task_ids': []}}
                    elif category == 2:
                        body = {'category': 2, 'task_id': current['id'], 'payload': {'expected_version': current['version'], 'action': 1}}
                    else:
                        body = {'category': 3, 'task_id': current['id'], 'payload': h.assessment_body(current)}
                else:
                    step = operation_index % 3
                    if step == 0:
                        op_id = 'changeTaskPlan'
                        body = {'expected_version': current['version'], 'plan': S.plan(start=-259200, end=-3600,
                            delay_contingency='Synthetic formal schedule ' + str(mutation_index)),
                            'reason': 'Synthetic new schedule version', 'evidence': S.EVIDENCE}
                    elif step == 1:
                        actor = service_labels[f['p']]
                        body = {'expected_version': current['version'], 'schedule_version': current['schedule_version'],
                                'rule_version': 1, 'scan_run_id': str(uuid.uuid4())}
                    else:
                        op_id = 'getTask'
                with lock: inflight.add(vu)
                start = time.perf_counter(); finish = start; status = 0; schema_ok = False; business_ok = False
                effective = False; replayed = False
                try:
                    start, finish, status, value, schema_ok = request(connection, op_id, f['p'], current['id'], body, actor)
                    business_ok = status == (202 if op_id == 'createEscalation' else 200)
                    if schema_ok and business_ok:
                        data = value['data']; replayed = value['meta']['replayed']
                        if op_id in ('transitionTask', 'changeTaskPlan'):
                            effective = data['task']['version'] == current['version'] + 1 and not replayed
                            if op_id == 'transitionTask': effective = effective and data['task']['state'] != current['state']
                            current = data['task']
                        elif op_id == 'getTask': current = data
                        elif op_id == 'createEscalation':
                            effective = data['created'] and data['task_version'] == current['version'] + 1 and not replayed
                            current['version'] = data['task_version']; current['escalation_count'] += 1
                        if op_id in ('transitionTask', 'changeTaskPlan', 'createEscalation') and not effective:
                            business_ok = False
                except Exception:
                    finish = time.perf_counter(); connection.close(); connection = cls(origin.hostname, origin.port, timeout=30)
                finally:
                    with lock: inflight.discard(vu)
                measured = start >= phase['steady'] and start < phase['end']
                row = [vu, round((start - phase['epoch']) * 1000, 3), round((finish - phase['epoch']) * 1000, 3),
                       op_id, status, round((finish - start) * 1000, 3), int(schema_ok), int(business_ok),
                       int(effective), int(replayed), 'steady' if measured else 'warmup']
                with lock:
                    raw_buffer.append(','.join(map(str, row)))
                    if measured: metrics.append((op_id, finish - start, status, schema_ok, business_ok, effective,
                                                  replayed, finish <= phase['end']))
                    if len(raw_buffer) >= 10000: flush()
                operation_index += 1
        finally:
            connection.close()
            with lock: active.discard(vu)
    barrier = threading.Barrier(401)
    machine = {'platform': platform.platform(), 'cpu_count': os.cpu_count(), 'loadavg_before': os.getloadavg(),
               'topology': 'Neutral runner client process to supplied reverse-proxy endpoint; no separate physical host attestation',
               'duration_seconds': 600, 'warmup_seconds': 15, 'active_virtual_users': 400,
               'client_memory_limit_bytes': resource.getrlimit(resource.RLIMIT_AS)}
    with cf.ThreadPoolExecutor(max_workers=400) as ex:
        futures = [ex.submit(worker, i) for i in range(400)]
        epoch = time.perf_counter(); phase.update(epoch=epoch, steady=epoch + 15, end=epoch + 615)
        barrier.wait()
        while time.perf_counter() < phase['end']:
            now = time.perf_counter()
            with lock:
                samples.append({'t': round(now - epoch, 3), 'phase': 'steady' if now >= phase['steady'] else 'warmup',
                                'active_vus': len(active), 'inflight_requests': len(inflight)})
            time.sleep(.1)
        for future in futures: future.result()
    with lock: flush()
    target = [x for x in metrics if x[0] == target_op]
    latencies = sorted(x[1] * 1000 for x in target)
    p95 = latencies[math.ceil(.95 * len(latencies)) - 1] if latencies else None
    failures = sum(not x[3] or not x[4] for x in metrics)
    target_completed = sum(x[7] and x[3] and x[4] for x in target)
    target_per_minute = target_completed / 10
    active_samples = [x['active_vus'] for x in samples if x['phase'] == 'steady']
    result = {'case': 'P-' + mode, 'data_census': counts, 'machine': machine, 'samples': samples,
              'steady_started_requests': len(metrics), 'target_requests': len(target), 'failures': failures,
              'target_completed_per_minute': target_per_minute, 'target_p95_ms': p95,
              'effective_target_writes': sum(x[5] for x in target), 'target_replays': sum(x[6] for x in target),
              'per_operation': {op: {'requests': sum(x[0] == op for x in metrics),
                                    'failures': sum(x[0] == op and (not x[3] or not x[4]) for x in metrics)}
                                for op in {x[0] for x in metrics}},
              'loadavg_after': os.getloadavg(), 'client_maxrss': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'raw_format': 'trace.log gzip-base64-csv-v1 frames; all warmup and steady request timings retained'}
    criterion = (len(active_samples) >= 5900 and min(active_samples, default=0) == 400 and
                 failures == 0 and p95 is not None and p95 <= 270 and target_per_minute >= 1000 and
                 result['target_replays'] == 0 and trace.stat().st_size <= 20 * 1024 * 1024)
    h.rec.results.append({'id': 'P-' + mode, 'status': 'pass' if criterion else 'fail_observed',
                          'reason': 'Frozen 400 active VUs/600s, target P95<=270ms, >=1000 target/min, zero failures and replay'})
    return h.rec.finish({'formal_measurement': result,
        'limitation': 'This entry measures only its named class; other two classes need their own separate full run. '
                      'Host co-location is explicitly reported, not hidden. No diagnostic result is a formal pass.'})

if __name__ == '__main__':
    raise SystemExit('Use one frozen 879/878/877 mode entry; do not infer a mode from a SUT')
