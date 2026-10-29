"""Exact027 provider/save -> published694 pure receipt contract; fake Docker/backend only."""

import hashlib
import json
import subprocess
import sys
import types
import unittest
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
TARGET="027deddfb43ec42b9a9ed40ac6afcbc2b7fd757b"
PROVIDER=HERE.parents[2]/"deployment-preparation-r30"


def source(path):
    return subprocess.check_output(["git","show",TARGET+":"+path])


raw=source("deployment/cloud-reuse/r30-window.py")
assert hashlib.sha256(raw).hexdigest()=="7efee30a2e3ef9552c9e2a5b321cebe4ddbd3eb3d8e652484017fd45e5f8d70f"
window=types.ModuleType("review_receipt03_provider")
window.__file__=str(PROVIDER/"deployment/cloud-reuse/r30-window.py")
exec(compile(raw,TARGET+"/r30-window.py","exec"),window.__dict__)
test_raw=source("tmp/759_deployment_neutral_receipt_r30/test_neutral_receipt.py")
test_text=test_raw.decode()
before="ROOT = Path(__file__).resolve().parents[2]"
assert test_text.count(before)==1
test_text=test_text.replace(before,"ROOT = Path("+repr(str(PROVIDER))+")")
before='W = load(ROOT / "deployment/cloud-reuse/r30-window.py", "r30_receipt_provider")'
assert test_text.count(before)==1
test_text=test_text.replace(before,"W = EXACT_FIXED_PROVIDER")
case=types.ModuleType("review_receipt03_contract")
case.__file__=str(HERE/"receipt03_case.py")
case.EXACT_FIXED_PROVIDER=window
sys.modules[case.__name__]=case
exec(compile(test_text,TARGET+"/test_neutral_receipt.py","exec"),case.__dict__)
suite=unittest.defaultTestLoader.loadTestsFromModule(case)
with (HERE/"receipt03-probe.log").open("w") as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
assert result.wasSuccessful() and result.testsRun==5
record=dict(target=TARGET,provider_sha256=hashlib.sha256(raw).hexdigest(),original_owner_test_sha256=hashlib.sha256(test_raw).hexdigest(),published_adapter_sha256=case.ADAPTER_SHA,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),Docker_backend_are_explicit_seams=True,real_original_provider_JSON_save=True,raw60_observed_preserved=True,old_string_and_changed_raw_receipt_rejected=True,temporary_synthetic_TLS_parser_key_deleted=True,actual_HTTP_or_cloud_or_Docker_or_session_calls=0)
(HERE/"receipt03-probe.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record))
