"""F-only fixed service child under actual9e lock; no arbitrary command or TTL."""
import argparse
import importlib.util
import json
import os
import secrets
import time
from pathlib import Path


def load(path, expected):
    import hashlib
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise ValueError("ROOT_PINNED_NEW_ADMIN_WRAPPER_REQUIRED")
    spec=importlib.util.spec_from_file_location("f_actual_admin",path)
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def run(args):
    a=load(args.admin_file,args.admin_sha256)
    args.mode="init-accounts"  # Reuse binding/plan/import checks, never the three-account action.
    gen,lib,budget,value,inputs=a.checked(args)
    if value["phase"]!="f":
        raise ValueError("F_SERVICE_ONLY_NO_P")
    a.private_result(args.project_receipt)
    project_raw=args.project_receipt.read_bytes()
    if a.digest(project_raw)!=args.project_receipt_sha256:
        raise ValueError("ORIGINAL_ACTUAL_F_PROJECT_RECEIPT_REQUIRED")
    project=json.loads(project_raw)
    if project["namespace"]!=value["project"] or project["binding_sha256"]!=args.binding_sha256:
        raise ValueError("SAME_F_PROJECT_ONLY")
    code=a.producer_files(args)
    inputs["F-project.private.json"]=project_raw
    a.stage(args,inputs,code)
    extra=args.output_dir/"extra"
    extra.mkdir(mode=0o755)
    extra.chmod(0o755)
    raw=Path(__file__).with_name("final-f-service-code.py").read_bytes()
    a.write(extra/"f-service.py",raw)
    (extra/"f-service.py").chmod(0o644)
    a.save(args.output_dir/"extra-code.PUBLIC.json",{"files":{"f-service.py":{"sha256":a.digest(raw),"bytes":len(raw)}}})
    with budget.operation_lock(args.phase_dir,args.binding_sha256):
        _,current=gen.phase_binding(args.phase_dir,args.binding_sha256)
        if current!=value:
            raise ValueError("F_BINDING_CHANGED")
        gen.valid_window(lib,value["stop_utc"],600)
        budget.verify_runtime_environment(value,lambda r:gen.live(lib,value,r))
        admission=budget.admit(args.phase_dir,args.binding_sha256,value,lambda r:gen.live(lib,value,r),args.budget_receipt,args.budget_receipt_sha256)
        a.save(args.output_dir/"admission.PUBLIC.json",{"actual_admit_return":admission,"original_probe_sha256":args.budget_receipt_sha256})
        name=value["project"]+"-f-services-"+secrets.token_hex(4)
        prefix=a.docker_prefix(args,value,name)
        argv=[*prefix[:-1],"--volume",str(extra)+":/operator-code:ro",prefix[-1],"-B","/operator-code/f-service.py",
              "--plan","/neutral-input/plan.json","--project","/neutral-input/F-project.private.json","--output","/neutral-output/result"]
        timeout=min(180,lib.expiry(value["stop_utc"])-time.time()-600)
        if timeout<=0:
            raise ValueError("F_SERVICE_CLEANUP_RESERVE_REQUIRED")
        rc=a.run_child(argv,args.output_dir/"logs/service.stdout.private",args.output_dir/"logs/service.stderr.private",None,timeout,
                       budget.clean_environment(),lambda stop=False:a.owned_finished(lib,value,name,stop=stop))
        if rc:
            raise ValueError("F_SERVICE_CHILD_FAILED_PREFIX_PRESERVED")
        result=args.output_dir/"output/result/f-service-proof.private.json"
        a.private_result(result)
    return {"status":"F_SERVICE_CLI_AND_DB_READBACK_DONE_NOT_QA","output":str(result),"sha256":a.digest(result.read_bytes())}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("admin-file","phase-dir","profile-json","code-dir","code-manifest","plan","intent","import-receipt","budget-receipt","output-dir","source-profile","project-receipt"):
        p.add_argument("--"+key,type=Path,required=True)
    for key in ("admin-sha256","binding-sha256","profile-sha256","code-manifest-sha256","budget-receipt-sha256","project-receipt-sha256"):
        p.add_argument("--"+key,required=True)
    args=p.parse_args()
    os.umask(0o077)
    print(json.dumps(run(args)))


if __name__=="__main__":
    main()
