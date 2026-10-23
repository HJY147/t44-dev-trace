"""Reviewer JSON/hash consistency audit only; imports no application or test module."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('target')
parser.add_argument('output')
args = parser.parse_args()
target = subprocess.check_output(['git', 'rev-parse', args.target], text=True).strip()
parent = subprocess.check_output(['git', 'rev-parse', 'ae60dc3'], text=True).strip()

def read(commit, name):
    return subprocess.check_output(['git', 'show', f'{commit}:{name}'])

def spec(commit):
    return json.loads(read(commit, 'specs/contracts/openapi.json'))

def operations(value):
    return {op['operationId']: op for methods in value['paths'].values() for op in methods.values()}

names = ['AGENTS.md', 'specs/requirements.md', 'specs/business-rules.md',
         'specs/backend-design.md', 'specs/contracts/openapi.json',
         'backend/t44/contracts/openapi.json', 'specs/contracts/README.md',
         'specs/database/field-dictionary.md', 'specs/database/persistence-contract.md',
         'specs/database/schema.sql', 'backend/t44/persistence/schema_v1.sql',
         'specs/changes/capacity-lifecycle-v1.1.md',
         'records/decisions/D005-capacity-lifecycle-adopted.md',
         'records/decisions/D006-rolled-back-capacity-adopted.md',
         'records/decisions/D002-prestart-edit-boundaries.md', 'records/spec-freezes/v1.json',
         'backend/t44/contracts/__init__.py', 'frontend/src/contract.ts']
raw = {name: read(target, name) for name in names}
manifest = {name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
            for name, data in raw.items()}
old = spec(parent)
new = json.loads(raw['specs/contracts/openapi.json'])
a, b = operations(old), operations(new)
checks = {}
checks['shape'] = [len(new['paths']), len(b), len(new['components']['schemas'])] == [31, 38, 130]
checks['ids_paths_unchanged'] = set(a) == set(b) and set(old['paths']) == set(new['paths'])
checks['runtime_copy_equal'] = raw['specs/contracts/openapi.json'] == raw['backend/t44/contracts/openapi.json']
checks['version_info_meta_equal_1_1'] = new['info']['version'] == new['components']['schemas']['Meta']['properties']['contract_version']['const'] == '1.1.0'
checks['status_38_and_top_frozen_v11'] = new['x-contract-status'] == 'frozen-v1.1' and all(x['x-contract-status'] == 'frozen-v1.1' for x in b.values())
checks['global_error_enum_unchanged'] = old['components']['schemas']['ErrorCode'] == new['components']['schemas']['ErrorCode']
changed_schemas = [k for k in old['components']['schemas'] if old['components']['schemas'][k] != new['components']['schemas'][k]]
checks['only_meta_schema_changed'] = changed_schemas == ['Meta']
meta = json.loads(json.dumps(new['components']['schemas']['Meta']))
meta['properties']['contract_version']['const'] = '1.0.0'
checks['meta_only_const_changed'] = meta == old['components']['schemas']['Meta']
case_changes = {}
for name, op in b.items():
    before = {c['code']: c for c in a[name]['x-error-cases']}
    after = {c['code']: c for c in op['x-error-cases']}
    added = set(after) - set(before)
    removed = set(before) - set(after)
    altered = [k for k in before.keys() & after.keys() if before[k] != after[k]]
    checks[f'{name}_retains_existing_error_cases'] = not removed and set(altered) <= {'CAPACITY_REFERENCE_INVALID'}
    checks[f'{name}_retains_existing_case_order'] = [c['code'] for c in op['x-error-cases'] if c['code'] in before] == [c['code'] for c in a[name]['x-error-cases']]
    expected = {'CAPACITY_REFERENCE_INVALID'} if name in ['changeTaskAssignment', 'transitionTask'] else set()
    checks[f'{name}_only_expected_added_error'] = added == expected
    if added or removed or altered:
        case_changes[name] = {'added': sorted(added), 'removed': sorted(removed), 'altered': sorted(altered)}

# Check all three per-operation declarations and its HTTP/code when adding the capacity branch.
capacity = {}
for name in ['changeTaskAssignment', 'transitionTask']:
    op = b[name]
    cases = [c for c in op['x-error-cases'] if c['code'] == 'CAPACITY_REFERENCE_INVALID']
    response = op['responses']['422']
    checks[f'{name}_capacity_declared_business_case_response'] = (
        'CAPACITY_REFERENCE_INVALID' in op['x-business-error-codes']
        and len(cases) == 1 and cases[0]['http_status'] == 422
        and 'CAPACITY_REFERENCE_INVALID' in response['x-error-codes']
        and 'CAPACITY_REFERENCE_INVALID' in json.dumps(response['content'])
    )
    capacity[name] = {'description': op['description'], 'cases': cases,
                      'response_422_codes': response['x-error-codes']}

# All references remain resolvable inside this document.
refs = []
def walk(value):
    if isinstance(value, dict):
        if '$ref' in value:
            refs.append(value['$ref'])
        for item in value.values():
            walk(item)
    elif isinstance(value, list):
        for item in value:
            walk(item)
walk(new)
missing = []
for ref in refs:
    try:
        assert ref.startswith('#/')
        cursor = new
        for part in ref[2:].split('/'):
            cursor = cursor[part.replace('~1', '/').replace('~0', '~')]
    except (AssertionError, KeyError, TypeError):
        missing.append(ref)
checks['internal_refs_resolve'] = not missing

ddl = raw['specs/database/schema.sql']
blocks = re.findall(r'CREATE TABLE (\w+)\s*\((.*?)\) ENGINE', ddl.decode(), re.S)
columns = {name: len(re.findall(r'^ {4}[a-z][a-z0-9_]*\s', body, re.M)) for name, body in blocks}
checks['ddl_18_226'] = len(columns) == 18 and sum(columns.values()) == 226
checks['ddl_schema_and_runtime_unchanged'] = ddl == raw['backend/t44/persistence/schema_v1.sql'] == read(parent, 'specs/database/schema.sql')
freeze = json.loads(raw['records/spec-freezes/v1.json'])
checks['old_manifest_bytes_preserved'] = raw['records/spec-freezes/v1.json'] == read(parent, 'records/spec-freezes/v1.json')
checks['old_11_historical_hashes_recoverable'] = all(hashlib.sha256(read(parent, name)).hexdigest() == digest for name, digest in freeze['files'].items())
current_changed = [name for name, digest in freeze['files'].items() if hashlib.sha256(read(target, name)).hexdigest() != digest]
freeze_exists = subprocess.run(['git', 'cat-file', '-e', f'{target}:records/spec-freezes/v1.1.json'], capture_output=True).returncode == 0
result = {'review_target_sha': target, 'original_freeze_commit': parent,
          'method': 'stdlib JSON/hash/git show only; no application/test import or execution',
          'inputs': manifest, 'checks': checks, 'all_structural_checks_pass': all(checks.values()),
          'path_operation_schema_counts': [len(new['paths']), len(b), len(new['components']['schemas'])],
          'case_changes': case_changes, 'capacity_operation_evidence': capacity,
          'ddl_columns_per_table': columns, 'old_frozen_files_intentionally_changed_in_v11': current_changed,
          'new_freeze_manifest_exists_at_target': freeze_exists,
          'manual_description_consistency_required': True,
          'unexecuted': ['OpenAPI validator dependency', 'services', 'HTTP', 'DB', 'tests', 'CI', 'performance', 'independent acceptance']}
Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'target': target, 'checks': len(checks), 'all_structural_checks_pass': all(checks.values()),
                  'counts': result['path_operation_schema_counts'], 'DDL': [len(columns), sum(columns.values())],
                  'runtime_contract_hash': manifest['backend/t44/contracts/openapi.json']['sha256'],
                  'new_manifest_present': freeze_exists}, ensure_ascii=False))
raise SystemExit(0 if all(checks.values()) else 1)
