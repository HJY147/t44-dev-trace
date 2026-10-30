"""Local negative context checks; no database, network or alternate product path."""
import unittest
from types import SimpleNamespace
from t44.services.application import Business
from t44.services.common import Call
from t44.services.errors import Rejected

class ContextChecks(unittest.TestCase):
 def test_other_gateway_refused(self):
  with self.assertRaises(Rejected) as error:
   Business().dispatch(object(),Call('transitionTask','synthetic',None),locked_task=(object(),{}))
  self.assertEqual(error.exception.code,'INTERNAL_ERROR')
 def test_get_cannot_use_context(self):
  g=object()
  with self.assertRaises(Rejected) as error:
   Business().dispatch(g,Call('getTask','synthetic',None),locked_task=(g,{}))
  self.assertEqual(error.exception.code,'INTERNAL_ERROR')
 def test_other_task_or_project_refused_before_gateway_use(self):
  g=object();c=Call('transitionTask','synthetic',None,path={'project_id':1,'task_id':2})
  for row in ({'id':3,'project_id':1},{'id':2,'project_id':3}):
   with self.subTest(row=row),self.assertRaises(Rejected) as error:
    Business().dispatch(g,c,locked_task=(g,row))
   self.assertEqual(error.exception.code,'RESOURCE_NOT_FOUND')
 def test_missing_target_uses_original_resource_read(self):
  calls=[]
  g=SimpleNamespace(get=lambda *a,**kw:calls.append((a,kw)))
  c=Call('transitionTask','synthetic',None,path={'project_id':1,'task_id':2})
  with self.assertRaises(Rejected) as error:Business().transitionTask(g,c)
  self.assertEqual(error.exception.code,'RESOURCE_NOT_FOUND')
  self.assertEqual(calls,[(('tasks',2),{'lock':None})])

if __name__=='__main__':unittest.main()
