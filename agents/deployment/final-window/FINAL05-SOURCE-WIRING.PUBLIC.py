"""Finalize new90b source wiring only from actual reviewed build/profile and QA public approvals."""
import argparse,ast,hashlib,json,os,re
from pathlib import Path
NEW='90b734f65ce6ee9f5c217e885bc7ea4857e32b48';OLD='356f29983c904e949245aedfad464efc1bf7b63d'
TEMPLATE_PINS={'F04-CONTINUOUS.PUBLIC.py': '2a9084a085f880da86428b04bf15149ce9fed67eadd74ace2cb1cdf3775df7c5', 'P04-CONTINUOUS.PUBLIC.py': '7e662ad294cbadc146f6f8ed4fcfb79d4048077eb25eeab0428ad7d81085464d', 'F04-TRANSPORT-APP.PUBLIC.py': 'c9a600a583de51885c6d57461e61955bda5fcb0348051537c964cc64b558f66e', 'F04-TRANSPORT-LOAD.PUBLIC.py': '8774d8f68a19db5dfe7742378a9f32c9912f9610fde8353879473ff0053bdb34', 'P04-TRANSPORT-APP.PUBLIC.py': '8f15a8e4487ffc51097f411141a66dd4f05f87cb5d1f9d3537e34ed39592dfce', 'P04-TRANSPORT-LOAD.PUBLIC.py': 'f7215ee85f5f6229bdf6ba6c82d4870b52b8369a4df4eedf84bff24e76a50006', 'final-app-prepare-resume04.py': 'd3a02f332d577e5e66738ebe279983447a7fb56481e88bd876ec42779e403b25', 'final-timeplan-resume04.py': '524c65ab7713a6d4581f452147a655a591c67a6de0793c8d122dff1e83e816dd', 'final-transport-profile.py': 'b3d4f734c83f55975d25ff3a09f1463d61b8e3b943e9991021cfa861dc2d3e2b', 'final-f-operator.py': '69bd7b3fb8382467b8baf514e43eee274d8653df7aa4ea6568a6c7bd0bf9bfdc'}
OLD_CODE='023063c342854c7b2bea107774007fcd89973a4d0ab85f5841db31a6a8cb2a5e';OLD_PROFILE='ce3975d1fb5e6f219467fa61cdd0386a182851145993a2a4cf5300688a5cbe5c';OLD_BUNDLE='1ddafb7aaa1c552172cc5a0c0f48881412a8fa1fabbb400037854f4bba77a6a2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,raw):
 if isinstance(raw,str):raw=raw.encode()
 if p.suffix=='.py':ast.parse(raw,feature_version=(3,10))
 with p.open('xb') as f:f.write(raw)
 p.chmod(0o600)
