"""Design-only static check. Never imports or executes the workload driver or application."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parent
results = {'kind': 'design-only static validation', 'sut_bound': False, 'network_or_database_workload': False,
           'application_imported_or_read': False, 'checks': [], 'failures': []}
for path in sorted(ROOT.glob('*.py')):
    try:
        node = ast.parse(path.read_text(), filename=str(path))
        compile(node, str(path), 'exec')  # Compile only; never execute this object.
        imports = [n.module for n in ast.walk(node) if isinstance(n, ast.ImportFrom)]
        imports += [a.name for n in ast.walk(node) if isinstance(n, ast.Import) for a in n.names]
        assert not any(name and (name=='t44' or name.startswith(('t44.','backend.','frontend.'))) for name in imports)
        results['checks'].append({'file': path.name, 'ast_compile': True, 'application_import_absent': True})
    except Exception as error:
        results['failures'].append({'file': path.name, 'error_type': type(error).__name__})
p = json.loads((ROOT/'inputs/openapi.json').read_text())
assert hashlib.sha256((ROOT/'inputs/openapi.json').read_bytes()).hexdigest() == 'a77a5cd635b8f6a9927b60f9befac017055442504e34a95b40eddda809e2782f'
assert p['info']['version']=='1.1.0'
assert len(p['paths'])==31
results['checks'].append({'frozen_contract_sha256': True, 'version_1_1_0': True, 'path_count_31': True})
# Fixture count algebra uses only this independently frozen plan, not application execution.
rolled = sum(q < 12 or (project < 20 and q==12) for project in range(40) for q in range(75))
reviews = (3000-rolled)*4+rolled*3
decisions = 3000+rolled
assert (rolled,reviews,decisions,reviews+decisions,40*75*3,40*150)==(500,11500,3500,15000,9000,6000)
assert all(q not in (20,21,22) for project in range(40) for q in range(75)
           if q < 12 or (project < 20 and q==12))
results['checks'].append({'fixture_algebra': True, 'dependency_predecessors_never_rolled': True})
# Offline contract examples validate input vocabulary only. No HTTP client/Driver import is used.
if importlib.util.find_spec('jsonschema'):
    from jsonschema import Draft202012Validator, FormatChecker
    schema = {'$ref': '#/components/schemas/TaskCreate', 'components': p['components']}
    Draft202012Validator.check_schema(schema)
    evidence=[{'kind':2,'locator':'synthetic/performance-v4/fixture','description':'Synthetic fixture only'}]
    plan={'planned_start':'2026-10-20T00:00:00Z','planned_end':'2026-10-21T00:00:00Z',
          'estimated_hours':8.25,'buffer_hours':2.0,'delay_contingency':'Synthetic contingency'}
    examples={
      'TaskCreate':{'title':'Synthetic task 0000','description':'Synthetic fixture','iteration_id':1,'owner_id':2,'plan':plan,'dependency_task_ids':[3,4,5]},
      'BlockTransition':{'expected_version':2,'action':2,'reason':'Synthetic blocker','responsibility_stage':2,'evidence':evidence},
      'UnblockTransition':{'expected_version':3,'action':3,'basis':'Synthetic clear','evidence':evidence},
      'TaskPlanChange':{'expected_version':3,'plan':plan,'reason':'Synthetic new schedule','evidence':evidence},
      'EscalationRequest':{'expected_version':4,'schedule_version':2,'rule_version':1,'scan_run_id':'00000000-0000-4000-8000-000000000001'}
    }
    for name,body in examples.items():
        Draft202012Validator({'$ref':'#/components/schemas/'+name,'components':p['components']},format_checker=FormatChecker()).validate(body)
    results['checks'].append({'offline_frozen_schema_examples': list(examples), 'meaning':'input vocabulary only, not product behavior'})
else:
    results['checks'].append({'offline_frozen_schema_examples':'not run: local jsonschema unavailable; no dependency installed'})
result=subprocess.run(['openssl','x509','-in',str(ROOT/'recipient.pem'),'-noout','-checkend','3600'],capture_output=True,text=True)
assert result.returncode==0
results['checks'].append({'recipient_valid_at_least_one_hour': True})
results['passed']=not results['failures']
(ROOT/'records/offline-check.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'design_static_check_passed':results['passed'],'application_or_sut_executed':False,'failures':len(results['failures'])}))
raise SystemExit(0 if results['passed'] else 1)
