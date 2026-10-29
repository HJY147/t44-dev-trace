"""Fixed P fixture chain; root passes an actual new LOAD readiness receipt. Never grants QA."""
import argparse,hashlib,importlib.util,json,os,secrets,subprocess,sys,time,types
from pathlib import Path
from datetime import datetime,timezone
R=Path('/root/t44-final-20261029');T=R/'ops01/deployment/cloud-reuse';C=R/'ops01/agents/backend/neutral-final-20261029'
PROFILE=R/'source-profile.root-approved.PUBLIC.json';PS='ce3975d1fb5e6f219467fa61cdd0386a182851145993a2a4cf5300688a5cbe5c'
CS='023063c342854c7b2bea107774007fcd89973a4d0ab85f5841db31a6a8cb2a5e';BS='1ddafb7aaa1c552172cc5a0c0f48881412a8fa1fabbb400037854f4bba77a6a2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(p,o):
 with Path(p).open('x') as f:json.dump(o,f,sort_keys=True,indent=2);f.write('\n')
 Path(p).chmod(0o600)
def stamp():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--load-ready',type=Path,required=True);p.add_argument('--load-ready-sha256',required=True)
 p.add_argument('--cost-approval',type=Path,required=True);p.add_argument('--cost-approval-sha256',required=True);a=p.parse_args();os.umask(0o077)
 if sha(PROFILE)!=PS or sha(C/'code-manifest.PUBLIC.json')!=CS or sha(a.load_ready)!=a.load_ready_sha256:raise ValueError('ROOT_PIN_CHANGED')
 ready=read(a.load_ready)
 if (ready.get('root_approved') is not True or ready.get('actual_LOAD_ready') is not True
  or ready['actual_image_id']!='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1'
  or not 0 <= time.time()-datetime.fromisoformat(ready['observed_utc'].replace('Z','+00:00')).timestamp() <=120):raise ValueError('ROOT_ACTUAL_NEW_LOAD_READY_WITHIN120_SECONDS_REQUIRED')
 out=R/'P03';logs=R/'r30finalp03-launcher';logs.mkdir(mode=0o700);i=0
 def run(label,cmd,cap=300):
  nonlocal i;i+=1
  with (logs/(f'{i:02d}-'+label+'.stdout.private')).open('xb') as so,(logs/(f'{i:02d}-'+label+'.stderr.private')).open('xb') as se:
   v=subprocess.run(list(map(str,cmd)),stdout=so,stderr=se,timeout=cap,check=False)
  if v.returncode:raise ValueError('FIXED_P_STEP_FAILED:'+label)
  return read(logs/(f'{i:02d}-'+label+'.stdout.private'))
 f=read(R/'F03/preparation.PUBLIC.json')['phase']
 phase=run('phase',['python3',T/'final-app-prepare-absolute.py','phase','--phase','p','--run-id','r30finalp03','--app-ip','172.21.182.245',
 '--package',R/'boot01/official','--bundle-sha256',BS,'--actual-first-boot-utc','2026-10-29T13:45:26Z','--source-profile',PROFILE,'--source-profile-sha256',PS,
 '--cost-approval',a.cost_approval,'--cost-approval-sha256',a.cost_approval_sha256,'--previous-f-phase-dir',f['phase_dir'],'--previous-f-binding-sha256',f['binding_sha256'],'--output',out],900)
 b=phase['phase'];d=Path(b['phase_dir']);bh=b['binding_sha256'];binding=read(d/'binding.json');clock=read(out/'timeplan.PUBLIC.json');profile=read(PROFILE);budget=phase['budget'];rt=out/'runtime';gen=out/'profile';inputs=out/'P-inputs';inputs.mkdir(mode=0o700)
 def observe(name):
  ids=subprocess.run(['docker','--context','default','ps','--quiet','--filter','label=com.docker.compose.project='+binding['project']],capture_output=True,check=True,timeout=20).stdout.decode().split()
  actual=json.loads(subprocess.run(['docker','--context','default','inspect',*ids],capture_output=True,check=True,timeout=20).stdout)
  roles={x['Config']['Labels']['com.docker.compose.service']:x for x in actual}
  required={'mysql','rabbitmq','api','consumer','web','tls-gateway'}|({'scheduler'} if name=='all-seven' else set())
  if not required<=set(roles) or any(not roles[k]['State']['Running'] for k in required):raise ValueError('ACTUAL_REQUIRED_P_ROLES_MISSING')
  receipt=inputs/(name+'.PUBLIC.json');save(receipt,{'observed_utc':stamp(),'project':binding['project'],'roles':{k:{'id':v['Id'],'running':v['State']['Running'],'image':v['Image']} for k,v in roles.items()}});return receipt,roles
 live,roles=observe('idle-six');plan=read(C/'plan.template.PUBLIC.json');loaded=read(phase['import']['receipt'])
 plan.update(run_id=clock['run_id'],namespace=binding['project'],synthetic=True,root_admit_preparation=True,benchmark_grant_allow=False,
 source_profile={'path':'/neutral-input/source-profile.PUBLIC.json','sha256':PS},gen_binding={'path':'/neutral-input/binding.json','sha256':bh,'original_host_path':str(d/'binding.json')},
 window={k:clock[k] for k in ('start_utc','end_utc','stop_utc')},lifecycle={k:clock[k] for k in ('t0_utc','cost_stop_utc','packet_cutoff_utc')},allowed_writes=['seed_demo','init-user','login','service-token','createTask','transitionTask','createEscalation','addProjectMember','createIteration'],service_name=binding['project']+'-service')
 plan['source'].update(git_commit=profile['source_sha'],manifest_sha256=profile['source_manifest_sha256'],bundle_manifest_sha256=BS,actual_loaded_receipt_path=phase['import']['receipt'],actual_loaded_receipt_sha256=phase['import']['sha256'],actual_loaded_observed_at=loaded['observed_utc'],expected_runtime_files=profile['runtime_file_count'],context_records=profile['context_file_count'],actual_loaded_full_chain_reviewed_by_root=True)
 plan['public_tool_approval'].update(supports_source_git=profile['source_sha'],adapter_sha256=profile['qa_adapter_sha256'],receipt_sha256=profile['qa_approval_receipt_sha256'],root_relayed_approval=True)
 plan['target'].update(compose_project=binding['project'],database=binding['database'],mysql_user=binding['database']+'_app',binding_sha256=bh,origin='https://172.21.182.245:'+str(binding['tls_port']),connect_ip='172.21.182.245',ca_sha256=binding['tls']['ca_sha256'])
 plan['images']={'backend':profile['backend_config_id'],'load_python':profile['load_python_config_id']};plan['budget'].update(helper_sha256=profile['budget_helper_sha256'],actual_admission_receipt_sha256=budget['budget_receipt_sha256'])
 plan['seed'].update(seed=44,anchor_utc='2026-10-28T04:00:00Z');now=stamp()
 for role in plan['runtime_roles']:plan['runtime_roles'][role].update(running_observed=(('rabbitmq' if role=='rabbit' else role) in roles or role=='load'),receipt_sha256=(a.load_ready_sha256 if role=='load' else sha(live)))
 for k,source in {'source':Path(phase['import']['receipt']),'images':Path(phase['import']['receipt']),'transfer':a.load_ready,'preflight':live}.items():plan['readiness'][k]={'sha256':sha(source),'completed_at':now}
 plan['readiness'].update(all_ready_at=now,admin_preserves_image_pythonpath=True)
 common=['--phase-dir',d,'--binding-sha256',bh,'--profile-json',gen/'profile.json','--profile-sha256',sha(gen/'profile.json'),'--code-dir',C,'--code-manifest',C/'code-manifest.PUBLIC.json','--code-manifest-sha256',CS,'--source-profile',PROFILE,'--import-receipt',phase['import']['receipt'],'--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256']]
 def admin(mode,operation,projects,empty=False,label=None):
  label=label or mode
  pp=inputs/(label+'-plan.json');ip=inputs/(label+'-intent.json');save(pp,plan);save(ip,{'run_id':clock['run_id'],'namespace':binding['project'],'database':binding['database'],'binding_sha256':bh,'operation':operation,'project_ids':projects,'empty_scope_observed':empty,'purpose':'material_preparation'})
  return run(label,['python3',rt/'r30-neutral-admin.py',mode,*common,'--plan',pp,'--intent',ip,'--output-dir',out/('P-'+label)])
 empty=admin('counts','seed_demo',[],label='empty-counts')
 if any(read(empty['output'])['actual_fixture_counts'].values()):raise ValueError('NEW_P_DATABASE_NOT_EMPTY')
 accounts=inputs/'accounts.init.private.json';save(accounts,{r:{'username':'synthetic-'+r,'user_id':None,'password':None} for r in ('manager','developer','reviewer')})
 pp=inputs/'accounts-plan.json';ip=inputs/'accounts-intent.json';save(pp,plan);save(ip,{'run_id':clock['run_id'],'namespace':binding['project'],'database':binding['database'],'binding_sha256':bh,'operation':'init-user','project_ids':[],'purpose':'material_preparation'})
 acc=run('accounts',['python3',rt/'r30-neutral-admin.py','init-accounts',*common,'--plan',pp,'--intent',ip,'--accounts',accounts,'--output-dir',out/'P-accounts'])
 seed=admin('seed','seed_demo',[],True);counts=admin('counts','seed_demo',[])
 plan['authorized_project_ids']=read(counts['output'])['project_ids']
 if len(plan['authorized_project_ids'])!=40:raise ValueError('ACTUAL_FORTY_PROJECTS_REQUIRED')
 service=admin('service','service-token',plan['authorized_project_ids']);token=out/'P-service/output/result/original-service.json';target=d/'scheduler-secrets/scheduler-token.json'
 with target.open('xb') as f:f.write(token.read_bytes())
 target.chmod(0o600);os.chown(target,10001,10001)
 run('scheduler',['python3',gen/'generation.py','scheduler-start','--phase-dir',d,'--binding-sha256',bh,'--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256']])
 allseven,roles=observe('all-seven')
 plan['runtime_roles']['scheduler'].update(running_observed=True,receipt_sha256=sha(allseven))
 httpplan=inputs/'http-plan.json';save(httpplan,plan)
 # Original packet may be at most300 seconds old at actual t0+20 execute.
 wake=datetime.fromisoformat(clock['start_utc'].replace('Z','+00:00')).timestamp()-290
 print(json.dumps({'status':'P_SEEDED_SERVICE_AND_SCHEDULER_READY_WAITING_FOR_FRESH_PACKET','wake_utc':datetime.fromtimestamp(wake,timezone.utc).isoformat(),'timeplan':clock}),flush=True)
 while time.time()<wake:time.sleep(min(10,wake-time.time()))
 run('http',['python3',rt/'http-prepare.py','--phase-dir',d,'--binding-sha256',bh,'--code-dir',C,'--code-manifest-sha256',CS,'--source-profile',PROFILE,'--plan',httpplan,'--accounts',acc['output'],'--service',service['output'],'--import-receipt',phase['import']['receipt'],'--ca',d/'tls/ca.pem','--output-dir',out/'P-http'])
 finalcounts=admin('counts','seed_demo',[],label='final-counts')
 actual=read(finalcounts['output'])['actual_fixture_counts']
 if actual!={'projects':40,'tasks':6400,'dependencies':9000,'reviews_and_decisions':15000}:raise ValueError('REAL_POST_HTTP_COUNTS_REQUIRED')
 observed,roles=observe('packet-all-seven')
 if set(roles)!={'mysql','rabbitmq','api','consumer','web','tls-gateway','scheduler'}:raise ValueError('UNEXPECTED_P_WORKLOAD_ROLE')
 if ready.get('QA_or_other_writer_started') is not False:raise ValueError('ROOT_QA_NOT_STARTED_AT_ADMISSION_REQUIRED')
 exclusive={'run_id':clock['run_id'],'namespace':binding['project'],'database':binding['database'],'binding_sha256':bh,'observed_at':stamp(),
 'other_workload_writer_absent':True,'scheduler_running':True,'consumer_running':True,'all_notifications_precreated':False,
 'writer_evidence_sha256':sha(observed),'writer_evidence':{'actual_roles_receipt':str(observed),'root_LOAD_not_started_receipt_sha256':a.load_ready_sha256,'isolated_new_schema':binding['database'],'chain_commands':i}}
 proof=inputs/'exclusive.PUBLIC.json';save(proof,exclusive);plan['readiness']['fixture_ready_at']=stamp()
 finalplan=inputs/'final-plan.json';save(finalplan,plan);intent=inputs/'final-intent.json';save(intent,{'run_id':clock['run_id'],'namespace':binding['project'],'database':binding['database'],'binding_sha256':bh,'operation':'seed_demo','project_ids':[],'purpose':'final_packet'})
 def module(path):
  spec=importlib.util.spec_from_file_location('p03admin',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 adm=module(rt/'r30-neutral-admin.py');ns=types.SimpleNamespace(mode='counts',phase_dir=d,binding_sha256=bh,profile_json=gen/'profile.json',profile_sha256=sha(gen/'profile.json'),code_dir=C,code_manifest=C/'code-manifest.PUBLIC.json',code_manifest_sha256=CS,source_profile=PROFILE,plan=finalplan,intent=intent,import_receipt=Path(phase['import']['receipt']),budget_receipt=Path(budget['budget_receipt']),budget_receipt_sha256=budget['budget_receipt_sha256'],output_dir=out/'P-packet')
 generation,lib,bm,value,staged=adm.checked(ns);code=adm.producer_files(ns)
 for name,path in {'facts.json':out/'P-http/output/result/factual-snapshots.json','sessions.json':out/'P-http/output/result/sessions.json','counts.json':Path(finalcounts['output']),'exclusive.json':proof,'ca.pem':d/'tls/ca.pem','source-manifest.json':R/'boot01/official/source-manifest.json','backend-bundle-manifest.json':R/'boot01/official/backend-bundle-manifest.json'}.items():staged[name]=path.read_bytes()
 adm.stage(ns,staged,code)
 fixed="import sys,runpy;sys.path.insert(0,'/neutral-code');sys.argv=['make_evidence','--plan','/neutral-input/plan.json','--facts','/neutral-input/facts.json','--counts','/neutral-input/counts.json','--exclusive-proof','/neutral-input/exclusive.json','--output','/neutral-output/evidence.json'];runpy.run_path('/neutral-code/make_evidence.py',run_name='__main__');sys.argv=['assemble','--plan','/neutral-input/plan.json','--evidence','/neutral-output/evidence.json','--sessions','/neutral-input/sessions.json','--counts','/neutral-input/counts.json','--ca','/neutral-input/ca.pem','--source-manifest','/neutral-input/source-manifest.json','--bundle-manifest','/neutral-input/backend-bundle-manifest.json','--import-receipt','/neutral-input/backend-import-receipt.json','--output','/neutral-output/packet','--root-admit-new-packet'];runpy.run_path('/neutral-code/assemble.py',run_name='__main__')"
 name=binding['project']+'-neutral-packet-'+secrets.token_hex(4)
 with bm.operation_lock(d,bh):
  generation.valid_window(lib,value['stop_utc'],600);bm.verify_runtime_environment(value,lambda role:generation.live(lib,value,role));admission=bm.admit(d,bh,value,lambda role:generation.live(lib,value,role),ns.budget_receipt,ns.budget_receipt_sha256);save(ns.output_dir/'admission.PUBLIC.json',{'actual_admit_return':admission})
  status=adm.run_child(adm.docker_prefix(ns,value,name)+['-B','-c',fixed],ns.output_dir/'logs/packet.stdout.private',ns.output_dir/'logs/packet.stderr.private',None,90,bm.clean_environment(),lambda stop=False:adm.owned_finished(lib,value,name,stop=stop))
  if status:raise ValueError('ORIGINAL_EVIDENCE_AND_ASSEMBLE_FAILED_PREFIX_PRESERVED')
 print(json.dumps({'status':'P_ORIGINAL_FIVE_FILE_PACKET_CREATED_NOT_QA_STARTED','packet':str(out/'P-packet/output/packet'),'directory':str(out),'timeplan':clock,'phase':b}),flush=True)
 # Original790 sealing/opaque transport is separate from QA authorization.
 subprocess.run(['python3',str(T/'P03-TRANSPORT-APP.PUBLIC.py'),'--f-dir',str(out),'--load-ip','172.21.182.244','--load-public-key',str(R/'ops01/qa-public/load-public.pem')],check=True)
 return
if __name__=='__main__':main()
