set -eu
python3 -B - <<'F_START'
from pathlib import Path
import subprocess,hashlib,json
p=Path('/root/t44-r9/resume-20261028-02/resume-profile/generation.py')
if hashlib.sha256(p.read_bytes()).hexdigest()!='4672a5838879ab1fde599c45d464906600373fdb38da654e21879881204d11a8':raise SystemExit('new frozen profile differs')
phase='/root/t44-r9/campaign-r28functional-01/f';b='be1975a7625eae32bf8aaae7e1f2de7d7aef8b20968aa5552320b22202258a9f'
for action in ('arm','config','infra','migrate','idle'):
 a=['python3','-B',str(p),action,'--phase-dir',phase,'--binding-sha256',b]
 if action=='migrate':a+=['--database','t44c_r28funcgen01_f']
 print(json.dumps({'kind':'ROOT_NEW_F_ACTION_BEGIN','action':action,'business_seed':False,'SUT_test_grant':False}),flush=True)
 x=subprocess.run(a,timeout=340)
 if x.returncode:raise SystemExit(x.returncode)
F_START
