import sys,json,pathlib,hashlib,zlib,collections,math,base64,io,http.client
sys.path.insert(0,'/tmp/t44-direct-p18-private')
from runtime import Seal
from verify_raw import verify
B=pathlib.Path('/tmp/t44-p18-actual-decrypted'); R=B/'results/r30posttools18'; W=B/'runs/r30posttools18'
raw=R/'evidence.772seal';key=(R/'evidence.key').read_bytes();integrity=verify(raw,key)
inv={x['client_id']:x for x in json.loads((W/'inventory.json').read_text())['clients']};sessions=json.loads((W/'sessions.json').read_text())
class Sock:
 def __init__(self,b):self.b=b
 def makefile(self,*a,**k):return io.BytesIO(self.b)
def decode(row,request=False):
 b=base64.b64decode(row['request_wire_base64' if request else 'response_wire_base64'])
 if request:return json.loads(b.split(b'\r\n\r\n',1)[1] or b'{}')
 h=http.client.HTTPResponse(Sock(b));h.begin();body=h.read();assert h.status==row['response_status'];return json.loads(body)
lat=collections.defaultdict(list);buckets=[0]*10;errors=collections.Counter();types=collections.Counter();first={};blocks={};last={};auditids=collections.defaultdict(set);posts=collections.defaultdict(list);clientcnt=collections.Counter();cohort=None;wire_errors=0;record_count=0;business_violations=collections.Counter();all_exchange_errors=0
z=zlib.decompressobj(31);pending=b''
for kind,p in Seal.read(raw,key):
 if kind==255:continue
 pending+=z.decompress(p)
 while b'\n'in pending:
  line,pending=pending.split(b'\n',1);row=json.loads(line);record_count+=1;typ=row.get('record');types[typ]+=1
  if typ=='cohort_start':cohort=row;continue
  if typ!='exchange':continue
  cid=row['client'];s=row['start_monotonic_ns'];e=row['end_monotonic_ns'];assert e-s==row['rtt_ns'] and e>=s
  try:d=decode(row)
  except Exception:wire_errors+=1;d={}
  if row['error']:all_exchange_errors+=1
  if cohort['steady_ns']<=s<cohort['steady_end_ns']:
   lat[row['class']].append(e-s);clientcnt[cid]+=1
   if row['error'] or not row['response_complete'] or row['response_status']!=(202 if row['class']=='escalation' else 200):errors[str(row['error'] or row['response_status'])]+=1
   bucket=(e-cohort['steady_ns'])//60000000000
   if 0<=bucket<10:buckets[bucket]+=1
  if row['phase']=='postcheck':posts[cid].append((row,d));continue
  data=d.get('data',{})
  if row['class']=='query':
   if cid not in first:first[cid]=(row,data)
   last[cid]=data
  elif row['class']=='transition':
   req=decode(row,True)
   if req.get('action')==2 and cid not in blocks:blocks[cid]=(row,last.get(cid,{}))
   if 'task'in data:
    before=last[cid];after=data['task'];action=req['action']
    valid=(after['id']==before['id'] and after['owner_id']==before['owner_id'] and after['project_id']==before['project_id'] and after['version']==before['version']+1 and after['state']==(3 if action==2 else 2) and after['blocked_from_state']==(2 if action==2 else None))
    if not valid:business_violations['transition_snapshot']+=1
    last[cid]=after;auditids[cid].add(data['audit_id'])
  elif row['class']=='escalation':
   expected=inv[cid]['escalation_event']
   if data.get('created') is not False or any(data.get('event',{}).get(k)!=expected[k]for k in ['id','task_id','project_id','schedule_version','rule_version','level']):business_violations['escalation_dedup']+=1
  elif row['class']=='contract':
   if data!={'valid':True,'category':2,'validated_operation_id':'transitionTask','schema_version':'1.0.0','business_guards_executed':False}:business_violations['contract']+=1
metrics={k:{'count':len(v),'p95_ms':sorted(v)[math.ceil(.95*len(v))-1]/1e6}for k,v in lat.items()}
deadline=cohort['steady_end_ns']+40000000000
snap=aud=late=0;posterrors=0;missing_audits=0;snapshot_mismatch=0;post_last=0
for cid in inv:
 found=set();pages=set();total=None;ss=False;good=True
 for row,d in posts[cid]:
  post_last=max(post_last,row['end_monotonic_ns'])
  if row['end_monotonic_ns']>deadline:late+=1;continue
  if row['error'] or row['response_status']!=200 or not row['response_complete']:posterrors+=1;good=False;continue
  data=d['data']
  if 'audit-events?'not in row['path']:
   equal=all(data[k]==last[cid][k]for k in ['id','project_id','version','state','blocked_from_state','block_reason','responsibility_stage','schedule_version','delivery_cycle','review_cycle','escalation_count'])
   if equal:ss=True
   else:snapshot_mismatch+=1
  else:
   import urllib.parse
   q=urllib.parse.parse_qs(urllib.parse.urlsplit(row['path']).query);pages.add(int(q['page'][0]));total=data['total']
   for x in data['items']:
    if x['task_id']!=inv[cid]['transition_task']['id'] or x['project_id']!=inv[cid]['project_id']:good=False
    if x['outcome']==1 and x['operation_id']=='transitionTask'and x['actor_id']==sessions['developer']['user_id']and x['actor_kind']==1:found.add(x['id'])
 snap+=ss
 complete=total is not None and set(range(1,math.ceil(total/100)+1))<=pages and auditids[cid]<=found and good
 aud+=complete;missing_audits+=len(auditids[cid]-found)
initial={'first_query_clients':len(first),'first_query_state_distribution':dict(collections.Counter(str(d.get('state'))for _,d in first.values())),'inventory_state_version_owner_matches':sum(all(d[k]==inv[cid]['transition_task'][k]for k in ['state','version','owner_id'])for cid,(_,d)in first.items()),'first_BLOCK_clients':len(blocks),'first_BLOCK_prestate_distribution':dict(collections.Counter(str(d.get('state'))for _,d in blocks.values())),'first_BLOCK_HTTP_200':sum(r['response_status']==200 and not r['error']for r,d in blocks.values())}
result=json.loads((R/'result.json').read_text())
out={'all_exchange_runtime_errors':all_exchange_errors,'independent_business_violations':dict(business_violations),'raw_integrity':integrity,'record_count':record_count,'record_types':dict(types),'wire_decode_errors':wire_errors,'cohort_clients':cohort['clients'],'warmup_seconds':(cohort['steady_ns']-cohort['start_ns'])/1e9,'steady_seconds':(cohort['steady_end_ns']-cohort['steady_ns'])/1e9,'steady_classes':metrics,'steady_requests':sum(map(len,lat.values())),'steady_errors':dict(errors),'completion_minute_buckets':buckets,'steady_client_coverage':len(clientcnt),'post_final_snapshots':snap,'post_complete_audits':aud,'post_late_responses_excluded':late,'post_http_or_runtime_errors':posterrors,'post_snapshot_mismatches':snapshot_mismatch,'post_missing_expected_audits':missing_audits,'last_post_response_seconds_after_steady':(post_last-cohort['steady_end_ns'])/1e9,'initial_conditions':initial,'runtime_binding_matches':result['effective_runtime_binding_sha256']=='af93a6ffd956c0a2ae86362a6a0e13db9be589e8cfde7335195020cc3a7401b7','recomputed_metrics_match_result':metrics==result['classes']}
pathlib.Path('/tmp/p18-independent-recomputed.PUBLIC.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
