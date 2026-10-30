"""Offline synthetic p13/material06/maintenance06 contract probe; no service calls."""
import importlib.util
import hashlib
import json
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'agents/backend/manual11-maintenance/v2'
sys.path.insert(0,str(HERE))
import cohort_maintenance as m
import offline_checks as fixtures
TOOLS=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/manual12-repair-kit/backend')
spec=importlib.util.spec_from_file_location('refresh_core',TOOLS/'refresh_core.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
old,accounts=fixtures.contract_inputs();raw=m.canonical(old)
material={'schema':'manual-material-preparation-v1','root_approved':True,'benchmark_grant_allow':False,'operations':c.OPERATIONS,'source_sha':c.SOURCE,'old_packet_sha256':c.sha(raw),'new_packet_run_id':'r30materialresume06','packet_nonce':'a'*64,'database':'t44_test_owned','namespace':'t44-test-owned'}
assert c.authorization(material,raw)==old
maintenance={'schema':'manual11-cohort-maintenance-authorization-v2','root_approved':True,'benchmark_grant_allow':False,'operations':m.OPS,'operation_id':'r30restoretransition06','source_sha':m.SOURCE,'old_packet_sha256':m.sha(raw),'namespace':'t44-test-owned','database':'t44_test_owned','original_ids_sha256':m.sha(m.canonical(m.inventory(old,accounts)[1])),'require_infrastructure_and_old_controller_guards':True,'require_exclusive_no_benchmark_or_other_writer':True}
assert len(m.authorization(old,raw,maintenance,accounts)[1])==800
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'auth';m.put(p,m.canonical(maintenance))
 try:m.put(p,m.canonical(maintenance))
 except (m.Stop,FileExistsError):pass
 else:raise AssertionError('overwrite accepted')
assert len(set(('r30manualp13',material['new_packet_run_id'],maintenance['operation_id'])))==3
print(json.dumps({'status':'SYNTHETIC_OFFLINE_CONTRACT_PASS','material06_authorization':True,'maintenance06_original800_authorization':True,'exclusive_output_refuses_overwrite':True,'three_ids_distinct':True,'cloud_calls':0,'SUT_calls':0,'real_material_generated':False,'tool_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(TOOLS.glob('*.py'))}},sort_keys=True,indent=2))
