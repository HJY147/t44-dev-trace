"""Check public recovery receipts and existing host pins locally; never connects."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / 'ssh-reconnect'
# This local readiness budget does not change the original runtime's 900s bound.
PREPARATION_SECONDS = 1800
FORMAL_SECONDS = 900
RECOVERY_SECONDS = 900
REQUIRED_SECONDS = PREPARATION_SECONDS + FORMAL_SECONDS + RECOVERY_SECONDS


def module(name):
    spec = importlib.util.spec_from_file_location('ssh_window_' + name, SCRIPTS / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def need(value, code):
    if not value:
        raise ValueError(code)


def utc(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(parsed.utcoffset() == timedelta(0), 'UTC_RECEIPT_TIME_REQUIRED')
    return parsed


def bounded_json(path):
    path = Path(path)
    need(path.resolve() == path and path.is_file() and not path.is_symlink()
         and path.stat().st_size <= 16384, 'BOUNDED_CANONICAL_PUBLIC_REPORT_REQUIRED')
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def check(known_hosts, reports, now=None):
    now = now or datetime.now(timezone.utc)
    need(now.utcoffset() == timedelta(0), 'UTC_CHECK_TIME_REQUIRED')
    updater, pin = module('update_ssh_addresses'), module('pin_ssh_host')
    _, original = updater.trusted_pins(known_hosts)
    need(set(reports) == set(updater.HOSTS), 'BOTH_ORIGINAL_PUBLIC_REPORTS_REQUIRED')
    rows = []
    for instance in updater.HOSTS:
        report, report_sha = bounded_json(reports[instance])
        _, host_key, fingerprint = pin.checked_report(report, instance, now)
        need(host_key == original[instance], 'ORIGINAL_HOST_PIN_MISMATCH')
        need(report.get('authorized_key_options') == 'restrict,expiry-time; no forwarding',
             'ORIGINAL_RESTRICTED_AUTHORIZATION_REQUIRED')
        installed, expires = utc(report['installed_utc']), utc(report['authorization_expires_utc'])
        need(installed <= now and expires - installed == timedelta(hours=2),
             'ORIGINAL_TWO_HOUR_WINDOW_REQUIRED')
        remaining = (expires - now).total_seconds()
        need(remaining >= REQUIRED_SECONDS, 'SSH_WINDOW_BELOW_PREPARATION_FORMAL_RECOVERY_BUDGET')
        rows.append(dict(instance_id=instance, receipt_sha256=report_sha,
                         host_fingerprint=fingerprint,
                         authorization_expires_utc=expires.isoformat(),
                         remaining_seconds=int(remaining)))
    return dict(status='LOCAL_SSH_RECEIPT_WINDOW_VALID_ACTUAL_LOGIN_STILL_REQUIRED',
                checked_utc=now.isoformat(),
                required_seconds=REQUIRED_SECONDS,
                budget=dict(preparation=PREPARATION_SECONDS, formal=FORMAL_SECONDS,
                            evidence_recovery=RECOVERY_SECONDS),
                receipts=rows, connection_attempted=False,
                actual_authorization_validity_proven=False, benchmark_authorized=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--known-hosts', type=Path, required=True)
    parser.add_argument('--app-report', type=Path, required=True)
    parser.add_argument('--load-report', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.known_hosts, {
        'i-bp13uag4r4u9r2hge0mt': args.app_report,
        'i-bp13uag4r4u9r2hge0mu': args.load_report,
    }), sort_keys=True))


if __name__ == '__main__':
    main()
