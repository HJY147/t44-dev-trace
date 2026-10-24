"""Bounded isolated driver calibration. No application/context/control imports."""
import argparse, asyncio, ast, collections, gzip, hashlib, json, math, os
from pathlib import Path
import resource, signal, struct, subprocess, sys, time, uuid
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'harness_common.py'
EXPECTED_SOURCE='40136e5d8fb152cbbfa35cca2fb489e1fa82503e8524c6b0f60d945395b31c65'
CASES=[{'name':'small_immediate','users':4,'seconds':4,'cap':1000,'delay':0},
       {'name':'large_immediate','users':400,'seconds':8,'cap':2500,'delay':0},
       {'name':'large_bounded_delay','users':400,'seconds':8,'cap':2500,'delay':0.05},
       {'name':'large_timeout_boundary','users':400,'seconds':7,'cap':800,'delay':5.2}]
BODY={'data':{'valid':True,'category':1,'validated_operation_id':'createTask','schema_version':'1.0.0','business_guards_executed':False},'meta':{'request_id':'isolated-calibration','server_time':'2026-10-24T00:00:00Z','contract_version':'1.1.0','replayed':False,'original_request_id':None}}

def utc():return datetime.now(timezone.utc).isoformat()
def sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def usage():
 r=resource.getrusage(resource.RUSAGE_SELF)
 return {'user_s':r.ru_utime,'system_s':r.ru_stime,'max_rss_raw':r.ru_maxrss,'max_rss_unit':'bytes on macOS; KiB on Linux','platform':sys.platform}

async def stub(out):
 out=Path(out);stop=asyncio.Event();loop=asyncio.get_running_loop()
 for sig in [signal.SIGTERM,signal.SIGINT]:loop.add_signal_handler(sig,stop.set)
 active=0;peak=0;received=0;replied=0;disconnected=0;connections=0;per={};tasks=set();writers=set()
 raw=gzip.open(out/'stub-events.jsonl.gz','wt');start=time.monotonic();sam=[]
 async def observe():
  previous=time.monotonic()
  while not stop.is_set():
   now=time.monotonic();sam.append({'t':now,'active':active,'received':received,'replied':replied,'lag_over_0_1s':max(0,now-previous-.1),'usage':usage()});previous=now
   try:await asyncio.wait_for(stop.wait(),.1)
   except asyncio.TimeoutError:pass
 async def handle(reader,writer):
  nonlocal active,peak,received,replied,disconnected,connections
  connections+=1;tasks.add(asyncio.current_task());writers.add(writer)
  try:
   while not stop.is_set():
    try:head=await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'),10)
    except (asyncio.IncompleteReadError,asyncio.TimeoutError,ConnectionError):break
    if len(head)>16384:break
    lines=head.decode('ascii').split('\r\n');name=lines[0].split(' ')[1].strip('/');case=next((c for c in CASES if c['name']==name),None)
    headers={k.lower():v.strip() for k,v in (l.split(':',1) for l in lines[1:] if ':' in l)};length=int(headers.get('content-length','0'))
    if length>4096 or case is None or received>=10000:break
    await reader.readexactly(length);received+=1;ident=received;active+=1;peak=max(peak,active)
    row=per.setdefault(name,{'received':0,'replied':0,'peak_active':0,'active':0});row['received']+=1;row['active']+=1;row['peak_active']=max(row['peak_active'],row['active']);s=time.monotonic()
    raw.write(json.dumps({'kind':'request','case':name,'id':ident,'at':s,'active':active})+'\n')
    try:
     if case['delay']:await asyncio.sleep(case['delay'])
     payload=json.dumps(BODY,separators=(',',':')).encode();writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nCache-Control: no-store\r\nConnection: keep-alive\r\nContent-Length: '+str(len(payload)).encode()+b'\r\n\r\n'+payload);await writer.drain();replied+=1;row['replied']+=1
     raw.write(json.dumps({'kind':'reply_write','case':name,'id':ident,'at':time.monotonic()})+'\n')
    except (ConnectionError,BrokenPipeError):disconnected+=1
    finally:active-=1;row['active']-=1
  except (ConnectionError,asyncio.IncompleteReadError):disconnected+=1
  finally:
   writers.discard(writer);writer.close();tasks.discard(asyncio.current_task())
 server=await asyncio.start_server(handle,'127.0.0.1',0,limit=16384);port=server.sockets[0].getsockname()[1];save(out/'stub-ready.json',{'pid':os.getpid(),'host':'127.0.0.1','port':port});observer=asyncio.create_task(observe())
 await stop.wait();server.close();await server.wait_closed()
 for w in list(writers):w.close()
 pending=list(tasks)
 for t in pending:t.cancel()
 await asyncio.gather(*pending,return_exceptions=True);await observer;raw.close()
 save(out/'stub-summary.json',{'pid':os.getpid(),'started_monotonic':start,'finished_monotonic':time.monotonic(),'received':received,'reply_writes':replied,'disconnected':disconnected,'peak_active':peak,'per_case':per,'samples':sam,'usage':usage(),'meaning':'Independent stub request parse/reply-write observations; socket write is not client acknowledgement.'})

