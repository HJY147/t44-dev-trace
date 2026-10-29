"""Actual runner and producer time blocks/argparse; no external execution or fake validator."""
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import types

ROOT = Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees')
SOURCE = ROOT / 'deployment-preparation-r30/deployment/cloud-reuse/r30-http-prepare.py'
EXPECTED = 'c2c322bd0c932928fcd811d49a4c92f2b45188d2f32b2669fab79a27df9e4e2e'
raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
runner = types.ModuleType('review_exact_http_runner')
exec(compile(raw, str(SOURCE), 'exec'), runner.__dict__)
git = lambda path: subprocess.check_output(['git', 'show', 'cb966f2117730d6b60227e85e30b6a8b0e3cc79a:agents/backend/neutral-r30-cas/' + path], cwd=ROOT / 'backend-neutral-r30')
guard = types.ModuleType('review_exact_future_guard')
graw = git('guard.py')
exec(compile(graw, 'exact guard', 'exec'), guard.__dict__)

def segment(tree, function, start, end):
    body = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function).body
    at = lambda name: next(i for i, n in enumerate(body) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
    return body[at(start):at(end)]

rblock = segment(ast.parse(raw), 'checked', 'now', 'inputs')
gbody = next(n for n in ast.parse(graw).body if isinstance(n, ast.FunctionDef) and n.name == 'check_plan').body
gstart = next(i for i,n in enumerate(gbody) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id == 'window' for t in n.targets))
gend = next(i for i,n in enumerate(gbody) if i>gstart and 'ACTUAL_SEED_ANCHOR_REQUIRED' in ast.dump(n))
gblock = gbody[gstart:gend]
t0 = datetime(2026, 11, 1, 12, tzinfo=timezone.utc).timestamp()
stamp = lambda n:datetime.fromtimestamp(t0+n, timezone.utc).isoformat().replace('+00:00','Z')
base = {'window':{'start_utc':stamp(1200),'end_utc':stamp(1980),'stop_utc':stamp(2100)}, 'lifecycle':{'t0_utc':stamp(0),'cost_stop_utc':stamp(2400),'packet_cutoff_utc':stamp(1050)}}
rows=[]
for name,section,key,value in [('valid',None,None,None),('C_equals_G','lifecycle','cost_stop_utc',stamp(2100)),('wrong_G','window','stop_utc',stamp(2160)),('cutoff_not_S_minus150','lifecycle','packet_cutoff_utc',stamp(1060)),('duration779','window','end_utc',stamp(1979)),('E_after_G','window','end_utc',stamp(2101))]:
    plan=copy.deepcopy(base)
    if section:plan[section][key]=value
    outcomes=[]
    for block,is_runner in [(rblock,True),(gblock,False)]:
        env=dict(runner.__dict__) if is_runner else dict(guard.__dict__)
        env.update(plan=plan,binding={'stop_utc':plan['window']['stop_utc']},time=types.SimpleNamespace(time=lambda:t0+600),now=datetime.fromtimestamp(t0+600,timezone.utc))
        try:exec(compile(ast.Module(body=block,type_ignores=[]),'<actual time block>','exec'),env);accepted=True
        except ValueError:accepted=False
        outcomes.append(accepted)
    assert outcomes == ([True,True] if name=='valid' else [False,False]), (name,outcomes)
    rows.append({'case':name,'runner':outcomes[0],'producer_guard':outcomes[1]})

tree=ast.parse(git('prepare_http.py'));main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');prefix=[]
for n in main.body:
    if 'parse_args' in ast.dump(n):break
    prefix.append(n)
env={'argparse':argparse,'Path':Path,'__doc__':'exact parser'};exec(compile(ast.Module(body=prefix,type_ignores=[]),'<exact parser>','exec'),env)
args=types.SimpleNamespace(output_dir=Path('/SYNTHETIC/new'))
argv=runner.argv(args,{'project':'t44-cloud-r30future02-p'},'t44-cloud-r30future02-p_edge','synthetic')
env['parser'].parse_args(argv[argv.index('/neutral-code/prepare_http.py')+1:])
for option,value in [('--user','10001:10001'),('--cpus','2'),('--memory','1g'),('--pids-limit','128')]:assert argv[argv.index(option)+1]==value
assert '--env' not in argv and '--env-file' not in argv and '-I' not in argv
receipt={'source_sha256':EXPECTED,'time_cases':rows,'actual_producer_argparse_pass':True,'fixed_resources_and_UID':True,'external_or_HTTP_execution':False,'full_check_plan_or_Docker_not_claimed':True}
Path(__file__).with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
