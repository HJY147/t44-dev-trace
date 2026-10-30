"""Offline contracts, real existing discovery/TLS primitives with fake I/O; no cloud."""
import copy
import importlib.util
import io
import json
import os
import ssl
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import cohort_maintenance as m
REPO=HERE.parents[3]
EXISTING=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/manual12-repair-kit/backend')


def contract_inputs():
    # Exact published account HTTP contract used by refresh_runtime payload['accounts'][role].
    accounts=json.loads((REPO/'agents/backend/neutral-r30-cas/accounts.http-input.template.NO_SECRETS.json').read_bytes())
    for i,role in enumerate(('manager','developer','reviewer'),1):
        accounts[role].update(user_id=i,password='fake-'+role)
    rows=[]
    for i in range(400):
        pid=i//10+1
        task={'id':i+1,'project_id':pid,'owner_id':2,'state':3 if i<138 else 2,
              'blocked_from_state':2 if i<138 else None,'version':99,'plan':{'planned_end':'2099-01-01T00:00:00Z'}}
        esc={'id':i+401,'project_id':pid,'owner_id':2,'state':2,'blocked_from_state':None,'version':11}
        rows.append({'client_id':i,'project_id':pid,'transition_task':task,'escalation_task':esc})
    old={'identity':{'git_commit':m.SOURCE},'run_id':'r30originalp09','environment':{'origin':'https://172.21.182.245:26445','connect_ip':'172.21.182.245','ca_sha256':'0'*64},'sessions':{r:{'user_id':a['user_id']} for r,a in accounts.items()},'inventory':{'clients':rows},'additional_neutral_snapshots':{'namespace':'t44-test-owned','database':'t44_test_owned'}}
    old['binding_sha256']=m.sha(m.canonical(old))
    return old,accounts


class FakeAPI:
    def __init__(self,old):
        self.tasks={t['id']:copy.deepcopy(t) for c in old['inventory']['clients'] for t in (c['transition_task'],c['escalation_task'])}
        self.calls=0;self.posts=[];self.audits={};self.fail_unknown=False;self.sent_unknown=False
    def request(self,path,token=None,body=None,key=None):
        self.calls+=1
        if path=='/auth/login':
            uid=2 if body['username']=='synthetic-developer' else 1
            return {'user':{'id':uid},'access_token':'fake-token-'+str(uid),'expires_at':'2099-01-01T00:00:00Z'}
        tid=int(path.split('/')[4])
        if body:
            self.posts.append((path,body,key))
            assert key and body['expected_version']==self.tasks[tid]['version'] and body['action']==3
            if self.fail_unknown:
                self.sent_unknown=True;raise m.Stop('HTTP_OUTCOME_UNKNOWN_STOP_NO_RETRY','UNKNOWN')
            self.tasks[tid].update(state=2,blocked_from_state=None,version=self.tasks[tid]['version']+1)
            return {'task':copy.deepcopy(self.tasks[tid]),'audit_id':tid+1000}
        return copy.deepcopy(self.tasks[tid])
    def pages(self,path,token):
        self.calls+=1
        pid=int(path.split('/')[2])
        if '/audit-events' in path:
            tid=int(path.split('task_id=')[1].split('&')[0]);rows=self.audits.get(tid,[])
            return copy.deepcopy(rows),len(rows)
        rows=[copy.deepcopy(t) for t in self.tasks.values() if t['project_id']==pid]
        return rows,len(rows)


