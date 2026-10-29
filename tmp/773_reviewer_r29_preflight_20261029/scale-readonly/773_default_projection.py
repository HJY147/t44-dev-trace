"""Unapplied size-only projection of the remaining frozen-DDL default duplication."""
import ast
import difflib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
source = HERE / 'application-snapshot/backend/t44/scheduling/facade.py'
raw = source.read_text()
remove = {'scan_runs': {'last_task_id','scanned_count','created_count','duplicate_count','finished_at','error_code'},
          'outbox_events': {'schema_version','status','attempts','lease_token','lease_until','confirmed_at','fallback_at','last_error_code'}}
lines=set()
fields=[]
for node in ast.walk(ast.parse(raw)):
    if not (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
            and node.func.attr=='insert' and len(node.args)==2
            and isinstance(node.args[0],ast.Constant) and node.args[0].value in remove):
        continue
    table=node.args[0].value
    values=node.args[1]
    assert isinstance(values,ast.Call) and isinstance(values.func,ast.Name) and values.func.id=='dict'
    for kw in values.keywords:
        if kw.arg in remove[table]:
            fields.append([table,kw.arg,kw.lineno,kw.end_lineno])
            lines.update(range(kw.lineno,kw.end_lineno+1))
assert len(fields)==len(lines)==14
projected=''.join(line for number,line in enumerate(raw.splitlines(keepends=True),1) if number not in lines)
ast.parse(projected)
candidate=HERE/'facade-projection.py'
candidate.write_text(projected)
subprocess.run(['perl',str(Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/cloc-2.10.pl')),
    '--quiet','--json','--by-file','--skip-uniqueness',str(source),str(candidate),
    '--report-file='+str(HERE/'projection-cloc.PUBLIC.json')],check=True)
count=json.loads((HERE/'projection-cloc.PUBLIC.json').read_bytes())
before=count[str(source)]['code']; after=count[str(candidate)]['code']
assert before-after==14
(HERE/'773_unapplied_default_projection.patch').write_text(''.join(difflib.unified_diff(
    raw.splitlines(keepends=True),projected.splitlines(keepends=True),
    fromfile='a/backend/t44/scheduling/facade.py',tofile='b/backend/t44/scheduling/facade.py')))
result={'applied_to_product':False,'behavior_tested':False,'syntax_only':True,'fields':fields,
    'before':before,'after':after,'physical_cloc_reduction':before-after,
    'whole_application_projection':5898-before+after,'remaining_over_5100':5898-before+after-5100,
    'risk':'Requires owner confirmation, actual MySQL full-row equivalence and fault/concurrency regressions; size-only projection is not safe product acceptance.'}
(HERE/'773_projection_summary.PUBLIC.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
