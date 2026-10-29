# 772-v1: minimal neutral handoff

Status: READY_OFFLINE. This addendum supplies transport and input details; the frozen benchmark and assertions are unchanged. No cloud action, Linux remote preflight or SUT execution has occurred.

## Frozen references

- PROTOCOL.md: frozen workload, 400 clients, 60s warmup + full 600s steady, four class P95 and ten minute buckets.
- ENVIRONMENT_SCHEMA.md: neutral private session/inventory shapes.
- environment.example.json: public environment template; fill real secrets only privately on LOAD.
- grant.default-false.json: one-time authorization template, still allow=false.
- manifest.json: exact runtime/capsule/specification hashes. FROZEN_INTERFACE.json fixes the public protocol/schema hashes.

## Minimum data to provide

1. LOAD SSH destination and an absolute private staging directory; exact existing source-free Linux AMD64/Python 3.12 image reference AND image digest. No SUT source checkout is mounted into LOAD. Existing Docker must support the stated CPU/RAM/PID caps and cgroup v2.
2. Real HTTPS origin, the corresponding private connect IP, and trusted CA file. TLS hostname verification uses the HTTPS origin while the socket connects to the private IP. Supply immutable source SHA-256, fixture SHA-256, exact image digest and declared fixture counts (about 40 projects/6000 tasks/9000 dependencies/15000 review+decision records).
3. Privately: manager, developer, reviewer and service sessions. Each has actual token, user_id, actual expires_at, project_ids and scopes. Human sessions carry their actual respective project roles; service has escalation:write and authorization for every benchmark project. No global administrator or cloud credentials are needed. The tester does not log in, renew or extend a session.
4. Privately: exactly 400 client inventory entries, client_id 0..399, with project_id, complete current transition Task, complete separate escalation Task, current existing EscalationEvent and all current manager IDs. There are 800 different task IDs across about 40 projects (runtime minimum 35 projects). The 400 transition tasks are developing, assigned to the actual developer, with valid current project membership/iteration capacity and delivered dependencies. Their planned_end is later than grant end +24h. The 400 escalation tasks already have their current highest-level event, current versions, current rule version and actual recipients. Keep the same highest level throughout the grant window: for example, an already severe-overdue level-3 task remains level 3; a level-2 task must not cross the 24h boundary during the window. No external writer targets these exclusive tasks.
5. A fresh environment and one explicit allow=true grant, issued only after staging and private delivery are ready. Include the separate server collector's run ID/time window. No developer diagnosis, expected bug, expected error, old result or private test source is an input.

The inventory is a factual snapshot, not an answer key. Full Task and EscalationEvent field definitions come from the already supplied public OpenAPI. Declared fixture counts alone are not independent data-scale acceptance.

## Fresh session/window rule

Use a new, explicit **15-minute UTC grant window** for the single invocation: window_end_utc = window_start_utc +900 seconds. Start the granted invocation within 20 seconds of window_start_utc. This accommodates bounded setup, 60s warmup, a new full 600s steady cohort, <=15s drain and <=40s postchecks. The hard stop is absolute UTC plus monotonic supervision; no later round is inferred.

All four actual session expires_at values must be **strictly later than window_end_utc**; a 60-second expiry margin is sensible. Thus, if the invocation window starts at 03:00:00Z and ends at 03:15:00Z, every actual session must expire after 03:15:00Z (preferably at or after 03:16:00Z). A 600-second lifetime or logical fixture age does not cover this new run. A session created earlier must still satisfy the actual expiry requirement; no old session/packet is extended.

## Coordinator: copy only public/opaque files

After the separately authorized cloud window opens and the exact original LOAD SSH target is supplied:

```sh
sh '/Users/yang/Desktop/nothing/软件开发大作业/tmp/772_independent_perf_20261029/PUBLIC/stage_opaque.sh' USER@ORIGINAL_LOAD /opt/independent772
```

The script copies only runtime.772seal, bootstrap.py, launch.py and manifest.json, and creates public/results staging directories. It contains no key, source, case, login, decrypt, SUT call, Docker run, VM control or software installation. The script has not been executed remotely during preparation.

## Independent tester: private delivery and standard-library install

The designated encrypted transport privately places capsule.key, ca.pem, sessions.json, inventory.json, environment.json and the final grant.json under /opt/independent772, with directory 0700/file 0600. Root may move/hash opaque files, but does not receive/read keys or plaintext sessions/inventory/source/cases. The output parent /opt/independent772/results exists; the new per-run output directory must not exist yet.

The standard-library capsule interface is:

```sh
python3 /opt/independent772/public/bootstrap.py /opt/independent772/public/runtime.772seal /opt/independent772/capsule.key /opt/independent772/runtime
```

If host Python is unavailable, use the exact ALREADY EXISTING source-free Python image with --pull=never and --network=none, mount /opt/independent772 at /private, and execute the same bootstrap.py with /private paths. No dependencies are downloaded. The coordinator does not run this decrypt step; the independent tester does it after private key delivery.

The single authorized Linux preflight/cohort command and resource caps are in RUNBOOK.md. Execute it only with the real fresh grant; a failed preflight consumes that grant and yields NP without an automatic retry. Keep all prefixes and results for review, then perform the separate owned-VM shutdown/automatic-release review within the <=1h billing window.
