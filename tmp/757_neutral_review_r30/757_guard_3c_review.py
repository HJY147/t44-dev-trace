"""Exact3c pure imports/guard regressions and actual GEN naming contrast; no execution entry."""

import copy
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
TARGET="3c1967b34c2f724682b47920145497e4df4abcdc"
spec=importlib.util.spec_from_file_location("review_old_plan_fixture",HERE/"757_plan_probe.py")
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
modules={}
for name in ["guard","http_primitives","admin_seed","admin","prepare_http","make_evidence","assemble"]:
    raw=subprocess.check_output(["git","show",TARGET+":agents/backend/neutral-r30/"+name+".py"])
    module=types.ModuleType(name);module.__file__=str(HERE/(name+".py"));sys.modules[name]=module
    exec(compile(raw,TARGET+"/"+name+".py","exec"),module.__dict__);modules[name]=module
plan=copy.deepcopy(fixture.plan)
plan["source"]["actual_loaded_full_chain_reviewed_by_root"]=True
results=[]
for scenario in ["baseline","wrong-sut","wrong-load","wrong-IP","window901","actual-GEN-project","actual-GEN-run"]:
    value=copy.deepcopy(plan)
    if scenario=="wrong-sut":value["images"]["backend"]="sha256:"+fixture.digest("wrong-backend")
    if scenario=="wrong-load":value["images"]["load_python"]="sha256:"+fixture.digest("wrong-load")
    if scenario=="wrong-IP":value["target"]["origin"]="https://different.example:26445"
    if scenario=="window901":value["window"]["end_utc"]=fixture.stamp(fixture.now+fixture.timedelta(seconds=1201));value["window"]["stop_utc"]=fixture.stamp(fixture.now+fixture.timedelta(seconds=1320))
    if scenario=="actual-GEN-project":value["namespace"]=value["target"]["compose_project"]="t44-cloud-r30window01-p"
    if scenario=="actual-GEN-run":value["run_id"]="r30window01"
    try:modules["guard"].check_plan(value,fixture.now,require_fixture_ready=False);outcome="ACCEPTED"
    except (ValueError,KeyError,TypeError) as error:outcome="REFUSED:"+str(error)
    results.append(dict(scenario=scenario,result=outcome))
assert results[0]["result"]=="ACCEPTED" and all(x["result"].startswith("REFUSED:") for x in results[1:])
record=dict(target=TARGET,real_pure_module_compile_imports=list(modules),results=results,
            original_target_IP_window_guard_defects_closed=True,GEN_binding_mapping_still_blocked=True,
            owner_26_tests_not_rerun=True,HTTP_or_services_or_session_calls=0)
(HERE/"guard-3c-review.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record))
