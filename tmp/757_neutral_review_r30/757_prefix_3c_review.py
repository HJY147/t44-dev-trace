"""Exact3c third-login fake failure preserves the first two original response prefixes."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
TARGET="3c1967b34c2f724682b47920145497e4df4abcdc"
spec=importlib.util.spec_from_file_location("review_prefix_plan",HERE/"757_plan_probe.py")
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
modules={}
for name in ["guard","http_primitives","prepare_http"]:
    raw=subprocess.check_output(["git","show",TARGET+":agents/backend/neutral-r30/"+name+".py"])
    module=types.ModuleType(name);module.__file__=str(HERE/(name+".py"));sys.modules[name]=module
    exec(compile(raw,TARGET+"/"+name+".py","exec"),module.__dict__);modules[name]=module
plan=fixture.plan;plan["source"]["actual_loaded_full_chain_reviewed_by_root"]=True
receipt=dict(kind="r30-backend-import-receipt-v1",source_sha=modules["guard"].SOURCE,bundle_manifest_sha256=modules["guard"].BUNDLE_MANIFEST,source_manifest_sha256=modules["guard"].SOURCE_MANIFEST,full_runtime_files=60,identity={"config_id":plan["images"]["backend"]},package_resolution={"fixture":"synthetic-not-a-loaded-proof"},business_services_started=False,volumes_modified=False)
raw=json.dumps(receipt).encode();plan["source"]["actual_loaded_receipt_sha256"]=hashlib.sha256(raw).hexdigest()
calls=[]


class Fake:
    def __init__(self,*args):self.last_meta={"server_time":fixture.stamp(fixture.now)}
    def close(self):pass
    def request(self,path,token=None,body=None):
        assert path=="/auth/login"
        role=body["username"];calls.append(role)
        if role=="reviewer":raise RuntimeError("synthetic third login fails")
        return dict(user={"id":1 if role=="manager" else 2},access_token="SYNTHETIC_NOT_A_TOKEN_"+role,expires_at=fixture.stamp(fixture.now+fixture.timedelta(seconds=1500)))


with tempfile.TemporaryDirectory(dir=HERE) as scratch:
    base=Path(scratch);ca=base/"ca";ca.write_bytes(b"ca");out=base/"out"
    accounts={role:dict(username=role,password="synthetic-only",user_id=index) for index,role in enumerate(["manager","developer","reviewer"],1)}
    try:modules["prepare_http"].prepare(plan,accounts,{"session":{},"attestation":{}},ca,out,clock=lambda:fixture.now,client_type=Fake,import_receipt_raw=raw)
    except RuntimeError as error:assert str(error)=="synthetic third login fails"
    else:raise AssertionError("Expected fake failure")
    for role in ["manager","developer"]:
        path=out/"session-prefix"/(role+".json");value=json.loads(path.read_text())
        assert path.stat().st_mode&0o777==0o600
        assert value["original_login_data"]["access_token"]=="SYNTHETIC_NOT_A_TOKEN_"+role
        assert modules["guard"].timestamp(value["login_request_started_at"])==modules["guard"].timestamp(value["response_observed_at"])==fixture.now
        assert value["response_meta"]["server_time"]==fixture.stamp(fixture.now)
    record=dict(target=TARGET,fake_login_order=calls,first_two_original_prefixes_saved=True,mode600=True,request_and_response_observations_not_claimed_as_server_issuance=True,actual_session_or_HTTP_or_service_calls=0,synthetic_import_receipt_not_a_target_proof=True)
    (HERE/"prefix-3c-review.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record))