class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.old,self.accounts=contract_inputs();self.items,self.ids=m.inventory(self.old,self.accounts)
        self.api=FakeAPI(self.old);self.ev=m.Evidence(self.root/'out','restore-test')
        self.summary={'operation_id':'restore-test','old_packet_sha256':m.sha(m.canonical(self.old)),'unblocked':0,'skipped_state2':0,'preflight400':0,'final400_state2':0}
    def tearDown(self):self.tmp.cleanup()
    def test400_restore_final800_counts_and_private_prefix(self):
        m.restore(self.api,self.old,self.items,self.accounts,self.ev,self.summary)
        self.assertEqual(len(self.api.posts),138)
        self.assertEqual(self.summary['final400_state2'],400)
        self.assertEqual(self.summary['original800_before'],800)
        self.assertEqual(self.summary['original800_after'],800)
        self.assertTrue(self.summary['project_task_totals_unchanged'])
        self.assertEqual(self.summary['skipped_state2'],262)
        self.assertEqual(len({p[2] for p in self.api.posts}),138)
        self.assertNotIn('fake-token',self.ev.progress.read_text())
        self.assertNotIn('fake-manager',self.ev.progress.read_text())
        self.assertEqual(stat.S_IMODE(self.ev.private.stat().st_mode),0o700)
    def test_bad_last_owner_or_state_zero_posts(self):
        for field,value in [('owner_id',9),('state',4),('blocked_from_state',1)]:
            with self.subTest(field=field):
                api=FakeAPI(self.old);api.tasks[400][field]=value
                with self.assertRaises(m.Stop):m.restore(api,self.old,self.items,self.accounts,self.ev,self.summary)
                self.assertEqual(api.posts,[])
    def test_unknown_write_stops_and_private_plan_is_durable(self):
        self.api.fail_unknown=True
        with self.assertRaisesRegex(m.Stop,'UNKNOWN'):m.restore(self.api,self.old,self.items,self.accounts,self.ev,self.summary)
        self.assertEqual(len(self.api.posts),1)
        self.assertEqual(self.summary['unblocked'],0)
        rows=[json.loads(s) for s in self.ev.journal.read_text().splitlines()]
        planned=[r for r in rows if r['event']=='UNBLOCK_ACTION_PLANNED']
        self.assertEqual(len(planned),1);self.assertEqual(planned[0]['before_version'],99)
    def test_original_accounts_shape_and_binding_guards(self):
        for which in ('nested','subject','duplicate','binding'):
            old,accounts=contract_inputs()
            if which=='nested':accounts={'accounts':accounts}
            elif which=='subject':accounts['developer']['user_id']=8
            elif which=='duplicate':
                old['inventory']['clients'][-1]['escalation_task']['id']=1
                old['binding_sha256']=m.sha(m.canonical({k:v for k,v in old.items() if k!='binding_sha256'}))
            else:old['binding_sha256']='f'*64
            with self.subTest(which=which),self.assertRaises((m.Stop,KeyError)):m.inventory(old,accounts)
    def test_inspect_unknown_with_audit_never_posts_or_resumes(self):
        prior=self.root/'prior';ev=m.Evidence(prior,'restore-old')
        m.put(prior/'guard.PUBLIC.json',m.canonical({'old_packet_sha256':self.summary['old_packet_sha256']}))
        ev.event('UNBLOCK_ACTION_PLANNED',{'task_id':1,'project_id':1,'before_version':99,'idempotency_key':'same-key','marker':'maintenance/restore-old/1'})
        self.api.tasks[1].update(state=2,blocked_from_state=None,version=100)
        self.api.audits[1]=[{'operation_id':'transitionTask','actor_id':2,'actor_kind':1,'project_id':1,'task_id':1,'outcome':1,'expected_version':99,'evidence':[{'locator':'maintenance/restore-old/1'}]}]
        m.inspect_previous(self.api,self.old,self.items,self.accounts,self.ev,self.summary,prior)
        self.assertEqual(self.api.posts,[])
        self.assertFalse(self.summary['automatic_resume'])
        self.assertEqual(self.summary['recovery_findings'][0]['classification'],'UNKNOWN_POST_COMMIT_PROVEN_BY_AUDIT_AND_READBACK')
    def test_inspect_unchanged_is_not_no_commit_proof(self):
        prior=self.root/'prior';ev=m.Evidence(prior,'restore-old')
        m.put(prior/'guard.PUBLIC.json',m.canonical({'old_packet_sha256':self.summary['old_packet_sha256']}))
        ev.event('UNBLOCK_ACTION_PLANNED',{'task_id':1,'project_id':1,'before_version':99,'idempotency_key':'same-key','marker':'maintenance/restore-old/1'})
        m.inspect_previous(self.api,self.old,self.items,self.accounts,self.ev,self.summary,prior)
        self.assertEqual(self.api.posts,[])
        self.assertIn('NOT_PROOF',self.summary['recovery_findings'][0]['classification'])
    def test_transport_private_raw_and_unknown_no_retry(self):
        envelope={'data':{'access_token':'fake-private-token','user':{'id':2},'expires_at':'2099-01-01T00:00:00Z'},'meta':{}}
        class Response:
            status=200
            def read(self,limit):return json.dumps(envelope).encode()
        class Connection:
            sock=None
            def __init__(self,*args,**kwargs):self.count=0
            def connect(self):pass
            def request(self,*args,**kwargs):self.count+=1
            def getresponse(self):return Response()
            def close(self):pass
        runtime=SimpleNamespace(PinnedHTTPSConnection=Connection)
        import time
        api=m.API(runtime,self.old,Path('unused-ca'),{'connect_ip':'192.168.96.99','connect_port':8443},self.ev,time.monotonic()+10)
        api.request('/auth/login',body={'username':'dev','password':'fake-password'})
        self.assertFalse((self.ev.private/'00001.response.private.bin').exists())
        self.assertTrue((self.ev.private/'00001.login-metadata.private.json').exists())
        self.assertNotIn('fake-password',self.ev.journal.read_text())
        self.assertNotIn('fake-private-token',self.ev.progress.read_text())
        envelope.clear();envelope.update({'code':'TRANSACTION_UNCERTAIN'})
        Response.status=503
        with self.assertRaises(m.Stop) as raised:
            api.request('/projects/1/tasks/1/transitions','fake-private-token',{'action':3},key='persisted-idempotency')
        self.assertEqual(raised.exception.category,'UNKNOWN')
        self.assertEqual(api.connection.count,2)
        self.assertIn('persisted-idempotency',self.ev.journal.read_text())
        for file in self.ev.root.rglob('*'):
            if file.is_file():
                for secret in ('fake-private-token','fake-password','Bearer fake-private-token'):
                    self.assertNotIn(secret.encode(),file.read_bytes())
    def test_horizon_strict_boundary_and_no_first_post(self):
        from datetime import datetime,timedelta,timezone
        at=datetime(2026,10,30,tzinfo=timezone.utc)
        task={'plan':{'planned_end':(at+timedelta(days=1,seconds=900)).isoformat()}}
        with self.assertRaisesRegex(m.Stop,'EXISTING_TRANSITION_TASK_NOT_ELIGIBLE'):
            m.guard_transition_horizon([task],at)
        task['plan']['planned_end']=(at+timedelta(days=1,seconds=900,microseconds=1)).isoformat()
        m.guard_transition_horizon([task],at)
        self.api.tasks[400]['plan']['planned_end']='2020-01-01T00:00:00Z'
        with self.assertRaisesRegex(m.Stop,'EXISTING_TRANSITION_TASK_NOT_ELIGIBLE'):
            m.restore(self.api,self.old,self.items,self.accounts,self.ev,self.summary)
        self.assertEqual(self.api.posts,[])
    def test_main_stdout_stderr_and_all_logs_exclude_credentials(self):
        from contextlib import redirect_stdout,redirect_stderr
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            m.restore(self.api,self.old,self.items,self.accounts,self.ev,self.summary)
        combined=out.getvalue()+err.getvalue()+''.join(p.read_text() for p in self.ev.root.rglob('*') if p.is_file())
        for secret in ('fake-manager','fake-developer','fake-reviewer','fake-token-1','fake-token-2','Authorization','Bearer '):
            self.assertNotIn(secret,combined)

    def test_dedicated_authorization_contract_and_no_material_grant(self):
        raw=m.canonical(self.old)
        auth={'schema':'manual11-cohort-maintenance-authorization-v2','root_approved':True,'benchmark_grant_allow':False,'operations':m.OPS,'operation_id':'cohort-maintenance-only','source_sha':m.SOURCE,'old_packet_sha256':m.sha(raw),'namespace':'t44-test-owned','database':'t44_test_owned','original_ids_sha256':m.sha(m.canonical(self.ids)),'require_infrastructure_and_old_controller_guards':True,'require_exclusive_no_benchmark_or_other_writer':True}
        self.assertEqual(len(m.authorization(self.old,raw,auth,self.accounts)[1]),800)
        auth['benchmark_grant_allow']=True
        with self.assertRaisesRegex(m.Stop,'DEDICATED'):m.authorization(self.old,raw,auth,self.accounts)

    def test_historical_not_found_inactive_rc1_is_accepted(self):
        original=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/manual11-live/old-timer.PUBLIC.json')
        evidence=json.loads(original.read_bytes())
        unit='t44-final-p09-continuous.service'
        before=evidence['after'][unit]
        def runner(argv,**kwargs):
            self.assertEqual(argv,['systemctl','show',unit,'--property=Id,LoadState,ActiveState'])
            return SimpleNamespace(returncode=1,stdout=''.join(k+'='+before[k]+'\n' for k in ('Id','LoadState','ActiveState')).encode(),stderr=b'')
        self.assertEqual(m.controller_idle(unit,runner)['LoadState'],'not-found')
        self.assertEqual(m.controller_idle(unit,runner)['ReturnCode'],1)
    def test_systemd_unknown_rc1_or_active_daemon_permission_are_rejected(self):
        unit='t44-final-p09-continuous.service'
        for rc,load,active,err in [(1,'loaded','inactive',b''),(1,'not-found','inactive',b'Access denied'),(1,'not-found','inactive',b'Failed to connect to bus'),(0,'loaded','active',b''),(0,'loaded','activating',b''),(1,'not-found','failed',b''),(2,'not-found','inactive',b''),(0,'masked','inactive',b'')]:
            raw=f'Id={unit}\nLoadState={load}\nActiveState={active}\n'.encode()
            with self.subTest(rc=rc,load=load,active=active,err=err),self.assertRaisesRegex(m.Stop,'OLD_CONTROLLER'):
                m.controller_idle(unit,lambda *a,**k:SimpleNamespace(returncode=rc,stdout=raw,stderr=err))
        with self.assertRaises(m.Stop):
            m.controller_idle(unit,lambda *a,**k:SimpleNamespace(returncode=1,stdout=b'ActiveState=inactive\n',stderr=b''))
        for state in ('inactive','failed'):
            raw=f'Id={unit}\nLoadState=loaded\nActiveState={state}\n'.encode()
            self.assertEqual(m.controller_idle(unit,lambda *a,**k:SimpleNamespace(returncode=0,stdout=raw,stderr=b''))['ActiveState'],state)

    def test_existing_owner_gateway_discovery_dynamic_not_old_ip(self):
        host=m.load_module('existing_host',EXISTING/'host_runner.py')
        networks={'owned-net':{'IPAddress':'192.168.96.99','NetworkID':'same-net-id'}}
        row={'id':'a'*64,'running':True,'labels':{'com.docker.compose.project':'t44-test-owned','com.docker.compose.service':'tls-gateway'},'networks':networks,'ports':{'8443/tcp':[{'HostPort':'26445'}]}}
        def run(argv,**kw):
            if 'ps' in argv:return SimpleNamespace(stdout=(row['id']+'\n').encode())
            if argv[-1]=='api-id':return SimpleNamespace(stdout=json.dumps({'owned-net':{'IPAddress':'192.168.96.3','NetworkID':'same-net-id'}}).encode())
            return SimpleNamespace(stdout=json.dumps(row).encode())
        args=SimpleNamespace(api_container='api-id',discover_maintenance_gateway=True,maintenance_gateway_container=None,maintenance_connect_ip=None,maintenance_connect_port=None)
        with patch.object(host.subprocess,'run',run):
            result=host.maintenance_endpoint(args,{'namespace':'t44-test-owned'},self.old)
        self.assertEqual(result['connect_ip'],'192.168.96.99')
        self.assertEqual(result['connect_port'],8443)
        row['networks']['owned-net']['NetworkID']='other-owner-network'
        with patch.object(host.subprocess,'run',run),self.assertRaisesRegex(ValueError,'UNIQUE_SHARED'):host.maintenance_endpoint(args,{'namespace':'t44-test-owned'},self.old)
    def test_existing_tls_identity_strict_ca_with_dynamic_connect(self):
        runtime=m.load_module('existing_tls',EXISTING/'runtime_support.py')
        seen={}
        class Context:
            verify_mode=ssl.CERT_REQUIRED;check_hostname=True
            def wrap_socket(self,raw,server_hostname):seen['sni']=server_hostname;return raw
        def context(**kwargs):seen['ca']=kwargs['cafile'];return Context()
        class Sock:
            def close(self):pass
        def connector(target,**kwargs):seen['connect']=target;return Sock()
        connection=runtime.PinnedHTTPSConnection(self.old['environment']['origin'],'192.168.96.99',Path('strict-ca.pem'),connector=connector,context_factory=context,connect_port=8443)
        connection.connect()
        self.assertEqual(seen,{'ca':'strict-ca.pem','connect':('192.168.96.99',8443),'sni':'172.21.182.245'})
        connection.close()
        with self.assertRaisesRegex(ValueError,'CERTIFICATE'):
            runtime.PinnedHTTPSConnection(self.old['environment']['origin'],'192.168.96.99',Path('ca'),context_factory=lambda **kw:SimpleNamespace(verify_mode=ssl.CERT_NONE,check_hostname=False),connect_port=8443)


if __name__=='__main__':unittest.main()
