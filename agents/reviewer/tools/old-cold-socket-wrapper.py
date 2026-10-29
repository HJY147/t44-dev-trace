"""Root-approved exact stale runtime-link omissions; original crypto/verify unchanged."""
import importlib.util,json,os,stat,sys
from pathlib import Path

TARGET='/var/run/mysqld/mysqld.sock'
def links(paths):
    for p in paths:
        assert stat.S_ISLNK(p.lstat().st_mode) and os.readlink(p)==TARGET,str(p)

def tar_argv(argv,omissions):
    links(omissions)
    i=argv.index('--')
    return argv[:i]+['--anchored','--no-wildcards']+['--exclude='+str(p).lstrip('/') for p in omissions]+argv[i:]

def main():
    base,draft,cert,certsha,out,approval=sys.argv[1:]
    assert approval=='APPROVE_EXACT_13_STALE_LINKS' and os.geteuid()==0
    base,draft,cert,out=map(Path,(base,draft,cert,out))
    import hashlib
    assert hashlib.sha256(base.read_bytes()).hexdigest()=='677a44f1bf90735bdf2a7cf71084621882828a967eb06f3c400e6ca2ac5f4a01'
    spec=importlib.util.spec_from_file_location('original_backup',base)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.regular(draft,'3ce5b28f7dfe3110978a625cefbebba5516636b2b4040ea2c566d3745f542899',private=True)
    s=json.loads(draft.read_bytes())
    assert s['root_approved'] is False and len(s['volumes'])==26
    assert s['directories']==['/root/t44-r9','/root/t44-r30']
    s['root_approved']=True
    roots=m.checked_inventory(s)
    omitted=[]
    for v,p in zip(s['volumes'],roots[2:]):
        a=m.inspect(['volume','inspect',v['name']])[0]
        assert p==Path('/var/lib/docker/volumes')/v['name']/'_data'
        if a['Labels'].get('com.docker.compose.volume')=='mysql_data':
            assert v['name'].endswith('_mysql_data')
            omitted.append(p/'mysql.sock')
    assert len(omitted)==13
    links(omitted)
    s['runtime_link_omissions']=[{'path':str(p),'target':TARGET,'reason':'stopped MySQL runtime socket symlink; not database data'} for p in omitted]
    selection=out.parent/(out.name+'.selection.private.json')
    m.checked_output(selection,roots);m.checked_output(out,roots)
    m.save(selection,s)
    original=m.tar_command
    m.tar_command=lambda paths:tar_argv(original(paths),omitted)
    sys.argv=[str(base),'backup','--inventory',str(selection),'--inventory-sha256',m.sha(selection),'--recipient-cert',str(cert),'--recipient-cert-sha256',certsha,'--output',str(out)]
    m.main()
    m.save(out/'runtime-link-omissions.PUBLIC.json',{'original_backup_receipt_sha256':m.sha(out/'backup.PUBLIC.json'),'selection_sha256':m.sha(selection),'omissions':s['runtime_link_omissions'],'original_backup_script_sha256':m.sha(base)})

if __name__=='__main__':main()