async def client(out,port):
 import httpx
 from jsonschema import Draft202012Validator,FormatChecker
 global SPEC,FMT,FRAME,PHASE,OPS
 SPEC=json.loads((HERE/'inputs/openapi.json').read_text());FMT=FormatChecker();FRAME=struct.Struct('<QIHHIHHII');PHASE={'setup':0,'warmup':1,'steady':2,'postcheck':3};OPS={'setup':1,'plan_prepare':2,'transition':10,'query_detail':11,'query_list':12,'query_history':13,'contract_valid':20,'contract_reject':21,'escalation_new':30,'escalation_duplicate':31,'notification_query':32,'postcheck':40}
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED_SOURCE
 source=SOURCE.read_text();tree=ast.parse(source);evidence=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Evidence');driver=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Driver');names={'key','validate_response','request','sampler'};methods=[n for n in driver.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names];assert len(methods)==4
 isolated=ast.ClassDef(name='IsolatedClient',bases=[],keywords=[],body=methods,decorator_list=[]);module=ast.fix_missing_locations(ast.Module(body=[evidence,isolated],type_ignores=[]));ns=dict(globals());ns.update({'httpx':httpx,'Draft202012Validator':Draft202012Validator,'FormatChecker':FormatChecker});exec(compile(module,'frozen-h2-ast-methods','exec'),ns)
 copied={n.name:hashlib.sha256(ast.get_source_segment(source,n).encode()).hexdigest() for n in [evidence,*methods]};results=[];overall=time.monotonic();out=Path(out)
 for case in CASES:
  if time.monotonic()-overall>=45:break
  d=ns['IsolatedClient']();d.mode=867;d.run_id=str(uuid.uuid4());d.validators={};d.phase='steady';d.inflight=collections.Counter();d.active_users=0;caseout=out/case['name'];caseout.mkdir(mode=0o700);d.e=ns['Evidence'](caseout,867);d.e.report['status']='CALIBRATION_ONLY';start=time.perf_counter_ns();d.phase_deadline=start+int(case['seconds']*1e9);d.e.report['phases']['steady']={'start_ns':start,'end_ns':d.phase_deadline,'duration_s':case['seconds']};d.client=httpx.AsyncClient(base_url=f'http://127.0.0.1:{port}',trust_env=False,http2=False,timeout=httpx.Timeout(5),limits=httpx.Limits(max_connections=800,max_keepalive_connections=800))
  stop=asyncio.Event();observer=asyncio.create_task(d.sampler(stop));issued=0;returned=0;ok=0;cycle=[];cpu0=usage();wall0=time.monotonic()
  async def worker(vu):
   nonlocal issued,returned,ok
   d.active_users+=1;seq=0
   try:
    while time.perf_counter_ns()<d.phase_deadline and issued<case['cap']:
     issued+=1;seq+=1;s=time.monotonic();value=await d.request('POST','/'+case['name'],'calibration-only-dummy',{'calibration':True},op='contract_valid',vu=vu,seq=seq,route='/projects/{project_id}/contract-validations');cycle.append({'start':s,'finish':time.monotonic(),'success':value is not None});returned+=1;ok+=value is not None
   finally:d.active_users-=1
  await asyncio.gather(*(worker(v) for v in range(case['users'])));stop.set();await observer;await d.client.aclose();cpu1=usage();d.e.finish();save(caseout/'cycle.json',cycle);results.append({'case':case,'started_monotonic':wall0,'finished_monotonic':time.monotonic(),'issued':issued,'returned':returned,'oracle_success':ok,'cpu_before':cpu0,'cpu_after':cpu1,'evidence_origin_ns':d.e.origin,'phase_start_ns':start,'phase_deadline_ns':d.phase_deadline,'validators_cached':len(d.validators)})
 save(out/'client-summary.json',{'pid':os.getpid(),'started_monotonic':overall,'finished_monotonic':time.monotonic(),'copied_source_sha256':EXPECTED_SOURCE,'copied_AST_segment_sha256':copied,'cases':results,'usage':usage(),'httpx_version':httpx.__version__,'jsonschema_version':__import__('importlib.metadata',fromlist=['version']).version('jsonschema'),'isolation':'Only selected tester Evidence/key/validate_response/request/sampler AST nodes compiled. No Driver initialization/control/fixture/product imports.','unknowns':['Not Linux/CI; no independent kernel packet capture; not all H2 request/response classes; no SUT data.']})

