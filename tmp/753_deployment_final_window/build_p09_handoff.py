from pathlib import Path
import ast,base64,hashlib,json,re,zlib
D=Path('agents/deployment/final-window')
def pin(b):return hashlib.sha256(b).hexdigest()
def save(n,s):ast.parse(s,feature_version=(3,10));(D/n).write_text(s)
oldpin='7cba1f0cd9925ba92da12849e4789af8378d1fe870698be02be292017796bb02'
splus=(D/'P08-SPLUS1-EXEC.PUBLIC.py').read_text().replace('P08','P09').replace('p08','p09');save('P09-SPLUS1-EXEC.PUBLIC.py',splus);newpin=pin(splus.encode())
for n in ['FACTS-CHECK','USER-COMMANDS','USER-LOAD-FACTS']:
 s=(D/('P08-'+n+'.PUBLIC.py')).read_text().replace('P08','P09').replace('p08','p09').replace(oldpin,newpin)
 if n=='FACTS-CHECK':s=s.replace('active_P07_units','active_P08_units')
 if n=='USER-COMMANDS':
  s=s.replace("helper=T+'/P09-SPLUS1-EXEC.PUBLIC.py';pin=", "helper=T+'/P09-SPLUS1-EXEC.PUBLIC.py';pin=")
  s=s.replace("need(load['public_files'].get(helper,{}).get('sha256')==pin,'SPLUS1_TOOL_NOT_IN_USER_FACTS')", "need(returned.get('splus1_helper',{}).get('path')==helper and returned['splus1_helper'].get('sha256')==pin,'SPLUS1_TOOL_NOT_IN_PREPARE_RECEIPT')")
  needle="'start_utc':clock['start_utc'],'grant_keys':sorted(GRANT_KEYS)"
  s=s.replace(needle,needle+",'splus1':blob((HERE/'P09-SPLUS1-EXEC.PUBLIC.py').read_bytes()),'splus1_path':T+'/P09-SPLUS1-EXEC.PUBLIC.py'")
  s=s.replace("W.mkdir(mode=0o700);(W/'public').mkdir(mode=0o700)","helper=Path(D['splus1_path']);helperraw=original(D['splus1'])\nif helper.exists():assert not helper.is_symlink() and digest(helper)==D['splus1']['sha256'],'EXISTING_SPLUS1_CHANGED'\nelse:put(helper,helperraw)\nW.mkdir(mode=0o700);(W/'public').mkdir(mode=0o700)")
  s=s.replace("'workspace':str(W),'default_false_grant_original'", "'workspace':str(W),'splus1_helper':{'path':D['splus1_path'],'sha256':digest(D['splus1_path'])},'default_false_grant_original'")
  s=s.replace("'launcher_sha256':app['tool_derivation']['tools']['P09-CONTINUOUS-fast10-cap50.PUBLIC.py']", "'launcher_sha256':app['tool_derivation']['tools']['P09-CONTINUOUS-fast10-cap50.PUBLIC.py'],'collector':blob((HERE/'P09-USER-APP-COLLECT.PUBLIC.py').read_bytes()),'collector_path':T+'/P09-USER-APP-COLLECT.PUBLIC.py'")
  s=s.replace("argv=['systemd-run','--unit=t44-final-p09-continuous'", "previous=subprocess.run(['systemctl','show','t44-final-p08-continuous.service','--property=LoadState','--value'],capture_output=True,check=False)\nloadstate=previous.stdout.decode().strip();assert loadstate in {'loaded','not-found'},'PREVIOUS_P08_LOADSTATE_UNKNOWN'\nif loadstate=='loaded':subprocess.run(['systemctl','stop','t44-final-p08-continuous.service'],check=True)\nassert subprocess.run(['systemctl','is-active','--quiet','t44-final-p08-continuous.service']).returncode!=0,'PREVIOUS_P08_LAUNCHER_STILL_ACTIVE'\ncollector=Path(D['collector_path'])\nif collector.exists():assert not collector.is_symlink() and digest(collector)==D['collector']['sha256'],'COLLECTOR_CHANGED'\nelse:put(collector,original(D['collector']))\nargv=['systemd-run','--unit=t44-final-p09-continuous'")
  s=s.replace("raise SystemExit(subprocess.run(argv,check=False).returncode)","assert subprocess.run(argv,check=False).returncode==0,'P09_DISPATCH_FAILED'\nraise SystemExit(subprocess.run(['python3','-B',D['collector_path'],'--wait-seconds','600'],check=False).returncode)")
 if n=='USER-COMMANDS':s=s.replace("'action':a.action,'file':str(a.output)","'action':a.action,'required_cloud_assistant_timeout_seconds':900 if a.action=='freeze' else 300,'file':str(a.output)")
 save('P09-'+n+'.PUBLIC.py',s)
