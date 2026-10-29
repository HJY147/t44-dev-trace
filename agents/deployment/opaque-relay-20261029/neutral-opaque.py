"""Private TLS opaque file only; no plaintext reads."""
import argparse,datetime as dt,hashlib,http.client,http.server,json,os,re,ssl,stat,subprocess,time
from pathlib import Path
APP,LOAD,PORT='172.21.182.245','172.21.182.244',18448
BASE=Path('/root/t44-r9');PHASE=BASE/'campaign-r29-01/p'
SOURCE=BASE/'neutral-fixture-r29-01/output/sealed-neutral/transfer.public.jsonl'
DEST=BASE/'neutral-opaque-load-r29-01'
TOOL=BASE/'p790-r29-01/transport/790_transfer.py'
TOOL_SHA='8600110b54f45240a6e45ea62c9be6f567529e374807d0ca593dde3fd7605db7'
def need(value,code):
 if not value:raise ValueError(code)
def h(value):return hashlib.sha256(value).hexdigest()
def read(path,cap):
 need(path.is_absolute() and path.resolve()==path,'CANONICAL_FILE')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  a=os.fstat(f.fileno());need(stat.S_ISREG(a.st_mode) and a.st_nlink==1 and a.st_size<=cap,'BOUNDED_REGULAR_FILE');value=f.read(cap+1);b=os.fstat(f.fileno())
 need((a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns) and len(value)==a.st_size,'STABLE_COMPLETE_FILE');return value
def save(path,value):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(value);f.flush();os.fsync(f.fileno())
def emit(value):print(json.dumps(value,sort_keys=True),flush=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['serve','fetch']);p.add_argument('--bytes',type=int,required=True);p.add_argument('--sha256',required=True);p.add_argument('--cost-stop-utc',required=True);p.add_argument('--binding-sha256');p.add_argument('--ca-sha256');p.add_argument('--public-record-sha256');a=p.parse_args()
 os.umask(0o077);need(os.geteuid()==0 and 1<=a.bytes<=4194304 and re.fullmatch('[a-f0-9]{64}',a.sha256),'ROOT_BOUNDED_EXACT_OPAQUE')
 end=dt.datetime.fromisoformat(a.cost_stop_utc.replace('Z','+00:00'));need(end.utcoffset().total_seconds()==0,'UTC_REQUIRED');left=lambda:end.timestamp()-time.time();need(0<left()<=3600,'FINITE_COST_WINDOW')
 if a.action=='serve':
  binding=read(PHASE/'binding.json',100000);need(re.fullmatch('[a-f0-9]{64}',a.binding_sha256 or '') and h(binding)==a.binding_sha256,'ACTUAL_PHASE_BINDING')
  b=json.loads(binding);need(b['source_sha']=='f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f' and b['app_private_ip']==APP,'SOURCE_PHASE')
  cert=PHASE/'tls/server/server.pem';need(h(read(cert,65536))==b['tls']['server_certificate_sha256'],'ORIGINAL_LEAF_CERT')
  payload=read(SOURCE,4194304);need(len(payload)==a.bytes and h(payload)==a.sha256,'COMPLETE_PUBLIC_SIZE_SHA')
  ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(str(cert),str(PHASE/'tls/server/server.key'))
  class Handler(http.server.BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    if self.path!='/opaque':self.send_error(404);return
    self.server.attempted=True
    try:
     self.send_response(200);self.send_header('Content-Length',str(a.bytes));self.send_header('X-T44-SHA256',a.sha256);self.end_headers();self.wfile.write(payload);self.wfile.flush();self.server.delivered=True
    except (OSError,ssl.SSLError):pass
  class Server(http.server.HTTPServer):
   attempted=False;delivered=False
   def get_request(self):
    c,peer=super().get_request()
    try:
     need(peer[0]==LOAD and left()>0,'EXACT_PRIVATE_LOAD_ONLY');c.settimeout(min(5,left()));return ctx.wrap_socket(c,server_side=True),peer
    except BaseException:c.close();raise OSError('PEER_REFUSED') from None
  server=Server((APP,PORT),Handler);server.timeout=.2
  emit({'kind':'NEUTRAL_OPAQUE_PRIVATE_LISTENING','pid':os.getpid(),'bytes':a.bytes,'sha256':a.sha256,'binding_sha256':a.binding_sha256,'cost_stop_utc':a.cost_stop_utc})
  try:
   while left()>0 and not server.attempted:server.handle_request()
  finally:server.server_close()
  need(server.delivered,'NO_COMPLETE_OPAQUE_DELIVERY');emit({'kind':'NEUTRAL_OPAQUE_SENT_ONCE','bytes':a.bytes,'sha256':a.sha256})
 else:
  need(left()>120 and re.fullmatch('[a-f0-9]{64}',a.ca_sha256 or '') and re.fullmatch('[a-f0-9]{64}',a.public_record_sha256 or ''),'FETCH_COST_PUBLIC_PINS')
  ca=BASE/'r29-ops-load-01/opened-resource-only/inputs/ca.pem';need(h(read(ca,65536))==a.ca_sha256 and h(read(TOOL,100000))==TOOL_SHA,'CA_OPEN_HELPER')
  need(DEST.parent.resolve()==DEST.parent,'CANONICAL_PARENT');DEST.mkdir(mode=0o700)
  c=http.client.HTTPSConnection(APP,PORT,timeout=min(30,left()),source_address=(LOAD,0),context=ssl.create_default_context(cafile=str(ca)))
  try:
   c.request('GET','/opaque',headers={'Connection':'close'});r=c.getresponse();need(r.status==200 and r.getheader('Content-Length')==str(a.bytes) and r.getheader('X-T44-SHA256')==a.sha256,'EXACT_OPAQUE_HTTP_RESPONSE');payload=r.read(4194305)
  finally:c.close()
  need(len(payload)==a.bytes and h(payload)==a.sha256,'EXACT_FETCH_BYTES_SHA');save(DEST/'transfer.OPAQUE.jsonl',payload)
  with (DEST/'open.stdout.PUBLIC.json').open('xb') as out,(DEST/'open.stderr.private').open('xb') as err:
   r=subprocess.run(['python3','-I','-B',str(TOOL),'open','--private-key',str(BASE/'r29-load-key-01/load-only-private.pem'),'--transfer-file',str(DEST/'transfer.OPAQUE.jsonl'),'--public-record-sha256',a.public_record_sha256,'--output-dir',str(DEST/'opened-neutral')],stdout=out,stderr=err,timeout=min(60,left()))
  need(r.returncode==0,'OPEN_FAILED_KEEP_PREFIX');receipt=read(DEST/'opened-neutral/receipt.public.json',100000)
  emit({'kind':'OPAQUE_FETCHED_ORIGINAL_OPENED','opaque_bytes':a.bytes,'opaque_sha256':a.sha256,'public_receipt':str(DEST/'opened-neutral/receipt.public.json'),'public_receipt_sha256':h(receipt),'test_agent_opened_dir':str(DEST/'opened-neutral'),'SUT_executed':False})
if __name__=='__main__':
 try:main()
 except Exception as e:emit({'kind':'NEUTRAL_OPAQUE_FAILED_NO_RETRY','error_type':type(e).__name__,'reason':str(e),'prefix_preserved':True});raise SystemExit(1) from None
