#!/usr/bin/env python3
"""Read-only SUT collector; only local own logs/evidence are read. No SUT calls."""
import collections,datetime,hashlib,importlib.util,json,os,signal,subprocess,sys,time
from pathlib import Path
os.umask(0o077)
B=Path('/private');P=B/'public';R=B/'results/r29qa772-01';K=B/'retained/r29qa772-01';RUN='r29qa772-01'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
def save(name,value):
 path=P/name;tmp=path.with_suffix('.new');tmp.write_text(json.dumps(value,separators=(',',':'),allow_nan=False)+'\n');tmp.chmod(0o600);os.replace(tmp,path)
def readj(path):return json.loads(Path(path).read_bytes())
def safe_error(value):
 if value is None:return None
 text=str(value);return text if len(text)<=180 and all(c.isalnum() or c in '_:.- ' for c in text) else text.split(':',1)[0]
def unit():
 path=P/'qa772-unit.properties';return dict(x.split('=',1) for x in path.read_text().splitlines() if '=' in x) if path.is_file() else {}
def resource_summary(rows):
 if not rows:return {'status':'NOT_OBSERVED','samples':0}
 first,last=rows[0],rows[-1];seconds=(last['elapsed_ns']-first['elapsed_ns'])/1e9;cpu=sum(last['rusage'][:2])-sum(first['rusage'][:2]);mem=[];pids=[];throttle=[]
 for row in rows:
  cg=row.get('cgroup',{})
  for name,dest in [('memory.current',mem),('pids.current',pids)]:
   try:dest.append(int(cg[name]))
   except (KeyError,ValueError,TypeError):pass
  try:throttle.append(dict((k,int(v)) for k,v in (line.split() for line in cg['cpu.stat'].splitlines())))
  except (KeyError,ValueError,TypeError):pass
 return {'status':'OBSERVED','samples':len(rows),'observed_seconds':seconds,'client_alive_min':min(x['alive'] for x in rows),'client_alive_max':max(x['alive'] for x in rows),'inflight_min':min(x['inflight'] for x in rows),'inflight_max':max(x['inflight'] for x in rows),'queue_max':max(x['queue_size'] for x in rows),'process_cpu_seconds_delta':cpu,'process_cpu_core_equivalent':cpu/seconds if seconds>0 else None,'peak_rss_kib':max(x['rusage'][2] for x in rows),'cgroup_memory_current_peak':max(mem) if mem else None,'cgroup_pids_peak':max(pids) if pids else None,'cgroup_throttled_usec_delta':throttle[-1].get('throttled_usec',0)-throttle[0].get('throttled_usec',0) if throttle else None,'adequacy':'OBSERVATIONS_ONLY_NO_NEW_THRESHOLD'}
def analyze_worker():
 try:
  sys.path.insert(0,str(B/'runtime'));spec=importlib.util.spec_from_file_location('qa772_existing_private_analyze',B/'runtime/analyze.py');private=importlib.util.module_from_spec(spec);spec.loader.exec_module(private);original=json.loads;resources=[];cohort=[]
  def observed_loads(data,*args,**kwargs):
   value=original(data,*args,**kwargs)
   if isinstance(value,dict):
    if value.get('record')=='load_resource':resources.append(value)
    if value.get('record')=='cohort_start':cohort.append({k:value[k] for k in ('start_ns','steady_ns','steady_end_ns','clients')})
   return value
  json.loads=observed_loads
  try:recomputed=private.analyze(R/'evidence.772seal',(R/'evidence.key').read_bytes())
  finally:json.loads=original
  (R/'raw-recomputed.private.json').write_text(json.dumps(recomputed,separators=(',',':'))+'\n');actual=readj(R/'result.json');matching=recomputed['metrics']['classes']==actual['classes'] and recomputed['metrics']['minute_buckets']==actual['minute_buckets'];summary={'schema':'772-public-evidence-analysis-v1','run_id':RUN,'observed_utc':utc(),'status':'COMPLETE','authenticated_prefix':recomputed['authenticated_prefix'],'complete_authenticated_footer':recomputed['complete_authenticated_footer'],'gzip_complete':recomputed['gzip_complete'],'serialized_records':recomputed['serialized_records'],'evidence_sha256':recomputed['sha256'],'recomputed_metrics_verdict':recomputed['metrics']['metrics_verdict'],'counts_p95_and_buckets_equal_runtime':matching,'classes':recomputed['metrics']['classes'],'minute_buckets':recomputed['metrics']['minute_buckets'],'failure_counts':{safe_error(k):v for k,v in recomputed['metrics']['failures'].items()},'cohort_clock':cohort,'original_load_resources':resource_summary(resources),'scope':'THIS_RUN_PERFORMANCE_ONLY','function_52_gate_conclusion':'NOT_IN_SCOPE','mq_delivery_and_fixture_scale_acceptance':'NOT_ESTABLISHED_BY_HTTP_PERFORMANCE','private_source_key_token_or_raw_body_output':False};save('qa772-evidence-analysis.json',summary)
 except Exception as exc:save('qa772-evidence-analysis.json',{'run_id':RUN,'status':'NP_POSTPROCESS','exception_type':type(exc).__name__,'observed_utc':utc(),'raw_evidence_preserved':True,'sut_calls':0})
