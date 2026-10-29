python3 - <<'PY'
import base64,gzip,hashlib,json,os,pathlib,stat
root=pathlib.Path('/root/t44-r9/p790-f7-2000-ui03')
bundle='2af6444892171c1004474379dff699f3ede876c6e7d55e85b72125cbce4626de'
first=False
final=False
data=json.loads(gzip.decompress(base64.b64decode('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',validate=True)))
def sha(raw): return hashlib.sha256(raw).hexdigest()
def write(path,raw,mode):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    os.fchmod(fd,mode)
    try:
        with os.fdopen(fd,'wb',closefd=False) as out:
            out.write(raw);out.flush();os.fsync(fd)
    finally: os.close(fd)
if first:
    root.mkdir(mode=0o755)
    root.chmod(0o755)
    write(root/'install-bundle.PUBLIC.json',(json.dumps({'bundle_sha256':bundle},sort_keys=True)+'\n').encode(),0o444)
assert root.is_dir() and not root.is_symlink() and root.resolve()==root
assert json.loads((root/'install-bundle.PUBLIC.json').read_text())=={'bundle_sha256':bundle}
installed=[]
for name,item in data.items():
    assert not pathlib.PurePosixPath(name).is_absolute() and '..' not in pathlib.PurePosixPath(name).parts and name in ['790_bootstrap.py', '790_host.py', '790_load.py', '790_budget.py', '790_producer.py', '790_consumer.py', '790_receive.py', 'data/790_select.py', 'data/790_stage1.py', 'edge/790_http.py', 'edge/790_stage2.py', 'edge/790_authority.py', 'transport/790_transfer.py', 'manifest.json']
    target=root/name
    target.parent.mkdir(parents=True,exist_ok=True)
    assert target.parent.resolve()==target.parent
    target.parent.chmod(0o755)
    raw=item['text'].encode('utf-8')
    assert sha(raw)==item['sha256']
    write(root/name,raw,0o444)
    installed.append({'name':name,'sha256':sha(raw),'bytes':len(raw)})
if final:
    raw=(root/'manifest.json').read_bytes();assert sha(raw)==bundle
    for name,item in json.loads(raw)['files'].items():
        path=root/name;assert path.is_file() and not path.is_symlink()
        assert sha(path.read_bytes())==item['sha256'] and path.stat().st_size==item['bytes']
        assert stat.S_IMODE(path.stat().st_mode)==0o444
print(json.dumps({'kind':'PUBLIC_SCOPE_BRIDGE_INSTALL','bundle_sha256':bundle,'installed':installed,'all_thirteen_verified':final,'no_SUT_or_cloud_action':True},sort_keys=True))
PY
