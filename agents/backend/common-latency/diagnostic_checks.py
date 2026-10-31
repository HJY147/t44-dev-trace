"""Diagnostic-off equivalence, privacy, exception cleanup and concurrent isolation."""
import importlib
import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from t44 import diagnostics as d

class Checks(unittest.TestCase):
 def test_disabled_is_noop(self):
  with d.span('unused'):d.count('unused')
  self.assertFalse(d.active())
 def test_exception_cleanup(self):
  class State:diagnostic_dispatch_ready_ns=0
  class Request:state=State()
  @d.diagnosed(True)
  def handle(request):raise ValueError('synthetic')
  with self.assertRaises(ValueError):handle(Request())
  self.assertFalse(d.active())
 def test_parallel_contexts_are_not_shared(self):
  barrier=threading.Barrier(2)
  def run(value):
   token=d._CURRENT.set({})
   try:
    d.count('count',value);barrier.wait(timeout=2);return dict(d._CURRENT.get())
   finally:d._CURRENT.reset(token)
  with ThreadPoolExecutor(2) as pool:
   jobs=[pool.submit(run,v) for v in [3,9]]
   self.assertEqual([j.result() for j in jobs],[{'count':3},{'count':9}])
 def test_real_http_on_off_and_no_token_projection(self):
  fixture=importlib.import_module('tmp.backend.contracts.conftest');http=importlib.import_module('tmp.backend.contracts.986_http')
  for flag in ['0','1']:
   os.environ['T44_REQUEST_DIAGNOSTICS']=flag;gen=fixture.application.__wrapped__();client,_=next(gen)
   try:
    tokens,pid,iid=http.setup_project(client);task=http.create_task(client,tokens,pid,iid)
    response=http.request(client,'getTask',token=tokens['manager'],project_id=pid,task_id=task['id'],expect=200)
    timing=response.headers['server-timing'];self.assertEqual('diag-handle-wall' in timing,flag=='1')
    self.assertNotIn(tokens['manager'],timing);self.assertNotIn('SELECT',timing);self.assertFalse(d.active())
   finally:
    try:next(gen)
    except StopIteration:pass
  os.environ.pop('T44_REQUEST_DIAGNOSTICS',None)
if __name__=='__main__':unittest.main()
