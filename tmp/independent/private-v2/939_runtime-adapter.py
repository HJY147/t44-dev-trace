#!/usr/bin/env python3
"""Versioned independent harness adapter; original frozen files remain byte-identical.

Observed run39963650474 was preserved. Its schema-valid createTask response has
TaskMutationEnvelope data, which the independent new_task fixture mis-unwrapped.
The unfiltered personal-notification list is correctly reachable by an outsider;
its PROJECT_ACCESS_DENIED recipe requires the explicit project filter. This adapter
repairs those two harness/precondition constructions against the already frozen
contract, without changing SUT assertions, thresholds or required coverage.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent
FROZEN=runpy.run_path(str(HERE/'949_harness.py'),run_name='frozen_independent_v2')
for _name in ['Blocked','EVIDENCE','plan','utc','ARTIFACT','OPS','CASES']:
    globals()[_name]=FROZEN[_name]
    setattr(sys.modules['__main__'],_name,FROZEN[_name])

class RuntimeAdapter(FROZEN['Harness']):
    def new_task(self,*args,**kwargs):
        value=super().new_task(*args,**kwargs)
        # Response already passed the exact frozen Draft202012 Schema in call().
        return value['task']

    def common_branch_sweep(self):
        # Reach the operation's declared optional-project-filter403 condition.
        self.data('listMyNotifications',query={'project_id':self.ids['project_id']},expected=200)
        return super().common_branch_sweep()


def run_adapter(phase='blackbox'):
    path=os.environ.get('T44_ACCEPTANCE_CONTEXT')
    if not path:raise Blocked('No bound SUT context')
    context=json.loads(Path(path).read_text())
    context['independent_phase']='fault' if phase.startswith('fault') else phase
    h=RuntimeAdapter(context)
    h.log('adapter_binding',adapter='939_runtime-adapter.py',preserved_first_run=39963650474,changes=['frozen-contract fixture envelope unwrapping','reachable optional project filter precondition'],assertions_or_thresholds_changed=False)
    if h.run('SETUP',h.setup)!='PASS':return h.finish()
    if phase=='blackbox':
        for case,fn in [('LIFE-01',h.core_lifecycle),('DEP-02',h.dependencies),('STAFF-01',h.staffing),('STAFF-03',h.staffing_rework),('CAS-01',h.race_cas),('REV-01',h.review_negative),('TIME-01',h.read_only_validation),('AUTH-02-SUBSET',h.membership_and_scope),('REL-01',h.release_plan_guard),('STAFF-04',h.staffing_races),('INPUT-01',h.common_branch_sweep),('DB-01-OBSERVE',h.storage_snapshot)]:h.run(case,fn)
    elif phase=='fault-all':
        mod=FROZEN['load_module']('947_faults.py','independent_v2_original_faults')
        for selected in ['scan20','mq-fallback','api-restart','db-down','mq-duplicate']:
            h.context['independent_fault_case']=selected
            h.run('FAULT-DRIVER-'+selected,lambda:mod.run(h))
    else:raise Blocked('Unbound independent phase')
    return h.finish()

if __name__=='__main__':
    try:sys.exit(run_adapter())
    except Blocked as exc:print('BLOCKED: '+str(exc));sys.exit(2)
