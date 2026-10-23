"""Validate report evidence and links only; does not run or inspect product tests."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
REPORTS = [ROOT / 'reports/final' / name for name in (
    'requirements-report.md', 'design-report.md', 'ai-development-report.md',
    'submission-map.md', 'ai-spec-guide.md'
)]

def read_json(relative: str):
    return json.loads((ROOT / relative).read_text())


def main() -> None:
    collection = read_json('docs/reports/M1-collection.json')
    assert [e['role'] for e in collection['events']] == ['backend', 'database']
    assert all(e['request'] and e['responses'] for e in collection['events'])
    assert all(e['method'] == 'collaboration.send_message' for e in collection['events'])
    manifest = read_json('docs/reports/M1-source-manifest.json')
    source_checks = []
    immutable_urls = set()
    for source in manifest['sources']:
        if 'absolute_path' in source:
            path = Path(source['absolute_path'])
            data = path.read_bytes()
        elif source.get('url'):
            data = subprocess.check_output(['git', 'show', source['commit'] + ':' + source['path']], cwd=ROOT)
            immutable_urls.add(source['url'])
        else:
            path = ROOT / source['path']
            data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == source['sha256'], source
        source_checks.append({'path': source.get('path', source.get('absolute_path')), 'sha256_match': True})
    snapshot = read_json('docs/reports/M1-github-snapshot.json')
    verified_remote = {p['url'] for p in snapshot['pull_requests']}
    verified_remote.add(snapshot['initial_deployment_actions_run']['url'])
    verified_remote.update(r['url'] for r in snapshot['design_review_comments'])
    verified_remote.update(c['url'] for c in snapshot.get('foundation_stage_comments', []))
    # Preserve earlier exact-body checks rather than refetch unchanged M0 comments.
    prior = read_json('docs/reports/github-comment-verification.json')
    verified_remote.update(c['url'] for c in prior['comments'] if c.get('verified'))
    links = []
    contents = {}
    for doc in REPORTS + [ROOT / 'docs/reports/M1-collection.md']:
        text = doc.read_text()
        contents[doc.name] = text
        if doc in REPORTS:
            assert '工作稿' in text and '非最终验收' in text
            assert 'Q002' in text
            if doc.name not in ('submission-map.md',):
                assert 'pending' in text
        for target in re.findall(r'\[[^\]\n]+\]\(([^)\s]+)\)', text):
            if target.startswith('https://'):
                assert target in verified_remote or target in immutable_urls, ('remote URL lacks scoped evidence', target)
                links.append({'document': str(doc.relative_to(ROOT)), 'target': target, 'kind': 'remote snapshot or immutable published blob', 'verified': True})
            elif target.startswith('#'):
                continue
            else:
                parsed = urlparse(target)
                destination = (doc.parent / unquote(parsed.path)).resolve()
                assert destination.is_relative_to(ROOT) and destination.is_file(), (doc, target)
                links.append({'document': str(doc.relative_to(ROOT)), 'target': target, 'kind': 'local file exists', 'verified': True})
    requirements = contents['requirements-report.md']
    assert all(f'FR-{n:02}' in requirements for n in range(1, 9))
    assert all(f'AC-{n:02}' in requirements for n in range(1, 10))
    handoff = read_json('records/handoffs/documentation.json')
    for key in ('role', 'stage', 'implementation_status', 'artifacts', 'interfaces', 'commands_executed', 'results', 'unverified', 'questions', 'prompt_refs', 'updated_at'):
        assert key in handoff, key
    for item in handoff['artifacts']:
        relative = item if isinstance(item, str) else item['path']
        # This report is written below, avoiding a self-hash dependency.
        if relative != 'docs/reports/M1-validation.json':
            assert (ROOT / relative).is_file(), relative
    submission = read_json('docs/reports/M1-submission-source-review.json')
    assert submission['normalized_text_matches_cache'] and submission['nonempty_paragraphs'] == 29
    assert submission['sha256'] == 'c688f2a25c8a1c73803e7e958e8c50681a0484ef1f34a679fa8b100ce2d64f32'
    assert 50 <= len((ROOT / 'reports/final/ai-spec-guide.md').read_text().splitlines()) <= 80
    history = ['docs/reports/collection-log.md', 'docs/reports/collection-events.json', 'docs/reports/github-comment-verification.json', 'reports/final/team-bootstrap-summary.md']
    modified = subprocess.check_output(['git', 'diff', '5d0c087f63812b0e00c7284afeafe4ec6a00c110', '--name-only', '--', *history], cwd=ROOT, text=True)
    assert not modified, ('M0 history modified', modified)
    result = {
        'checked_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'scope': 'Report JSON, explicit evidence hashes, local links, scoped remote URL evidence and unchanged M0 history only; no software tests.',
        'reports': [{'path': str(p.relative_to(ROOT)), 'lines': len(p.read_text().splitlines()), 'work_draft_non_acceptance_label': True} for p in REPORTS],
        'source_checks': source_checks, 'links': links,
        'original_submission_docx_content_reviewed': True,
        'final_foundation_responses_received': 2, 'real_inquiries_received': 2, 'followup_messages_archived': 2,
        'requirements_fr_count': 8, 'requirements_ac_count': 9,
        'm0_history_unchanged': True, 'handoff_required_fields_valid': True,
        'q002_pending': True, 'software_tests_executed_by_documentation': 0,
        'independent_acceptance_passed': False,
    }
    (ROOT / 'docs/reports/M1-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'reports': len(REPORTS), 'sources': len(source_checks), 'links': len(links), 'real_inquiries': 2, 'software_tests': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
