"""Fixed two F-only official CLI service sessions and actual DB scope readback."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def save(path, value):
    with path.open("x") as stream:
        path.chmod(0o600)
        json.dump(value,stream,sort_keys=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--project",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    os.umask(0o077)
    sys.path.insert(0,"/neutral-code")
    from guard import load_source_profile
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.services.common import wire
    from t44.settings import Settings
    plan=json.loads(args.plan.read_bytes())
    project=json.loads(args.project.read_bytes())
    load_source_profile(plan)
    pid=project["project"]["id"]
    if (project["kind"]!="actual-fixed-F-project-and-members-v1" or not plan["namespace"].endswith("-f")
            or project["namespace"]!=plan["namespace"] or project["database"]!=plan["target"]["database"]
            or project["binding_sha256"]!=plan["target"]["binding_sha256"]
            or project["source_profile_sha256"]!=plan["source_profile"]["sha256"]
            or type(pid) is not int or pid<=0):
        raise ValueError("ONE_ACTUAL_F_PROJECT_AND_ORIGINAL_SCOPE_REQUIRED")
    settings=Settings.from_env()
    mysql=settings.mysql_settings()
    if mysql.database!=project["database"]:
        raise ValueError("ACTUAL_F_DATABASE_ONLY")
    factory=SqlAlchemyUnitOfWorkFactory(create_mysql_engine(mysql))
    args.output.mkdir(mode=0o700)
    results={}
    for label,ttl in (("service",3600),("expired",60)):
        original=args.output/(label+".original.private.json")
        env=dict(os.environ,T44_SESSION_TTL_SECONDS=str(ttl))
        argv=[sys.executable,"-B","-m","t44.cli","service-token","--name",plan["namespace"]+"-"+label,
              "--project-id",str(pid),"--token-file",str(original)]
        result=subprocess.run(argv,check=False,capture_output=True,timeout=40,env=env)
        (args.output/(label+".stdout.private")).write_bytes(result.stdout)
        (args.output/(label+".stderr.private")).write_bytes(result.stderr)
        if result.returncode:
            raise ValueError("ORIGINAL_F_SERVICE_CLI_FAILED_PREFIX_PRESERVED")
        token=json.loads(original.read_bytes())
        printed=json.loads(result.stdout)
        with factory() as uow:
            row=uow.gateway.get("auth_sessions",token["session_id"])
        if (printed["session_id"]!=token["session_id"] or printed["credential_written"] is not True
                or row["token_hash"]!=hashlib.sha256(token["access_token"].encode()).digest()
                or row["revoked_at"] is not None or row["project_ids"]!=[pid]
                or row["user_id"] is not None or type(row["service_account_id"]) is not int
                or row["scopes"]!=["escalation:write"] or wire(row["expires_at"])!=token["expires_at"]
                or (row["expires_at"]-row["created_at"]).total_seconds()!=ttl):
            raise ValueError("ACTUAL_F_SERVICE_TOKEN_SCOPE_EXPIRY_DB_READBACK_REQUIRED")
        results[label]={"original_file":original.name,"original_sha256":hashlib.sha256(original.read_bytes()).hexdigest(),
                        "session_id":token["session_id"],"expires_at":token["expires_at"],"project_ids":[pid],
                        "scopes":["escalation:write"],"ttl_seconds":ttl,"actual_DB_readback":True}
    if results["service"]["session_id"]==results["expired"]["session_id"]:
        raise ValueError("DISTINCT_F_ONLY_SERVICE_SESSIONS_REQUIRED")
    save(args.output/"f-service-proof.private.json",{"kind":"actual-fixed-F-service-sessions-v1","source_sha":project["source_sha"],
        "namespace":project["namespace"],"database":project["database"],"binding_sha256":project["binding_sha256"],
        "source_profile_sha256":project["source_profile_sha256"],"project_id":pid,"sessions":results})


if __name__=="__main__":
    main()
