#!/bin/bash
# USER-EXECUTED ONLY: new temporary root SSH access needs explicit action-time approval.
# Existing SSH software/config only. No security-group, firewall, password or VM changes.
set -euo pipefail
umask 077
python3 - <<'SSH_RECOVERY'
import base64,datetime,hashlib,json,os,subprocess
from pathlib import Path
PUBLIC_KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICLTLyfapsVhTi6VODdUDR3CQ4ov5YVex/eOhSplS7ff'
if os.geteuid()!=0:raise SystemExit('ROOT_REQUIRED')
def run(argv):return subprocess.run(argv,check=True,capture_output=True,text=True,timeout=15).stdout.strip()
ip=json.loads(run(['ip','-4','-j','route','get','1.1.1.1']))[0]['prefsrc']
allowed={'172.21.182.245':'i-bp13uag4r4u9r2hge0mt','172.21.182.244':'i-bp13uag4r4u9r2hge0mu'}
if ip not in allowed:raise SystemExit('UNEXPECTED_MACHINE_NO_CHANGES')
sshd=Path('/usr/sbin/sshd')
if not sshd.is_file():raise SystemExit('SSHD_NOT_INSTALLED_NO_CHANGES')
run([str(sshd),'-t'])
config=dict(line.split(' ',1)for line in run([str(sshd),'-T']).splitlines()if ' 'in line)
if config.get('pubkeyauthentication')!='yes' or config.get('permitrootlogin')not in {'yes','prohibit-password','without-password'} or config.get('port')!='22':raise SystemExit('EXISTING_SSH_CONFIG_NOT_COMPATIBLE_NO_CHANGES')
keydir=Path('/root/.ssh');authorized=keydir/'authorized_keys'
if keydir.is_symlink()or authorized.is_symlink():raise SystemExit('SSH_PATH_SYMLINK_REFUSED_NO_CHANGES')
host=Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
if host[0]!='ssh-ed25519':raise SystemExit('EXPECTED_ED25519_HOST_KEY')
now=datetime.datetime.now(datetime.timezone.utc);expiry=now+datetime.timedelta(hours=2)
# OpenSSH 8.9 parses only local YYYYMMDDHHMMSS; a trailing Z is rejected.
entry='restrict,expiry-time="'+expiry.astimezone().strftime('%Y%m%d%H%M%S')+'" '+PUBLIC_KEY+' t44-manual-recovery'
keydir.mkdir(mode=0o700,exist_ok=True);keydir.chmod(0o700)
with authorized.open('a')as out:
 if authorized.stat().st_size and not authorized.read_bytes().endswith(b'\n'):out.write('\n')
 out.write(entry+'\n')
authorized.chmod(0o600)
# Start the already-installed SSH service only; no root/password/port policy edits.
run(['systemctl','start','ssh.service'])
state=run(['systemctl','is-active','ssh.service'])
fingerprint='SHA256:'+base64.b64encode(hashlib.sha256(base64.b64decode(host[1],validate=True)).digest()).decode().rstrip('=')
print(json.dumps({'kind':'T44_TEMPORARY_SSH_RECOVERY','private_ip':ip,'expected_instance_id_from_known_private_ip':allowed[ip],'installed_utc':now.isoformat(),'authorization_expires_utc':expiry.isoformat(),'authorized_key_options':'restrict,expiry-time; no forwarding','host_public_key':' '.join(host[:2]),'host_fingerprint':fingerprint,'ssh_service_state':state,'port':22,'security_group_firewall_password_or_VM_changed':False},sort_keys=True))
SSH_RECOVERY