def collect():
 state=unit();cipher=R/'evidence.772seal';result=R/'result.json';status={'schema':'772-public-readonly-status-v1','run_id':RUN,'observed_utc':utc(),'unit':state,'result_present':result.is_file(),'cipher_bytes':cipher.stat().st_size if cipher.is_file() else None,'sut_calls_by_collector':0,'new_grants_or_runs':0};save('qa772-readonly-status.json',status)
 if result.is_file():
  actual=readj(result);fields=['schema','benchmark','run_id','utc','identity','runtime_sha256','declared_fixture_counts','fixture_scale_observation','metrics_verdict','reasons','full_cohort','warmup_seconds','steady_seconds','observed_elapsed_seconds','classes','minute_buckets','escalation_api_created','escalation_api_created_p95_ms','inter_request_gap','client_completion_min','client_completion_max','postconditions','mq_delivery_postcondition','independent_conclusion','raw_evidence_encrypted','raw_plain_bytes','raw_compressed_bytes','raw_cipher_bytes','writer_queue_highwater','writer_enqueue_block_ns'];summary={k:actual.get(k) for k in fields};summary['failures']={safe_error(k):v for k,v in actual.get('failures',{}).items()};summary['capacity_or_writer_stop']=safe_error(actual.get('capacity_or_writer_stop'));samples=actual.get('active_client_samples',[]);summary['client_coverage_samples']={'count':len(samples),'alive_min':min((x['alive'] for x in samples),default=None),'alive_max':max((x['alive'] for x in samples),default=None)};summary['scope']='THIS_RUN_PERFORMANCE_ONLY; NO_FUNCTIONAL_GATE_CLAIM';save('qa772-metrics.json',summary)
 if state.get('ActiveState')!='active' and result.is_file() and not (P/'qa772-evidence-analysis.json').exists():
  deadline=min(time.time()+100,datetime.datetime.fromisoformat('2026-10-29T04:55:34+00:00').timestamp());proc=subprocess.Popen([sys.executable,__file__,'--analyze-worker'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  while proc.poll() is None and time.time()<deadline:time.sleep(.1)
  if proc.poll() is None:
   os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(1)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(1)
   save('qa772-evidence-analysis.json',{'run_id':RUN,'status':'NP_POSTPROCESS_DEADLINE','observed_utc':utc(),'raw_evidence_preserved':True,'sut_calls':0})
 elif state.get('ActiveState')!='active' and not result.is_file():save('qa772-final-scope.json',{'run_id':RUN,'status':'NP_NO_RUNTIME_RESULT','unit':state,'observed_utc':utc(),'scope':'THIS_RUN_PERFORMANCE_ONLY','raw_first_failure_retained_privately':True,'no_retry_or_new_grant':True})
 output={'status':readj(P/'qa772-readonly-status.json')}
 for name,key in [('qa772-metrics.json','metrics'),('qa772-evidence-analysis.json','authenticated_evidence_analysis'),('qa772-final-scope.json','scope')]:
  if (P/name).is_file():output[key]=readj(P/name)
 print(json.dumps(output,separators=(',',':'),allow_nan=False),flush=True)
if __name__=='__main__':
 if '--analyze-worker' in sys.argv:analyze_worker()
 else:collect()
