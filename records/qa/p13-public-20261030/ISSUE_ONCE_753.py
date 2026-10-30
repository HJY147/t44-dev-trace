#!/usr/bin/env python3
"""Independent tester only, after current neutral evidence review. Never invoked by preparation."""
import argparse,datetime,hashlib,json,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('default_false');p.add_argument('independent_decision');p.add_argument('output');a=p.parse_args();os.umask(0o077)
b=Path(a.default_false).read_bytes();g=json.loads(b);d=json.loads(Path(a.independent_decision).read_bytes());now=datetime.datetime.now(datetime.timezone.utc)
def utc(s):
 v=datetime.datetime.fromisoformat(s.replace('Z','+00:00'));assert v.utcoffset()==datetime.timedelta(0);return v
assert d['status']=='INDEPENDENT_CURRENT_NEUTRAL_REVIEW_APPROVED_ONCE'
assert d['default_false_sha256']==hashlib.sha256(b).hexdigest()
assert d['run_id']==g['run_id']=='r30manualp13' and d['environment_sha256']==g['environment_sha256']
assert utc(d['reviewed_utc'])<=now<utc(d['latest_trigger_before_utc'])
assert (utc(d['minimum_real_session_expiry'])-datetime.timedelta(seconds=900))>=utc(d['latest_trigger_before_utc'])
assert all(d[k] is True for k in ['current_identity_reviewed','current_app_load_resources_reviewed','current_exclusion_reviewed','real_sessions_scope_reviewed','current_inventory_eligibility_reviewed','original_prepare_receipt_reviewed','new_output_and_unconsumed_reviewed'])
assert g['allow'] is False and (g['clients'],g['warmup_seconds'],g['steady_seconds'])==(400,60,600)
assert g['manual_start_protocol']=='753-ready-manual-once-v1' and g['max_elapsed_seconds']==900
original=dict(g);g['allow']=True;assert {k for k in g if original[k]!=g[k]}=={'allow'}
with Path(a.output).open('xb') as f:f.write(json.dumps(g,separators=(',',':'),sort_keys=True).encode()+b'\n')
print(json.dumps({'run_id':g['run_id'],'only_allow_changed':True,'approved_grant_sha256':hashlib.sha256(Path(a.output).read_bytes()).hexdigest(),'latest_trigger_before_utc':d['latest_trigger_before_utc'],'performance_conclusion':False}))
