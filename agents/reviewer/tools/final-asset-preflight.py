"""Root-run stat/Docker metadata only. Full reports stay0600; no data file reads."""
import hashlib,json,os,stat,subprocess,sys
from pathlib import Path

TARGET='/var/run/mysqld/mysqld.sock'
def docker(*a):return subprocess.check_output(['docker','--context','default',*a],text=True,timeout=20)
def covers(p,roots):return any(p==r or p.is_relative_to(r) for r in roots)
def containers():
    fmt='{"Name":{{json .Name}},"State":{{json .State}},"Mounts":{{json .Mounts}}}'
    return [json.loads(docker('inspect','--format',fmt,c)) for c in docker('ps','-aq').split()]
def main():
    role,oldfile,out=sys.argv[1:];out=Path(out)
    assert os.geteuid()==0 and role in ('APP','LOAD')
    assert out.is_absolute() and out.parent.resolve()==out.parent and not out.exists()
    old=set()
    if role=='APP':
        raw=Path(oldfile).read_bytes()
        assert hashlib.sha256(raw).hexdigest()=='032e231e7e529d7466451ff3eb4f5d45515f5f61ff944bbc274a1df0eed2fc86'
        old={v['Name'] for v in json.loads(raw)['volumes']}
    dirs=[Path('/root/t44-final-20261029')] if role=='APP' else sorted(p for p in Path('/root').iterdir() if p.name.lower().startswith('t44') and p.is_dir() and not p.is_symlink())
    roots=list(dirs);vols=[];mysql=set();bad=[];sizes=[];required=[];omissions=[]
    fmt='{"Name":{{json .Name}},"Mountpoint":{{json .Mountpoint}},"Labels":{{json .Labels}}}'
    for name in docker('volume','ls','-q').split():
        a=json.loads(docker('volume','inspect','--format',fmt,name));labels=a['Labels'] or {};project=labels.get('com.docker.compose.project')
        if not (name.startswith('t44') or (project or '').startswith('t44')) or name in old:continue
        p=Path(a['Mountpoint']);assert p==Path('/var/lib/docker/volumes')/name/'_data'
        roots.append(p);vols.append({'name':name,'project':project})
        if labels.get('com.docker.compose.volume')=='mysql_data':mysql.add(p)
    assert roots and len(set(roots))==len(roots) and not covers(out,roots)
    for c in containers():
        for m in c['Mounts']:
            if m.get('Type') not in ('bind','volume') or not m.get('Source'):continue
            p=Path(m['Source'])
            if c['State']['Running'] and (covers(p,roots) or any(r.is_relative_to(p) for r in roots)):bad.append(['RUNNING_REFERENCE',c['Name'],str(p)])
            if m.get('RW') and (role=='LOAD' or 't44' in c['Name'].lower() or 't44' in str(p).lower()) and not covers(p,roots) and not (role=='APP' and (covers(p,[Path('/root/t44-r9'),Path('/root/t44-r30')]) or m.get('Name') in old)):
                bad.append(['UNCOVERED_RW_MOUNT',c['Name'],str(p)])
    for root in roots:
        assert root.resolve()==root and root.is_dir()
        dev=root.stat().st_dev;stack=[root];seen=set();allocated=logical=count=0;first=None
        while stack:
            p=stack.pop();s=p.lstat();count+=1;k=(s.st_dev,s.st_ino)
            if k not in seen:allocated+=s.st_blocks*512;logical+=s.st_size;seen.add(k)
            if p.name=='backup-selection.private.json':bad.append(['DUPLICATE_SELECTION',str(p)])
            if stat.S_ISLNK(s.st_mode):
                target=os.readlink(p)
                if p.parent in mysql and p.name=='mysql.sock' and target==TARGET:omissions.append({'path':str(p),'target':target,'reason':'stopped MySQL runtime socket symlink'})
                elif Path(target).is_absolute() or '..' in Path(target).parts:bad.append(['UNSAFE_LINK',str(p)])
            elif stat.S_ISDIR(s.st_mode):
                if s.st_dev!=dev:bad.append(['NESTED_MOUNT',str(p)]);continue
                stack.extend(Path(e.path) for e in os.scandir(p))
            elif stat.S_ISREG(s.st_mode):
                if first is None:first=str(p)
            else:bad.append(['SPECIAL_FILE',str(p)])
        if first:required.append(first)
        sizes.append({'root':str(root),'entries':count,'allocated_bytes':allocated,'logical_bytes':logical})
    key=Path('/root/t44-r9/r29-load-key-01/load-only-private.pem')
    if role=='LOAD':
        if not covers(key,roots) or not key.exists() or not stat.S_ISREG(key.lstat().st_mode):bad.append(['LOAD_KEY_NOT_COVERED'])
        else:required.append(str(key))
    os.umask(0o077);out.mkdir(mode=0o700)
    def save(n,v):
        with (out/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
        (out/n).chmod(0o600)
    save('preflight.private.json',{'metadata_only':True,'problems':bad,'sizes':sizes,'runtime_link_omissions':omissions})
    save('selection.draft.private.json',{'kind':'root-approved-APP-backup-selection-v1','role':role,'root_approved':False,'absolute_cost_cutoff_utc':'2026-10-29T19:50:00Z','directories':list(map(str,dirs)),'volumes':vols,'restore_required_files':sorted(set(required)),'runtime_link_omissions':omissions,'preflight_problem_count':len(bad),'old_APP_cipher_sha256':'ca7fdb08f01bbdace49421899f74e6630062606aa74c92ba3c97dd484e891fe9' if role=='APP' else None})
    print(json.dumps({'role':role,'directories':len(dirs),'volumes':len(vols),'problems':len(bad),'metadata_only':True,'root_approved':False}))
    sys.exit(bool(bad))
if __name__=='__main__':main()
