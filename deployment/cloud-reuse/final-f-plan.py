"""Write fresh F preparation inputs from actual immutable files; never issue sessions."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path,value):
    with path.open("x") as stream:
        path.chmod(0o600);json.dump(value,stream,indent=2);stream.write("\n")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("producer","source-profile","timeplan","phase-dir","import-receipt","budget-receipt","output"):
        p.add_argument("--"+name,type=Path,required=True)
    args=p.parse_args();os.umask(0o077)
    profile,clock,binding,loaded=map(read,(args.source_profile,args.timeplan,args.phase_dir/"binding.json",args.import_receipt))
    if (profile.get("root_approved") is not True or clock["phase"]!="f" or binding["phase"]!="f"
            or profile["source_sha"]!=binding["source_sha"] or clock["stop_utc"]!=binding["stop_utc"]
            or loaded["source_sha"]!=binding["source_sha"] or loaded["identity"]["config_id"]!=profile["backend_config_id"]
            or loaded["business_services_started"] is not False or loaded["volumes_modified"] is not False):
        raise ValueError("ACTUAL_APPROVED_F_SOURCE_BINDING_IMPORT_REQUIRED")
    plan=read(args.producer/"plan.template.PUBLIC.json")
    bind_sha=sha(args.phase_dir/"binding.json")
    plan.update(run_id=clock["run_id"],namespace=binding["project"],synthetic=True,root_admit_preparation=True,benchmark_grant_allow=False,
        source_profile={"path":"/neutral-input/source-profile.PUBLIC.json","sha256":sha(args.source_profile)},
        gen_binding={"path":"/neutral-input/binding.json","sha256":bind_sha,"original_host_path":str(args.phase_dir/"binding.json")},
        window={"stop_utc":clock["stop_utc"]},lifecycle={"t0_utc":clock["t0_utc"],"cost_stop_utc":clock["cost_stop_utc"]},
        functional_fixture={"root_admit":True},authorized_project_ids=[])
    plan["source"].update(git_commit=profile["source_sha"],manifest_sha256=profile["source_manifest_sha256"],
        bundle_manifest_sha256=profile["backend_bundle_manifest_sha256"],actual_loaded_receipt_path=str(args.import_receipt),
        actual_loaded_receipt_sha256=sha(args.import_receipt),actual_loaded_observed_at=loaded["observed_utc"],
        expected_runtime_files=profile["runtime_file_count"],context_records=profile["context_file_count"],
        actual_loaded_full_chain_reviewed_by_root=True)
    plan["target"].update(compose_project=binding["project"],database=binding["database"],mysql_host="mysql",mysql_port=3306,
        mysql_user=binding["database"]+"_app",binding_sha256=bind_sha,origin="https://"+binding["app_private_ip"]+":"+str(binding["tls_port"]),
        connect_ip=binding["app_private_ip"],ca_sha256=binding["tls"]["ca_sha256"])
    plan["images"]={"backend":profile["backend_config_id"],"load_python":profile["load_python_config_id"]}
    plan["budget"].update(helper_sha256=profile["budget_helper_sha256"],actual_admission_receipt_sha256=sha(args.budget_receipt))
    intent=read(args.producer/"intent.template.PUBLIC.json")
    intent.update(run_id=clock["run_id"],namespace=binding["project"],database=binding["database"],binding_sha256=bind_sha,
                  purpose="material_preparation",operation="init-user",project_ids=[])
    accounts={r:{"username":"synthetic-"+clock["run_id"]+"-f-"+r,"display_name":"[synthetic] "+r,"password":None,"user_id":None}
              for r in ("manager","developer_a","developer_b","reviewer_a","reviewer_b","outsider","login_only")}
    args.output.mkdir(mode=0o700)
    for name,value in (("plan.json",plan),("intent.json",intent),("empty-service-stage.json",{}),
        ("accounts.init.private.json",{"schema":"final-f-account-init-v1","synthetic":True,"phase":"f","binding_sha256":bind_sha,
          "source_profile_sha256":sha(args.source_profile),"accounts":accounts})):
        save(args.output/name,value)
    print(json.dumps({"status":"F_INPUTS_CREATED_NO_ACCOUNTS_OR_SESSIONS_YET","directory":str(args.output)}))


if __name__=="__main__":main()
