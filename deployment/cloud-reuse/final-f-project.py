"""Fixed isolated F normal-API identities/project/members; no SQL, service issuing or QA."""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROLES = ("manager", "developer_a", "developer_b", "reviewer_a", "reviewer_b", "outsider")
MEMBERS = {"developer_a": [2, 3], "developer_b": [2], "reviewer_a": [3], "reviewer_b": [3]}


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # noqa: UP017 -- stdlib host tests too


def prepare(plan, binding, accounts, ca, output, client_type, save):
    if (binding["phase"] != "f" or plan["target"]["compose_project"] != binding["project"]
            or plan["target"]["database"] != binding["database"] or plan.get("benchmark_grant_allow") is not False
            or plan.get("functional_fixture", {}).get("root_admit") is not True
            or set(accounts) != {*ROLES, "login_only"}
            or len({accounts[r]["user_id"] for r in ROLES}) != 6
            or hashlib.sha256(ca.read_bytes()).hexdigest() != binding["tls"]["ca_sha256"]):
        raise ValueError("FIXED_SEPARATE_ROOT_ADMITTED_F_SCOPE_AND_SIX_IDENTITIES_REQUIRED")
    if output.exists():
        raise ValueError("NEW_F_API_OUTPUT_REQUIRED")
    output.mkdir(mode=0o700)
    records = output / "requests"
    records.mkdir(mode=0o700)
    stop = datetime.fromisoformat(binding["stop_utc"].replace("Z", "+00:00")).timestamp()  # noqa: FURB162 -- source Python3.12 and host3.10
    api = client_type(plan["target"]["origin"], ca, records, time.monotonic() + min(180, stop - time.time() - 600))
    sessions = {}
    try:
        for role in (*ROLES, "disposable"):
            actual = accounts["manager" if role == "disposable" else role]
            data = api.request("/auth/login", body={"username":actual["username"],"password":actual["password"]})
            if (data["user"]["id"] != actual["user_id"] or data["user"]["username"] != actual["username"]
                    or not isinstance(getattr(api,"last_meta",None),dict) or "server_time" not in api.last_meta):
                raise ValueError("ACTUAL_F_LOGIN_ID_USERNAME_AND_ORIGINAL_SERVER_META_REQUIRED")
            session = {"token":data["access_token"],"user_id":data["user"]["id"],"username":data["user"]["username"],
                       "expires_at":data["expires_at"],"project_ids":[],"scopes":[]}
            if any(v["token"] == session["token"] for v in sessions.values()):
                raise ValueError("DISTINCT_NEW_F_SESSIONS_REQUIRED")
            sessions[role] = session
            save(output / (role + ".login.private.json"), {"original":data,"meta":api.last_meta,"observed_utc":stamp()})
        project = api.request("/projects", sessions["manager"]["token"],
                              {"name":"[synthetic] functional " + plan["run_id"],"description":"Isolated synthetic F preparation."})
        pid = project["id"]
        if type(pid) is not int or pid <= 0 or project["my_roles"] != [1]:
            raise ValueError("ACTUAL_NEW_F_PROJECT_AND_MANAGER_ONLY_ROLE_REQUIRED")
        for role, roles in MEMBERS.items():
            actual = api.request(f"/projects/{pid}/members",sessions["manager"]["token"],
                {"username":accounts[role]["username"],"roles":roles,"reason":"[synthetic] isolated functional preparation"})
            if actual["user"]["id"] != accounts[role]["user_id"] or sorted(actual["roles"]) != roles:
                raise ValueError("ACTUAL_FIXED_F_MEMBERSHIP_REQUIRED")
        page = api.request(f"/projects/{pid}/members?page=1&page_size=100",sessions["manager"]["token"])
        members = page["items"]
        expected = {accounts["manager"]["user_id"]:[1],**{accounts[r]["user_id"]:roles for r,roles in MEMBERS.items()}}
        if (page["total"] != 5 or len(members) != 5 or {m["user"]["id"]:sorted(m["roles"]) for m in members} != expected
                or any(m["active"] is not True for m in members) or accounts["outsider"]["user_id"] in expected):
            raise ValueError("ORIGINAL_F_MEMBER_READBACK_NO_OUTSIDER_NO_EXTRA_ROLE_REQUIRED")
        for role in (*ROLES,"disposable"):
            if role != "outsider":
                sessions[role]["project_ids"] = [pid]
        save(output / "human-sessions.private.json",sessions)
        save(output / "project-and-members.private.json", {"kind":"actual-fixed-F-project-and-members-v1",
            "source_sha":binding["source_sha"],"namespace":binding["project"],"database":binding["database"],
            "binding_sha256":plan["target"]["binding_sha256"],"source_profile_sha256":plan["source_profile"]["sha256"],
            "project":project,"members":members,"observed_utc":stamp()})
    finally:
        api.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("plan","accounts","service","ca","output","import-receipt","binding"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--root-admit-http-preparation",action="store_true")
    args=p.parse_args()
    if not args.root_admit_http_preparation:
        raise ValueError("ROOT_F_PREPARATION_ONLY")
    os.umask(0o077)
    sys.path.insert(0,"/neutral-code")
    from guard import load_source_profile, validate_loaded_receipt
    from http_primitives import Client, save
    plan=json.loads(args.plan.read_bytes())
    load_source_profile(plan)
    validate_loaded_receipt(plan,args.import_receipt.read_bytes())
    binding_raw=args.binding.read_bytes()
    if (plan["gen_binding"]["path"] != str(args.binding)
            or hashlib.sha256(binding_raw).hexdigest() != plan["gen_binding"]["sha256"]
            or hashlib.sha256(args.import_receipt.read_bytes()).hexdigest() != plan["source"]["actual_loaded_receipt_sha256"]):
        raise ValueError("ORIGINAL_F_BINDING_AND_IMPORT_REQUIRED")
    prepare(plan,json.loads(binding_raw),json.loads(args.accounts.read_bytes()),args.ca,args.output,Client,save)


if __name__=="__main__":
    main()
