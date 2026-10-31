"""Freeze exact source/bundle hashes into an exclusive offline material-tool release."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

SOURCE='bcec3326b40814fdb1922bbfea7c29473b47ba47'
HERE=Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def freeze(source_path,bundle_path,output,repo):
    for path in (source_path,bundle_path):
        if path.is_symlink() or not path.is_file() or path.stat().st_size>16*1024*1024:
            raise ValueError('BOUNDED_ORIGINAL_MANIFEST_REQUIRED')
    source_raw,bundle_raw=source_path.read_bytes(),bundle_path.read_bytes()
    source,bundle=json.loads(source_raw),json.loads(bundle_raw)
    if not(source['source_sha']==bundle['source_sha']==SOURCE
           and bundle['kind']=='final-backend-web-bundle-v1'
           and bundle['source_manifest_sha256']==sha(source_raw)
           and bundle['files']['source-manifest.json']['sha256']==sha(source_raw)
           and bundle['files']['source-manifest.json']['bytes']==len(source_raw)):
        raise ValueError('EXACT_NEW_SOURCE_BUNDLE_BYTES_REQUIRED')
    archive=subprocess.run(['git','-C',str(repo),'archive',SOURCE,'backend/t44','backend/requirements.lock','backend/pyproject.toml'],capture_output=True,check=True,timeout=20).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        expected={m.name:{'sha256':sha(tar.extractfile(m).read()),'bytes':m.size,'mode':0o755 if m.mode & 0o111 else 0o644} for m in tar.getmembers() if m.isfile()}
    rows=source['backend_runtime_files']
    actual={r['path']:{k:r[k] for k in ['sha256','bytes','mode']} for r in rows}
    if len(actual)!=len(rows) or actual!=expected:
        raise ValueError('COMPLETE_EXACT_GIT_SOURCE_RUNTIME_BYTES_REQUIRED')
    image=bundle['images']['backend'];proof=bundle['ci_image_proofs']['backend']
    if not(image['revision_label']==SOURCE and image['architecture']=='amd64' and image['os']=='linux'
           and image['image_id']==proof['config_id']==proof['actual_id'] and proof['success'] is True):
        raise ValueError('EXACT_NEW_BACKEND_CONFIG_PROOF_REQUIRED')
    if output.is_symlink() or output.exists() or output.parent.resolve()!=output.parent:
        raise ValueError('EXCLUSIVE_CANONICAL_NEW_RELEASE_REQUIRED')
    output.mkdir(mode=0o700)
    # A partial prefix is intentionally retained on failure; never overwrite/retry it.
    replacements={'__SOURCE_MANIFEST_SHA256__':sha(source_raw),'__BUNDLE_MANIFEST_SHA256__':sha(bundle_raw)}
    files={}
    for path in sorted(HERE.iterdir()):
        if path.suffix!='.py' and path.name!='authorization.TEMPLATE.json':continue
        if path.name in {'offline_checks.py'}:continue
        raw=path.read_bytes()
        if path.name=='refresh_core.py':
            text=raw.decode()
            for old,new in replacements.items():
                if text.count(old)!=1:raise ValueError('EXACT_UNFROZEN_TEMPLATE_REQUIRED')
                text=text.replace(old,new)
            raw=text.encode()
        with (output/path.name).open('xb') as f:f.write(raw)
        files[path.name]={'bytes':len(raw),'sha256':sha(raw)}
    receipt={'status':'OFFLINE_RELEASE_FROZEN_LIVE_ADMISSION_PENDING','source_sha':SOURCE,'source_manifest_sha256':sha(source_raw),'bundle_manifest_sha256':sha(bundle_raw),'backend_config':image['image_id'],'files':files,'cloud_calls':0,'sessions_issued':False,'grant_allow':False}
    with (output/'RELEASE.PUBLIC.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['source-manifest','bundle-manifest','output','repo']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();receipt=freeze(a.source_manifest,a.bundle_manifest,a.output,a.repo)
    print(json.dumps(receipt))
if __name__=='__main__':main()
