#!/bin/bash
# User-authorized persistent key access for the two original T44 servers.
# Run on the selected original server through its cloud-assistant console.
set -euo pipefail
umask 077
python3 - <<'T44_PERSISTENT_SSH'
import base64,datetime,fcntl,hashlib,json,os,stat,subprocess
from pathlib import Path
PUBLIC_KEY = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICLTLyfapsVhTi6VODdUDR3CQ4ov5YVex/eOhSplS7ff'
HOST_PINS = {'i-bp13uag4r4u9r2hge0mt': 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKgIJ8/L0DlPBZrCupxL/zsshjQAKVZ//llDjBhzqIlm', 'i-bp13uag4r4u9r2hge0mu': 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINxgSGq2rWNm5lmnhEyXfZPU6r0ZJVRGv6JbMJ0+SIHP'}
HOSTS = {'172.21.182.245':'i-bp13uag4r4u9r2hge0mt','172.21.182.244':'i-bp13uag4r4u9r2hge0mu'}
def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True,timeout=20).stdout.strip()
if os.geteuid()!=0:
    raise SystemExit('ROOT_REQUIRED')
private_ip=json.loads(run(['ip','-4','-j','route','get','1.1.1.1']))[0]['prefsrc']
instance=HOSTS.get(private_ip)
if instance is None:
    raise SystemExit('ORIGINAL_MACHINE_REQUIRED_NO_CHANGES')
host=' '.join(Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()[:2])
if host!=HOST_PINS[instance]:
    raise SystemExit('ORIGINAL_HOST_KEY_REQUIRED_NO_CHANGES')
run(['/usr/sbin/sshd','-t'])
config=dict(line.split(' ',1)for line in run(['/usr/sbin/sshd','-T']).splitlines()if ' 'in line)
if config.get('pubkeyauthentication')!='yes' or config.get('permitrootlogin')not in {'yes','prohibit-password','without-password'} or config.get('port')!='22':
    raise SystemExit('EXISTING_SSH_POLICY_INCOMPATIBLE_NO_CHANGES')
keydir=Path('/root/.ssh'); authorized=keydir/'authorized_keys'
if keydir.is_symlink() or authorized.is_symlink():
    raise SystemExit('SSH_SYMLINK_REFUSED_NO_CHANGES')
keydir.mkdir(mode=0o700,exist_ok=True)
if keydir.stat().st_uid!=0:
    raise SystemExit('ROOT_OWNED_DIRECTORY_REQUIRED')
keydir.chmod(0o700)
fd=os.open(authorized,os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_NOFOLLOW,0o600)
added=False
try:
    fcntl.flock(fd,fcntl.LOCK_EX)
    metadata=os.fstat(fd)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid!=0 or metadata.st_nlink!=1 or metadata.st_size>1048576:
        raise SystemExit('ROOT_SINGLE_LINK_BOUNDED_AUTHORIZED_KEYS_REQUIRED')
    os.fchmod(fd,0o600)
    before=os.read(fd,metadata.st_size)
    entry=('restrict '+PUBLIC_KEY+' t44-persistent-access').encode()
    if entry not in [line.strip() for line in before.splitlines()]:
        payload=(b'\n' if before and not before.endswith(b'\n') else b'')+entry+b'\n'
        remaining=memoryview(payload)
        while remaining:
            remaining=remaining[os.write(fd,remaining):]
        os.fsync(fd)
        added=True
finally:
    os.close(fd)
# Existing installed service only. Keep current root/password/port/firewall policy.
run(['systemctl','enable','--now','ssh.service'])
state=run(['systemctl','is-active','ssh.service'])
fingerprint='SHA256:'+base64.b64encode(hashlib.sha256(base64.b64decode(host.split()[1],validate=True)).digest()).decode().rstrip('=')
print(json.dumps({'kind':'T44_PERSISTENT_SSH_AUTHORIZATION','instance_id':instance,'private_ip':private_ip,'installed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorization_expires_utc':None,'authorized_key_options':'restrict; no expiry; no forwarding','key_added':added,'host_public_key':host,'host_fingerprint':fingerprint,'ssh_service_state':state,'security_group_firewall_password_or_VM_changed':False},sort_keys=True))
T44_PERSISTENT_SSH
