#!/usr/bin/env python3
"""Independent current review only. Default validates without writing any grant."""
import argparse,datetime,hashlib,json,os
from pathlib import Path
RUN='r30manualp15';MATERIAL='r30materialresume09';SOURCE='bcec3326b40814fdb1922bbfea7c29473b47ba47'
CORE='9cf747e308969ceba37e2cfcfa6591def45e118ad928c4f310f57b6ecf37542a'
MANIFEST='fd8c8fb6ec7b655c5e4699774cdc4e1fbac151eb77fe41bf5f74add0d059b882'
ADAPTER='44451456d63d94b612924d215ece822dfce127f4cc67926294f33b643fd14cf3'
REVIEW=['current_identity_reviewed','current_app_load_resources_reviewed','current_exclusion_reviewed','real_sessions_scope_reviewed','current_inventory_eligibility_reviewed','original_prepare_receipt_reviewed','new_output_and_unconsumed_reviewed','current_schema_fixture_and_nonce_reviewed','tool_release_independently_approved']
def need(ok,msg):
 if not ok:raise ValueError(msg)
def utc(s):
 v=datetime.datetime.fromisoformat(s.replace('Z','+00:00'));need(v.utcoffset()==datetime.timedelta(0),'UTC_REQUIRED');return v

def validate(b,d,now=None):
 now=now or datetime.datetime.now(datetime.timezone.utc);g=json.loads(b)
 need(d['status']=='INDEPENDENT_CURRENT_NEUTRAL_REVIEW_APPROVED_ONCE','CURRENT_REVIEW_REQUIRED')
 need(d['default_false_sha256']==hashlib.sha256(b).hexdigest(),'DEFAULT_FALSE_SHA')
 need(d['run_id']==g['run_id']==RUN and g['packet_run_id']==d['material_run_id']==MATERIAL,'FRESH_P15_MATERIAL')
 need(d['environment_sha256']==g['environment_sha256'],'ENVIRONMENT_SHA')
 need(d['source_git_commit']==SOURCE and d['source_manifest_sha256']==g['source_sha256'],'SOURCE13AC')
 need(g['runtime_sha256']==CORE and d['tool_manifest_sha256']==MANIFEST and d['qa_adapter_sha256']==ADAPTER,'V52_TOOL_BINDING')
 need(d['current_actual_app_config_digest']==g['image_digest'],'CURRENT_IMAGE_BINDING')
 need(isinstance(d['nonce'],str) and len(d['nonce'])>=32 and d['neutral_binding_sha256'] and d['current_schema_fingerprint'],'NONCE_SCHEMA_NEUTRAL_BINDING')
 need(utc(d['reviewed_utc'])<=now<utc(d['latest_trigger_before_utc']),'CURRENT_REVIEW_WINDOW')
 need(utc(d['latest_trigger_before_utc'])<=utc(d['minimum_real_session_expiry'])-datetime.timedelta(seconds=900),'SESSION_WINDOW')
 need(all(d[k] is True for k in REVIEW),'ALL_CURRENT_REVIEW_GATES')
 need(g['schema']=='772-grant-v1' and g['allow'] is False,'ORIGINAL_DEFAULT_FALSE_REQUIRED')
 need((g['clients'],g['warmup_seconds'],g['steady_seconds'])==(400,60,600),'ORIGINAL_COHORT')
 need(g['manual_start_protocol']=='753-ready-manual-once-v1' and g['max_elapsed_seconds']==900,'ORIGINAL_PROTOCOL')
 need(g['request_timeout_seconds']==15 and g['postcheck_seconds']==40,'ORIGINAL_AUXILIARY_BUDGET')
 need(g['limits']=={'cpu':8,'memory_bytes':8589934592,'pids':2048,'plain_bytes':10737418240,'compressed_bytes':11811160064,'cipher_bytes':12884901888},'ORIGINAL_LIMITS')
 return g

def main():
 os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('default_false');p.add_argument('independent_decision');p.add_argument('--issue-after-current-review',metavar='NEW_OUTPUT');a=p.parse_args();b=Path(a.default_false).read_bytes();g=validate(b,json.loads(Path(a.independent_decision).read_bytes()))
 if not a.issue_after_current_review:print(json.dumps({'status':'VALIDATED_ONLY_NO_GRANT_WRITTEN','run_id':RUN}));return
 original=dict(g);g['allow']=True;need({k for k in g if g[k]!=original[k]}=={'allow'},'ONLY_ALLOW_CHANGE')
 with Path(a.issue_after_current_review).open('xb') as f:f.write(json.dumps(g,separators=(',',':'),sort_keys=True).encode()+b'\n');f.flush();os.fsync(f.fileno())
 print(json.dumps({'run_id':RUN,'only_allow_changed':True,'performance_conclusion':False}))
if __name__=='__main__':main()
