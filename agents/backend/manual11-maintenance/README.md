# Existing MANUAL11 cohort maintenance

Prompt ID: `ROLE-backend-MANUAL11-MAINTENANCE-20261030-v1`; operator/author backend AI. Coordinator dispatch authorizes preparation only here; coordinator executes on the original APP host. No cloud execution was performed by this role.

Copy only `restore_transition_cohort.py` to the original APP host, then run stdlib Python3 (credential values never enter command arguments):

```sh
python3 restore_transition_cohort.py --packet /original/P09packet.json --accounts /existing/accounts.private.json --ca /existing/ca.pem --output /new/maintenance-output
```

Output must be a new directory under an existing parent. Do not rerun/overwrite the failed material04. This helper does not create material05 or run the benchmark.

Transport is fixed: origin/Host `https://172.21.182.245:26445`, TCP connect `192.168.96.4:8443`, SSL server_hostname and certificate identity `172.21.182.245`, default strict CA/hostname verification. CA SHA must match the original packet's environment. No insecure flag, DNS redirection, product/DB/seed imports or requests retries exist.

Input uses original `inventory.clients[*].project_id` and `.transition_task.id/project_id/owner_id`, exactly400 unique task IDs; the existing developer account must match packet developer user ID. A fresh real HTTPS developer login occurs. Issued session is a real side effect even if subsequent maintenance fails; it is not rolled back, cached in output or claimed absent. No passwords/tokens appear in output. Existing inventory/expiry/packet inputs are read only.

Each original task is GET-validated before any POST. Required live owner matches developer, task ID/project match, state2 or state3 with blocked_from_state2. Invalid last task causes zero transition POSTs. Only the latter tasks receive:

`POST /api/v1/projects/{pid}/tasks/{tid}/transitions`

```json
{"expected_version":"actual GET integer", "action":3, "basis":"Restore original transition cohort after completed MANUAL11 BLOCK/UNBLOCK cycle", "evidence":[{"kind":2,"locator":"MANUAL11/PUBLIC/INDEPENDENT_REPORT.PUBLIC.md","description":"Maintenance restores existing owned blocked tasks to recorded prior state"}]}
```

`expected_version` is sent as the actual integer, not the explanatory string above. Authorization uses the fresh login bearer; each POST has a fresh UUID Idempotency-Key. Actual schema UNBLOCK requires expected_version/action/basis/evidence. State2 is frozen DEVELOPING, and UNBLOCK restores the recorded prior state; no task is forced to state1/PENDING. GET state2 is skipped. Each successful transition must increment version by1, state2/from null. Final400GETs verify state2/from null and expected unchanged versions; a concurrent writer/version conflict stops immediately.

With root-observed138blocked and262state2, expected939HTTP requests = login1 + preflightGET400 + UNBLOCK138 + finalGET400. There is a180s helper deadline and15s individual timeout. Any failed/unknown response stops with no retry. Public journal records status, request IDs and timestamps; public states log records original/project/task IDs, before/final states and versions, successful audit IDs. Both flush/fsync after every entry. Summary preserves partial effects and failure code; response bodies/credentials are not published. A failed POST may have committed: its result remains unknown and must be inspected, never blindly retried.

Local verification: `python3 -m py_compile restore_transition_cohort.py`; `python3 mock_checks.py` =>4passed/0.004s. These are fake-API checks, not a live repair or formal performance result. They cover exact400/138mutation/final400, complete-preflight refusal before writes, unknown-write no retry, duplicate IDs. Prompt refinement: reject the entire batch before writes when any original task is not restorable; preserve partial real effects rather than claiming rollback.
