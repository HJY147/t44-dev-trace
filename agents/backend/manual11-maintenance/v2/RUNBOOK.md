# Cohort maintenance v2: prepared offline; execute only in the future approved APP window

Prompt `ROLE-backend-MANUAL11-MAINTENANCE-V2-20261030-v1`; backend AI author. This package was prepared locally while the user requested VM shutdown. No SSH, cloud, Docker inspection, real API call, login, repair, material05 generation or p12 preparation was executed by this role. The older fixed-IP v1 remains historical and is not the supported continuation.

## Bundle and integration contract

Place `cohort_maintenance.py` in the same `bundle/backend/` directory as the exact existing `host_runner.py` and `runtime_support.py`. The helper reuses owner-provided `inspect_api` and `maintenance_endpoint(discover_maintenance_gateway=True)`, including exact original API image/revision90b, same Compose namespace, unique running tls-gateway, shared NetworkID/IP and original HostPort checks. The discovered address is dynamic;192.168.96.4 is not embedded. Strict `PinnedHTTPSConnection` preserves original origin/Host/SNI and CA/hostname verification. Runtime pins both dependency SHAs; exact files appear in `MANIFEST.PUBLIC.json`. No product module, private QA artifact, DB library or generated source is imported.

`make_authorization.py` is optional offline authorization-file preparation; `cohort_maintenance.py` is its only local import. Deployment's wrapper may construct the exact same dedicated authorization itself. Tests and this runbook are not runtime dependencies.

The wrapper owner should import/call `invoke_before_material(...)`, or invoke the following exact CLI in a foreground subprocess and verify its exit and receipt. The function is supplied as a reusable sequence hook and never invokes host_runner's main or prepares material itself:

```sh
python3 -B bundle/backend/cohort_maintenance.py --mode apply --root-admit-maintenance --backend-tools bundle/backend --old-packet /original/inputs/session.private.json --accounts /original/accounts.private.json --authorization /new-operation/authorization.PUBLIC.json --ca /original/inputs/ca.pem --output /new-operation/cohort --api-container ORIGINAL_API_ID --expected-api-image-id sha256:PINNED_ORIGINAL_API_IMAGE
```

Use absolute paths in the actual wrapper; output must be a new canonical directory with an existing parent. The caller first owns original7/container/image/resource checks, old controller/timer idle proof, current index/DB count evidence and exclusive no-load/no-other-writer admission. The helper independently rechecks the original API owner/image/revision, original controller services inactive/failed (read-only systemctl), exclusive maintenance flock and dynamic gateway before TLS/login. It changes no service/timer or process. Its foreground deadline is300seconds inclusive of these checks; caller timeout330seconds. There are no detached processes, thread pools, automatic retries, fallback IPs or insecure TLS options.

Only after helper exit0 and its complete receipt should the wrapper invoke the existing `prepare_next_manual.py` once with a new material05 ID. That original tool then owns fresh host_runner material, scheduler rotation/scan and CMS. Original failed04 remains untouched. Backend helper never changes inventories, sessions' expiry, packet binding, original800 IDs, seed data, current product or benchmark assertions, and never starts QA/p12.

## Dedicated authorization (separate from material/read-only authorization)

Required JSON fields:

- schema=`manual11-cohort-maintenance-authorization-v2`, root_approved=true, benchmark_grant_allow=false.
- operations exactly `["login","readonly-inventory","unblock-existing-owned","readonly-audit","final-inventory"]`.
- operation_id: dedicated maintenance name, different from original packet and material04/material05/p12 IDs; source_sha exact90b.
- old_packet_sha256: exact original packet raw bytes; namespace/database: exact original additional_neutral_snapshots scope.
- original_ids_sha256: SHA256 of canonical sorted original800 disjoint integer task IDs, encoded `json.dumps(ids,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n'` UTF8.
- require_infrastructure_and_old_controller_guards=true and require_exclusive_no_benchmark_or_other_writer=true. These are admission requirements, not fabricated claims that live checks were performed while offline. The deployment wrapper supplies actual future observations before invoking apply.

For explicit future root-authorized authorization-file preparation, the optional maker accepts `--root-admit-maintenance --old-packet ... --accounts ... --operation-id ... --output NEWFILE`; it performs no Docker/network operation. Its output alone is not proof of running infrastructure and not a benchmark grant.

## Actual input and execution contract

Accounts use the existing initializer/runtime shape `{manager:{username,password,user_id},developer:{...},reviewer:{...}}`, directly passed as `payload['accounts'][role]` in existing refresh_runtime. Tests load the project's real published `accounts.http-input.template.NO_SECRETS.json` and fill fake values in that shape; no real secret file was opened locally. This is not the initializer's separate `roles/password_stdin_file` input shape. Each account ID must equal its original packet session subject.

The original packet binding and source are checked. Its400client IDs must be exactly0..399, with40projects,400unique transition IDs and400disjoint escalation IDs. Both original task kinds retain their project; transition owner must be the original developer. Fresh real developer and manager logins occur over the existing HTTPS origin. An issued login remains a real side effect on every later failure; raw successful login responses are retained only in PRIVATE, never claimed rolled back.