# APP facts preparation reuses reviewed original validation, replacing only derivation seam.
s=(D/'P08-USER-APP-PREPARE-v2.INLINE.PUBLIC.sh').read_text();body=s.split("<<'USER_APP_STAGE'\n",1)[1].rsplit('\nUSER_APP_STAGE',1)[0]
body=re.sub(r"BLOB=base64.b64decode\('[^']+'\);assert hashlib.sha256\(BLOB\).hexdigest\(\)=='[^']+'",'',body)
a=body.index('for name,item in json.loads');b=body.index("record={'kind':",a)
body=body[:a]+"derived=json.loads(run(['python3','-B',str(T/'P09-DERIVE-TOOLS.PUBLIC.py')]))\n"+body[b:]
body=body.replace('P08','P09').replace('p08','p09').replace('active_P07_units','active_P08_units').replace("'t44-final-p07*'","'t44-final-p08*'")
# old P07 pin used only audit validation of existing artifact, not derive dependency.
body=body.replace("assert sha(old)==oldsha and sha(profile)==", "assert sha(profile)==")
body=body.replace("'Use earliest of both current actual resume boots after LOAD facts arrive; never reuse old 2026-10-29T17:29Z'", "'Use earliest current actual boot and newly reviewed platform cutoff; no old campaign fee'")
save('P09-USER-APP-FACTS.PUBLIC.py',body)
# Inline installation of only local public code, byte pins and no lifecycle.
def inline(kind,members,entry):
 payload={n:{'text':v,'sha256':pin(v.encode())}for n,v in members.items()};blob=zlib.compress(json.dumps(payload,separators=(',',':')).encode(),9)
 return "umask 077\npython3 -B - <<'USER_P09_"+kind+"'\nimport base64,hashlib,json,subprocess,zlib\nfrom pathlib import Path\nT=Path('/root/t44-final-20261029/ops01/deployment/cloud-reuse')\nblob=base64.b64decode("+repr(base64.b64encode(blob).decode())+");assert hashlib.sha256(blob).hexdigest()=="+repr(pin(blob))+"\nfor name,item in json.loads(zlib.decompress(blob)).items():\n raw=item['text'].encode();assert hashlib.sha256(raw).hexdigest()==item['sha256'];dest=T/name\n if dest.exists():assert not dest.is_symlink() and hashlib.sha256(dest.read_bytes()).hexdigest()==item['sha256'],'EXISTING_PUBLIC_TOOL_DIFFERS_NO_OVERWRITE'\n else:\n  with dest.open('xb') as out:out.write(raw)\n  dest.chmod(0o600)\nraise SystemExit(subprocess.run(['python3','-B',str(T/"+repr(entry)+")],check=False).returncode)\nUSER_P09_"+kind+"\n"
appmembers={n:(D/n).read_text()for n in ['P09-DERIVE-TOOLS.PUBLIC.py','P09-USER-APP-FACTS.PUBLIC.py','P09-USER-APP-COLLECT.PUBLIC.py']}
# Original generic transport raw bytes from reviewed P08 install payload.
s=(D/'P08-USER-LOAD-FACTS.INLINE.PUBLIC.sh').read_text();blob=base64.b64decode(re.search("blob=base64.b64decode\\('([^']+)'\\)",s).group(1));oldmembers=json.loads(zlib.decompress(blob));transport=oldmembers['P08-USER-TRANSPORT-LOAD.PUBLIC.py']['text'];assert pin(transport.encode())=='d1ed953dc7c0dd9d048dc3318c27015d3f71968499ba7d17dcd1841422d84601'
loadmembers={n:(D/n).read_text()for n in ['P09-USER-LOAD-FACTS.PUBLIC.py','P09-SPLUS1-EXEC.PUBLIC.py']};loadmembers['P09-USER-TRANSPORT-LOAD.PUBLIC.py']=transport
for kind,members,entry in [('APP_FACTS',appmembers,'P09-USER-APP-FACTS.PUBLIC.py'),('LOAD_FACTS',loadmembers,'P09-USER-LOAD-FACTS.PUBLIC.py')]:
 s=inline(kind,members,entry);assert len(s.encode())<=16384;(D/('P09-USER-'+kind+'.INLINE.PUBLIC.sh')).write_text(s)
print(json.dumps({'new_splus1_sha256':newpin,'app_inline_bytes':(D/'P09-USER-APP_FACTS.INLINE.PUBLIC.sh').stat().st_size,'load_inline_bytes':(D/'P09-USER-LOAD_FACTS.INLINE.PUBLIC.sh').stat().st_size}))
