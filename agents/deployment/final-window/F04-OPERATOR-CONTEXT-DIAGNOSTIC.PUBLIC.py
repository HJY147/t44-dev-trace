"""Read-only original operator context/request validation; never operate/respond/replay."""
import datetime,hashlib,importlib.util,json,re,types
from pathlib import Path
R=Path('/root/t44-final-20261029');F=R/'F04';T=R/'ops01/deployment/cloud-reuse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(e):
 text=str(e)
 return text if re.fullmatch('[A-Z0-9_:. -]{1,200}',text) else 'DETAIL_REDACTED_NON_FIXED_CODE'
def main():
 report={'kind':'F04_OPERATOR_ORIGINAL_CONTEXT_READ_ONLY','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operate_called':False,'respond_called':False,'original_response_unchanged':True}
 prep=json.loads((F/'preparation.PUBLIC.json').read_bytes());b=prep['phase'];budget=prep['budget'];request=F/'operator-channel/r30finalf04-001.request.json'
 args=types.SimpleNamespace(phase_dir=Path(b['phase_dir']),binding_sha256=b['binding_sha256'],gen_profile=F/'profile/profile.json',source_profile=R/'source-profile.root-approved.PUBLIC.json',request_file=request,request_sha256=sha(request),evidence_dir=F/'UNUSED_READ_ONLY_DIAGNOSTIC',budget_receipt=Path(budget['budget_receipt']),budget_receipt_sha256=budget['budget_receipt_sha256'],timeplan=F/'timeplan.PUBLIC.json',f_started_utc='2026-10-29T17:50:58.757650Z',cost_cutoff_utc='2026-10-29T19:30:00Z')
 args.gen_profile_sha256=sha(args.gen_profile);args.source_profile_sha256=sha(args.source_profile);args.timeplan_sha256=sha(args.timeplan)
 report['input_hashes']={k:sha(v) for k,v in {'request':request,'gen_profile':args.gen_profile,'source_profile':args.source_profile,'timeplan':args.timeplan,'binding':args.phase_dir/'binding.json'}.items()};report['f_closed_exists']=(args.phase_dir/'F-CLOSED').exists()
 spec=importlib.util.spec_from_file_location('original_f04operator_diagnostic',T/'final-f-operator.py');op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
 try:
  gen,lib,value,bm,profile=op.context(args);report['context']={'success':True,'phase':value['phase'],'source_sha':value['source_sha'],'project':value['project']}
 except Exception as e:
  report['context']={'success':False,'error_class':type(e).__name__,'fixed_code':safe(e)};print(json.dumps(report,sort_keys=True));return
 try:
  row,end=op.request(args,profile,value);report['request']={'success':True,'action':row['action'],'request_id':row['request_id'],'effective_deadline_epoch':end}
 except Exception as e:report['request']={'success':False,'error_class':type(e).__name__,'fixed_code':safe(e),'note':'request validation uses current actual time; expiry now does not prove expiry at original attempt'}
 # Same ownership lookup as original operate, read-only; no DB admission, lock or lifecycle call.
 try:
  row=json.loads(request.read_bytes());role={'scheduler_restart':'scheduler','mq_stop':'rabbitmq','mq_start':'rabbitmq','api_restart':'api','api_ready_wait':'api'}[row['action']];facts=gen.live(lib,value,role)
  report['owned_role']={'role':role,'absent':facts.get('absent',False),'container_id':facts.get('container_id'),'image_id':facts.get('image_id'),'running':facts.get('state',{}).get('Running'),'restart_count':facts.get('restart_count')}
 except Exception as e:report['owned_role']={'success':False,'error_class':type(e).__name__,'fixed_code':safe(e)}
 print(json.dumps(report,sort_keys=True))
if __name__=='__main__':main()
