"""User-run Docker start of exact old P09 container IDs only; no controller/recreate/pull/seed."""
import argparse,datetime,hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT='t44-cloud-r30finalp09-p';ROLES={'mysql','rabbitmq','api','consumer','scheduler','web','tls-gateway'}
FMT='{"id":{{json .Id}},"image_id":{{json .Image}},"name":{{json .Name}},"project":{{json (index .Config.Labels "com.docker.compose.project")}},"role":{{json (index .Config.Labels "com.docker.compose.service")}},"user":{{json .Config.User}},"running":{{json .State.Running}},"health":{{if .State.Health}}{{json .State.Health.Status}}{{else}}null{{end}},"limits":{"CpuPeriod":{{json .HostConfig.CpuPeriod}},"CpuQuota":{{json .HostConfig.CpuQuota}},"Memory":{{json .HostConfig.Memory}},"MemorySwap":{{json .HostConfig.MemorySwap}},"NanoCpus":{{json .HostConfig.NanoCpus}},"PidsLimit":{{json .HostConfig.PidsLimit}},"Ulimits":{{json .HostConfig.Ulimits}}}}'
def need(v,c):
 if not v:raise ValueError(c)
def call(argv,timeout=15):
 p=subprocess.run(argv,capture_output=True,check=False,timeout=timeout);need(p.returncode==0,'CONTAINER_CLI_FAILED_NO_PRIVATE_STDERR');return p.stdout.decode()
def expected():
 v=json.loads((HERE/'P09-existing-containers.PUBLIC.json').read_bytes());rows=v['containers'];need(v['project']==PROJECT and len(rows)==7 and {x['role']for x in rows}==ROLES and all(x['project']==PROJECT for x in rows),'EXACT_PUBLISHED_SEVEN_EXPECTED');return {x['role']:x for x in rows}
def inspect(exp):
 ids=call(['docker','--context','default','ps','--all','--quiet','--no-trunc','--filter','label=com.docker.compose.project='+PROJECT]).split()
 need(set(ids)=={x['id']for x in exp.values()}and len(ids)==7,'EXACT_EXISTING_P09_SEVEN_IDS_REQUIRED')
 raw=call(['docker','--context','default','inspect','--format',FMT,*ids]);rows=[json.loads(x)for x in raw.splitlines()];need(len(rows)==7 and {x['role']for x in rows}==ROLES,'EXACT_SEVEN_ROLE_INSPECTION_REQUIRED');actual={x['role']:x for x in rows}
 for role,row in actual.items():
  need(all(row.get(k)==exp[role][k]for k in ['id','role','project','image_id','name','user','limits']),'EXISTING_CONTAINER_IDENTITY_OR_RESOURCES_CHANGED:'+role)
 return actual
def wait(exp,roles,healthy,end):
 while True:
  state=inspect(exp)
  if all(state[x]['running']and (not healthy or state[x]['health']=='healthy')for x in roles):return state
  need(time.monotonic()<end,'EXISTING_CONTAINER_HEALTH_NOT_READY_NO_RECREATE');time.sleep(min(1,max(0,end-time.monotonic())))
def start(exp,roles):
 state=inspect(exp);ids=[exp[x]['id']for x in roles if not state[x]['running']]
 if ids:call(['docker','--context','default','start',*ids],30)
def resume(action,ack=False,wait_seconds=180):
 need(0<wait_seconds<=300,'BOUNDED_HEALTH_WAIT_REQUIRED');exp=expected()
 active=subprocess.run(['systemctl','is-active','--quiet','t44-final-p09-continuous.service'],capture_output=True,check=False,timeout=10)
 need(active.returncode in {3,4},'OLD_P09_LAUNCHER_ACTIVE_OR_UNKNOWN_NO_REPLAY')
 state=inspect(exp);end=time.monotonic()+wait_seconds
 if action=='infra':
  need(not state['consumer']['running']and not state['scheduler']['running'],'OLD_WORKERS_ALREADY_RUNNING_REQUIRES_ROOT_REVIEW')
  start(exp,['mysql','rabbitmq']);wait(exp,['mysql','rabbitmq'],True,end)
  start(exp,['api']);wait(exp,['api'],True,end)
  start(exp,['web','tls-gateway']);state=wait(exp,['web','tls-gateway'],False,end)
 elif action=='workers':
  need(ack,'BACKEND_SERVICE_REISSUE_AND_EXISTING_SCHEDULER_TOKEN_REFRESH_MUST_COMPLETE_FIRST')
  need(all(state[x]['running']for x in ['mysql','rabbitmq','api','web','tls-gateway'])and all(state[x]['health']=='healthy'for x in ['mysql','rabbitmq','api']),'INFRA_NOT_READY')
  start(exp,['consumer','scheduler']);state=wait(exp,['consumer','scheduler'],True,end)
 else:need(action=='observe','UNKNOWN_ACTION')
 return {'status':'EXISTING_P09_'+action.upper()+'_OBSERVED_NOT_QA','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containers':list(state.values()),'service_refresh_flag_is_operator_ack_not_credential_proof':bool(ack),'container_recreated_or_config_changed':False,'build_pull_seed_or_old_controller_executed':False,'private_contents_read':False,'QA_executed':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['observe','infra','workers']);p.add_argument('--service-and-scheduler-token-refreshed',action='store_true');p.add_argument('--wait-seconds',type=int,default=180);a=p.parse_args();print(json.dumps(resume(a.action,a.service_and_scheduler_token_refreshed,a.wait_seconds),sort_keys=True))
if __name__=='__main__':main()
