"""Public generic-only CI. No business cases, SUT source/accounts or production keys."""
import argparse,asyncio,datetime,gzip,hashlib,http.client,importlib.util,io,json,os,platform,queue,resource,ssl,subprocess,sys,tarfile,threading,time,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent;STAGE=Path('/stage');REPORT=STAGE/'report';REPORT.mkdir(exist_ok=True)
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def write(name,v):(REPORT/name).write_text(json.dumps(v,indent=2)+'\n')
def facts():
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'system':platform.system(),'machine':platform.machine(),'os_cpu_count':os.cpu_count(),'affinity_count':len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,'ssl':ssl.OPENSSL_VERSION,'cgroup':{}}
 for n in ['cpu.max','memory.max','pids.max']:
  p=Path('/sys/fs/cgroup')/n;result['cgroup'][n]=p.read_text().strip() if p.exists() else None
 return result
def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['reject-unbounded','constrained']);mode=ap.parse_args().mode;builder=load(ROOT/'generic_engine.py','qa772_generic_builder');observed=facts()
 if mode=='reject-unbounded':
  try:builder.platform_resource_guard();outcome='ACCEPTED'
  except Exception as e:outcome=str(e)
  report={'scope':'OBSERVED_UNCONSTRAINED_LINUX_GUARD_NEGATIVE','actual':observed,'guard_outcome':outcome,'expected_reject':outcome!='ACCEPTED','SUT_calls':0};write('unbounded-guard.json',report);print(json.dumps(report));assert outcome!='ACCEPTED';return
 builder.platform_resource_guard();threading.stack_size(builder.WORKER_STACK_BYTES)
 private=STAGE/'private';private.mkdir(mode=0o700,exist_ok=True);key=os.urandom(32);keyfile=private/'capsule.key';keyfile.write_bytes(key);keyfile.chmod(0o600);buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w:gz') as tar:
  for n in ['generic_engine.py','provenance.json']:
   data=(ROOT/n).read_bytes();entry=tarfile.TarInfo(n);entry.size=len(data);entry.mode=0o600;tar.addfile(entry,io.BytesIO(data))
 payload=buf.getvalue();capsule=private/'generic-tool-source.772seal';seal=builder.Seal(capsule,key)
 for off in range(0,len(payload),builder.FRAME):seal.frame(payload[off:off+builder.FRAME])
 seal.close({'payload_sha256':hashlib.sha256(payload).hexdigest()});dest=private/'decrypted';completed=subprocess.run([sys.executable,str(ROOT/'bootstrap.py'),str(capsule),str(keyfile),str(dest)],capture_output=True,text=True);assert completed.returncode==0;assert (dest/'generic_engine.py').read_bytes()==(ROOT/'generic_engine.py').read_bytes();g=load(dest/'generic_engine.py','qa772_decrypted_generic');g.platform_resource_guard();checks=[]
 # Real bounded transient pressure: every original record must survive authentication.
 log=private/'pressure';log.mkdir();stop=threading.Event();sink=g.Sink(log,key,{'plain_bytes':10*g.GIB,'compressed_bytes':11*g.GIB,'cipher_bytes':12*g.GIB},stop,queue_slots=2);old=sink.emit;sink.emit=lambda p:(time.sleep(.12),old(p))[1];expected=[{'index':i,'zero':0,'null':None} for i in range(20)]
 for v in expected:assert sink.put(v)
 sink.close();z=zlib.decompressobj(31);plain=b'';footer=None
 for k,p in g.Seal.read(log/'evidence.772seal',key):
  if k==255:footer=json.loads(p)
  else:plain+=z.decompress(p)
 assert [json.loads(x) for x in plain.splitlines()]==expected and z.eof and footer['records']==20 and sink.reason is None;checks.append('transient_pressure_no_drop_zero_null')
 # Execute the exact extracted cleanup wrapper against an initialization exception.
 obj=object.__new__(g.Lifecycle);obj.env={'run_id':'GENERIC_LINUX','output_dir':str(private/'lifecycle')};obj.out=Path(obj.env['output_dir']);obj.out.mkdir();obj.stop=threading.Event();obj.barrier=threading.Barrier(2);obj.worker_threads=[];obj.connections=[];obj._startup_error=None;obj.post_pool=None;obj.post_pool_lock=threading.Lock();obj.post_validation_jobs=0;obj.sink=g.Sink(obj.out,key,{'plain_bytes':10*g.GIB,'compressed_bytes':11*g.GIB,'cipher_bytes':12*g.GIB},obj.stop)
 def fail():raise FileNotFoundError('synthetic missing local input')
 obj._execute=fail;value=obj.execute();assert value['metrics_verdict']=='NP' and value['full_cohort'] is False and (obj.out/'result.json').exists() and not obj.sink.thread.is_alive();checks.append('exact_cleanup_wrapper_explicit_np')
 unrelated=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True)
 try:
  start=time.monotonic();code,reason,pid=g.supervise_owned([sys.executable,'-c','import time;time.sleep(60)'],time.time()+.3,time.monotonic()+.3);assert reason=='HARD_DEADLINE' and code!=0 and time.monotonic()-start<3 and unrelated.poll() is None;checks.append('owned_deadline_preserves_unrelated')
 finally:unrelated.terminate();unrelated.wait(2)
 # Actual 400 native threads and TLS sockets; generic /probe only, no application API.
 ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(STAGE/'tls.crt',STAGE/'tls.key');ready=threading.Event();port=[];server_loop=asyncio.new_event_loop()
 async def handler(reader,writer):
  try:
   while True:
    line=await reader.readline()
    if not line:break
    while await reader.readline()!=b'\r\n':pass
    body=b'{"ok":true,"zero":0,"null":null}';writer.write(b'HTTP/1.1 200 OK\r\nContent-Length: '+str(len(body)).encode()+b'\r\nContent-Type: application/json\r\n\r\n'+body);await writer.drain()
  except (ConnectionError,asyncio.IncompleteReadError):pass
  finally:writer.close()
 async def serve():
  server=await asyncio.start_server(handler,'127.0.0.1',0,ssl=ctx,backlog=1024);port.append(server.sockets[0].getsockname()[1]);ready.set()
  async with server:await server.serve_forever()
 def loop():
  asyncio.set_event_loop(server_loop)
  try:server_loop.run_until_complete(serve())
  except RuntimeError:pass
 server_thread=threading.Thread(target=loop,daemon=True);server_thread.start();assert ready.wait(10);client_ctx=ssl.create_default_context(cafile=str(STAGE/'tls.crt'));barrier=threading.Barrier(401);slots=threading.BoundedSemaphore(8);end=[0];counts=[0]*400;errors=[]
 def client(index):
  connection=None
  try:
   with slots:
    connection=g.Connection('localhost',port[0],'127.0.0.1',client_ctx,5);connection.connect()
   barrier.wait(timeout=20)
   while time.monotonic()<end[0]:
    connection.request('GET','/probe');response=connection.getresponse();assert response.status==200 and json.loads(response.read())=={'ok':True,'zero':0,'null':None};counts[index]+=1
  except Exception as exc:errors.append(type(exc).__name__)
  finally:
   if connection:connection.close()
 workers=[threading.Thread(target=client,args=(i,),daemon=True) for i in range(400)]
 for t in workers:t.start()
 until=time.monotonic()+20
 while barrier.n_waiting<400 and time.monotonic()<until:time.sleep(.01)
 assert barrier.n_waiting==400;end[0]=time.monotonic()+3;barrier.wait()
 for t in workers:t.join(10)
 assert not errors and all(n>0 for n in counts) and not any(t.is_alive() for t in workers);checks.append('400_native_linux_tls_clients_finite');server_loop.call_soon_threadsafe(server_loop.stop)
 report={'status':'PASS','scope':'GENERIC_TOOL_ONLY_LINUX_SUBSET','actual':observed,'resource_guard':'PASS_ON_ACTUAL_2CPU_8G_PID2048_CGROUP','unwrapped_source_exact':True,'checks':checks,'native_tls_clients':400,'native_tls_requests':sum(counts),'minimum_client_requests':min(counts),'errors':errors,'formal_private_business_executor_tested':False,'LOAD_original_image_4f3b_tested':False,'formal_8CPU_machine_claim':False,'SUT_calls':0,'no_private_case_or_production_key_uploaded':True,'provenance':json.loads((ROOT/'provenance.json').read_text())};write('linux-tool-subset.json',report);print(json.dumps(report))
if __name__=='__main__':main()
