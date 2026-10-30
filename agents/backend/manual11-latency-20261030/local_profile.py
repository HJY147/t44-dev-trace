"""Local sequential SQLite SQL/cProfile evidence; never cloud or formal load."""
import cProfile
import importlib
import json
import pstats
import sys
import time
from collections import Counter
from pathlib import Path
from uuid import uuid4

from sqlalchemy import event
from t44.contracts import OPERATIONS, violations
from t44.services.common import Call, wire

fixture = importlib.import_module('tmp.backend.contracts.conftest')
http = importlib.import_module('tmp.backend.contracts.986_http')
gen = fixture.application.__wrapped__()
client, factory = next(gen)
try:
    tokens, pid, iid = http.setup_project(client)
    task = http.create_task(client, tokens, pid, iid)
    engine = factory._sessions.kw['bind']
    runtime = client.app.state.runtime
    counts = Counter()
    @event.listens_for(engine, 'before_cursor_execute')
    def count(conn, cursor, statement, params, context, many):
        counts[statement.split()[0].upper()] += 1
    event.listen(engine, 'checkout', lambda *args: counts.update(['CHECKOUT']))
    event.listen(engine, 'commit', lambda *args: counts.update(['COMMIT']))
    report = {'scope': 'Sequential local SQLite, real Runtime and jsonschema; not MySQL/lock/network/formal evidence', 'phases': {}}
    payload = {'category': 1, 'payload': {'title': 'Synthetic', 'owner_id': 2, 'iteration_id': iid, 'plan': http.PLAN, 'dependency_task_ids': []}}
    for operation in ('getTask', 'validateContractPayload', 'transitionTask'):
        rows = []
        profile = cProfile.Profile()
        for i in range(30):
            body = payload if operation == 'validateContractPayload' else ({'expected_version': task['version'], 'action': (2 if i % 2 == 0 else 3), **({'reason': 'Synthetic profile', 'responsibility_stage': 1} if i % 2 == 0 else {'basis': 'Synthetic profile'}), 'evidence': http.EVIDENCE} if operation == 'transitionTask' else {})
            call = Call(operation, str(uuid4()), tokens['manager'], path={'project_id': pid, **({'task_id': task['id']} if operation != 'validateContractPayload' else {})}, key=str(uuid4()))
            def validate(c):
                if body:
                    schema = OPERATIONS[operation]['requestBody']['content']['application/json']['schema']
                    assert not violations(schema, body)
                c.body = body
            counts.clear()
            profile.enable()
            started = time.perf_counter()
            status, result, replayed, original = runtime.execute(call, validate)
            assert status == 200, (operation, status, result)
            envelope = {'data': result, 'meta': {'request_id': call.request_id, 'server_time': wire(call.clock), 'contract_version': '1.2.0', 'replayed': replayed, 'original_request_id': original}}
            assert not violations(OPERATIONS[operation]['responses']['200']['content']['application/json']['schema'], envelope)
            rows.append({'sql': dict(counts), 'ms': (time.perf_counter() - started)*1000})
            profile.disable()
            if operation == 'transitionTask':
                task = result['task']
        report['phases'][operation] = {'samples': rows, 'mean_ms': sum(x['ms'] for x in rows)/len(rows)}
        with Path(sys.argv[1] + '.' + operation + '.profile.txt').open('w') as stream:
            pstats.Stats(profile, stream=stream).sort_stats('cumtime').print_stats(35)
    Path(sys.argv[1]).write_text(json.dumps(report, indent=2)+'\n')
finally:
    try:
        next(gen)
    except StopIteration:
        pass
