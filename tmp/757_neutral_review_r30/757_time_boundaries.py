"""Real pure deadline guards plus synthetic arithmetic; no clocks/windows are rewritten."""

import ast
import importlib.util
import json
import types
from datetime import UTC,datetime,timedelta
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location("review_deadline",ROOT/"deployment/cloud-reuse/derive-resume-profile.py")
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
t0=datetime(2026,11,1,tzinfo=UTC);stop=t0+timedelta(minutes=35)
text=(ROOT/"deployment/cloud-reuse/generation-f4.py").read_text()
tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="valid_window")
simulation=types.SimpleNamespace(value=t0.timestamp())
namespace=dict(time=types.SimpleNamespace(time=lambda:simulation.value),HARDSTOP=stop.isoformat().replace("+00:00","Z"))
exec(compile(ast.Module(body=[node],type_ignores=[]),"actual_GEN_valid_window","exec"),namespace)
lib=types.SimpleNamespace(expiry=lambda value:datetime.fromisoformat(value.replace("Z","+00:00")).timestamp())
checks=[]
for seconds,expected in [(300,True),(301,False)]:
    try:parent.deadline(namespace["HARDSTOP"],t0+timedelta(seconds=seconds));accepted=True
    except ValueError:accepted=False
    assert accepted==expected
    checks.append(dict(guard="local derive >=1800s",T0_offset=seconds,accepted=accepted))
for seconds,expected in [(600,True),(900,True),(1500,True),(1501,False)]:
    simulation.value=t0.timestamp()+seconds
    try:namespace["valid_window"](lib,namespace["HARDSTOP"],600);accepted=True
    except ValueError:accepted=False
    assert accepted==expected
    checks.append(dict(guard="GEN prepare/operate >=600s",T0_offset=seconds,accepted=accepted))
case=dict(packet=1050,transfer_prepare=120,authorization_dispatch=30,start=1200,duration=780,end=1980,GEN_stop=2100,cost_stop=2400)
assert case["packet"]+case["transfer_prepare"]+case["authorization_dispatch"]<=case["start"]
assert case["end"]==case["start"]+case["duration"]<=case["GEN_stop"]
assert case["end"]<=case["cost_stop"]-90 and case["start"]+10-case["packet"]<=300
value=dict(checks=checks,fixed_example=case,actual_start_allowed="S <= execute < S+20s",packet_creation_and_windows_are_never_retimed=True,not_a_generation_or_grant=True,service_or_Docker_or_HTTP_or_session_calls=0)
(HERE/"time-boundaries.json").write_text(json.dumps(value,indent=2)+"\n")
print(json.dumps(value))
