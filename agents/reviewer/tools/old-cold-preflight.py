"""Root-run metadata only; never backup, stop, read contents or approve selection."""
import hashlib,json,os,re,stat,subprocess,sys
from pathlib import Path
assert os.geteuid()==0
src,out=map(Path,sys.argv[1:3])
s=src.lstat()
assert src.is_absolute() and src.resolve()==src and stat.S_ISREG(s.st_mode) and s.st_uid==0
raw=src.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='032e231e7e529d7466451ff3eb4f5d45515f5f61ff944bbc274a1df0eed2fc86'
old=json.loads(raw)
assert len(old['volumes'])==26
roots=[Path('/root/t44-r9'),Path('/root/t44-r30')]
assert set(map(str,roots))<={x['path'] for x in old['directory_sizes']}
assert out.is_absolute() and out.parent.resolve()==out.parent and not out.exists()
os.umask(0o077)
def docker(*args):
    return subprocess.check_output(['docker','--context','default',*args],timeout=20,text=True)
bad=[];vols=[];refs=[]
for v in old['volumes']:
    name=v['Name'];project=v['Labels']['com.docker.compose.project']
    assert re.fullmatch(r't44-cloud-[a-z][a-z0-9]{5,17}-[fp]',project)
    fmt='{"Name":{{json .Name}},"Mountpoint":{{json .Mountpoint}},"Labels":{{json .Labels}}}'
    a=json.loads(docker('volume','inspect','--format',fmt,name))
    assert (a['Name'],a['Mountpoint'],a['Labels']['com.docker.compose.project'])==(name,v['Mountpoint'],project)
    p=Path(a['Mountpoint'])
    assert p==Path('/var/lib/docker/volumes')/name/'_data'
    for cid in docker('ps','-aq','--filter','volume='+name).split():
        state=json.loads(docker('inspect','--format','{{json .State}}',cid))
        refs.append({'volume':name,'container':cid,'state':state})
        if state['Running'] or state.get('Restarting'):bad.append(['VOLUME_IN_USE',name,cid])
    roots.append(p);vols.append({'name':name,'project':project})
assert len(set(roots))==len(roots)
assert not any(out==p or out.is_relative_to(p) or p.is_relative_to(out) for p in roots)
sizes=[];required=[]
for root in roots:
    assert root.resolve()==root and root.is_dir()
    dev=root.stat().st_dev;stack=[root];first=None;seen=set();allocated=0;logical=0;count=0
    while stack:
        p=stack.pop();s=p.lstat();count+=1
        key=(s.st_dev,s.st_ino)
        if key not in seen:allocated+=s.st_blocks*512;logical+=s.st_size;seen.add(key)
        if p.name=='backup-selection.private.json':bad.append(['DUPLICATE_SELECTION',str(p)])
        if stat.S_ISLNK(s.st_mode):
            link=Path(os.readlink(p))
            if link.is_absolute() or '..' in link.parts:bad.append(['UNSAFE_LINK',str(p)])
        elif stat.S_ISDIR(s.st_mode):
            if s.st_dev!=dev:bad.append(['NESTED_MOUNT',str(p)]);continue
            if p.name.lower() in {'private','qa-private','qa_private','review_r30_only'}:
                bad.append(['QA_PRIVATE_NOT_SCANNED',str(p)]);continue
            stack.extend(Path(e.path) for e in os.scandir(p))
        elif stat.S_ISREG(s.st_mode):
            if first is None:first=str(p)
        else:bad.append(['SPECIAL_FILE',str(p)])
    if first:required.append(first)
    else:bad.append(['NO_REGULAR_SENTINEL',str(root)])
    sizes.append({'root':str(root),'entries':count,'du_allocated_bytes':allocated,'logical_bytes':logical})
out.mkdir(mode=0o700)
def save(name,value):
    with (out/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    (out/name).chmod(0o600)
save('preflight.private.json',{'metadata_only':True,'problems':bad,'volume_refs':refs,'sizes':sizes})
save('selection.draft.private.json',{'kind':'root-approved-APP-backup-selection-v1','role':'APP','root_approved':False,'absolute_cost_cutoff_utc':'2026-10-29T19:50:00Z','directories':list(map(str,roots[:2])),'volumes':vols,'restore_required_files':required})
print(json.dumps({'volumes':len(vols),'roots':len(roots),'problems':len(bad),'selection_approved':False}))
sys.exit(bool(bad))
