# Material07 owner interface and interrupted-scan analysis

ROLE-backend-MATERIAL07-20261031-v1. Offline only, no SSH/cloud/SUT/QA PRIVATE. Original source90b/tools remain unchanged. Existing maintenance and material tools accept operation_id=r30restoretransition07 and new_packet_run_id=r30materialresume07 with fresh exclusive paths. Deployment owns QA/run isolation and exact identity pins.

## Partial06 effects and shortest safe route

Original06 service-token CLI and three real logins may have created/revoked sessions; scheduler credential file was atomically replaced. Do not replay06 or treat its token as07. New07 CLI freshly issues service credentials and validates the persisted session; fresh three role logins, scope/readback and new material fixture/count hashes remain mandatory. Original packet remains provenance for original task/subject/source identities; current task versions/states/counts/events/rules/horizon come from actual new readbacks. The material runtime reads current task snapshot and hashes it; it does not assert the old snapshot SHA is the present fixture. New original service bytes must again be rotated into the scheduler directory; prior backup preserved.

Maintenance06 fully restored400 tasks and preserved800, but that is historical. New current all800/count/schema/identity and400 state2 readback permits skipping redundant UNBLOCK apply: material's current_inventory/validate_stable_inventory still checks actual roles/tasks/owner/plans/events/rules/horizon. Legal state3 requires original helper all-batch guards; other mismatches block. No direct DB edits, seed, time rewrites or retries.

## Known unresolved scan gate

prepare_next_manual.py lines115–120 adds a deployment readiness condition started_at>=rotation plus full successful scan. Its rationale is new credential use and persistent scanner completion; it is not identified here as a frozen independent benchmark assertion. Do not silently remove it.

Source90b Scanner.run preserves start time on recovery. tick resumes all same-rule stale-running runs sequentially before starting a new run. _execute obtains token_provider() per task; scheduling main supplies lambda read_token(path). Runtime.prepare authenticates even before idempotency replay. Thus there is no source evidence for a process-lifetime cached service token. Public scan92 cursor/created progression shows recovery, not a new scan. Old started_at predates rotation and cannot pass the existing condition.

Public snapshots show earlier3000-candidate scans with approximately302/180.6/55.2 seconds elapsed, while the extra prep wait allows150 seconds and scheduler interval is60 seconds. Stop/resume can retain an old start time, so elapsed wall time is not proof of continuous slow execution. Even a normally completed scan plus scheduler wait can exceed150 seconds. Run07 renaming does not remove this known risk.

Proposed equivalent proof ONLY, not adopted: capture a baseline AFTER completed rotation, require exact new credential bytes hash before baseline and completion, fresh DB session identity/scope/expiry/revocation and exact owned scheduler mapping; observe same-run created_count+duplicate_count strictly grow after baseline then status2/finished_at after baseline/no error. Merely heartbeat/scanned_count growth is insufficient because out-of-scope candidates advance those counters without authenticated execution. Growth followed by full completion, under dynamic read_token source and exclusive writer evidence, can prove new-token use plus completed scan without a new started_at. Needs coordinator/reviewer decision, exact source binding, and actual field verification. Existing150-second duration remains unchanged unless separately reviewed; cannot guarantee success offline. Audit actor_id alone cannot distinguish two tokens for the same service actor.

## Remaining live facts

Current no-other-writer/scan status, token hash/session,800/400 eligibility, event/rule stable window, original7/schema/disk identity, real fresh07 session lifetime, exact finished scan and owner process exit cannot be proven while stopped. No claim retest is ready until the known scanner blocker has an adopted, reviewed solution. No product source, durability or original benchmark gate is changed.
