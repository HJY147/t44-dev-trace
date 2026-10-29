"""Reclaim only root-selected old network IDs after exact inventory hash and live recheck."""
import argparse,datetime,hashlib,json,os,re,subprocess
from pathlib import Path

def cmd(argv,check=True):return subprocess.run(['docker','--context','default',*argv],capture_output=True,check=check,timeout=30)
def now():return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def eligible(row):
 labels=row.get('Labels') or {};project=labels.get('com.docker.compose.project','');network=labels.get('com.docker.compose.network','')
 return bool(re.fullmatch(r't44-cloud-[a-z0-9][a-z0-9-]{3,100}',project) and network in {'data','edge','application','default'} and row['Name']==project+'_'+network and row.get('Containers')=={} and row.get('Driver')=='bridge' and row.get('Scope')=='local' and not row.get('Ingress'))
def compare(row):return {k:row.get(k) for k in ['Id','Name','Created','Driver','Scope','Internal','Ingress','Labels','Containers','IPAM','Options','Attachable']}
def save(p,o):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(o,f,sort_keys=True,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--inventory-sha256',required=True);p.add_argument('--network-id',action='append',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--approve-selected-empty-t44-removal',action='store_true');a=p.parse_args();os.umask(0o077)
 raw=a.inventory.read_bytes()
 if a.inventory.is_symlink() or hashlib.sha256(raw).hexdigest()!=a.inventory_sha256 or not a.approve_selected_empty_t44_removal:raise ValueError('ROOT_SELECTED_ORIGINAL_INVENTORY_SHA_AND_APPROVAL_REQUIRED')
 original=json.loads(raw)
 if not isinstance(original,list):raise ValueError('ORIGINAL_DOCKER_NETWORK_INSPECT_JSON_ARRAY_REQUIRED')
 table={x['Id']:x for x in original}
 if len(table)!=len(original) or len(set(a.network_id))!=len(a.network_id) or any(not re.fullmatch('[0-9a-f]{64}',x) or x not in table or not eligible(table[x]) for x in a.network_id):raise ValueError('EXACT_ROOT_SELECTED_UNIQUE_FULL_NETWORK_IDS_REQUIRED')
 if not a.output.is_absolute() or a.output.exists() or a.output.parent.resolve()!=a.output.parent:raise ValueError('NEW_CANONICAL_RECEIPT_REQUIRED')
 # Whole selected set must match before the first removal; each gets another recheck at removal.
 for identity in a.network_id:
  current=json.loads(cmd(['network','inspect',identity]).stdout)
  if len(current)!=1 or not eligible(current[0]) or compare(current[0])!=compare(table[identity]):raise ValueError('SELECTED_NETWORK_CHANGED_BEFORE_ANY_REMOVAL')
 receipt={'kind':'ROOT_SELECTED_EMPTY_T44_NETWORK_RECLAIM_V1','inventory_sha256':a.inventory_sha256,'started_utc':now(),'selected_ids':a.network_id,'removed':[],'volumes_images_containers_changed':False,'status':'PARTIAL_PREFIX_PRESERVED'}
 try:
  for identity in a.network_id:
   current=json.loads(cmd(['network','inspect',identity]).stdout)
   if len(current)!=1 or not eligible(current[0]) or compare(current[0])!=compare(table[identity]):raise ValueError('SELECTED_NETWORK_CHANGED_AT_REMOVAL')
   result=cmd(['network','rm',identity]);returned=result.stdout.decode().strip()
   if returned!=identity:raise ValueError('EXACT_DOCKER_RM_RETURN_REQUIRED')
   receipt['removed'].append({'id':identity,'name':current[0]['Name'],'removed_utc':now()})
  receipt['status']='SELECTED_EMPTY_T44_NETWORKS_REMOVED'
 finally:receipt['finished_utc']=now();save(a.output,receipt)
 print(json.dumps({'status':receipt['status'],'removed':len(receipt['removed']),'receipt':str(a.output),'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
