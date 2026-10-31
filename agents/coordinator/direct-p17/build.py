"""Build an offline public direct-run kit, without contacting either server."""
import argparse,hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if not a.output.is_absolute() or a.output.exists():raise ValueError('EXCLUSIVE_ABSOLUTE_ARCHIVE_REQUIRED')
 selected={}
 for src,dst in [('agents/backend/fast-bootstrap','backend'),('agents/deployment/direct-start','deployment'),('records/qa/direct-p17.PUBLIC','qa')]:
  base=ROOT/src
  for f in base.iterdir():
   if f.is_file() and not f.is_symlink():selected[dst+'/'+f.name]=f.read_bytes()
 for folder,manifest in [('backend','MANIFEST.PUBLIC.json'),('deployment','MANIFEST.PUBLIC.json'),('qa','DELIVERY_MANIFEST.PUBLIC.json')]:
  for name,v in json.loads(selected[folder+'/'+manifest])['files'].items():
   expected=v if isinstance(v,str)else v['sha256']
   if sha(selected[folder+'/'+name])!=expected:raise ValueError('OWNER_MANIFEST_MISMATCH:'+name)
 for n in ('RUN.PUBLIC.json','PERSISTENCE.PUBLIC.json'):
  selected['deployment/'+n]=(ROOT/'agents/deployment/direct-p17'/n).read_bytes()
 for name in ('launch.py','run.py'):selected['coordinator/'+name]=(Path(__file__).parent/name).read_bytes()
 selected['coordinator/ssh/update_ssh_addresses.py']=(ROOT/'agents/coordinator/manualp15-preparation/ssh/update_ssh_addresses.py').read_bytes()
 old=ROOT/'agents/coordinator/manualp15-preparation/coordinator/manual13-observe.py'
 selected['coordinator/manual13-observe.py']=old.read_bytes()
 common=__import__('subprocess').check_output(['git','rev-parse','--git-common-dir'],cwd=ROOT,text=True).strip();common=Path(common)
 if not common.is_absolute():common=ROOT/common
 mainroot=common.resolve().parent
 cms=mainroot/'.agent-worktrees/.runtime/manual13-ready-20261030/deployment/cms_five_transport.py'
 selected['transport/cms_five_transport.py']=cms.read_bytes()
 if sha(selected['transport/cms_five_transport.py'])!='466fa0b7ce4d00d1cf5ab1209bdaff0ee266279210971cc76145d677af51ab26':raise ValueError('ORIGINAL_TRANSPORT_REQUIRED')
 for n,h in [('source-manifest.json','52d74144437ad77140ccb8cab44bf82c4826e4ba00b9d2dc04895f35100bcfd7'),('backend-bundle-manifest.json','3e09cc1bfe5074832fbb61bc2e500f5b27bc23a987c3d68f9744dd650c126d29')]:
  raw=(mainroot/'.submission-private/build-candidates/global-latency-bcec-20261031'/n).read_bytes()
  if sha(raw)!=h:raise ValueError('ORIGINAL_SOURCE_PROVENANCE_REQUIRED')
  selected['provenance/'+n]=raw
 contract=json.loads(selected['qa/CLI_CONTRACT.PUBLIC.json']);assert contract['run_id']=='r30posttools17' and contract['workspace']=='/root/t44-final-20261101/QA753_POSTTOOLS_V12_P17'
 manifest={'schema':'T44_DIRECT_KIT_V1','source':'bcec3326b40814fdb1922bbfea7c29473b47ba47','run':'r30posttools17','classification':'DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE','actual_cloud_calls':0,'automatic_vm_shutdown':False,'files':{n:{'bytes':len(b),'sha256':sha(b)}for n,b in selected.items()}}
 selected['MANIFEST.PUBLIC.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 import io
 with tarfile.open(a.output,'w:gz')as t:
  for n,b in sorted(selected.items()):
   info=tarfile.TarInfo(n);info.size=len(b);info.mode=0o600;t.addfile(info,io.BytesIO(b))
 with tarfile.open(a.output)as t:
  for m in t.getmembers():
   if not m.isfile()or t.extractfile(m).read()!=selected[m.name]:raise ValueError('ARCHIVE_ROUNDTRIP_MISMATCH')
 print(json.dumps({'archive':str(a.output),'bytes':a.output.stat().st_size,'sha256':sha(a.output.read_bytes()),'payload_files':len(manifest['files'])}))
if __name__=='__main__':main()
