"""Bounded preparation scanner wait; no Docker, DB, HTTP or network."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('prepare07',ROOT/'deployment/cloud-reuse/prepare07-next-manual.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Scan(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name);self.clock=0.;m.TOTAL_DEADLINE=None
 def row(self,status=2,started='2026-10-31T00:00:01Z',error=None,scanned=1):
  return json.dumps([dict(id=93,status=status,started_at=started,finished_at='2026-10-31T00:00:02Z',error_code=error,scanned_count=scanned)])
 def sleep(self,n):self.clock+=n
 def test_fresh_success_original_assertions(self):
  with patch.object(m.time,'monotonic',side_effect=lambda:self.clock),patch.object(m,'command',return_value=self.row()):
   x=m.scan_after_rotation('owned','2026-10-31T00:00:00Z',self.out)
  self.assertEqual(x['successful_new_scan_ids'],[93]);self.assertFalse(x['new_scanner_started'])
 def test_old_started_run_cannot_pass_despite_finish_and_heartbeat(self):
  with patch.object(m.time,'monotonic',side_effect=lambda:self.clock),patch.object(m.time,'sleep',side_effect=self.sleep),patch.object(m,'command',return_value=self.row(started='2026-10-30T23:59:00Z')):
   with self.assertRaisesRegex(ValueError,'NO_SUCCESSFUL_POST_ROTATION_SCAN_WITHIN_BOUND'):
    m.scan_after_rotation('owned','2026-10-31T00:00:00Z',self.out,seconds=10)
  self.assertFalse((self.out/'scanner.PUBLIC.json').exists())
 def test_fresh_failed_scan_remains_fatal(self):
  with patch.object(m.time,'monotonic',return_value=0),patch.object(m,'command',return_value=self.row(status=3,error='FAILED')):
   with self.assertRaisesRegex(ValueError,'POST_ROTATION_SCAN_REPORTED_FAILURE'):
    m.scan_after_rotation('owned','2026-10-31T00:00:00Z',self.out)
 def test_exact900_boundary_rejects_late_success(self):
  with patch.object(m.time,'monotonic',side_effect=[0,0,900]),patch.object(m,'command',return_value=self.row()):
   with self.assertRaisesRegex(ValueError,'NO_SUCCESSFUL_POST_ROTATION_SCAN_WITHIN_BOUND'):
    m.scan_after_rotation('owned','2026-10-31T00:00:00Z',self.out)
 def test_remaining_total_deadline_caps_command(self):
  m.TOTAL_DEADLINE=3
  with patch.object(m.time,'monotonic',side_effect=[0,0,1]),patch.object(m,'command',return_value=self.row()) as command:
   m.scan_after_rotation('owned','2026-10-31T00:00:00Z',self.out)
  self.assertEqual(command.call_args.kwargs['timeout'],3)
 def test_zero_scan_not_success(self):
  with patch.object(m.time,'monotonic',side_effect=lambda:self.clock),patch.object(m.time,'sleep',side_effect=self.sleep),patch.object(m,'command',return_value=self.row(scanned=0)):
   with self.assertRaises(ValueError):m.scan_after_rotation('owned','2026-10-31T00:00:00Z',self.out,seconds=5)
if __name__=='__main__':unittest.main()
