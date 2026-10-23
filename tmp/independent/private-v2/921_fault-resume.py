#!/usr/bin/env python3
"""Independent continuation of previously BLOCKED frozen947 cases, fixed SUT.
Only runtime transport/TSV/per-call receipt adapters. Original files remain unchanged.
"""
from pathlib import Path
import csv
import io
import json
import os
import runpy
import sys
import types

HERE=Path(__file__).resolve().parent
P=runpy.run_path(str(HERE/'939_runtime-adapter.py'),run_name='independent_fault_resume_parent')
Blocked=P['Blocked']

class FaultRuntime(P['RuntimeAdapter']):
    def audit(self,sql):
        value=super().audit(sql)
        if isinstance(value,dict) and 'unparsed' in value:
            text=value['unparsed']
            return list(csv.DictReader(io.StringIO(text),delimiter='\t')) if text.strip() else []
        return value
    def control(self,args,*a,**kw):
        value=super().control(args,*a,**kw)
        if args==['recover']:
            try:r=json.loads(value)
            except (TypeError,json.JSONDecodeError) as e:raise Blocked('Per-call neutral recovery receipt not JSON') from e
            required={'mysql','rabbitmq','api','consumer','scheduler','web'}
            if not isinstance(r,dict) or r.get('schema_version')!=1 or not r.get('recovery_id') or r.get('recovery_completed') is not True:raise Blocked('Per-call neutral recovery receipt not successful schema1')
            if set(r.get('requested_services',[]))!=required or set(r.get('restored_services',[]))!=required:raise Blocked('Per-call recovery service scope incomplete')
            steps=r.get('steps',[])
            if not steps or any(s.get('exit_code') not in (0,None) for s in steps) or any(s.get('exit_code') is None and s.get('needed') is not False for s in steps):raise Blocked('Per-call recovery has missing/failed required step receipt')
            self.log('recovery_capability_verified',recovery_id=r['recovery_id'],requested_services=r['requested_services'],restored_services=r['restored_services'])
        return value

original=(HERE/'947_faults.py').read_text()
needle="            connection=pika.BlockingConnection(pika.URLParameters(h.context['amqp_url']));channel=connection.channel()"
insert="""            rows=h.audit('SELECT o.id,o.schema_version,o.event_type FROM outbox_events o JOIN escalation_events e ON o.id=e.event_id WHERE e.project_id='+str(h.ids['project_id'])+' AND e.task_id='+str(t['id'])+' ORDER BY e.id')
            if not isinstance(rows,list) or len(rows)!=1:raise Blocked('Exact actual escalation/outbox row required for safe original-message identity')
            expected_wrapper={'event_id':int(rows[0]['id']),'schema_version':int(rows[0]['schema_version']),'event_type':int(rows[0]['event_type'])}
            h.log('actual_mq_wrapper_binding',task_id=t['id'],wrapper=expected_wrapper)
"""+needle
replacements=[
 (needle,insert),
 ("if str(t['id']) in json.dumps(payload) and ('escalation' in json.dumps(payload) or topology.get('event_match_confirmed_by_tester')):","if payload==expected_wrapper:"),
 ("channel.basic_publish(exchange='',routing_key=topology['queue'],body=captured[1],properties=captured[0],mandatory=True)","channel.basic_publish(exchange=topology['exchange'],routing_key=topology['routing_key'],body=captured[1],properties=captured[0],mandatory=True)")
]
adapted=original
for before,after in replacements:
    if adapted.count(before)!=1:raise RuntimeError('Frozen947 transport expression not uniquely matched')
    adapted=adapted.replace(before,after)
module=types.ModuleType('independent_v2_frozen_fault_transport_adapter')
exec(compile(adapted,str(HERE/'947_faults.py')+'[transport-adapter]', 'exec'),module.__dict__)

def main():
    context=json.loads(Path(os.environ['T44_ACCEPTANCE_CONTEXT']).read_text())
    if context.get('product_source_sha')!='4c20f32b71635016815420472b9d4bb4fa850df0':raise Blocked('Exact original SUT binding missing')
    context['independent_phase']='fault'
    t=context.get('mq_transport')
    if not isinstance(t,dict) or t.get('product_source_sha')!=context['product_source_sha'] or (t.get('exchange'),t.get('queue'),t.get('routing_key'))!=('t44.events','t44.notifications','t44.notifications'):raise Blocked('Neutral actual mq_transport binding unavailable')
    context['independent_mq_topology']=t
    h=FaultRuntime(context)
    h.log('fault_resume_binding',original_H='27c9a0a6af10a21eb475ef42c9e98e13b8334a43',H3='99906b1fb1ef376cc819c1a3af9558906331f8c0',preserved_blocked_run=39969411280,environment_implementation='f118f9dd35bc2cde69affe235f5a499d03a396fc',neutral_manifest_sha256='362a9914e31bfdc3709a941ca9cb26b199a933f3ca8e1c959d0c9bde86c6f21b',original_assertions_changed=False,completed_api_cases_selected=False)
    if h.run('SETUP',h.setup)!='PASS':return h.finish()
    # All five remain incomplete/BLOCKED in the original preserved fault run.
    # Capture on the fresh queue before the other bounded fault fixtures.
    for selected in ['mq-duplicate','scan20','mq-fallback','api-restart','db-down']:
        h.context['independent_fault_case']=selected
        module.run(h)
    return h.finish()

if __name__=='__main__':
    try:sys.exit(main())
    except Blocked as e:print('BLOCKED: '+str(e));sys.exit(2)
