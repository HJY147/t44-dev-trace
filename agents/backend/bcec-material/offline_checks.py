"""Synthetic local release freezing only, no Docker/HTTP/VM or real admission."""
import copy
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
import freeze_release as f

REPO=Path(__file__).resolve().parents[3]
class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  raw=subprocess.check_output(['git','-C',str(REPO),'archive',f.SOURCE,'backend/t44','backend/requirements.lock','backend/pyproject.toml','specs/contracts','specs/database','deployment/runtime_probe.py','deployment/credential_admin.py'])
  with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
   files=[{'path':m.name,'bytes':m.size,'sha256':f.sha(tar.extractfile(m).read()),'mode':0o755 if m.mode&0o111 else 0o644} for m in tar.getmembers() if m.isfile()]
  self.source={'source_sha':f.SOURCE,'backend_runtime_files':files}
  self.source_path=self.root/'source.json';self.bundle_path=self.root/'bundle.json'
  self.config='sha256:'+'7'*64
 def write(self,source=None,bundle_change=None):
  self.source_path.write_text(json.dumps(self.source if source is None else source))
  bundle={'source_sha':f.SOURCE,'kind':'final-backend-web-bundle-v1','source_manifest_sha256':f.sha(self.source_path.read_bytes()),'files':{'source-manifest.json':{'sha256':f.sha(self.source_path.read_bytes()),'bytes':self.source_path.stat().st_size}},'images':{'backend':{'revision_label':f.SOURCE,'architecture':'amd64','os':'linux','image_id':self.config}},'ci_image_proofs':{'backend':{'config_id':self.config,'actual_id':self.config,'success':True}}}
  if bundle_change:bundle_change(bundle)
  self.bundle_path.write_text(json.dumps(bundle))
 def test_actual_git_bytes_synthetic_bundle_freeze_and_exclusive(self):
  self.write();out=self.root/'release';receipt=f.freeze(self.source_path,self.bundle_path,out,REPO)
  self.assertEqual(receipt['source_sha'],f.SOURCE)
  core=(out/'refresh_core.py').read_text();self.assertNotIn('__SOURCE_MANIFEST_SHA256__',core);self.assertIn(f.sha(self.source_path.read_bytes()),core)
  auth=json.loads((out/'authorization.TEMPLATE.json').read_text());self.assertIs(auth['root_approved'],False);self.assertIsNone(auth['packet_nonce']);self.assertEqual(auth['qa_run_id'],'r30manualp15')
  with self.assertRaises(ValueError):f.freeze(self.source_path,self.bundle_path,out,REPO)
 def test_omitted_duplicate_modified_source_rejected(self):
  for kind in ['omit','duplicate','modify']:
   source=copy.deepcopy(self.source)
   if kind=='omit':source['backend_runtime_files'].pop()
   elif kind=='duplicate':source['backend_runtime_files'].append(source['backend_runtime_files'][0])
   else:source['backend_runtime_files'][0]['sha256']='0'*64
   self.write(source)
   with self.subTest(kind=kind),self.assertRaises(ValueError):f.freeze(self.source_path,self.bundle_path,self.root/'never',REPO)
   self.assertFalse((self.root/'never').exists())
 def test_old_source_and_mismatched_config_rejected(self):
  for change in [lambda b:b.update(source_sha='13acb43a804e717e7485091895378511fe3d9b76'),lambda b:b['ci_image_proofs']['backend'].update(actual_id='sha256:'+'8'*64)]:
   self.write(bundle_change=change)
   with self.assertRaises(ValueError):f.freeze(self.source_path,self.bundle_path,self.root/'never',REPO)
 def test_template_false_and_consumed_ids_refused(self):
  import refresh_core as core
  template=json.loads((f.HERE/'authorization.TEMPLATE.json').read_text())
  with self.assertRaises(ValueError):core.authorization(template,b'{}')
  old={'identity':{'git_commit':core.HISTORY_SOURCE},'run_id':'r30materialresume07','additional_neutral_snapshots':{'database':'test','namespace':'test'}}
  old['binding_sha256']=core.sha(core.canonical(old));raw=core.canonical(old)
  auth={**template,'root_approved':True,'old_packet_sha256':core.sha(raw),'packet_nonce':'a'*64,'database':'test','namespace':'test'}
  self.assertEqual(core.authorization(auth,raw),old)
  for field,value in [('qa_run_id','r30manualp14'),('new_packet_run_id','r30materialresume08'),('maintenance_id','r30restoretransition08')]:
   with self.subTest(field=field),self.assertRaises(ValueError):core.authorization({**auth,field:value},raw)
 def test_raw_manifest_tamper_rejected(self):
  self.write();self.source_path.write_bytes(self.source_path.read_bytes()+b' ')
  with self.assertRaises(ValueError):f.freeze(self.source_path,self.bundle_path,self.root/'never',REPO)
if __name__=='__main__':unittest.main()
