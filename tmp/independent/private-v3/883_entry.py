"""Hosted neutral Python entry. No positional arguments or inferred product checkout."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def own(name, label):
    spec = importlib.util.spec_from_file_location(label, HERE / name)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def main():
    own('874_verify.py', 'iv3_freeze_verify').verify()
    S = own('881_support.py', 'iv3_support_main')
    h = S.Harness('functional-http-and-storage')
    setup = h.rec.run('preconditions-neutral-accounts-and-auth', h.setup_users)
    if setup['status'] == 'pass':
        selection = HERE / 'continuation-selection.json'
        if selection.exists():
            plan = json.loads(selection.read_text())
            S.check(plan['product_source_sha'] == h.c['product_source_sha'], 'Continuation stays on the exact same SUT')
            h.rec.case_filter = plan['functional_case_ids']
        own('882_http.py', 'iv3_http_cases').run(h, S)
    else:
        catalog = json.loads((HERE / 'cases.json').read_text())
        for item in catalog['functional_cases']:
            h.rec.results.append({'id': item['id'], 'status': 'not_executed',
                                  'reason': 'Neutral account/auth precondition did not complete'})
    for blocker in ['B-SPEC-01-exact-empty-evidence-error-subclass',
                    'B-SEC-01-raw-password-hash-only-persistence-entry',
                    'B-SEC-02-cli-global-session-revocation']:
        h.rec.results.append({'id': blocker, 'status': 'capability_blocked',
                              'reason': 'See frozen case catalog; no runtime guess or application import permitted'})
    return h.rec.finish({'operations_observed': sorted(h.covered),
        'formal_performance': 'not executed by this entry; use 879/878/877 independently',
        'browser_and_operational_faults': 'not executed by this entry; use 880 and 875 separately',
        'all_error_branches': 'No blanket pass; branch-inventory.json preserves every declared branch and execution scope'})

if __name__ == '__main__':
    raise SystemExit(main())
