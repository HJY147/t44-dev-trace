"""User-executed exact P08->fresh P09 clone and first freeze, no old-window retime."""
import argparse,ast,base64,datetime,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path('/root/t44-final-20261029');T=R/'ops01/deployment/cloud-reuse'
PINS={'P08-CONTINUOUS-fast10-cap50.PUBLIC.py': 'dc811694da339101095b79819c96a07f0edc0b397feb131e2b97b4e343ad2d9d', 'final-app-prepare-pfast08-cap50.py': 'b6c09ab1d2646cffc2cafd4f68be039cf88ec005d5d3a943727cd46a5bdc9843', 'final-image-bundle-pfast08-cap50.py': 'a18ca38623aba2aba1a4a0e12e9698f8ce3bd1309896b7d087ee1a1a843de7bf', 'final-timeplan-pfast08-cap50.py': 'bff1ad2479b65849f01a1670429d8d3198879c5c5b6ac55afc818a37caf9ca01'}
FEE_B64='ewogICJBUFBfZmFjdHNfc2hhMjU2IjogImIzMTdjYzI5MGYzYTgzYWU0ZGVjYmRiZDhiMjg1MWMyZTA5MTllNjBhZWFiMTZhZWZmMTJhNDUzODU4YjA4ZmYiLAogICJMT0FEX2ZhY3RzX3NoYTI1NiI6ICJjM2M2NWI5NTAxZjI1OTJkYTcxZDk3NmQyMGYxNzllNTAyYzRlYzBmMGQ3MTFlNmRjOThhMjVmMjNkOGRhNzg3IiwKICAiYWJzb2x1dGVfY29zdF9jdXRvZmZfdXRjIjogIjIwMjYtMTAtMzBUMDM6MDA6MDBaIiwKICAiYWN0dWFsX0FQUF9yZXN1bWVfYm9vdF91dGMiOiAiMjAyNi0xMC0zMFQwMTo1NzozOVoiLAogICJhY3R1YWxfTE9BRF9yZXN1bWVfYm9vdF91dGMiOiAiMjAyNi0xMC0zMFQwMTo1NzoyN1oiLAogICJhcHByb3ZhbF9vYnNlcnZlZF91dGMiOiAiMjAyNi0xMC0zMFQwMjowMzozM1oiLAogICJjYW1wYWlnbl9zY29wZSI6ICJPTkVfUDA5X1NUUklDVF9QRVJGT1JNQU5DRV9NRUFTVVJFTUVOVF9PTkxZIiwKICAiY29zdF9vcmlnaW5fYmFzaXMiOiAiQ29uc2VydmF0aXZlIGFjY291bnRpbmcgb3JpZ2luIGRlcml2ZWQgcmV0cm9zcGVjdGl2ZWx5IGZyb20gZWFybGllc3Qgb2YgdGhlIHR3byBhY3R1YWwga2VybmVsIGJvb3RzOyBub3QgYSBjb250ZW1wb3JhbmVvdXMgVUkgb2JzZXJ2YXRpb24uIiwKICAiaGlzdG9yaWNhbF9BUFBfZmlyc3RfYm9vdF91dGMiOiAiMjAyNi0xMC0yOVQxMzo0NToyNloiLAogICJtYXhpbXVtX3F1b3RlX2Zyb21fb3JpZ2luYWxfcmVzdW1lX0NOWSI6IDE2LjIzODUwMTI1LAogICJwbGF0Zm9ybV90YXNrX2V4ZWN1dGlvbl9pZCI6ICJleGVjLTVkZDUyMWMzMzVjZTRhODhhMmU3IiwKICAicHJpb3JfUDA4X2ZlZV9zaGEyNTYiOiAiYjA3ZjcxOGE3ZWUwYmRmNDhmMTBmNjNlM2IyYzIzODRlNjljNWYwNWM1NmZlMThiNmIwMTIzOWNkMzBlNjg4YSIsCiAgInJlbWFpbmluZ19idWRnZXRfQ05ZIjogNTAsCiAgInJlc3VtZV9vYnNlcnZlZF91dGMiOiAiMjAyNi0xMC0zMFQwMTo1NzoyN1oiLAogICJyb290X2FwcHJvdmVkIjogdHJ1ZSwKICAic2NvcGVfbm90ZSI6ICJVc2VyIGF1dGhvcml6ZWQgZnJlc2ggUDA5IGFmdGVyIFAwOCBuZXZlciBlbnRlcmVkIFFBIG1lYXN1cmVtZW50OyBzYW1lIGFjdHVhbCBib290cy9jb3N0IG9yaWdpbi9jYXA1MC8wMzowMCBvdXRlcjsgbm8gbmV3IHJlc291cmNlcywgb2xkIFAwOCBjbG9ja3MvZGF0YSByZXRhaW5lZC4iLAogICJzdGF0dXMiOiAiUk9PVF9BUFBST1ZFRF9BQ1RVQUxfQk9PVFNfVkVSSUZJRUQiLAogICJ1c2VyX2F1dGhvcml6YXRpb25fcXVvdGUiOiAiXHU2NzAwXHU1NDBlMTAwXHU1NzU3XHU5NGIxXHVmZjBjXHU2NWUwXHU4YmJhXHU1OTgyXHU0ZjU1XHVmZjBjXHU0ZjYwXHU5MGZkXHU1ZmM1XHU5ODdiXHU1YjhjXHU2MjEwXHU1MzhiXHU2ZDRiXHVmZjBjXHU1MTc2XHU0ZWQ2XHU2MjExXHU0ZTBkXHU3YmExXHU0ZTg2XHVmZjBjXHU2NzAwXHU1NDBlXHU0ZTAwXHU2YjIxIiwKICAidXNlcl9vdmVyYWxsX2ZpbmFsX3RvcHVwX2F1dGhvcml6YXRpb25fQ05ZIjogMTAwLAogICJ2YXJpYW5jZV9yZXNlcnZlX0NOWSI6IDMKfQo='
FEE_SHA='fdb7b91e0be795f2fdbbbefb535208e6b13a7b5d74de2fb3298f961d3a3562d1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ready-b64',required=True);p.add_argument('--ready-sha256',required=True);a=p.parse_args();os.umask(0o077)
 ready_raw=base64.b64decode(a.ready_b64,validate=True)
 if hashlib.sha256(ready_raw).hexdigest()!=a.ready_sha256:raise ValueError('ACTUAL_NEW_LOAD_READY_RAW_SHA_REQUIRED')
 ready=json.loads(ready_raw);age=time.time()-datetime.datetime.fromisoformat(ready['observed_utc'].replace('Z','+00:00')).timestamp()
 if ready.get('root_approved')is not True or ready.get('actual_LOAD_ready')is not True or ready.get('QA_or_other_writer_started')is not False or ready.get('actual_image_id')!='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1' or not 0<=age<=120:raise ValueError('ACTUAL_LOAD_READY_WITHIN120_REQUIRED')
 fee_raw=base64.b64decode(FEE_B64);assert hashlib.sha256(fee_raw).hexdigest()==FEE_SHA;fee=json.loads(fee_raw)
 outer=datetime.datetime.fromisoformat(fee['absolute_cost_cutoff_utc'].replace('Z','+00:00')).timestamp()
 if fee.get('remaining_budget_CNY')!=50 or fee.get('root_approved')is not True or outer-time.time()<2160:raise ValueError('P09_FIRST_FREEZE_KEEP_ORIGINAL03_OUTER_AND36MIN_DISPATCH_MARGIN')
 if (R/'P09').exists()or(R/'r30finalp09-launcher').exists():raise ValueError('P09_ATTEMPT_EXISTS_NO_REPLAY')
 for n,h in PINS.items():
  if sha(T/n)!=h:raise ValueError('ACTUAL_USER_P08_TOOL_PREIMAGE_CHANGED:'+n)
 outputs={}
 for n in PINS:
  text=(T/n).read_text();newname=n.replace('P08','P09').replace('pfast08','pfast09')
  text=text.replace('r30finalp08','r30finalp09').replace("R/'P08'","R/'P09'").replace('pfast08','pfast09')
  if n.startswith('P08-'):
   text=text.replace("R/'P07/campaign/p'","R/'P08/campaign/p'").replace('t44-cloud-r30finalp07-p','t44-cloud-r30finalp08-p').replace('t44-final-p07*','t44-final-p08*').replace('stop-old-P07','stop-old-P08').replace('PREVIOUS_P07','PREVIOUS_P08')
  ast.parse(text,feature_version=(3,10));outputs[newname]=text
 for n,text in outputs.items():
  with (T/n).open('x')as out:out.write(text)
  (T/n).chmod(0o600)
 # Only this exact known previous actor unit is stopped. New launcher separately checks and stops exact previous P08 container ownership.
 subprocess.run(['systemctl','stop','t44-final-p08-continuous.service'],check=False,timeout=40)
 state=subprocess.run(['systemctl','is-active','t44-final-p08-continuous.service'],capture_output=True,check=False,timeout=10).stdout.strip()
 if state in {b'active',b'activating',b'deactivating'}:raise ValueError('OLD_P08_ACTOR_NOT_STOPPED_NO_NEW_START')
 fee_path=R/'P09-current-resume-cost.PUBLIC.json';ready_path=R/'P09-current-LOAD-ready.PUBLIC.json'
 for p,raw in [(fee_path,fee_raw),(ready_path,ready_raw)]:
  with p.open('xb')as out:out.write(raw)
  p.chmod(0o600)
 print(json.dumps({'status':'FRESH_P09_EXACT_TOOLS_PREPARED_OLD_P08_ACTOR_STOPPED','new_tools':{n:sha(T/n)for n in outputs},'fee_sha256':FEE_SHA,'LOAD_ready_sha256':a.ready_sha256,'old_P08_data_retained':True}),flush=True)
 raise SystemExit(subprocess.run(['systemd-run','--unit=t44-final-p09-continuous','--property=Type=exec','--property=UMask=0077','--property=RuntimeMaxSec=2400','--collect','python3','-B',str(T/'P09-CONTINUOUS-fast10-cap50.PUBLIC.py'),'--load-ready',str(ready_path),'--load-ready-sha256',a.ready_sha256,'--cost-approval',str(fee_path),'--cost-approval-sha256',FEE_SHA],check=False).returncode)
if __name__=='__main__':main()
