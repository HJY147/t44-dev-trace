"""Combine only original F facts/sessions into private functional input; never read QA output."""
import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

ROLES=("manager","developer_a","developer_b","reviewer_a","reviewer_b","outsider")


def raw(path, expected=None):
    if path.is_symlink() or path.resolve()!=path or not path.is_absolute() or path.stat().st_mode&0o077:
        raise ValueError("ORIGINAL_PRIVATE_F_INPUT_REQUIRED")
    data=path.read_bytes()
    if expected and hashlib.sha256(data).hexdigest()!=expected:
        raise ValueError("ORIGINAL_RAW_HASH_REQUIRED")
    return data


def utc(text):
    return datetime.fromisoformat(text.replace("Z","+00:00")).timestamp()  # noqa: FURB162 -- APP Python3.10


def finalize(args):
    plan=json.loads(raw(args.plan))
    actors=json.loads(raw(args.accounts))
    humans=json.loads(raw(args.human_sessions,args.human_sessions_sha256))
    proof=json.loads(raw(args.service_proof,args.service_proof_sha256))
    if (not plan["namespace"].endswith("-f") or proof["namespace"]!=plan["namespace"]
            or proof["binding_sha256"]!=plan["target"]["binding_sha256"] or proof["source_profile_sha256"]!=plan["source_profile"]["sha256"]
            or set(humans)!={*ROLES,"disposable"} or len({humans[r]["user_id"] for r in ROLES})!=6
            or len({s["token"] for s in humans.values()})!=7):
        raise ValueError("SAME_F_SCOPE_AND_DISTINCT_ACTUAL_HUMANS_REQUIRED")
    sessions=dict(humans)
    for label in ("service","expired"):
        row=proof["sessions"][label]
        original=raw(args.service_proof.parent/row["original_file"],row["original_sha256"])
        token=json.loads(original)
        if (row["actual_DB_readback"] is not True or row["session_id"]!=token["session_id"]
                or row["expires_at"]!=token["expires_at"] or row["project_ids"]!=[proof["project_id"]]
                or row["scopes"]!=["escalation:write"]):
            raise ValueError("ACTUAL_F_ONLY_SERVICE_READBACK_REQUIRED")
        sessions[label]={"token":token["access_token"],"user_id":None,"username":None,"expires_at":token["expires_at"],
                         "project_ids":row["project_ids"],"scopes":row["scopes"]}
    wait=utc(sessions["expired"]["expires_at"])-time.time()+1
    if wait>70:
        raise ValueError("ORIGINAL_ACTUAL_TTL60_SESSION_REQUIRED")
    if wait>0:
        time.sleep(wait)  # No SQL admin lock is held while awaiting actual expiry.
    now=time.time()
    maximum=min(1500,2400,int(utc(plan["window"]["stop_utc"])-now)-180)
    if maximum<60 or not all(utc(sessions[r]["expires_at"])>now+maximum+90 for r in (*ROLES,"disposable","service")):
        raise ValueError("REAL_F_SESSION_LIFETIME_AND_G_CLEANUP_RESERVE_REQUIRED")
    if any(humans[r]["user_id"]!=actors[r]["user_id"] or humans[r]["username"]!=actors[r]["username"] for r in ROLES):
        raise ValueError("ORIGINAL_INIT_USER_ACTUAL_IDENTITIES_REQUIRED")
    value={"schema":"753-functional-env-v1","run_id":plan["run_id"],"origin":plan["target"]["origin"],
        "connect_ip":plan["target"]["connect_ip"],"ca_file":"/private/functional-input/ca.pem",
        "output_dir":"/private/functional-results/"+plan["run_id"],"max_seconds":maximum,"project_id":proof["project_id"],
        "identity":{"source_git_commit":plan["source"]["git_commit"],"source_manifest_sha256":plan["source"]["manifest_sha256"],
            "backend_bundle_manifest_sha256":plan["source"]["bundle_manifest_sha256"],"image_digest":plan["images"]["backend"],
            "backend_import_receipt_sha256":plan["source"]["actual_loaded_receipt_sha256"],"openapi_sha256":plan["source"]["openapi_sha256"]},
        "sessions":sessions,"login_credentials":{"username":actors["login_only"]["username"],"password":actors["login_only"]["password"]},
        "operator_channel":"/private/operator-channel","operator_actions":["scheduler_restart","mq_stop","mq_start","api_restart","api_ready_wait"]}
    fd=os.open(args.output,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,"w") as stream:
        json.dump(value,stream,sort_keys=True,indent=2)
        stream.write("\n")
    return {"status":"PRIVATE_F_INPUT_CREATED_NOT_QA_STARTED","path":str(args.output),"sha256":hashlib.sha256(args.output.read_bytes()).hexdigest(),
            "max_seconds":maximum,"prepared_utc":datetime.now(timezone.utc).isoformat(),"dispatch_within_seconds":60}  # noqa: UP017 -- APP Python3.10


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("plan","accounts","human-sessions","service-proof","output"):
        p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--human-sessions-sha256",required=True)
    p.add_argument("--service-proof-sha256",required=True)
    os.umask(0o077)
    print(json.dumps(finalize(p.parse_args())))


if __name__=="__main__":
    main()
