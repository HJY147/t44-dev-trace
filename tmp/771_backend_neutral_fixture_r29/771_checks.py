import datetime as dt
import importlib.util
import json
import tempfile
import subprocess
import hashlib
import jsonschema
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT/'agents/backend/neutral-fixture-20261029'
spec=importlib.util.spec_from_file_location('neutral_edge',DIR/'edge.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

class FiniteNeutralChecks(unittest.TestCase):
    def test_admission_required_before_http_or_files(self):
        with tempfile.TemporaryDirectory() as d:
            c=Path(d)/'config.json';c.write_text('{}')
            with patch.object(e,'Client',side_effect=AssertionError('NO_HTTP')):
                with self.assertRaisesRegex(ValueError,'ROOT_PREPARATION'):
                    e.run(c,Path(d)/'new')
            self.assertFalse((Path(d)/'new').exists())

    def test_stable_disjoint_level3_selection(self):
        now=dt.datetime(2026,10,29,4,tzinfo=dt.timezone.utc)
        rows=[{'id':i,'state':2,'plan':{'planned_end':e.stamp(now-dt.timedelta(days=2))}} for i in range(1,15)]
        rows += [{'id':99,'state':6,'plan':{'planned_end':e.stamp(now-dt.timedelta(days=9))}}]
        self.assertEqual([r['id'] for r in e.choose_escalations(rows,{1,2,3},now)],list(range(4,14)))
        with self.assertRaisesRegex(ValueError,'INSUFFICIENT'):
            e.choose_escalations(rows,set(range(1,15)),now)

    def test_seed_math_no_natural_future_and_600_developing(self):
        anchor=dt.datetime(2026,10,28,4,tzinfo=dt.timezone.utc)
        stop=dt.datetime(2026,10,29,4,56,tzinfo=dt.timezone.utc)
        states=[6 if i<60 else (1,2,3,4,5,7)[(i-60)%6] for i in range(150)]
        self.assertEqual(states.count(2)*40,600)
        future=[i for i,s in enumerate(states) if s==2 and anchor+dt.timedelta(hours=(i+44)%96-48)>stop+dt.timedelta(days=1)]
        self.assertEqual(future,[])
        self.assertEqual(max((i+44)%96-48 for i in range(150) if states[i]!=6),47)

    def test_full_neutral_shape_and_original_scope_untouched(self):
        now=dt.datetime.now(dt.timezone.utc)
        stop=now+dt.timedelta(minutes=40)
        accounts={r:{'username':r,'password':'private-'+r,'user_id':i} for i,r in enumerate(('manager','developer','reviewer'),1)}
        calls=[];stored={};next_ids={i:6000+i*20 for i in range(1,41)}
        class Fake:
            def __init__(self,*a):pass
            def close(self):pass
            def request(self,path,token=None,body=None,method=None):
                calls.append((path,body))
                schema_name=('LoginRequest' if path=='/auth/login' else 'StartTransition' if path.endswith('/transitions') else 'EscalationRequest' if path.startswith('/internal/') else 'TaskCreate' if path.endswith('/tasks') and body is not None else None)
                if schema_name:
                    spec=json.loads((ROOT/'specs/contracts/openapi.json').read_bytes())
                    registry=jsonschema.RefResolver.from_schema(spec)
                    jsonschema.Draft202012Validator(spec['components']['schemas'][schema_name],resolver=registry,format_checker=jsonschema.FormatChecker()).validate(body)
                if path=='/auth/login':
                    uid=accounts[body['username']]['user_id']
                    return {'user':{'id':uid},'access_token':'real-shaped-'+str(uid),'expires_at':e.stamp(stop+dt.timedelta(minutes=10))}
                if path.startswith('/projects?page='):
                    return {'items':[{'id':i} for i in range(1,41)],'total':40}
                parts=path.split('/');pid=int(parts[2] if parts[1]=='projects' else parts[3]);base=pid*100000
                if '/members?' in path:
                    return {'items':[{'user':{'id':i},'roles':[i],'active':True} for i in (1,2,3)],'total':3}
                if '/iterations?' in path:
                    return {'items':[{'id':pid,'plan':{'capacity':[{'user_id':2}], 'planned_end':e.stamp(stop+dt.timedelta(days=7))}}],'total':1}
                if '/tasks?' in path:
                    return {'items':[{'id':base+i,'project_id':pid,'state':1,'version':1,'schedule_version':1,'plan':{'planned_end':e.stamp(now-dt.timedelta(days=4))}} for i in range(10)],'total':10}
                if path.endswith('/escalation-rules'):return {'version':1}
                if path.endswith('/tasks'):
                    self_case.assertEqual(set(body),{'title','description','iteration_id','owner_id','dependency_task_ids','plan'})
                    self_case.assertEqual(body['dependency_task_ids'],[])
                    self_case.assertGreater(e.parsed(body['plan']['planned_end']),stop+dt.timedelta(days=1))
                    next_ids[pid]+=1;tid=next_ids[pid]
                    row={'id':tid,'project_id':pid,'owner_id':2,'state':1,'version':1,'schedule_version':1,'plan':body['plan']};stored[tid]=row
                    return {'task':dict(row)}
                if path.endswith('/transitions'):
                    tid=int(parts[-2]);self_case.assertEqual(body,{'expected_version':1,'action':1})
                    stored[tid].update(state=2,version=2);return {'task':dict(stored[tid])}
                if path.startswith('/internal/'):
                    tid=int(parts[-2]);stored[tid]={'id':tid,'project_id':pid,'version':2,'state':1,'schedule_version':1,'plan':{'planned_end':e.stamp(now-dt.timedelta(days=4))}}
                    return {'event':{'id':tid,'level':3},'created':True}
                if '/escalations?' in path:
                    tid=int(path.split('task_id=')[1].split('&')[0]);return {'items':[{'id':tid,'level':3}],'total':1}
                return dict(stored[int(parts[-1])])
        self_case=self
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);(d/'accounts.json').write_text(json.dumps(accounts))
            service={'token':'private-service','user_id':9,'expires_at':e.stamp(stop+dt.timedelta(minutes=10)), 'project_ids':list(range(1,41)), 'scopes':['escalation:write']}
            (d/'service.json').write_text(json.dumps(service))
            c={'admit_real_HTTP_fixture_preparation':True,'original_short_diagnostic_finished':True,'cost_stop_utc':e.stamp(stop),
                'accounts_file':str(d/'accounts.json'),'service_file':str(d/'service.json'),'origin':'https://127.0.0.1',
                'ca_file':str(d/'ca.pem'),'exclude_short_task_ids':list(range(1,883))}
            (d/'config.json').write_text(json.dumps(c))
            with patch.object(e,'Client',Fake):
                result=e.run(d/'config.json',d/'new')
            inv=json.loads((d/'new/inventory.json').read_text())
            self.assertEqual(result['new_tasks'],400);self.assertEqual(len(inv['clients']),400)
            ids=[x[k]['id'] for x in inv['clients'] for k in ('transition_task','escalation_task')]
            self.assertEqual(len(set(ids)),800);self.assertFalse(set(ids)&set(range(1,883)))
            self.assertEqual(len([p for p,b in calls if p.endswith('/transitions')]),400)
            self.assertEqual(len([p for p,b in calls if p.startswith('/internal/')]),400)
            before=(d/'new/inventory.json').read_bytes()
            with self.assertRaises(FileExistsError):
                with patch.object(e,'Client',side_effect=AssertionError('NO_RETRY_HTTP')):e.run(d/'config.json',d/'new')
            self.assertEqual((d/'new/inventory.json').read_bytes(),before)

    def test_complete_installer_pins_and_exclusive_files(self):
        script=(DIR/'install.PUBLIC.sh').read_text()
        self.assertLess(len(script.encode())+300,16500)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d).resolve()/'neutral'
            altered=script.replace("Path('/root/t44-r9/neutral-fixture-r29-01')",'Path('+repr(str(base))+')')
            result=subprocess.run(['/bin/sh'],input=altered.encode(),capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual((base/'code').stat().st_mode&0o777,0o755)
            pins=json.loads((DIR/'code-manifest.PUBLIC.json').read_bytes())['files']
            for name,wanted in pins.items():
                self.assertEqual(hashlib.sha256((base/'code'/name).read_bytes()).hexdigest(),wanted)
                self.assertEqual((base/'code'/name).stat().st_mode&0o777,0o444)
            before=(base/'code/host.py').read_bytes()
            second=subprocess.run(['/bin/sh'],input=altered.encode(),capture_output=True)
            self.assertNotEqual(second.returncode,0)
            self.assertEqual((base/'code/host.py').read_bytes(),before)

if __name__=='__main__':unittest.main(verbosity=2)
