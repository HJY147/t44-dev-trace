from pathlib import Path
import copy,hashlib,importlib.util,json,os,stat,tempfile,types
D=Path(__file__).resolve().parents[2]/'agents/deployment/manual-handoff';s=importlib.util.spec_from_file_location('rotate',D/'rotate_scheduler_token.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory()as tmp:
 r=Path(tmp).resolve();m.SECRETS=r/'scheduler-secrets';m.SECRETS.mkdir();target=m.SECRETS/'scheduler-token.json';old=b'SYNTHETIC_OLD_SECRET_NOT_REAL';new=b'SYNTHETIC_NEW_SECRET_NOT_REAL';target.write_bytes(old);target.chmod(0o600);st=target.stat();source=r/'service-cli.original.private.json';source.write_bytes(new);source.chmod(0o600);material=r/'material.PUBLIC.json'
 v={'status':'FRESH_MATERIAL_NOT_BENCHMARK_AUTHORIZATION','material_process_exit_proof':{'process_exit_proven':True},'service_cli_original_sha256':m.sha(new),'service_credential_private_file':str(source)}
 expected=json.loads((D/'P09-existing-containers.PUBLIC.json').read_bytes());row=next(x for x in expected['containers']if x['role']=='scheduler');actual={k:row[k]for k in ['id','image_id','project','role','user']};actual['mounts']=[{'Destination':'/run/t44-secrets','Type':'bind','RW':False,'Source':str(m.SECRETS)}]
 calls=[]
 def run(argv,**kwargs):calls.append(argv);assert argv[:5]==['docker','--context','default','inspect','--format'];return types.SimpleNamespace(returncode=0,stdout=json.dumps(actual).encode())
 m.subprocess.run=run;origuid=m.os.geteuid;origchown=m.os.chown;origfchown=m.os.fchown;chowns=[];m.os.geteuid=lambda:0;m.os.chown=lambda p,u,g:chowns.append((str(p),u,g));m.os.fchown=lambda fd,u,g:chowns.append(('fd',u,g))
 try:
  for case in ['failed_exit','wrong_sha','wrong_owner','single_file_bind']:
   bad=copy.deepcopy(v);original_actual=copy.deepcopy(actual)
   if case=='failed_exit':bad['material_process_exit_proof']['process_exit_proven']=False
   if case=='wrong_sha':bad['service_cli_original_sha256']='0'*64
   if case=='wrong_owner':actual['project']='other-project'
   if case=='single_file_bind':actual['mounts'][0]['Destination']='/run/t44-secrets/scheduler-token.json'
   material.write_text(json.dumps(bad))
   try:m.rotate(material,r/('backup-'+case));raise AssertionError('bad rotation accepted:'+case)
   except ValueError:pass
   assert target.read_bytes()==old and not(r/('backup-'+case)).exists();actual.clear();actual.update(original_actual)
  material.write_text(json.dumps(v));receipt=m.rotate(material,r/'backup-success');assert target.read_bytes()==new and(r/'backup-success/scheduler-token.original.private.json').read_bytes()==old
  assert stat.S_IMODE(target.stat().st_mode)==0o600 and (target.stat().st_uid,target.stat().st_gid)==(st.st_uid,st.st_gid)
  assert any(x[1:]==(st.st_uid,st.st_gid)for x in chowns)and any(x[1:]==(0,0)for x in chowns);assert new.decode()not in json.dumps(receipt)and old.decode()not in json.dumps(receipt)
  assert not receipt['scanner_HTTP_success_proven']and not receipt['container_restarted'];assert not list(m.SECRETS.glob('.scheduler-token.rotate-*'))
 finally:m.os.geteuid=origuid;m.os.chown=origchown;m.os.fchown=origfchown
print(json.dumps({'status':'LOCAL_ATOMIC_FILESYSTEM_LOOP_AND_DOCKER_UID_SPIES_PASSED','normal':'exact new bytes/readback0600/old bytes backup/preserve UIDGID/temporary removed','negative_cases':['exit proof false','original CLI SHA mismatch','wrong scheduler owner','single-file bind'],'actual_ownership_root_calls':'spied on macOS; file writes/fsync/replace/readback real in temp','cloud_Docker_credentials_or_HTTP_used':False,'scanner_success_claimed':False},sort_keys=True))
