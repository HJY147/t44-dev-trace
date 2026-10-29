"""Fake client only: exact staged prepare must preserve a partial issuance prefix."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
STAGE = "ffae5d84c37fde181a1e12e871954b1d6af73e94"
spec = importlib.util.spec_from_file_location("review_plan_fixture",HERE/"757_plan_probe.py")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
modules = {}
for name, filename in [("guard","guard.py"),("http_primitives","http_primitives.py"),("review_prepare","prepare_http.py")]:
    module = types.ModuleType(name)
    raw = subprocess.check_output(["git","show",STAGE+":agents/backend/neutral-r30/"+filename])
    exec(compile(raw,STAGE+"/"+filename,"exec"),module.__dict__)
    sys.modules[name] = module
    modules[name] = module
responses=[]


class Fake:
    def __init__(self,*args):pass

    def request(self,path,token=None,body=None):
        assert path == "/auth/login"
        role=body["username"]
        if role == "reviewer":raise RuntimeError("synthetic third login rejected")
        responses.append(role)
        return dict(user=dict(id=1 if role=="manager" else 2),access_token="SYNTHETIC_NOT_A_TOKEN_"+role,expires_at=fixture.stamp(fixture.now+fixture.timedelta(seconds=1500)))

    def close(self):pass


with tempfile.TemporaryDirectory(dir=HERE) as scratch:
    base=Path(scratch); ca=base/"ca";ca.write_bytes(b"ca")
    accounts={role:dict(username=role,password="SYNTHETIC_NOT_A_PASSWORD",user_id=index) for index,role in enumerate(["manager","developer","reviewer"],start=1)}
    service=dict(session=dict(token="SYNTHETIC_NOT_A_SERVICE_TOKEN",user_id=4,expires_at=fixture.stamp(fixture.now+fixture.timedelta(seconds=1500)),project_ids=list(range(1,41)),scopes=["escalation:write"]),attestation=dict())
    output=base/"output"
    try:
        modules["review_prepare"].prepare(fixture.plan,accounts,service,ca,output,clock=lambda:fixture.now,client_type=Fake)
    except RuntimeError as error:
        failure=str(error)
    else:raise AssertionError("expected third fake login failure")
    saved=(output/"sessions.json").exists() or (output/"session-attestations.json").exists()
    assert responses==["manager","developer"] and not saved
    record=dict(stage=STAGE,finding="R30-NEUTRAL-LOGIN-PREFIX-02",priority="P2",completed_fake_logins=2,third_fake_login_rejected=True,partial_session_or_attestation_prefix_saved=saved,actual_session_or_HTTP_calls=0)
    (HERE/"login-prefix-probe.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record))
