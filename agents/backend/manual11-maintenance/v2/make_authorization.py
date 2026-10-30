"""Offline dedicated maintenance authorization; never calls Docker, HTTPS or a VM."""
import argparse
import json
from pathlib import Path
import cohort_maintenance as core


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('old-packet','accounts','output'):
        p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--operation-id',required=True)
    p.add_argument('--root-admit-maintenance',action='store_true')
    args=p.parse_args()
    core.need(args.root_admit_maintenance,'EXPLICIT_MAINTENANCE_AUTHORIZATION_REQUIRED')
    raw=core.read(args.old_packet);old=json.loads(raw);accounts=json.loads(core.read(args.accounts))
    _,ids=core.inventory(old,accounts)
    value={'schema':'manual11-cohort-maintenance-authorization-v2','root_approved':True,
           'benchmark_grant_allow':False,'operations':core.OPS,'operation_id':args.operation_id,
           'source_sha':core.SOURCE,'old_packet_sha256':core.sha(raw),
           'namespace':old['additional_neutral_snapshots']['namespace'],
           'database':old['additional_neutral_snapshots']['database'],
           'original_ids_sha256':core.sha(core.canonical(ids)),
           'require_infrastructure_and_old_controller_guards':True,
           'require_exclusive_no_benchmark_or_other_writer':True}
    core.authorization(old,raw,value,accounts)
    core.put(args.output,core.canonical(value))
    print(json.dumps({'status':'AUTHORIZATION_FILE_PREPARED_NOT_EXECUTED','output':str(args.output)}))


if __name__=='__main__':
    try:main()
    except Exception:
        print(json.dumps({'status':'AUTHORIZATION_PREPARATION_REFUSED_NO_CREDENTIALS_PRINTED'}));raise SystemExit(2)
