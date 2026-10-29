"""Before first P05 freeze only: derive S10/E23/G25/C30 prep sidecars; measurement unchanged."""
import argparse,ast,hashlib,json,os
from pathlib import Path
R=Path('/root/t44-final-20261029');T=R/'ops01/deployment/cloud-reuse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):
 if isinstance(s,str):s=s.encode()
 if p.suffix=='.py':ast.parse(s,feature_version=(3,10))
 with p.open('xb') as f:f.write(s)
 p.chmod(0o600)
def replace(s,old,new,count=1):
 if s.count(old)!=count:raise ValueError('EXACT_P_FAST_PREIMAGE_REQUIRED:'+old)
 return s.replace(old,new)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--launcher',type=Path,default=T/'P05-CONTINUOUS-profile02.PUBLIC.py');p.add_argument('--launcher-sha256',required=True);a=p.parse_args();os.umask(0o077)
 if (R/'P05').exists() or (R/'r30finalp05-launcher').exists():raise ValueError('FIRST_P05_FREEZE_ONLY_NO_RETIME')
 if sha(a.launcher)!=a.launcher_sha256:raise ValueError('ROOT_PINNED_ORIGINAL_P05_LAUNCHER_REQUIRED')
 text=a.launcher.read_text();tree=ast.parse(text);c=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='C' for x in n.targets))
 if not isinstance(c.value,ast.Call) or c.value.func.id!='Path':raise ValueError('EXACT_DERIVED_C_PATH_REQUIRED')
 producer=Path(ast.literal_eval(c.value.args[0]));manifest=json.loads((producer/'code-manifest.PUBLIC.json').read_bytes());files={}
 if manifest['source_sha']!='90b734f65ce6ee9f5c217e885bc7ea4857e32b48' or len(manifest['files'])!=18:raise ValueError('EXACT90B18_REQUIRED')
 for n,h in manifest['files'].items():
  b=(producer/n).read_bytes()
  if hashlib.sha256(b).hexdigest()!=h or len(b)!=manifest['file_sizes'][n]:raise ValueError('ORIGINAL18_BYTES_CHANGED')
  files[n]=b
 guard=files['guard.py'].decode();guard=replace(guard,'stop == t0 + timedelta(minutes=35)','stop == t0 + timedelta(minutes=25)');guard=replace(guard,'cost == t0 + timedelta(minutes=40)','cost == t0 + timedelta(minutes=30)');files['guard.py']=guard.encode()
 dest=producer.with_name(producer.name+'-pfast10');dest.mkdir(mode=0o700)
 for n,b in files.items():put(dest/n,b)
 newmanifest={**manifest,'files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()},'file_sizes':{n:len(b) for n,b in files.items()},'preparation_window_sidecar':{'S':10,'E':23,'G':25,'C':30,'measurement_seconds':780,'original_manifest_sha256':sha(producer/'code-manifest.PUBLIC.json')}}
 put(dest/'code-manifest.PUBLIC.json',json.dumps(newmanifest,sort_keys=True,indent=2)+'\n');newcodepin=sha(dest/'code-manifest.PUBLIC.json')
 clock=(T/'final-timeplan-resume05.py').read_text()
 clock=replace(clock,'def freeze(args):','def freeze(args):\n    if args.phase != "p":raise ValueError("FRESH_P05_FAST10_ONLY")')
 for old,new in [('now + timedelta(minutes=45) > outer','now + timedelta(minutes=35) > outer'),('stop_utc": text(now + timedelta(minutes=35))','stop_utc": text(now + timedelta(minutes=25))'),('cost_stop_utc": text(now + timedelta(minutes=40))','cost_stop_utc": text(now + timedelta(minutes=30))'),('start_utc=text(now + timedelta(minutes=20))','start_utc=text(now + timedelta(minutes=10))'),('end_utc=text(now + timedelta(minutes=33))','end_utc=text(now + timedelta(minutes=23))'),('minutes=17, seconds=30','minutes=7, seconds=30')]:clock=replace(clock,old,new)
 runtime=(T/'final-runtime-profile.py').read_text();runtime=replace(runtime,'    f_http = http','    http = replace(http, "stop != t0 + 35 * 60", "stop != t0 + 25 * 60")\n    http = replace(http, "cost != t0 + 40 * 60", "cost != t0 + 30 * 60")\n    f_http = http')
 prepare=(T/'final-app-prepare-resume05.py').read_text();prepare=replace(prepare,'final-timeplan-resume05.py','final-timeplan-pfast05.py');prepare=replace(prepare,'final-runtime-profile.py','final-runtime-profile-pfast05.py');prepare=replace(prepare,'self.end = stamp(plan["t0_utc"]) + 17.5 * 60','self.end = stamp(plan["packet_cutoff_utc"])')
 text=replace(text,ast.get_source_segment(text,c.value),'Path('+repr(str(dest))+')');oldpin=sha(producer/'code-manifest.PUBLIC.json');text=replace(text,oldpin,newcodepin);text=replace(text,'final-app-prepare-resume05.py','final-app-prepare-pfast05.py')
 outputs={'final-timeplan-pfast05.py':clock,'final-runtime-profile-pfast05.py':runtime,'final-app-prepare-pfast05.py':prepare,'P05-CONTINUOUS-fast10.PUBLIC.py':text}
 for n,s in outputs.items():put(T/n,s)
 receipt={'status':'FRESH_P05_FAST10_PREPARED_NOT_FROZEN_OR_STARTED','producer':str(dest),'producer_manifest_sha256':newcodepin,'original_launcher_sha256':a.launcher_sha256,'tools':{n:sha(T/n) for n in outputs},'measurement_seconds':780,'clients':400,'minimum_actual_steady_seconds':660,'S_T0_seconds':600,'E_T0_seconds':1380,'G_T0_seconds':1500,'C_T0_seconds':1800,'packet_cutoff_T0_seconds':450,'absolute_cutoff_unchanged':'2026-10-29T19:30:00Z'}
 put(T/'P05-fast10-preparation.PUBLIC.json',json.dumps(receipt,sort_keys=True,indent=2)+'\n');print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
