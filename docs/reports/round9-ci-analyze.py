"""Read sealed Actions evidence, calculate JUnit and coverage facts, no SUT execution."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location('collector', Path(__file__).with_name('round9-ci-collector.py'))
collector = module_from_spec(spec)
spec.loader.exec_module(collector)


def sha_from_checkout(text):
    lines = text.splitlines()
    result = []
    for index, line in enumerate(lines[:-1]):
        if 'git log -1 --format=%H' in line:
            match = re.search(r'\b([0-9a-f]{40})\s*$', lines[index + 1])
            assert match, lines[index + 1]
            result.append(match.group(1))
    return result


def junit(raw):
    root = ET.fromstring(raw)
    cases = root.findall('.//testcase')
    suites = root.findall('.//testsuite') if root.tag == 'testsuites' else [root]
    declared = {key: sum(int(suite.get(key, 0)) for suite in suites) for key in ['tests', 'failures', 'errors', 'skipped']}
    actual = {'tests': len(cases), 'failures': 0, 'errors': 0, 'skipped': 0, 'passed': 0}
    for case in cases:
        outcomes = [name for name in ['failure', 'error', 'skipped'] if case.find(name) is not None]
        assert len(outcomes) <= 1
        actual[{'failure': 'failures', 'error': 'errors', 'skipped': 'skipped'}.get(outcomes[0], 'passed') if outcomes else 'passed'] += 1
    assert all(actual[key] == count for key, count in declared.items())
    return {'declared': declared, 'actual': actual, 'declarations_match_testcases': True}, {(case.get('classname'), case.get('name')) for case in cases}


result = {'schema_version': 1, 'analyzed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'runs': {}, 'duplicate_pr_runs': []}
artifact_count = artifact_bytes = log_count = log_bytes = member_count = 0
for run_id, expected in collector.RUNS.items():
    root = Path('records/ci') / str(run_id)
    binding = json.loads((root / 'archive-binding.json').read_text())
    data = {'source_sha': expected, 'event': binding['event'], 'conclusion': binding['conclusion'], 'checkout': [], 'junit': {}}
    with zipfile.ZipFile(root / 'official-run-logs.zip') as archive:
        for name in archive.namelist():
            if 'checkout' in name:
                shas = sha_from_checkout(archive.read(name).decode())
                if shas:
                    assert shas == [expected]
                    data['checkout'].append({'member': name, 'actual_checked_out_sha': shas[0]})
    assert len(data['checkout']) == len(binding['jobs'])
    subset_ids, full_ids = set(), set()
    for item in binding['artifacts']:
        checked = collector.validate_zip(root / item['file'])
        assert checked['bytes'] == item['official_size']
        assert 'sha256:' + checked['sha256'] == item['official_digest']
        assert checked['members'] == item['members']
        artifact_count += 1
        artifact_bytes += checked['bytes']
        member_count += len(checked['members'])
        with zipfile.ZipFile(root / item['file']) as archive:
            for name in archive.namelist():
                if name.endswith('.xml') and ('junit' in name or name.startswith('contracts/')):
                    counts, identities = junit(archive.read(name))
                    data['junit'][name] = {'zip': item['file'], **counts}
                    if name.startswith('contracts/'):
                        subset_ids.update(identities)
                    else:
                        full_ids = identities
            if 'coverage/coverage.json' in archive.namelist():
                raw = json.loads(archive.read('coverage/coverage.json'))
                totals = raw['totals']
                xml = ET.fromstring(archive.read('coverage/coverage.xml'))
                assert int(xml.get('lines-valid')) == totals['num_statements']
                assert int(xml.get('lines-covered')) == totals['covered_lines']
                covered = sum(len(v['executed_lines']) for v in raw['files'].values())
                total = sum(v['summary']['num_statements'] for v in raw['files'].values())
                assert covered == totals['covered_lines'] and total == totals['num_statements']
                data['backend_coverage'] = {
                    'zip': item['file'], 'members': ['coverage/coverage.json', 'coverage/coverage.xml', 'coverage/gate.json'],
                    'measured_files': len(raw['files']), 'covered_lines': covered, 'total_lines': total,
                    'line_percent': covered / total * 100,
                    'covered_branches': totals['covered_branches'], 'total_branches': totals['num_branches'],
                    'branch_percent': totals['covered_branches'] / totals['num_branches'] * 100,
                    'coveragepy_line_plus_branch_percent': totals['percent_covered'],
                    'mixed_numerator': covered + totals['covered_branches'],
                    'mixed_denominator': total + totals['num_branches'],
                    'line_json_xml_member_counts_match': True,
                }
            if 'frontend/coverage/test-results.json' in archive.namelist():
                tests = json.loads(archive.read('frontend/coverage/test-results.json'))
                cov = json.loads(archive.read('frontend/coverage/coverage-summary.json'))['total']
                cases = [case for suite in tests['testResults'] for case in suite['assertionResults']]
                outcomes = {status: sum(case['status'] == status for case in cases) for status in ['passed', 'failed', 'pending', 'todo']}
                assert len(cases) == tests['numTotalTests']
                assert outcomes['passed'] == tests['numPassedTests']
                assert outcomes['failed'] == tests['numFailedTests']
                data['frontend'] = {'zip': item['file'], 'tests': len(cases), 'outcomes': outcomes, 'summary_matches_cases': True, 'coverage': cov}
            if 'result.json' in archive.namelist():
                docker = json.loads(archive.read('result.json'))
                assert docker['source_sha'] == expected and docker['passed']
                restoration = docker['restoration']
                assert restoration['source'] == restoration['recovered']
                assert restoration['matched']
                assert next(step['exit_code'] for step in docker['steps'] if step['name'] == 'shared-flock-rejects-second-scanner') == 1
                data['docker'] = {
                    'zip': item['file'], 'source_sha': docker['source_sha'], 'passed': docker['passed'], 'scope': docker['scope'],
                    'workers': docker['api_processes']['workers'], 'seed_version': docker['seed']['manifest']['version'],
                    'seed_tasks': docker['seed']['tasks'], 'restored_tables': len(restoration['recovered']['counts']),
                    'restore_counts_and_checksums_matched': True,
                    'expected_second_flock_owner_exit': 1,
                }
    if not full_ids and binding['conclusion'] == 'cancelled':
        data['full_suite_result'] = 'Unavailable: cancelled coverage artifact contains no JUnit or coverage JSON/XML; never count as zero tests or a pass.'
    if full_ids:
        data['contract_subset_identity_count'] = len(subset_ids)
        data['contract_subset_matches_full_suite'] = subset_ids <= full_ids
        data['contract_subset_not_in_full_suite'] = len(subset_ids - full_ids)
        data['aggregation_rule'] = 'Full-suite 695 is the backend result. Contract/integration/fault executions are separate repeated subsets and are not added to 695.'
    log_checked = collector.validate_zip(root / 'official-run-logs.zip')
    assert log_checked['sha256'] == binding['official_run_logs']['sha256']
    log_count += 1
    log_bytes += log_checked['bytes']
    member_count += len(log_checked['members'])
    result['runs'][str(run_id)] = data

for run_id, merge in [(40200935848, '00c1278bec48b21d5a7387da27ca879c7ec3999a'), (40201588604, 'c6b140fcbc8316768009fb53394a11b5cb0ac2eb')]:
    root = Path('records/ci') / str(run_id)
    run = json.loads((root / 'run-rest.json').read_bytes())
    raw = (root / 'static-job-original.log').read_bytes()
    text = raw.decode()
    assert run['event'] == 'pull_request'
    assert sha_from_checkout(text) == [merge]
    assert 'refs/remotes/pull/21/merge' in text
    result['duplicate_pr_runs'].append({
        'run_id': run_id, 'event': run['event'], 'metadata_head_sha': run['head_sha'], 'conclusion': run['conclusion'],
        'actual_static_checkout_ref': 'refs/remotes/pull/21/merge', 'actual_static_checkout_sha': merge,
        'log_file': str(root / 'static-job-original.log'), 'log_bytes': len(raw), 'log_sha256': hashlib.sha256(raw).hexdigest(),
        'not_primary_exact_source_evidence': True,
        'warning': 'Do not infer historical checkout from nested pull_requests.head.sha; that PR association can show its newer head.',
    })

result['archive_totals'] = {'artifact_zip_count': artifact_count, 'artifact_zip_bytes': artifact_bytes, 'official_run_log_zip_count': log_count, 'official_run_log_zip_bytes': log_bytes, 'validated_zip_members': member_count}
result['claims'] = {'independent_acceptance': False, 'formal_performance': False, 'source_size_gate_passed': False, 'final_billing_verified': False}
Path('docs/reports/round9-ci-analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