def supervise(out):
 out=Path(out);out.mkdir(mode=0o700,parents=True,exist_ok=False);start=time.monotonic();children=[];record={'started_at_utc':utc(),'supervisor_pid':os.getpid(),'maximum_total_wall_s':150,'maximum_client_lifetime_s':55,'request_cap_sum':sum(c['cap'] for c in CASES),'cases':CASES,'ownership':[]};files=[]
 def abort(signum,frame):raise TimeoutError('Independent parent hard alarm')
 signal.signal(signal.SIGALRM,abort);signal.alarm(150)
 try:
  for role in ['stub','client']:
   if role=='client':
    ready_path=out/'stub-ready.json';deadline=time.monotonic()+10
    while not ready_path.exists() and time.monotonic()<deadline and children[0].poll() is None:time.sleep(.05)
    if not ready_path.exists():raise RuntimeError('Owned stub readiness not established')
    ready=json.loads(ready_path.read_text());assert ready['pid']==children[0].pid and ready['host']=='127.0.0.1';port=ready['port']
   log=(out/(role+'-process.log')).open('wb');files.append(log);args=[sys.executable,str(Path(__file__).resolve()),role,str(out)]
   if role=='client':args.append(str(port))
   proc=subprocess.Popen(args,stdout=log,stderr=log,close_fds=True);children.append(proc);record['ownership'].append({'role':role,'pid':proc.pid,'started_monotonic':time.monotonic()})
  born=time.monotonic();deadline=born+55
  while children[1].poll() is None and time.monotonic()<deadline:time.sleep(.05)
  record['client_observed_wall_s']=time.monotonic()-born;record['client_hard_limit_reached']=children[1].poll() is None
  if children[1].poll() is None:children[1].terminate();children[1].wait(timeout=2)
  record['client_exit_code']=children[1].returncode
 except BaseException as e:record['error']={'type':type(e).__name__,'message':str(e)}
 finally:
  for proc in reversed(children):
   if proc.poll() is None:
    proc.terminate()
    try:proc.wait(timeout=3)
    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
  signal.alarm(0)
  for f in files:f.close()
  record.update(finished_at_utc=utc(),parent_wall_s=time.monotonic()-start,owned_children_exit_codes=[p.returncode for p in children],owned_processes_reaped=all(p.poll() is not None for p in children),parent_usage=usage());save(out/'parent-summary.json',record)
  for p in out.rglob('*'):
   if p.is_file():os.chmod(p,0o600)
 print(json.dumps({'parent_wall_s':record['parent_wall_s'],'client_exit_code':record.get('client_exit_code'),'error':record.get('error'),'owned_processes_reaped':record['owned_processes_reaped']}))

if __name__=='__main__':
 os.umask(0o077);role=sys.argv[1];out=sys.argv[2]
 if role=='supervise':supervise(out)
 elif role=='stub':asyncio.run(stub(out))
 elif role=='client':asyncio.run(client(out,int(sys.argv[3])))
 else:raise SystemExit('Unknown fixed role')
