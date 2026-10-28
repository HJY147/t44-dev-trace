set -eu
python3 -B - <<'WINDOW_CHECK'
from pathlib import Path
import json,datetime,subprocess,hashlib
p=Path('/root/t44-r9/campaign-r28p16-02/p/fixture790-01/split790-v3-01/s1/candidate-01/candidate.private.json')
c=json.loads(p.read_bytes());e=datetime.datetime.fromisoformat(c['service']['expires_at'].replace('Z','+00:00'));n=datetime.datetime.now(datetime.timezone.utc)
print(json.dumps({'kind':'SERVICE_SESSION_WINDOW_BEFORE_S2','utc':n.isoformat(),'actual_expires_at':e.isoformat(),'remaining_seconds':(e-n).total_seconds(),'S2_executed':False}),flush=True)
if (e-n).total_seconds()<600:raise SystemExit('insufficient real service session window; zero S2')
p=Path('/root/t44-r9/resume-20261028-02/790_v3_producer.py')
if hashlib.sha256(p.read_bytes()).hexdigest()!='54bd59480ec9b60e5da69ecc35d54ea2d73e4538d6a32400c7de1811f1b49e6b':raise SystemExit('producer code changed')
WINDOW_CHECK
python3 -B /root/t44-r9/resume-20261028-02/790_v3_producer.py
