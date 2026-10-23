"""Coarse operational faults are separate from unavailable exact commit/ACK cutpoints."""
import importlib.util
from pathlib import Path
import json
import uuid

def support():
    spec = importlib.util.spec_from_file_location('iv3_support_fault', Path(__file__).with_name('881_support.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def run(h, S):
    C, E = S.check, S.EVIDENCE
    def recover():
        value = h.control('recover')
        C(value.get('recovery_completed') is True, 'Actual neutral recovery receipt must report completion')
        h.rec.event({'kind': 'recovery_receipt', 'receipt': value})
    def event(f, t, service):
        return h.data('createEscalation', actor=service, ids=h.ids(f, t), expected=202, body={
            'expected_version': t['version'], 'schedule_version': t['schedule_version'],
            'rule_version': 1, 'scan_run_id': str(uuid.uuid4())})
    def event_rows(t):
        rows = h.sql('SELECT event_id FROM escalation_events WHERE task_id=' + str(t['id']))
        C(len(rows) == 1, 'One escalation ledger for synthetic task')
        return rows[0]['event_id']
    def notice_rows(event_id):
        return h.sql('SELECT id,event_id,recipient_id,version,fallback,read_at,handled_at,handling_note '
                     'FROM notifications WHERE event_id=' + str(event_id) + ' ORDER BY recipient_id')
    def duplicate(event_id):
        try:
            import pika
        except ImportError:
            raise S.Blocked('Neutral locked Pika client not available')
        row = h.sql('SELECT id,schema_version,event_type FROM outbox_events WHERE id=' + str(event_id))[0]
        transport = h.c.get('mq_transport', {})
        if not all(isinstance(transport.get(k), str) for k in ('exchange', 'routing_key')):
            raise S.Blocked('Neutral MQ transport string field binding unavailable')
        conn = pika.BlockingConnection(pika.URLParameters(h.c['amqp_url']))
        try:
            channel = conn.channel(); channel.confirm_delivery()
            wrapper = {'event_id': row['id'], 'schema_version': row['schema_version'], 'event_type': row['event_type']}
            for _ in range(3):
                channel.basic_publish(exchange=transport['exchange'], routing_key=transport['routing_key'],
                    body=json.dumps(wrapper).encode(), mandatory=True,
                    properties=pika.BasicProperties(content_type='application/json', delivery_mode=2,
                                                    message_id=str(row['id']), type='t44.event.v1'))
        finally:
            conn.close()
    def mark(f, t, eid):
        rows = h.data('listMyNotifications', actor='a', query={'project_id': f['p']}, expected=200)['items']
        n = next(x for x in rows if x['event_id'] == eid)
        n = h.data('markNotificationRead', actor='a', ids=h.ids(f, notification_id=n['id']),
                   body={'expected_version': n['version']}, expected=200)
        h.data('handleNotification', actor='a', ids=h.ids(f, notification_id=n['id']),
               body={'expected_version': n['version'], 'note': 'Synthetic preserved handling', 'evidence': E}, expected=200)

    def api_restart():
        f = h.fixture(); t = h.task(f)
        value = h.request('transitionTask', actor='a', ids=h.ids(f, t), expected=200,
                          body={'expected_version': t['version'], 'action': 1})
        committed = value['data']['task']; h.audit(value, 1)
        h.control('fault', '--service', 'api', '--action', 'stop', '--lease-seconds', 60)
        recover()
        C(h.get(f, t) == committed, 'API restart preserves committed full task snapshot')
        h.audit(value, 1)
    h.rec.run('O01-committed-state-and-audit-survive-api-restart', api_restart)

    def mq_fallback():
        f = h.fixture(); svc = h.service(f['p']); t = h.task(f, timing=S.plan(start=-172800, end=-3600))
        h.control('fault', '--service', 'rabbitmq', '--action', 'stop', '--lease-seconds', 120)
        try:
            accepted = event(f, t, svc)
            C(accepted['created'], 'MQ outage must not erase reliably committed accepted event')
            eid = event_rows(t)
            def fallback():
                out = h.sql('SELECT status,fallback_at FROM outbox_events WHERE id=' + str(eid))
                notes = notice_rows(eid)
                return notes if out[0]['status'] == 4 and out[0]['fallback_at'] is not None and len(notes) == 3 else None
            notes = h.wait(fallback, seconds=80)
            C(all(r['fallback'] == 1 for r in notes), 'Outage creates explicitly marked fallback notices for all recipients')
            mark(f, t, eid); before = notice_rows(eid)
        finally:
            recover()
        duplicate(eid)
        h.wait(lambda: h.sql('SELECT status FROM outbox_events WHERE id=' + str(eid))[0]['status'] == 4, seconds=10)
        # Poll long enough for a real consumer redelivery cycle; this is a diagnostic budget, not an SLA.
        import time
        for _ in range(10):
            C(notice_rows(eid) == before, 'Late duplicate cannot replace fallback, read or handled state')
            time.sleep(.5)
        fresh = h.task(f, timing=S.plan(start=-172800, end=-3600)); event(f, fresh, svc)
        new_eid = event_rows(fresh)
        notices = h.wait(lambda: notice_rows(new_eid) if len(notice_rows(new_eid)) == 3 else None, seconds=60)
        C(all(n['fallback'] == 0 for n in notices), 'New post-recovery event uses normal MQ delivery')
    h.rec.run('O02-mq-outage-fallback-recovery-and-late-duplicate', mq_fallback)

    def normal_duplicate():
        f = h.fixture(); svc = h.service(f['p']); t = h.task(f, timing=S.plan(start=-172800, end=-3600))
        event(f, t, svc); eid = event_rows(t)
        h.wait(lambda: len(notice_rows(eid)) == 3, seconds=60)
        mark(f, t, eid); before = notice_rows(eid)
        duplicate(eid)
        import time
        for _ in range(10):
            C(notice_rows(eid) == before, 'Real AMQP duplicate preserves one notice per recipient and handling fields')
            time.sleep(.5)
    h.rec.run('O03-real-mq-duplicate-consumption', normal_duplicate)

    def scanner():
        f = h.fixture()
        # Scope deliberately contains only this new project, preventing unrelated fixture interference.
        h.control('scheduler-scope', '--project-id', f['p'])
        tasks = [h.task(f, timing=S.plan(start=-259200, end=-3600 - i)) for i in range(20)]
        tasks[0] = h.trans(f, tasks[0], 2, reason='Synthetic blocker still timed', responsibility_stage=5, evidence=E)
        def twenty():
            rows = h.sql('SELECT task_id,COUNT(*) AS n FROM escalation_events WHERE project_id=' +
                         str(f['p']) + ' GROUP BY task_id ORDER BY task_id')
            return rows if len(rows) == 20 else None
        rows = h.wait(twenty, seconds=150, interval=1)
        C(all(r['n'] == 1 for r in rows), 'All twenty overdue tasks including blocker upgrade once')
        before = h.sql('SELECT id AS task_id,escalation_count FROM tasks WHERE project_id=' + str(f['p']) + ' ORDER BY id')
        h.control('fault', '--service', 'scheduler', '--action', 'stop', '--lease-seconds', 60)
        recover()
        # Observe a real additional scan after restart through durable scan_runs.
        last = h.sql('SELECT MAX(id) AS n FROM scan_runs')[0]['n'] or 0
        h.wait(lambda: (h.sql('SELECT MAX(id) AS n FROM scan_runs')[0]['n'] or 0) > last,
               seconds=150, interval=1)
        C(h.sql('SELECT id AS task_id,escalation_count FROM tasks WHERE project_id=' + str(f['p']) + ' ORDER BY id') == before,
          'Restart and rescan cannot increment existing upgrade counts')
        C(all(r['n'] == 1 for r in twenty()), 'Restart preserves unique upgrade ledger')
    h.rec.run('O04-twenty-overdue-tasks-and-scheduler-restart', scanner)

    blockers = {
        'O05-before-commit-rollback-cutpoint': 'Need deterministic transaction cutpoint before COMMIT and release receipt; whole MySQL stop is not equivalent',
        'O06-commit-ack-loss-uncertain-recovery': 'Need selective COMMIT acknowledgement loss after known commit with same-key retry; no such neutral control',
        'O07-publisher-confirm-ack-loss': 'Need broker publish accepted but confirm ACK selectively withheld plus timeline; stop/pause alone does not establish this',
        'O08-consumer-db-commit-before-basic-ack': 'Need deterministic consumer commit-completed/ACK-not-sent barrier and release; no cutpoint capability',
        'O09-idempotency-owner-lease-recovery': 'Need controlled original owner paused/terminated at leased main transaction boundary plus lease metadata; no cutpoint capability'}
    for case_id, reason in blockers.items():
        def blocked(reason=reason):
            raise S.Blocked(reason)
        h.rec.run(case_id, blocked)

def main():
    S = support(); h = S.Harness('operational-faults')
    try:
        h.setup_users()
        selection = Path(__file__).with_name('continuation-selection.json')
        if selection.exists():
            h.rec.case_filter = json.loads(selection.read_text()).get('operational_case_ids')
        h.runtime_snapshot('before-remaining-original-fault-case')
        run(h, S)
        h.runtime_snapshot('after-remaining-original-fault-case')
    finally:
        try:
            receipt = h.control('recover')
            h.rec.event({'kind': 'final_recovery_receipt', 'receipt': receipt})
            if not receipt.get('recovery_completed'):
                h.rec.results.append({'id': 'O-final-recovery', 'status': 'execution_error'})
        except Exception as exc:
            h.rec.results.append({'id': 'O-final-recovery', 'status': 'execution_error', 'type': type(exc).__name__})
    return h.rec.finish({'runtime_observations': getattr(h, 'runtime_observations', []), 'limitations': 'Exact commit/confirm/ACK and lease cutpoints remain separately blocked'})

if __name__ == '__main__':
    raise SystemExit(main())
