"""Synthetic plan guards only; no HTTP, services, sessions, or private data."""

import copy
import hashlib
import json
import subprocess
import sys
import types
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parents[2] / "backend-neutral-r30/agents/backend/neutral-r30"
STAGE = "ffae5d84c37fde181a1e12e871954b1d6af73e94"
stage_source = subprocess.check_output(["git","show",STAGE+":agents/backend/neutral-r30/guard.py"])
guard = types.ModuleType("review_neutral_guard")
exec(compile(stage_source,STAGE+"/guard.py","exec"),guard.__dict__)
now = datetime(2026,10,29,9,tzinfo=UTC)
stamp = lambda value: value.isoformat().replace("+00:00","Z")
digest = lambda value: hashlib.sha256(value.encode()).hexdigest()
plan = json.loads(subprocess.check_output(["git","show",STAGE+":agents/backend/neutral-r30/plan.template.PUBLIC.json"]))
plan.update(root_admit_preparation=True,run_id="r30-review01",namespace="t44-r30-review01")
plan["source"].update(actual_loaded_receipt_sha256=digest("loaded"),actual_loaded_receipt_path="/review/loaded.PUBLIC.json",actual_loaded_observed_at=stamp(now-timedelta(seconds=60)))
plan["budget"]["actual_admission_receipt_sha256"] = digest("budget")
plan["target"].update(compose_project=plan["namespace"],database="t44c_r30_review01",mysql_user="t44c_r30_review01_app",binding_sha256=digest("binding"),ca_sha256=digest("ca"),origin="https://10.0.0.1:26445",connect_ip="10.0.0.1")
for role, value in plan["runtime_roles"].items():
    value.update(running_observed=role!="scheduler",receipt_sha256=digest(role))
plan["window"].update(start_utc=stamp(now+timedelta(seconds=300)),end_utc=stamp(now+timedelta(seconds=1080)),stop_utc=stamp(now+timedelta(seconds=1200)))
plan["seed"].update(seed=20261029,anchor_utc=stamp(now-timedelta(days=6)))
plan["readiness"].update(all_ready_at=stamp(now-timedelta(seconds=30)),admin_preserves_image_pythonpath=True,fixture_ready_at=stamp(now-timedelta(seconds=10)))
for key in ("source","images","transfer","preflight"):
    plan["readiness"][key].update(sha256=digest(key),completed_at=stamp(now-timedelta(seconds=40)))
plan["authorized_project_ids"] = list(range(1,41))
plan["allowed_writes"] = ["login","createTask","transitionTask","createEscalation"]
results=[]
for scenario in ["baseline","wrong-sut-config","wrong-load-config","window901s","origin-connect-mismatch"]:
    altered=copy.deepcopy(plan)
    if scenario=="wrong-sut-config":altered["images"]["backend"]="sha256:"+digest("old backend")
    if scenario=="wrong-load-config":altered["images"]["load_python"]="sha256:"+digest("wrong source-bearing runtime")
    if scenario=="window901s":altered["window"]["end_utc"]=stamp(now+timedelta(seconds=1201));altered["window"]["stop_utc"]=stamp(now+timedelta(seconds=1320))
    if scenario=="origin-connect-mismatch":altered["target"]["origin"]="https://different.example:26445"
    try:
        guard.check_plan(altered,now,require_fixture_ready=False)
        result="ACCEPTED"
    except (guard.Refused,KeyError,ValueError) as error:
        result="REFUSED:"+str(error)
    results.append(dict(scenario=scenario,result=result))
assert results[0]["result"]=="ACCEPTED"
record=dict(stage=STAGE,source_sha256=hashlib.sha256(stage_source).hexdigest(),results=results,all_values_synthetic=True,HTTP_or_session_or_service_calls=0)
(HERE/"plan-probe.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record))
