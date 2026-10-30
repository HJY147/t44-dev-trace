#!/usr/bin/env python3
"""Neutral bytes only; never signs or runs SUT."""
import argparse,datetime,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('evidence_dir');p.add_argument('inputs_dir');a=p.parse_args();m=json.loads(Path(a.manifest).read_bytes())
assert (m['schema'],m['qa_run'],m['material_id'],m['maintenance_id'])==('t44-schema-supplement-current-neutral-v1','r30manualp13','r30materialresume07','r30restoretransition07')
assert m['not_original_tool_builtin_schema_verification'] is True
for k in ['current_schema_fingerprint_sha256','current_index_layout_sha256','transport_receipt_sha256','runtime_material_public_sha256']:assert isinstance(m[k],str) and re.fullmatch('[0-9a-f]{64}',m[k])
assert isinstance(m['runtime_source'],str) and re.fullmatch('[0-9a-f]{40}',m['runtime_source'])
assert isinstance(m['database'],str) and m['database']
d=datetime.datetime.fromisoformat(m['current_observed_utc'].replace('Z','+00:00'));assert d.utcoffset()==datetime.timedelta(0) and d<=datetime.datetime.now(datetime.timezone.utc)
assert set(m['five_input_binding'])=={'session.private.json','ca.pem','source-manifest.json','backend-bundle-manifest.json','backend-import-receipt.json'}
for group,base in [('files',a.evidence_dir),('five_input_binding',a.inputs_dir)]:
 assert m[group]
 for n,v in m[group].items():
  assert Path(n).name==n and n not in ('.','..')
  f=Path(base)/n;assert f.is_file() and f.stat().st_size==v['bytes'];assert hashlib.sha256(f.read_bytes()).hexdigest()==v['sha256']
print(json.dumps({'status':'NEUTRAL_BYTES_MATCH_ONLY','identity_approved':False,'grant_allow':False,'current_facts_or_semantic_approval':False}))
