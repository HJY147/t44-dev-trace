"""Count only committed application source and locate literal AST duplication."""
import ast
import hashlib
import io
import json
import subprocess
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/resume-coordination-20261029')
OUT = Path(__file__).resolve().parent
CLOC = ROOT.parent / '.runtime/cloc-2.10.pl'
assert hashlib.sha256(CLOC.read_bytes()).hexdigest() == 'bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', head, '--',
    'backend/t44', 'frontend/src', 'frontend/index.html'], cwd=ROOT).decode().splitlines()
names = [n for n in names if Path(n).suffix in {'.py', '.ts', '.vue', '.css', '.html'}]
archive = subprocess.check_output(['git', 'archive', '--format=tar', head, '--', *names], cwd=ROOT)
snapshot = OUT / 'application-snapshot'
snapshot.mkdir()
with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
    stream.extractall(snapshot, filter='data')
listing = OUT / 'application.list'
listing.write_text('\n'.join(str(snapshot / n) for n in names)+'\n')
subprocess.run(['perl', str(CLOC), '--quiet', '--json', '--by-file', '--list-file='+str(listing),
    '--report-file='+str(OUT / 'cloc.PUBLIC.json')], check=True)
cloc = json.loads((OUT / 'cloc.PUBLIC.json').read_bytes())
files = {str(Path(k).relative_to(snapshot)):v['code'] for k,v in cloc.items() if k not in {'header','SUM'}}
groups = Counter()
for name, lines in files.items():
    p = Path(name)
    group = 'frontend' if p.parts[0] == 'frontend' else '/'.join(p.parts[:3])
    groups[group] += lines
blocks = defaultdict(list)
for name in names:
    if not name.endswith('.py'):
        continue
    tree = ast.parse((snapshot/name).read_bytes())
    for owner in ast.walk(tree):
        for _, value in ast.iter_fields(owner):
            if not isinstance(value,list) or not value or not all(isinstance(n,ast.stmt) for n in value):
                continue
            for index in range(len(value)):
                for width in range(1,min(5,len(value)-index)+1):
                    section=value[index:index+width]
                    # A literal duplicate is only a locator; not automatically removable.
                    if section[-1].end_lineno-section[0].lineno+1 >= 4:
                        key='|'.join(ast.dump(n,include_attributes=False) for n in section)
                        blocks[key].append({'file':name,'line':section[0].lineno,
                            'end':section[-1].end_lineno,'statements':width})
duplicates = [rows for rows in blocks.values() if len(rows)>1]
result={'head':head,'application_code':cloc['SUM']['code'],'files':len(files),'upper':5100,
 'over':cloc['SUM']['code']-5100,'by_group':dict(groups),'largest_files':sorted(files.items(),key=lambda p:p[1],reverse=True)[:18],
 'exact_AST_duplicate_blocks_spanning_4_or_more_physical_lines':duplicates,
 'source_diff_from_f7':subprocess.check_output(['git','diff','--name-only','f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f',head,'--','backend/t44','frontend/src','frontend/index.html'],cwd=ROOT).decode().splitlines(),
 'source_changed':False,'tests_or_private_or_cloud_read':False}
(OUT/'773_scale_summary.PUBLIC.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
