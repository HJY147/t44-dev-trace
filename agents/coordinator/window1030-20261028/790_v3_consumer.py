"""Fixed LOAD opaque receiver and unmodified v3 short matrix; resource-only marker is never used."""
from pathlib import Path
import base64,gzip,hashlib,io,json,os,re,subprocess
ROOT=Path('/root/t44-r9/resume-20261028-01')
WORK=ROOT/'pressure-input-p16gen02-01'
TOOLS=ROOT/'tools790-v3-window1030-01'
TRANSFER=ROOT/'transport790-v3-window1030-01'
BINDING='161f0b91c6ebca459cd7393e8ed373c025703ae566616809baf45c2aa8d37959'
MANIFEST='0ef08aab3e14887b703c9a2fa5e5265d60fbbcb4172d1d6deb20b5f746df048a'
MIRROR=Path('/root/t44-r9/resource-mirror-r28p16-02')
MIRROR_BIND='97497b2d935ac0c443c8825caf84af9cf351f89a993948598d4424f6b48cf27d'
def h(b):return hashlib.sha256(b).hexdigest()
def save(p,b):
 f=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(f,'wb') as s:s.write(b);s.flush();os.fsync(s.fileno())
def main():
 if h((TOOLS/'manifest.json').read_bytes())!=MANIFEST:raise SystemExit('frozen v3 tools differ')
 if h((TRANSFER/'790_transfer.py').read_bytes())!='7e2dfb5b4c4fd3766769d4c5f15ac65fa8b61e7286e09ee402ff10fa650816f3':raise SystemExit('transfer differs')
 m=json.loads((WORK/'metadata.PUBLIC.json').read_bytes());p=m['original_public_meta']
 if m['phase_binding_sha256']!=BINDING or m['source_sha']!='a12e9e70b963bacafda3242bb6d82e53ee912ff1' or p['binding_sha256']!=BINDING or p['key_sha256']!='fb8216a01b0e9fb1902bb89753c6156ac6f1fb655abff6fd2159b451a6adf97c':raise SystemExit('new arm or recipient differs')
 if p['files']['control.private.json']['sha256']!='8a3b053f35ff4edd594bed5c2f7ce00c9ecdb43fd36756c2e5c176aee9a25ce0' or p['files']['ca.pem']['sha256']!='ccca697ac0ef2edb9f42ef7fa7d9fee3394528d8373c72d422c01683e285e1ee':raise SystemExit('actual APP control or CA differs')
 if p['files']['session.private.json']['bytes']<1000 or not re.fullmatch('[a-f0-9]{64}',p['files']['session.private.json']['sha256']):raise SystemExit('noncredential material rejected before matrix')
 n=m['part_count']
 if type(n) is not int or not 1<=n<=4:raise SystemExit('bounded complete parts required')
 compressed=b''.join((WORK/('part-'+str(i)+'.OPAQUE')).read_bytes() for i in range(n))
 if len(compressed)!=m['compressed_bytes'] or len(compressed)>47200 or h(compressed)!=m['compressed_sha256']:raise SystemExit('complete ciphertext transport differs')
 with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:raw=stream.read(2_000_001)
 if len(raw)>2_000_000 or len(raw)!=m['raw_bytes'] or h(raw)!=m['raw_sha256']:raise SystemExit('exact restored ciphertext envelope required')
 save(WORK/'transfer.OPAQUE.jsonl',raw)
 subprocess.run(['python3','-B',str(TRANSFER/'790_transfer.py'),'open','--private-key',str(TRANSFER/'key-p16gen02-01/load-only-private.pem'),'--transfer-file',str(WORK/'transfer.OPAQUE.jsonl'),'--public-record-sha256',p['public_record_sha256'],'--output-dir',str(WORK/'actual-session-opened01')],check=True,timeout=60)
 if h((MIRROR/'binding.json').read_bytes())!=MIRROR_BIND:raise SystemExit('prestarted mirror binding differs')
 x=subprocess.run(['python3','-B',str(MIRROR/'controller.py'),'status','--directory',str(MIRROR),'--binding-sha256',MIRROR_BIND],capture_output=True,timeout=15)
 save(WORK/'mirror-before.PUBLIC.json',x.stdout)
 if x.returncode:raise SystemExit('mirror status refused; no matrix')
 v=json.loads(x.stdout)
 if not v['observed_before_pid'] or v['observed_before_pid']!=v['observed_after_pid'] or not v.get('progress',{}).get('raw_bytes_observed'):raise SystemExit('live numeric resource transport unproven')
 argv=['python3','-B',str(TOOLS/'790_load.py'),'--inputs-dir',str(WORK/'actual-session-opened01/inputs'),'--output-dir',str(WORK/'matrix01'),'--control-sha256',p['files']['control.private.json']['sha256'],'--packet-sha256',p['files']['session.private.json']['sha256'],'--manifest-sha256',MANIFEST,'--expected-host','i-bp13uag4r4u9r2hge0mu','--python-image','t44-official-python:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70','--python-image-id','sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1']
 x=subprocess.run(argv,capture_output=True,timeout=300);save(WORK/'matrix.stdout.PUBLIC.jsonl',x.stdout);save(WORK/'matrix.stderr.PRIVATE',x.stderr)
 print(x.stdout.decode(),end='',flush=True)
 if x.returncode:print(json.dumps({'kind':'V3_MATRIX_FAILED_PREFIX_PRESERVED_NO_RETRY','exit_code':x.returncode}));return x.returncode
 print(json.dumps({'kind':'V3_MATRIX_CONTROLLER_COMPLETE_NOT_ACCEPTANCE','source_sha':m['source_sha'],'namespace':'t44-cloud-r28p16gen02-p','noncredential_resource_marker_never_used_as_session':True}),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
