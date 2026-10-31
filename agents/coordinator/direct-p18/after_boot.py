"""Run the already prepared direct package after the user supplies current public IPs."""
import argparse,hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--app-ip',required=True);p.add_argument('--load-ip',required=True);a=p.parse_args()
 ready=json.loads((HERE/'READY.PUBLIC.json').read_bytes())
 if ready['status']!='READY_FOR_USER_BOOT':raise SystemExit('OFFLINE_PREPARATION_NOT_COMPLETE_DO_NOT_START_SERVERS')
 for name,expected in ready["local_files_sha256"].items():
  if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=expected:raise SystemExit("PREPARED_LOCAL_SOURCE_CHANGED_DO_NOT_CONNECT")
 root=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=HERE,text=True).strip())
 if not root.is_absolute():root=HERE/root
 root=root.resolve().parent
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 output=root/'.submission-private'/('posttools18-'+stamp)
 argv=[sys.executable,'-B',str(HERE/'run.py'),'--app-ip',a.app_ip,'--load-ip',a.load_ip,
       '--kit',str(HERE/ready['archive_name']),'--kit-sha256',ready['archive_sha256'],
       '--identity',str(root/'.submission-private/cloud-access/FINAL-20261030/id_ed25519'),
       '--known-hosts',str(root/'.submission-private/cloud-access/FINAL-20261030/manual13-pins/known_hosts'),
       '--output',str(output)]
 raise SystemExit(subprocess.run(argv).returncode)
if __name__=='__main__':main()