Before mutations, manager paginated task lists record per-project total counts and all800original tasks. Each original transition task additionally receives a developer GET; every live ID/project/owner/version must match, and state must be2/from-null or3/from2. All400must pass before any transition POST. State2 is frozen DEVELOPING, not PENDING. State3/from2 receives the frozen UNBLOCK operation, action3, actual expected_version, meaningful basis and evidence, with a fresh UUID Idempotency-Key persisted before sending. State2 is skipped. Successful response requires state2/from-null, version+1 and an audit_id.

After writes, all400transition tasks are individually GET-checked for state2, original owner and expected version. Manager lists then read back all800original IDs and each project total; the sets/totals must equal the actual preflight, original escalation task snapshots must remain byte-for-byte equivalent JSON values, and transition final versions/states/owners must still match. No task-create endpoint exists in this helper. Deployment's separate raw DB counts remain an additional owner gate; API list totals do not replace those observations.

## Progress, private prefix and successful receipt

Output:

- `guard.PUBLIC.json`: operation, original packet/800-ID hashes, admitted scope/API/image, process PID, authorization hash.
- `progress.PUBLIC.jsonl`: sanitized timestamps, current phase/counts, task IDs/version/state, successful audit IDs, dependency/endpoint checks; no passwords/tokens.
- `PRIVATE/events.private.jsonl`: fsynced prepared requests and preplanned action/key/marker, sent and received events, before/after800snapshots, actual login issuance and audit inspection. Login request credentials and bearer headers are redacted.
- `PRIVATE/NNNNN.response.private.bin`: exact bounded successful or rejected HTTP response, including real login token in root-only private evidence. An incomplete HTTP response retains a separate partial prefix when the transport supplies it. Directories0700 and evidence files0600.
- `receipt.PUBLIC.json`: final safe receipt on graceful success/failure. A SIGKILL may leave only fsynced guard/private/progress prefix; absence of a receipt is a failure requiring inspection, not permission to rerun.

Success requires all of:

```json
{"status":"COMPLETE_EXISTING400_STATE2_ORIGINAL800_PRESERVED","exit_code":0,"preflight400":400,"final400_state2":400,"original800_before":800,"original800_after":800,"project_task_totals_unchanged":true,"new_tasks":0,"seed_calls":0,"benchmark_started":false,"material05_generated":false,"automatic_resume":false}
```

Other fields include unblocked/skipped counts, HTTP requests, original hashes, operation ID and timestamps. `foreground_execution_finished` is not a claim that a still-running process already exited; the caller's returned foreground subprocess exit is the process-exit evidence. Never print private response bodies, raw exceptions or captured child output.

## Interruption and error routing

Exit0 applies only to a complete repair. Exit2 means guard refusal; exit3 means a definite HTTP/business rejection; exit4 means unknown/ambiguous outcome or any read-only recovery inspection; exit5 means the helper deadline. Any nonzero stops material generation. Even a definite rejection or timeout can follow earlier committed actions and real logins. VERSION_CONFLICT/state/owner mismatches require coordinator review; do not rewrite expected versions or inputs to conceal them. TRANSACTION_UNCERTAIN,503/5xx, unavailable audit/dependency/internal failure and IDEMPOTENCY_IN_PROGRESS are treated conservatively as unknown.

Do not rerun apply against a failed operation, reuse its output, or blindly repeat a POST/key. Use the same original inputs and a new inspection output with:

```sh
python3 -B bundle/backend/cohort_maintenance.py --mode inspect --previous /original-failed-cohort-output --root-admit-maintenance --backend-tools bundle/backend --old-packet /original/inputs/session.private.json --accounts /original/accounts.private.json --authorization /new-inspection/authorization.PUBLIC.json --ca /original/inputs/ca.pem --output /new-inspection/cohort --api-container ORIGINAL_API_ID --expected-api-image-id sha256:PINNED_ORIGINAL_API_IMAGE
```

Inspection never transitions a task. It performs a fresh manager login, reads the800original tasks and project totals, and for each planned but unconfirmed POST reads actual task audit pages. A commit is classified proven only when exactly one success audit matches original project/task, human developer, operation, expected_version and that action's unique maintenance evidence marker, and live task is state2/version+1. A matching prior successful response is separately checked against live version. An unchanged state3/version with no audit is explicitly **not proof of no commit**; the transaction could still be in progress. Conflicts/multiple audits/unavailable readback remain ambiguous.

All inspection results, even proven commits, exit4 with `automatic_resume=false`; they cannot automatically unlock material or trigger another POST. Coordinator must inspect raw evidence/process state and make a new explicit decision after uncertainty is resolved. Unattempted actions can be considered in a separately authorized new maintenance operation; original failed prefixes and actions remain intact. No old packet/material/grant is rewritten, and the script never silently upgrades a partial run to complete.

## Offline validation

Ten unittest checks pass with all I/O mocked:400restore/138POSTs/final800and totals; whole-batch preflight refusal for last-task owner/state/from mismatch; unknown POST single attempt with durable planned prefix; exact published account shape and packet/ID guards; audit-proven and unchanged-ambiguous read-only recovery; actual existing same-owner gateway function discovers a changed `.99` address and rejects a mismatched NetworkID; actual existing strict TLS primitive checks dynamic TCP destination, original hostname and rejects disabled certificate verification; transport raw login evidence stays private and503unknown is not retried; dedicated authorization rejects benchmark grant. No module test is called real physical, MySQL, cloud or performance validation.
