import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = 'e45a2b980c6ba8c61761f897414d54a10000409d'
CLOC = ROOT.parent/'.runtime/cloc-2.10.pl'
assert hashlib.sha256(CLOC.read_bytes()).hexdigest() == 'bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83'
files = sorted([*ROOT.glob('backend/t44/domain/**/*.py'), *ROOT.glob('backend/t44/services/**/*.py'),ROOT/'backend/t44/api.py',ROOT/'backend/t44/contracts/__init__.py'])
counts={}
for phase in ('before','after'):
 listing=HERE/(phase+'.list')
 targets=[]
 for file in files:
  path=file.relative_to(ROOT)
  if phase=='before':
   target=HERE/'baseline'/path
   target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT))
  else:
   target=file
  targets.append(target)
 listing.write_text('\n'.join(map(str,targets))+'\n')
 output=HERE/(phase+'-cloc.json')
 subprocess.run(['/usr/bin/perl',str(CLOC),'--quiet','--json','--by-file','--list-file='+str(listing),'--report-file='+str(output)],check=True,capture_output=True)
 counts[phase]=json.loads(output.read_text())['SUM']['code']
print(json.dumps({**counts,'net':counts['before']-counts['after']}))
