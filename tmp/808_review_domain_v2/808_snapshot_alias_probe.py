"""Minimal pure internal-v2 snapshot counterexample; no test oracle or SUT."""
import sys, json, hashlib
from pathlib import Path
ROOT=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/backend-size-optimize-20261025')
def audit(event,args):
    if event.startswith('socket.'): raise RuntimeError('network forbidden')
sys.addaudithook(audit)
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'backend'))
for name,sha in [('models.py','550d817d5b5aadb5384d5ed319c3dd3cd0ee838feb97063d6e39cca5dbaec170'),('state_machine.py','65a743e2f30e3459568491dfb25e3db387bfb019db5a05dd7125c07fcd1ec9a8')]:
    assert hashlib.sha256((ROOT/'backend/t44/domain'/name).read_bytes()).hexdigest()==sha
from t44.domain.models import Transition,Action,State,Role,DomainViolation
from t44.domain.state_machine import decide
def outcome(context):
    try:return {'kind':'decision','values':dict(decide(context).values)}
    except DomainViolation as e:return {'kind':'rejection','code':e.code}
def build(evidence):
    task={'state':State.PENDING_RELEASE,'blocked_from_state':None,'delivery_cycle':1,'review_cycle':1,'schedule_version':1,'owner_id':1,'artifact_revision':'synthetic','latest_review_id':10,'approved_review_id':10}
    body={'action':Action.DELIVER,'assessment_id':20,'assessment_version':2,'release_version':'synthetic-v1','reason':'synthetic release'}
    review={'id':10,'version':1,'delivery_cycle':1,'review_cycle':1,'artifact_revision':'synthetic','verdict':1,'reviewer_id':2}
    assessment={'id':20,'version':2,'delivery_cycle':1,'schedule_version':1,'status':2,'created_by':1,'reviewed_by':2,'review_evidence':evidence}
    return Transition(task,body,frozenset({Role.MANAGER}),evidence=('synthetic-locator',),review=review,assessment=assessment,review_complete=True)
rows=[]
for direction in ('append','clear'):
    original=[] if direction=='append' else ['synthetic-review-proof']
    context=build(original);before=outcome(context)
    if direction=='append':original.append('synthetic-review-proof')
    else:original.clear()
    after=outcome(context)
    rows.append({'direction':direction,'same_frozen_context':True,'before':before,'after':after,'outcome_changed':before!=after,'collection_alias_retained':context.assessment['review_evidence'] is original})
assert all(x['outcome_changed'] and x['collection_alias_retained'] for x in rows)
print(json.dumps({'scope':'pure internal API snapshot alias counterexample only','source':'a07ad028a8efad4ecd186246bf2b7935c361b117','scenarios':rows,'SUT_HTTP_DB_requests':0,'oracle_imports':[name for name in sys.modules if name.startswith('tmp.') or 'baseline_domain' in name]},indent=2))
