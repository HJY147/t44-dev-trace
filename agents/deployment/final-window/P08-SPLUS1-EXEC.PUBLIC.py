"""Describe or execute one root-approved original P entry at S+1; never retry or retime."""
import argparse,datetime,hashlib,json,os,time
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def text(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['describe','execute']);p.add_argument('--entry',type=Path,required=True);p.add_argument('--entry-sha256',required=True);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--grant-file',type=Path,required=True);p.add_argument('--grant-sha256',required=True);p.add_argument('--run-id',default='r30finalp08');a=p.parse_args()
 for file,pin in [(a.entry,a.entry_sha256),(a.grant_file,a.grant_sha256)]:
  if not file.is_absolute() or file.is_symlink() or sha(file)!=pin:raise ValueError('ORIGINAL_EXACT_ENTRY_AND_APPROVED_GRANT_REQUIRED')
 grant=json.loads(a.grant_file.read_bytes())
 if a.run_id!='r30finalp08' or grant.get('run_id')!=a.run_id or grant.get('allow') is not True or grant.get('clients')!=400 or grant.get('warmup_seconds')!=60 or grant.get('steady_seconds')!=600:raise ValueError('EXACT_ROOT_SINGLE_STRICT_P08_GRANT_REQUIRED')
 start=utc(grant['window_start_utc']);end=utc(grant['window_end_utc']);cost=utc(grant['cost_stop_utc']);target=start+1;now=time.time()
 if end-start!=780 or cost-end<90:raise ValueError('ORIGINAL_STRICT_780_WINDOW_AND_COST_RESERVE_REQUIRED')
 argv=['/bin/sh',str(a.entry),'execute',str(a.workspace),a.run_id,str(a.grant_file)]
 if a.action=='describe':
  print(json.dumps({'status':'DESCRIBED_ONLY_NOT_ARMED_OR_EXECUTED','run_id':a.run_id,'S':text(start),'E':text(end),'C':text(cost),'execute_at_S_plus1':text(target),'arm_no_later_than':text(start-30),'seconds_until_target':target-now,'entry_sha256':a.entry_sha256,'grant_sha256':a.grant_sha256,'execution_argv':argv,'QA_or_SUT_requests':0}));return
 if not target<=now<start+20:raise ValueError('ACTUAL_S_PLUS1_TO_S_PLUS20_ONLY_NO_LATE_OVERRIDE')
 os.execv('/bin/sh',argv)
if __name__=='__main__':main()
