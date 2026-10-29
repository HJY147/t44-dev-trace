"""Before P07 first freeze: root-owned same-byte service staging and actual90b manifest paths."""
import argparse,ast,hashlib,json,os
from pathlib import Path
R=Path('/root/t44-final-20261029');T=R/'ops01/deployment/cloud-reuse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--launcher-sha256',required=True);p.add_argument('--package',type=Path,required=True);a=p.parse_args();os.umask(0o077);original=T/'P07-CONTINUOUS-fast10.PUBLIC.py'
 if (R/'P07').exists() or (R/'r30finalp07-launcher').exists():raise ValueError('BEFORE_FIRST_P07_FREEZE_ONLY')
 if sha(original)!=a.launcher_sha256:raise ValueError('EXACT_NEW_P07_LAUNCHER_PREIMAGE_REQUIRED')
 text=original.read_text();tree=ast.parse(text);n=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROFILE' for t in n.targets));profile_path=Path(ast.literal_eval(n.value.args[0]));profile=json.loads(profile_path.read_bytes())
 if sha(profile_path)!='346d19344281b9e02046a27cf9d24f07ebceb9c8f920105a981d7bfdc056ac1f':raise ValueError('EXACT_APPROVED90B_PROFILE_REQUIRED')
 package=a.package
 if not package.is_absolute() or package.resolve()!=package or package.is_symlink() or sha(package/'backend-bundle-manifest.json')!=profile['backend_bundle_manifest_sha256']:raise ValueError('EXACT_EXPLICIT_ACTUAL90B_PACKAGE_REQUIRED')
 for name,key in [('source-manifest.json','source_manifest_sha256'),('backend-bundle-manifest.json','backend_bundle_manifest_sha256')]:
  if sha(package/name)!=profile[key]:raise ValueError('ACTUAL90B_MANIFEST_SHA_REQUIRED')
  old="R/'boot01/official/"+name+"'"
  if text.count(old)!=1:raise ValueError('EXACT_OLD_PACKET_MANIFEST_PATH_PREIMAGE_REQUIRED:'+name)
  text=text.replace(old,'Path('+repr(str(package/name))+')')
 marker=" httpplan=inputs/'http-plan.json';save(httpplan,plan)"
 copy=''' # The official service producer output is owned by10001. Preserve it and stage an exact-byte root-owned input for the strict host reader.
 service_source=Path(service['output']);st=service_source.lstat()
 import stat
 if service_source.resolve()!=service_source or not stat.S_ISREG(st.st_mode) or st.st_uid!=10001 or stat.S_IMODE(st.st_mode)!=0o600 or st.st_nlink!=1 or st.st_size>4*1024*1024:raise ValueError('EXACT_ORIGINAL_SERVICE_RESULT_OWNER_MODE_REQUIRED')
 original_service_bytes=service_source.read_bytes();service_root=inputs/'service.original-root-copy.private.json'
 with service_root.open('xb') as rootcopy:rootcopy.write(original_service_bytes)
 service_root.chmod(0o600)
 if service_root.stat().st_uid!=os.geteuid() or sha(service_root)!=sha(service_source):raise ValueError('EXACT_SAME_BYTES_ROOT_INPUT_COPY_REQUIRED')
 save(inputs/'service-root-copy.PUBLIC.json',{'original_path':str(service_source),'original_uid':st.st_uid,'original_mode':stat.S_IMODE(st.st_mode),'copy_path':str(service_root),'copy_uid':service_root.stat().st_uid,'sha256':sha(service_root),'same_original_bytes':True,'sessions_modified':False})
'''
 if text.count(marker)!=1 or text.count("'--service',service['output']")!=1:raise ValueError('EXACT_HTTP_SERVICE_COPY_SEAM_REQUIRED')
 text=text.replace(marker,copy+marker).replace("'--service',service['output']","'--service',service_root")
 ast.parse(text,feature_version=(3,10));dest=T/'P07-CONTINUOUS-copyfix.PUBLIC.py'
 with dest.open('x') as f:f.write(text)
 dest.chmod(0o600)
 print(json.dumps({'status':'P07_SAME_BYTE_HOST_INPUT_AND_SOURCE_MANIFEST_FIX_PREPARED_NOT_FROZEN','launcher':str(dest),'sha256':sha(dest),'original_launcher_sha256':a.launcher_sha256,'source_manifest_sha256':profile['source_manifest_sha256'],'bundle_manifest_sha256':profile['backend_bundle_manifest_sha256']}))
if __name__=='__main__':main()
