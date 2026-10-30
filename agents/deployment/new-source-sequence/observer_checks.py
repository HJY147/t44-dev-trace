"""Pure local observer guards with synthetic data; no Docker/network/real sessions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import observe_full_scan as observer
import rotate_current

class Checks(unittest.TestCase):
    def setUp(self):
        self.snapshot={'root_approved':True,'source_sha':rotate_current.SOURCE,
            'observed_at':'synthetic','containers':[{'role':r,'id':'synthetic-'+r,
            'image_id':rotate_current.IMAGE} for r in ['api','consumer','scheduler','web','mysql','rabbitmq','tls-gateway']]}
        self.material={'status':'FRESH_MATERIAL_NOT_BENCHMARK_AUTHORIZATION',
            'packet_run_id':'r30materialresume08','material_process_exit_proof':{'process_exit_proven':True}}
        self.raw=json.dumps(self.material).encode()
        self.rotation={'status':'SCHEDULER_TOKEN_FILE_ATOMICALLY_REPLACED_NOT_SCANNER_USE_PROOF',
            'material_sha256':observer.digest(self.raw),'scheduler_id':'synthetic-scheduler',
            'rotation_completed_utc':'2026-01-01T00:00:00Z'}

    def test_current_binding_positive(self):
        observer.validate_rotation_material(self.rotation,self.raw,self.snapshot)

    def test_historical_rotation_material_hash_refused(self):
        r={**self.rotation,'material_sha256':'0'*64}
        with self.assertRaises(ValueError):observer.validate_rotation_material(r,self.raw,self.snapshot)

    def test_wrong_scheduler_refused(self):
        r={**self.rotation,'scheduler_id':'old-scheduler'}
        with self.assertRaises(ValueError):observer.validate_rotation_material(r,self.raw,self.snapshot)

    def test_unapproved_snapshot_refused(self):
        with self.assertRaises(ValueError):observer.validate_rotation_material(self.rotation,self.raw,{**self.snapshot,'root_approved':False})

    def test_old_material_or_missing_exit_proof_refused(self):
        for patch_value in [{'packet_run_id':'r30materialresume07'},{'material_process_exit_proof':{'process_exit_proven':False}}]:
            raw=json.dumps({**self.material,**patch_value}).encode()
            with self.subTest(patch_value=patch_value),self.assertRaises(ValueError):
                observer.validate_rotation_material({**self.rotation,'material_sha256':observer.digest(raw)},raw,self.snapshot)

    def test_future_nonUTC_and_naive_refused(self):
        for stamp in ['2099-01-01T00:00:00Z','2026-01-01T00:00:00+08:00','2026-01-01T00:00:00']:
            with self.subTest(stamp=stamp),self.assertRaises(ValueError):observer.validate_rotation_material({**self.rotation,'rotation_completed_utc':stamp},self.raw,self.snapshot)

    def test_deadline_crossing_success_refused(self):
        rows=[{'id':1,'status':2,'error_code':None,'scanned_count':100,'started_at':'2026-01-01T00:01:00Z','finished_at':'2026-01-01T00:02:00Z'}]
        with tempfile.TemporaryDirectory() as directory,patch.object(observer.time,'monotonic',side_effect=[0,1,901]),patch.object(observer,'command',return_value=json.dumps(rows).encode()) as command:
            with self.assertRaisesRegex(ValueError,'POST_COMMAND_SCAN_DEADLINE_EXCEEDED'):
                observer.scan_after_rotation('synthetic-api','2026-01-01T00:00:00Z',Path(directory),seconds=900)
            command.assert_called_once()
            self.assertFalse((Path(directory)/'scanner.PUBLIC.json').exists())

if __name__=='__main__':unittest.main()
