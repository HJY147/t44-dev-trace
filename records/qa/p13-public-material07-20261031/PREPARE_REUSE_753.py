#!/usr/bin/env python3
"""Public local identity binder and original zero-request prepare launcher. No HTTP."""
import argparse, hashlib, json, os, shutil, subprocess
from pathlib import Path
IMAGE='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1'
ADAPTER='a4cbb793ac6ecb292ad6d4c6451052b051a1ea50fbf798ccad4463b92173fc1c'
ENTRY='d15874c477fef0d92bc68ab77802a5354d15be237c853621b56467005c20d43e'
def need(x,m):
 if not x: raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_identity(identity, run):
 t=identity/'TARGET_PROFILE_753.json'; a=identity/'APPROVAL_753.json'; v=json.loads(t.read_bytes()); q=json.loads(a.read_bytes())
 need(v['run_id']==run and v['phase']=='p','NEW_RUN_PROFILE')
 need(q['approved'] is True and q['target_profile_sha256']==sha(t) and q['qa_adapter_sha256']==ADAPTER,'INDEPENDENT_IDENTITY_BINDING')
 need('IDENTITY_ONLY_FOR_ZERO_SUT_PREPARE' in q['scope'],'IDENTITY_SCOPE')
 need(q['supports_source']==v['git_commit'],'SOURCE_BINDING')
 for x in (v,q):
  for k in ['functional_authorized','benchmark_authorized','grant_allow']:need(x.get(k) is False,'NO_EXECUTE_PERMISSION')
 need(q.get('manual_start_protocol')=='753-ready-manual-once-v1','MANUAL_PROTOCOL')
 return v,q

def main():
 os.umask(0o077); p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);p.add_argument('--identity-dir',required=True);p.add_argument('--packet-opened',required=True);p.add_argument('--check-only',action='store_true');a=p.parse_args()
 w=Path(a.workspace); identity=Path(a.identity_dir); packet=Path(a.packet_opened);run='r30manualp13'
 need(all(x.is_absolute() for x in [w,identity,packet]),'ABSOLUTE_PATHS');check_identity(identity,run)
 need(sha(w/'public/ADAPTER_MANUAL_753.py')==ADAPTER and sha(w/'public/ENTRY_MANUAL_753.sh')==ENTRY,'ORIGINAL_PUBLIC_BYTES')
 for x in [w/'runs'/run,w/'results'/run,w/'results'/(run+'.phase.json'),w/'identity-history'/(run+'-before-bind')]:need(not x.exists(),'FRESH_OUTPUT_REQUIRED:'+str(x))
 if a.check_only:print(json.dumps({'status':'OFFLINE_PUBLIC_BINDINGS_VALID_ONLY','run_id':run,'execute_authorized':False}));return
 # Only the fixed original container reads installed tool bytes; stdout exposes no tool content.
 code="import hashlib,json,pathlib; w=pathlib.Path('/private');m=json.loads((w/'public/tool-manifest.json').read_bytes());assert all(hashlib.sha256((w/'private_tools'/n).read_bytes()).hexdigest()==h for n,h in m['files'].items());print('INSTALLED_FIXED_TOOL_HASHES_MATCH')"
 need(sha(w/'public/tool-manifest.json')=='78a0aca6e90b61695338a332f7adb1becb5f7eebd13d0c8bd28d3f6ff4f09a05','FROZEN_MANIFEST')
 subprocess.run(['docker','run','--rm','--pull=never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--mount',f'type=bind,src={w},dst=/private,readonly','--entrypoint','python3',IMAGE,'-c',code],check=True)
 history=w/'identity-history'/(run+'-before-bind');history.mkdir(parents=True,mode=0o700)
 for name in ['TARGET_PROFILE_753.json','APPROVAL_753.json']:
  shutil.copyfile(w/'public'/name,history/name)
  with (history/(name+'.new')).open('xb') as f:f.write((identity/name).read_bytes())
  os.replace(history/(name+'.new'),w/'public'/name)
 subprocess.run(['sh',str(w/'public/ENTRY_MANUAL_753.sh'),'prepare',str(w),run,str(packet)],check=True)
if __name__=='__main__':main()
