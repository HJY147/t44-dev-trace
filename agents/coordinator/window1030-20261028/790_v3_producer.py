"""Fixed APP S2 and opaque-only export for r28p16gen02; no performance verdict."""
from pathlib import Path
import base64,datetime,gzip,hashlib,json,os,subprocess,sys
ROOT=Path('/root/t44-r9/resume-20261028-02')
PHASE=Path('/root/t44-r9/campaign-r28p16-02/p')
TOOLS=Path('/root/t44-r9/resume-20261028-01/tools790-v3-window1030-01')
TRANSFER=Path('/root/t44-r9/resume-20261028-01/transport790-v3-window1030-01')
BINDING='161f0b91c6ebca459cd7393e8ed373c025703ae566616809baf45c2aa8d37959'
MANIFEST='0ef08aab3e14887b703c9a2fa5e5265d60fbbcb4172d1d6deb20b5f746df048a'
KEY='fb8216a01b0e9fb1902bb89753c6156ac6f1fb655abff6fd2159b451a6adf97c'
RUN=ROOT/'pressure-export-p16gen02-01'
def h(b):return hashlib.sha256(b).hexdigest()
def save(p,b):
 f=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(f,'wb') as s:s.write(b);s.flush();os.fsync(s.fileno())
def main():
 if h((TOOLS/'manifest.json').read_bytes())!=MANIFEST or h((PHASE/'binding.json').read_bytes())!=BINDING:raise SystemExit('frozen manifest or phase differs')
 if h((TRANSFER/'790_transfer.py').read_bytes())!='7e2dfb5b4c4fd3766769d4c5f15ac65fa8b61e7286e09ee402ff10fa650816f3':raise SystemExit('transfer helper differs')
 if h((TRANSFER/'load-public-p16gen02-01.pem').read_bytes())!=KEY:raise SystemExit('recipient differs')
 RUN.mkdir(mode=0o700)
 argv=['python3','-B',str(TOOLS/'790_host.py'),'edge','--phase-dir',str(PHASE),'--binding-sha256',BINDING,'--fixture-name','fixture790-01','--split-name','split790-v3-01','--manifest-sha256',MANIFEST]
 try:x=subprocess.run(argv,capture_output=True,timeout=340)
 except subprocess.TimeoutExpired as error:
  save(RUN/'stage2.stdout.PUBLIC',error.stdout or b'');save(RUN/'stage2.stderr.PRIVATE',error.stderr or b'')
  name='t44-cloud-r28p16gen02-p-790s2'
  info=json.loads(subprocess.check_output(['docker','--context','default','inspect','--format','{{json .}}',name],timeout=15))
  if info['Image']!='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1' or info['Config']['Labels'].get('io.t44.contrast.owner')!='t44-cloud-r28p16gen02-p':raise SystemExit('timeout owner differs; no signal')
  subprocess.run(['docker','--context','default','stop','--time','15',name],check=True,timeout=30)
  print(json.dumps({'kind':'S2_TIMEOUT_PARTIAL_PRESERVED_NO_RETRY','SUT_pressure_executed':False}));return 1
 save(RUN/'stage2.stdout.PUBLIC',x.stdout);save(RUN/'stage2.stderr.PRIVATE',x.stderr)
 if x.returncode:print(json.dumps({'kind':'S2_FAILED_PARTIAL_PRESERVED_NO_RETRY','exit_code':x.returncode,'SUT_pressure_executed':False}));return x.returncode
 rows=[json.loads(v) for v in x.stdout.decode().splitlines()]
 complete=next(v for v in rows if v.get('kind')=='contrast790-s2-host-complete')
 finished=next(v for v in rows if v.get('kind')=='stage2-complete-not-acceptance')
 if not finished['diagnostic_valid'] or finished['slots']!=441:raise SystemExit('incomplete real stage2')
 argv=['python3','-B',str(TRANSFER/'790_transfer.py'),'seal','--public-key-file',str(TRANSFER/'load-public-p16gen02-01.pem'),'--public-key-sha256',KEY,'--binding-sha256',BINDING,'--control',complete['control_path'],'--control-sha256',complete['control_sha256'],'--session',complete['packet_path'],'--packet-sha256',complete['packet_sha256'],'--ca',complete['ca_path'],'--ca-sha256','ccca697ac0ef2edb9f42ef7fa7d9fee3394528d8373c72d422c01683e285e1ee','--mirror','/root/t44-r9/resource-r28p16-02/private-mirror-handoff.json','--mirror-sha256','2b7e5d8388e0beb25fc5d0d37f2889ecfc9875cfc5af131161c1005f32252c25','--output-dir',str(RUN/'sealed')]
 x=subprocess.run(argv,capture_output=True,timeout=60);save(RUN/'seal.stdout.PUBLIC',x.stdout);save(RUN/'seal.stderr.PRIVATE',x.stderr)
 if x.returncode:raise SystemExit(x.returncode)
 raw=(RUN/'sealed/transfer.public.jsonl').read_bytes();meta=json.loads(raw.splitlines()[0]);compressed=gzip.compress(raw,mtime=0);parts=[compressed[i:i+11800] for i in range(0,len(compressed),11800)]
 if len(parts)>4:raise SystemExit('bounded export exceeded; no pressure')
 metadata={'kind':'V3_OPAQUE_TRANSFER_METADATA','source_sha':'a12e9e70b963bacafda3242bb6d82e53ee912ff1','phase_binding_sha256':BINDING,'s2_complete_utc':finished['utc'],'seal_complete_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_public_meta':meta,'compressed_bytes':len(compressed),'compressed_sha256':h(compressed),'raw_bytes':len(raw),'raw_sha256':h(raw),'part_count':len(parts),'SUT_pressure_executed':False}
 save(RUN/'metadata.PUBLIC.json',json.dumps(metadata,separators=(',',':')).encode())
 for i,b in enumerate(parts):save(RUN/('part-'+str(i)+'.OPAQUE.json'),json.dumps({'index':i,'parts':len(parts),'bytes':len(b),'sha256':h(b),'data':base64.b64encode(b).decode()},separators=(',',':')).encode())
 first=json.loads((RUN/'part-0.OPAQUE.json').read_bytes());result={'metadata':metadata,'first_opaque_part':first};out=json.dumps(result,separators=(',',':'))
 if len(out.encode())>20000:out=json.dumps({'metadata':metadata,'first_opaque_part':None},separators=(',',':'))
 save(RUN/'terminal.PUBLIC.json',out.encode());print(out,flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
