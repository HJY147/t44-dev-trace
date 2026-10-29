"""Read-only original JSON/Git plus synthetic local derive boundaries; no cloud or keys."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path('/Users/yang/Desktop/nothing/软件开发大作业')
OPS = ROOT / '.agent-worktrees/deployment-final-window/deployment/cloud-reuse'
ART = OPS.parents[1] / 'tmp/753_deployment_final_window/official-artifact'
BACKEND = '1b4f30c72beee10da14e0c56a0358a2c2ae16577'
PREFIX = 'agents/backend/neutral-final-20261029/'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
git = lambda ref, name: subprocess.check_output(['git', 'show', ref+':'+name], cwd=ROOT)

def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

snapshots={name:sha((OPS/name).read_bytes()) for name in ['final-image-bundle.py','final-runtime-profile.py','final-f-operator.py','final-app-backup.py','final-timeplan.py','final-f-project.py']}
bundle=json.loads((ART/'backend-bundle-manifest.json').read_bytes())
source=json.loads((ART/'source-manifest.json').read_bytes())
profile=json.loads((ART/'source-profile.PUBLIC.json').read_bytes())
assert profile['root_approved'] is False and profile['actual_loaded'] is False
assert bundle['tool_git_sha']=='63c781692b66bbf75f5bb5eed3eaf95a6eb82235'
for row in source['files']:
    raw=git(source['source_sha'],row['path'])
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
runtime=json.loads((ART/'actual-runtime-files.json').read_bytes())
assert runtime['files']==source['backend_runtime_files'] and len(runtime['files'])==60
manifest_raw=git(BACKEND,PREFIX+'code-manifest.PUBLIC.json')
assert sha(manifest_raw)=='023063c342854c7b2bea107774007fcd89973a4d0ab85f5841db31a6a8cb2a5e'
manifest=json.loads(manifest_raw)
assert len(manifest['files'])==18

with tempfile.TemporaryDirectory(prefix='751-derive-') as directory:
    base=Path(directory).resolve();code=base/'producer';code.mkdir()
    for name,expected in manifest['files'].items():
        raw=git(BACKEND,PREFIX+name)
        assert sha(raw)==expected and len(raw)==manifest['file_sizes'][name]
        (code/name).write_bytes(raw)
    (code/'code-manifest.PUBLIC.json').write_bytes(manifest_raw)
    guard=load(code/'guard.py','review_final_guard')
    # Pure target identity validation, not an approval or a live LOAD observation.
    identity=dict(profile,load_python_expected_runtime_id='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1',load_python_identity_projection_sha256='ce562c117428face0b421e06b33c361b291cab26d8d3a51d24484dbd0841da2a')
    guard.validate_load_runtime_target(identity)
    try:guard.validate_load_runtime_target(dict(identity,load_python_expected_runtime_id=profile['load_python_config_id']))
    except ValueError:pass
    else:raise AssertionError('config ID must not replace runtime ID')
    # Explicit synthetic approval only exercises local code generation. Original build profile unchanged.
    approved=dict(identity,root_approved=True)
    p=base/'synthetic-source.json';p.write_text(json.dumps(approved))
    gen=base/'gen';gen.mkdir()
    gp={'source_sha':source['source_sha'],'backend_bundle_manifest_sha256':profile['backend_bundle_manifest_sha256'],'derived_budget_sha256':profile['budget_helper_sha256'],'derived_files':{'final-image-bundle.py':{'sha256':snapshots['final-image-bundle.py']}}}
    (gen/'profile.json').write_text(json.dumps(gp))
    derive=load(OPS/'final-runtime-profile.py','review_profile_derive')
    args=SimpleNamespace(source_profile=p,source_profile_sha256=sha(p.read_bytes()),gen_profile=gen,gen_profile_sha256=sha((gen/'profile.json').read_bytes()),source_manifest=ART/'source-manifest.json',output=base/'derived')
    derive.derive(args)
    http=load(args.output/'http-prepare.py','review_derived_http')
    a=http.tools()
    inputs=SimpleNamespace(code_dir=code,code_manifest=code/'code-manifest.PUBLIC.json',code_manifest_sha256=sha(manifest_raw))
    staged=a.producer_files(inputs)
    body=next(n for n in ast.parse((args.output/'http-prepare.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='run').body
    gate=next(n for n in body if isinstance(n,ast.If) and 'EXACT_REVIEWED_FUTURE18_SOURCE_AND_BUNDLE_REQUIRED' in ast.dump(n))
    exec(compile(ast.Module(body=[gate],type_ignores=[]),'<actual derived manifest gate>','exec'),{'manifest':manifest,'SOURCE':source['source_sha'],'code':staged,'a':a,'SOURCE_MANIFEST':profile['source_manifest_sha256'],'BUNDLE':profile['backend_bundle_manifest_sha256']})
    operator=load(OPS/'final-f-operator.py','review_F_operator')
    now=2000000000.0
    stamp=lambda value:operator.datetime.fromtimestamp(value,operator.timezone.utc).isoformat().replace('+00:00','Z')
    results=[]
    for label,started,stop,accepted in [('valid',now-60,now+2000,True),('past1500',now-1600,now+400,False),('pastGreserve',now-1000,now+100,False)]:
        request={'schema':'753-neutral-operator-request-v1','run_id':'r30review01','phase':'f','request_id':'r30review01-001','action':'api_restart','requested_utc':stamp(now),'deadline_utc':stamp(now+60)}
        request_path=base/(label+'.json');request_path.write_text(json.dumps(request))
        expected_name=base/'r30review01-001.request.json';expected_name.write_bytes(request_path.read_bytes())
        plan={'kind':'final-immutable-timeplan-v1','phase':'f','run_id':'r30review01','source_sha':source['source_sha'],'stop_utc':stamp(stop),'absolute_cost_cutoff_utc':stamp(now+10800),'t0_utc':stamp(stop-2100),'cost_stop_utc':stamp(stop+300)}
        plan_path=base/'timeplan.json';plan_path.write_text(json.dumps(plan))
        values=SimpleNamespace(request_file=expected_name,request_sha256=sha(expected_name.read_bytes()),f_started_utc=stamp(started),cost_cutoff_utc=stamp(now+10800),timeplan=plan_path,timeplan_sha256=sha(plan_path.read_bytes()))
        with patch.object(operator.time,'time',return_value=now):
            try:operator.request(values,{'run_id':'r30review01'},{'stop_utc':stamp(stop),'source_sha':source['source_sha']});actual=True
            except ValueError:actual=False
        assert actual==accepted,(label,actual)
        results.append({'case':label,'accepted':actual})
    backup=load(OPS/'final-app-backup.py','review_backup')
    selected=base/'selected';selected.mkdir()
    backup.checked_output(base/'sibling-output',[selected])
    for output in [selected/'nested',base]:
        try:backup.checked_output(output,[selected])
        except ValueError:pass
        else:raise AssertionError('recursive backup selection accepted')

assert {name:sha((OPS/name).read_bytes()) for name in snapshots}==snapshots,'owner changed during exact snapshot'
result={'source':'356f29983c904e949245aedfad464efc1bf7b63d','CI_build_git_sha':bundle['tool_git_sha'],'CI_build_tool_sha':bundle['tool_sha256'],'ops_snapshots':snapshots,'context_Git_bytes_verified':len(source['files']),'CI_runtime_records':len(runtime['files']),'actual_APP_loaded':False,'producer_final':BACKEND,'producer_manifest':sha(manifest_raw),'LOAD_config_distinct_runtime_pure_checks':True,'new18_manifest_actual_derived_gate_pass':True,'F_operator_pure_cases':results,'backup_output_recursion_bounds':True,'synthetic_approval_used_only_in_disposable_local_derive_fixture':True,'cloud_services_HTTP_keys_or_QA_private_read':False}
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