def encoded(o):return json.dumps(o,sort_keys=True,indent=2)+'\n'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['tools','producer','package','source-profile','qa-adapter','qa-target-template','qa-approval','output-code']:p.add_argument('--'+n,type=Path,required=True)
 for n in ['source-profile-sha256','qa-adapter-sha256','qa-target-template-sha256','qa-approval-sha256']:p.add_argument('--'+n,required=True)
 a=p.parse_args();os.umask(0o077)
 for path,pin in [(a.source_profile,a.source_profile_sha256),(a.qa_adapter,a.qa_adapter_sha256),(a.qa_target_template,a.qa_target_template_sha256),(a.qa_approval,a.qa_approval_sha256)]:
  if path.is_symlink() or sha(path)!=pin:raise ValueError('NEW_ORIGINAL_RAW_PIN_REQUIRED')
 profile=read(a.source_profile);bundle=read(a.package/'backend-bundle-manifest.json');sm=read(a.package/'source-manifest.json')
 if (profile.get('root_approved') is not True or profile['source_sha']!=NEW or bundle['source_sha']!=NEW or sm['source_sha']!=NEW or profile['backend_bundle_manifest_sha256']!=sha(a.package/'backend-bundle-manifest.json') or profile['source_manifest_sha256']!=sha(a.package/'source-manifest.json') or profile['qa_adapter_sha256']!=a.qa_adapter_sha256 or profile['qa_approval_receipt_sha256']!=a.qa_approval_sha256):raise ValueError('ACTUAL_NEW90B_BUILD_PROFILE_AND_QA_APPROVAL_REQUIRED')
 # Keep exact original18 producer set and verify every preimage; only guard source/adapter and actual public build manifests change.
 manifest=read(a.producer/'code-manifest.PUBLIC.json')
 if sha(a.producer/'code-manifest.PUBLIC.json')!=OLD_CODE or len(manifest['files'])!=18:raise ValueError('EXACT_ORIGINAL18_REQUIRED')
 files={}
 for name,pin in manifest['files'].items():
  path=a.producer/name;raw=path.read_bytes()
  if sha(path)!=pin or len(raw)!=manifest['file_sizes'][name]:raise ValueError('ORIGINAL18_PREIMAGE_CHANGED')
  files[name]=raw
 guard=files['guard.py'].decode();oldsource='SOURCE = "'+OLD+'"';oldadapter='NEW_ADAPTER = "15b91449627218b011fff0768b1f84fe2e9274ec06c0486fd28f2ae9dce03f5d"'
 if guard.count(oldsource)!=1 or guard.count(oldadapter)!=1:raise ValueError('EXACT_TWO_GUARD_CONSTANT_PREIMAGES_REQUIRED')
 files['guard.py']=guard.replace(oldsource,'SOURCE = "'+NEW+'"').replace(oldadapter,'NEW_ADAPTER = "'+a.qa_adapter_sha256+'"').encode()
 target=json.loads(files['TARGET_753.template.json']);ref=target['load_runtime_identity_reference'];ref['qa_adapter_sha256']=a.qa_adapter_sha256;ref['qa_target_template_sha256']=a.qa_target_template_sha256
 files['TARGET_753.template.json']=encoded(target).encode()
 for name in ['source-manifest.json','backend-bundle-manifest.json']:files[name]=(a.package/name).read_bytes()
 newmanifest={**manifest,'source_sha':NEW,'files':{n:hashlib.sha256(v).hexdigest() for n,v in files.items()},'file_sizes':{n:len(v) for n,v in files.items()},'derived_from_original18_manifest_sha256':OLD_CODE,'actual_cloud_SUT_sessions':0}
 if a.output_code.exists() or not a.output_code.is_absolute():raise ValueError('NEW_ABSOLUTE_PRODUCER_DIRECTORY_REQUIRED')
 a.output_code.mkdir(mode=0o700)
 for n,v in files.items():put(a.output_code/n,v)
 put(a.output_code/'code-manifest.PUBLIC.json',encoded(newmanifest));codepin=sha(a.output_code/'code-manifest.PUBLIC.json')
 tools=a.tools
 for name,pin in TEMPLATE_PINS.items():
  if sha(tools/name)!=pin:raise ValueError('EXACT_REVIEWED_TEMPLATE_PIN_REQUIRED:'+name)
 texts={n:(tools/n).read_text() for n in ['F04-CONTINUOUS.PUBLIC.py','P04-CONTINUOUS.PUBLIC.py','F04-TRANSPORT-APP.PUBLIC.py','F04-TRANSPORT-LOAD.PUBLIC.py','P04-TRANSPORT-APP.PUBLIC.py','P04-TRANSPORT-LOAD.PUBLIC.py','final-app-prepare-resume04.py','final-timeplan-resume04.py','final-transport-profile.py']}
 outputs={}
 for n,text in texts.items():
  newname=n.replace('F04','F05').replace('P04','P05').replace('resume04','resume05')
  if n=='final-transport-profile.py':newname='final-transport-profile05.py';text=text.replace(OLD,NEW)
  if 'TRANSPORT-' in n:text=text.replace('final-transport-profile.py','final-transport-profile05.py')
  if 'CONTINUOUS' in n:
   text=text.replace(OLD_PROFILE,a.source_profile_sha256).replace(OLD_BUNDLE,profile['backend_bundle_manifest_sha256']).replace(OLD_CODE,codepin)
   text=text.replace("ROOT/'source-profile.root-approved.PUBLIC.json'",'Path('+repr(str(a.source_profile))+')').replace("R/'source-profile.root-approved.PUBLIC.json'",'Path('+repr(str(a.source_profile))+')')
   text=text.replace("CODE=OPS/'agents/backend/neutral-final-20261029'",'CODE=Path('+repr(str(a.output_code))+')').replace("C=R/'ops01/agents/backend/neutral-final-20261029'",'C=Path('+repr(str(a.output_code))+')')
   # Both old launchers have exact CODE/profile assignments above; assert no stale source-profile constant remains.
   text=text.replace('final-app-prepare-resume04.py','final-app-prepare-resume05.py').replace("R/'boot01/official'",'Path('+repr(str(a.package))+')')
   text=text.replace('r30finalf04','r30finalf05').replace('r30finalp04','r30finalp05').replace("ROOT/'F04'","ROOT/'F05'").replace("R/'F04/preparation.PUBLIC.json'","R/'F05/preparation.PUBLIC.json'").replace("R/'P04'","R/'P05'")
   text=text.replace('F04-TRANSPORT-APP.PUBLIC.py','F05-TRANSPORT-APP.PUBLIC.py').replace('P04-TRANSPORT-APP.PUBLIC.py','P05-TRANSPORT-APP.PUBLIC.py')
   text=text.replace("'source_sha':'"+OLD+"'","'source_sha':'"+NEW+"'")
   if n.startswith('F04'):
    text=text.replace("('F02','F03')","('F02','F03','F04')")
    marker='    if not args.after_phase:\n'
    extra='''    if not args.after_phase:
        previous=ROOT/'P04/preparation.PUBLIC.json'
        if previous.exists():
            p=json.loads(previous.read_bytes())['phase'];pd=Path(p['phase_dir']);pv=json.loads((pd/'binding.json').read_bytes())
            if sha(pd/'binding.json')!=p['binding_sha256'] or pv['project']!='t44-cloud-r30finalp04-p' or pv['source_sha']!='__OLD__' or sha(pd/'controller.py')!=pv['file_hashes']['controller.py']:raise ValueError('EXACT_OLD_P04_OWNER_REQUIRED')
            run('stop-old-P04',['python3',pd/'controller.py','stop','--phase-dir',pd,'--binding-sha256',p['binding_sha256']],180)
            if subprocess.run(['docker','--context','default','ps','--quiet','--filter','label=com.docker.compose.project='+pv['project']],capture_output=True,check=True,timeout=20).stdout.strip():raise ValueError('OLD_P04_STILL_RUNNING')
'''.replace('__OLD__',OLD)
    text=text.replace(marker,extra,1)
  if n=='final-app-prepare-resume04.py':text=text.replace('final-timeplan-resume04.py','final-timeplan-resume05.py')
  # Defaults and F/P references in each transport only; they never alter old files.
  if 'TRANSPORT-' in n:text=text.replace("BASE/'F04'","BASE/'F05'").replace("BASE/'P04'","BASE/'P05'")
  outputs[newname]=text
 operator=(tools/'final-f-operator.py').read_text()
 if operator.count('not requested <= now < end <= requested + 180:')!=1:raise ValueError('EXACT_ORIGINAL_OPERATOR_PRECISION_PREIMAGE_REQUIRED')
 outputs['final-f-operator05.py']=operator.replace('not requested <= now < end <= requested + 180:','not requested <= now < end <= requested + 180.001:')
 for n,text in outputs.items():put(tools/n,text)
 receipt={'status':'NEW90B_SOURCE_WIRING_PREPARED_NO_CLOUD_START','source_sha':NEW,'source_profile_sha256':a.source_profile_sha256,'producer_manifest_sha256':codepin,'producer':str(a.output_code),'tools':{n:sha(tools/n) for n in outputs},'qa_public_pins':{'adapter':a.qa_adapter_sha256,'target':a.qa_target_template_sha256,'approval':a.qa_approval_sha256},'old_F04_P04_unchanged':True}
 put(tools/'final05-wiring.PUBLIC.json',encoded(receipt));print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
