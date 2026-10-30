"""Build a new offline p13 continuation from exact reviewed public source bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(original, output, previous_prefix):
    assert original.is_absolute() and original.resolve()==original
    assert output.is_absolute() and not output.exists() and output.parent.resolve()==output.parent
    old=json.loads((original/'MANIFEST.PUBLIC.json').read_bytes())
    # Verify every supplied original file before output, including historical wrapper.
    for name,row in old['files'].items():
        p=original/name
        assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(original)
        assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
    assert previous_prefix.is_absolute() and previous_prefix.resolve()==previous_prefix and not previous_prefix.is_symlink()
    assert sha(previous_prefix)=='e485eabd7cc3c436e60545dba885c0e235e0bed3d69c7dd5eb5d4617255a6f7f'
    output.mkdir(mode=0o700)
    paths={name:original/name for name in old['files'] if name not in ['RUNBOOK.md','run/manual13-resume-prepare.py']}
    paths['provenance/STOPPED06-PREFIX.PUBLIC.json']=previous_prefix
    paths.update({'run/manual13-resume07-prepare.py':ROOT/'deployment/cloud-reuse/manual13-resume07-prepare.py',
                  'deployment/prepare_next_manual.py':ROOT/'deployment/cloud-reuse/prepare07-next-manual.py',
                  'run/manual13-observe.py':ROOT/'deployment/cloud-reuse/manual13-observe.py',
                  'RUNBOOK.md':ROOT/'agents/deployment/manual13-retest/P13_07_RUNBOOK.md',
                  'deployment/manual13-retest/check_ssh_window.py':ROOT/'deployment/cloud-reuse/manual13-retest/check_ssh_window.py'})
    for name in ('pin_ssh_host.py','update_ssh_addresses.py'):
        paths['deployment/ssh-reconnect/'+name]=ROOT/'deployment/cloud-reuse/ssh-reconnect'/name
    for name,source in paths.items():
        dest=output/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    files={name:{'sha256':sha(output/name),'bytes':(output/name).stat().st_size}for name in sorted(paths)}
    manifest={'kind':'P13_STORAGE_ONLY_MATERIAL07_CONTINUATION','status':'OFFLINE_CHECKED_LIVE_GATES_PENDING',
      'executed':False,'contains_accounts_tokens_or_keys':False,'distribution':'RESTRICTED_RUNTIME_PACKAGE_CONTAINS_INTERNAL_TOPOLOGY','product_source':old['product_source'],
      'applied_index_layout_sha256':old['applied_index_layout_sha256'],
      'qa_run':'r30manualp13','material_run':'r30materialresume07','maintenance_run':'r30restoretransition07',
      'original_manifest_sha256':sha(original/'MANIFEST.PUBLIC.json'),'files':files}
    (output/'MANIFEST.PUBLIC.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return {'directory':str(output),'files':len(files),'manifest_sha256':sha(output/'MANIFEST.PUBLIC.json')}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('original',type=Path);p.add_argument('output',type=Path);p.add_argument('--previous-prefix',required=True,type=Path);a=p.parse_args();print(json.dumps(build(a.original,a.output,a.previous_prefix)))
