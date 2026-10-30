"""Pure local new-source admission, original bytes immutable, no Docker or network."""
import copy
import json
import unittest
from pathlib import Path
import refresh_core as c

PACKAGE=Path('/Users/yang/Desktop/nothing/软件开发大作业/.submission-private/build-candidates/locked-task-13ac-20261031')
class Checks(unittest.TestCase):
 def setUp(self):
  self.files={n:(PACKAGE/n).read_bytes() for n in ['source-manifest.json','backend-bundle-manifest.json']}
  bundle=json.loads(self.files['backend-bundle-manifest.json']);config=bundle['images']['backend']['image_id']
  # Synthetic receipt expressly does not represent real APP import.
  receipt={'kind':'final-backend-web-import-v1','source_sha':c.SOURCE,'bundle_manifest_sha256':c.sha(self.files['backend-bundle-manifest.json']),'source_manifest_sha256':c.sha(self.files['source-manifest.json']),'identity':{'config_id':config,'actual_id':config,'success':True},'observed_utc':'2026-01-01T00:00:00Z'}
  self.files['backend-import-receipt.json']=c.canonical(receipt);self.files['ca.pem']=b'synthetic-ca'
  identity={'git_commit':c.SOURCE,'source_manifest_sha256':c.sha(self.files['source-manifest.json']),'backend_bundle_manifest_sha256':c.sha(self.files['backend-bundle-manifest.json']),'sut_image_config_digest':config,'runtime_sha256':'81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf','load_runtime_image_config_digest':'sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1','openapi_sha256':'6'*64}
  self.old={'identity':{**identity,'git_commit':c.HISTORY_SOURCE},'environment':{'ca_sha256':c.sha(self.files['ca.pem'])},'run_id':'r30materialresume07','additional_neutral_snapshots':{'database':'test','namespace':'test'}}
  self.old['binding_sha256']=c.sha(c.canonical(self.old));self.raw=c.canonical(self.old)
  self.auth={'schema':'manual-material-new-source-v2','root_approved':True,'benchmark_grant_allow':False,'operations':c.OPERATIONS,'source_sha':c.SOURCE,'old_packet_sha256':c.sha(self.raw),'new_packet_run_id':'r30materialresume08','qa_run_id':'r30manualp14','maintenance_id':'r30restoretransition08','packet_nonce':'a'*64,'database':'test','namespace':'test','new_identity':identity,'expected_api_image_id':config,'loaded_receipt_reference':{'sha256':c.sha(self.files['backend-import-receipt.json']),'original_path':'/root/SYNTHETIC/receipt','observed_at':receipt['observed_utc']}}
 def test_positive_dual_chain_no_old_rewrite(self):
  self.assertEqual(c.authorization(self.auth,self.raw),self.old);c.validate_new_source(self.auth,self.old,self.files);self.assertEqual(c.canonical(self.old),self.raw)
 def test_default_false_and_consumed_names(self):
  for patch in [{'root_approved':False},{'new_packet_run_id':'r30materialresume07'},{'qa_run_id':'r30manualp13'},{'maintenance_id':'r30restoretransition07'}]:
   with self.subTest(patch=patch),self.assertRaises(ValueError):c.authorization({**self.auth,**patch},self.raw)
 def test_wrong_history(self):
  old=copy.deepcopy(self.old);old['identity']['git_commit']=c.SOURCE
  with self.assertRaises(ValueError):c.authorization(self.auth,c.canonical(old))
 def test_wrong_source_or_receipt_bytes(self):
  for name in ['source-manifest.json','backend-bundle-manifest.json','backend-import-receipt.json']:
   files={**self.files,name:self.files[name]+b' '}
   with self.subTest(name=name),self.assertRaises(ValueError):c.validate_new_source(self.auth,self.old,files)
 def test_wrong_config_or_legacy_runtime(self):
  for key,value in [('sut_image_config_digest','sha256:'+'0'*64),('runtime_sha256','0'*64)]:
   auth=copy.deepcopy(self.auth);auth['new_identity'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):c.validate_new_source(auth,self.old,self.files)
 def test_new_core_cannot_replace_legacy_transport_runtime(self):
  auth=copy.deepcopy(self.auth);auth['new_identity']['runtime_sha256']='9cf747e308969ceba37e2cfcfa6591def45e118ad928c4f310f57b6ecf37542a'
  with self.assertRaises(ValueError):c.validate_new_source(auth,self.old,self.files)
 def test_future_and_non_utc_receipt_refused(self):
  for stamp in ['2099-01-01T00:00:00Z','2026-01-01T00:00:00+08:00','invalid']:
   files=copy.deepcopy(self.files);auth=copy.deepcopy(self.auth);receipt=json.loads(files['backend-import-receipt.json']);receipt['observed_utc']=stamp;files['backend-import-receipt.json']=c.canonical(receipt);auth['loaded_receipt_reference'].update(observed_at=stamp,sha256=c.sha(files['backend-import-receipt.json']))
   with self.subTest(stamp=stamp),self.assertRaises(ValueError):c.validate_new_source(auth,self.old,files)
 def test_import_observation_remote_copy_binding(self):
  import tempfile
  import host_runner as host
  with tempfile.TemporaryDirectory() as tmp:
   receipt=Path(tmp)/'receipt.json';obs=Path(tmp)/'observation.json';raw=self.files['backend-import-receipt.json'];receipt.write_bytes(raw)
   original='/root/SYNTHETIC/receipt'
   observed={'kind':'actual-APP-import-file-observation-v1','receipt_path':original,'receipt_sha256':c.sha(raw),'observed_utc':self.auth['loaded_receipt_reference']['observed_at'],'receipt_bytes':len(raw),'receipt_uid':0,'receipt_mode':384,'receipt_mtime_ns':1}
   obs.write_text(json.dumps(observed))
   self.assertEqual(host.validate_import_observation(self.auth,receipt,obs,remote_path=original),observed)
   with self.assertRaises(ValueError):host.validate_import_observation(self.auth,receipt,obs)
   for patch in [{'original_path':'/root/OLD90B/receipt.json'},{'sha256':'0'*64}]:
    auth=copy.deepcopy(self.auth);auth['loaded_receipt_reference'].update(patch)
    with self.subTest(patch=patch),self.assertRaises(ValueError):host.validate_import_observation(auth,receipt,obs,remote_path=original)
   for key,value in [('receipt_path','/root/OLD90B/receipt.json'),('receipt_bytes',len(raw)+1),('receipt_uid',1),('receipt_mode',420),('receipt_mtime_ns',0)]:
    obs.write_text(json.dumps({**observed,key:value}))
    with self.subTest(field=key),self.assertRaises(ValueError):host.validate_import_observation(self.auth,receipt,obs,remote_path=original)
 def test_new_reference_required(self):
  auth=copy.deepcopy(self.auth);auth['loaded_receipt_reference']['observed_at']='2000-01-01T00:00:00Z'
  with self.assertRaises(ValueError):c.validate_new_source(auth,self.old,self.files)
if __name__=='__main__':unittest.main()
