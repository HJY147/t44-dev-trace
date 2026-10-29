"""Reviewer-only frozen-DDL equivalence and trust-boundary probes; no database access."""
import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy.dialects import mysql, sqlite
from sqlalchemy.schema import CreateIndex, CreateTable
from t44.persistence import migrations, schema

ROOT = Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/database-scale-r29')
BASE = 'f5e0d95ea68af33dfb213ac6e8d6b496527ed7b2'
PRODUCT = '274e2e6bfa6dfb2d90926773002a1a62808ec060'
SQL_SHA = 'c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4'
FILE = 'backend/t44/persistence/schema.py'
RESULT = {'operator':'AI reviewer','product':PRODUCT,'base':BASE,
          'cloud_Docker_native_MySQL_or_private_test_reads':False}


def git(*argv):
    return subprocess.check_output(['git',*argv],cwd=ROOT)


class Resource:
    def __init__(self, value):
        self.value = value

    def joinpath(self, name):
        if name != 'schema_v1.sql':
            raise AssertionError('Unexpected resource')
        return self

    def read_text(self, encoding):
        if encoding != 'utf-8':
            raise AssertionError('Unexpected encoding')
        return self.value


class Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        path = Path(cls.scratch.name)/'before.py'
        path.write_bytes(git('show',BASE+':'+FILE))
        spec = importlib.util.spec_from_file_location('t44.persistence.reviewer_r29_old',path)
        cls.old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.old)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def test_only_schema_changes_and_frozen_bytes_identical(self):
        changed=git('diff','--name-only',BASE,PRODUCT,'--','backend/t44','frontend','specs','tmp/backend').decode().splitlines()
        self.assertEqual(changed,[FILE])
        self.assertEqual(git('show',PRODUCT+':'+FILE),Path(schema.__file__).read_bytes())
        for name in ('backend/t44/persistence/schema_v1.sql','specs/database/schema.sql'):
            self.assertEqual(git('show',BASE+':'+name),git('show',PRODUCT+':'+name))
            self.assertEqual(hashlib.sha256(git('show',PRODUCT+':'+name)).hexdigest(),SQL_SHA)
        self.assertEqual(schema.DDL_SHA256,self.old.DDL_SHA256)
        self.assertEqual(schema.SCHEMA_VERSION,self.old.SCHEMA_VERSION)

    def test_twenty_actual_payloads_and_all_metadata_objects(self):
        sql=schema.ddl_text()
        bodies=[body for _,body in re.findall(r'CREATE TABLE (\w+) \(\n(.*?)\n\) ENGINE=',sql,re.S)]
        bodies += [body for _,body in re.findall(r'ALTER TABLE (\w+)\s+(.*?);',sql,re.S)]
        self.assertEqual(len(bodies),20)
        for body in bodies:
            self.assertEqual(schema._parts(body),self.old._parts(body))
        self.assertEqual(tuple(schema.TABLES),tuple(self.old.TABLES))
        self.assertEqual(len(schema.TABLES),18)
        self.assertEqual(sum(len(t.c) for t in schema.TABLES.values()),226)
        for dialect in (mysql.dialect(),sqlite.dialect()):
            for name,left in schema.TABLES.items():
                right=self.old.TABLES[name]
                def columns(table):
                    return [(c.name,str(c.type.compile(dialect=dialect)),c.nullable,
                        c.primary_key,c.autoincrement,
                        str(c.server_default.arg) if c.server_default is not None else None)
                        for c in table.c]
                self.assertEqual(columns(left),columns(right))
                def constraints(table):
                    return sorted((c.__class__.__name__,c.name or '',tuple(x.name for x in c.columns),
                        str(getattr(c,'sqltext','')),getattr(c,'ondelete',None),
                        getattr(c,'onupdate',None),getattr(c,'deferrable',None),
                        getattr(c,'initially',None),tuple(getattr(x,'target_fullname','')
                        for x in getattr(c,'elements',()))) for c in table.constraints)
                self.assertEqual(constraints(left),constraints(right))
                self.assertEqual(dict(left.dialect_options['mysql']),dict(right.dialect_options['mysql']))
                def compiled(table):
                    ddl=str(CreateTable(table).compile(dialect=dialect))
                    prefix,_,rest=ddl.partition('(\n')
                    declarations,_,suffix=rest.rpartition('\n)')
                    return prefix,sorted(self.old._parts(declarations)),suffix
                self.assertEqual(compiled(left),compiled(right))
                self.assertEqual(sorted(str(CreateIndex(i).compile(dialect=dialect)) for i in left.indexes),
                                 sorted(str(CreateIndex(i).compile(dialect=dialect)) for i in right.indexes))
        RESULT['actual_create_alter_payloads']=20
        RESULT['tables']=18
        RESULT['columns']=226
        RESULT['table_dialect_comparisons']=36

    def test_untrusted_added_or_changed_ddl_stops_before_split(self):
        sql=schema.ddl_text()
        variants=[sql+'\nCREATE TABLE extra_review (id INT);\n',
                  sql+'\nALTER TABLE users ADD extra_review INT;\n',
                  sql.replace('id INT UNSIGNED','id GEOMETRY',1),
                  sql.replace('    id INT','  id INT',1)]
        for unknown in variants:
            with self.subTest(kind=unknown[-60:]):
                with patch.object(schema,'files',return_value=Resource(unknown)), \
                     patch.object(schema,'_parts',side_effect=AssertionError('unverified split reached')) as split:
                    with self.assertRaisesRegex(RuntimeError,'checksum does not match'):
                        schema.build_metadata()
                    split.assert_not_called()
        RESULT['unknown_DDL_unchanged_hash_rejections_before_parser']=len(variants)

    def test_module_import_checksum_gate_and_migration_gate_before_connect(self):
        sql=schema.ddl_text()+'\n-- unreviewed\n'
        raw=Path(schema.__file__).read_text()
        with patch('importlib.resources.files',return_value=Resource(sql)):
            with self.assertRaisesRegex(RuntimeError,'checksum does not match'):
                exec(compile(raw,'review_untrusted_import','exec'),
                     {'__name__':'t44.persistence.review_untrusted_import',
                      '__package__':'t44.persistence'})
        connection_calls=[]
        class Engine:
            dialect=SimpleNamespace(name='mysql')
            url=SimpleNamespace(database='t44_reviewer_r29')
            def connect(self):
                connection_calls.append(True)
                raise AssertionError('Untrusted DDL must not touch database')
        with patch.object(schema,'files',return_value=Resource(sql)):
            with self.assertRaisesRegex(RuntimeError,'checksum does not match'):
                migrations.migrate(Engine(),expected_database='t44_reviewer_r29')
        self.assertEqual(connection_calls,[])
        RESULT['checksum_gate_at_import_and_before_migration_connect']=True


if __name__ == '__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Review)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    RESULT.update(passed=result.testsRun-len(result.errors)-len(result.failures),
                  failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped))
    (Path(__file__).resolve().parent/'773_scope.PUBLIC.json').write_text(json.dumps(RESULT,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
