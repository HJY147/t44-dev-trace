#!/usr/bin/env python3
"""Read only the exact high-level phase metadata and public trigger, never tools/cases/results."""
import argparse,datetime,json,re,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('workspace');p.add_argument('run_id');a=p.parse_args()
if not Path(a.workspace).is_absolute() or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}',a.run_id):raise SystemExit(2)
w=Path(a.workspace);phase=w/'results'/(a.run_id+'.phase.json');trigger=w/'runs'/a.run_id/'actual-trigger.PUBLIC.json'
value={'schema':'753-authorized-public-phase-projection-v1','run_id':a.run_id,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase_metadata_exists':phase.is_file(),'actual_trigger_exists':trigger.is_file(),'metrics_or_steady_completion_proven':False}
if trigger.is_file():
 t=json.loads(trigger.read_text());value['actual_trigger_utc']=t.get('actual_trigger_utc');value['dispatch_only']=True
if phase.is_file():
 d=json.loads(phase.read_text());value['phase']={k:d[k] for k in ['schema','run_id','status','phase','utc','monotonic_ns','clients_started','threads_active'] if k in d};running=d.get('phase')in ['RUNNING','FINISHED'] and d.get('clients_started')==400;value['cohort400_barrier_released_observed']=running
 if d.get('phase')=='RUNNING' and isinstance(d.get('monotonic_ns'),int):
  elapsed=max(0,(time.monotonic_ns()-d['monotonic_ns'])/1e9);value['seconds_since_public_RUNNING_marker']=round(elapsed,3);value['nominal_interval_only']='warmup' if elapsed<60 else 'steady_expected_subject_to_live_cohort_and_final_evidence' if elapsed<660 else 'postcheck_or_finalizing_expected_subject_to_final_evidence'
 value['meaning']='RUNNING400 proves all400client threads crossed readiness barrier; it does not prove400simultaneous HTTP requests, current alive400, steady completion or P95/throughput.'
print(json.dumps(value,separators=(',',':')))
