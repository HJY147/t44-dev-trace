# p13 follow-up algorithm opportunities (not adopted)

ROLE-backend-P13-ALGORITHM-20261031-v1. User asks whether algorithms can be optimized for better use of64 cores and when VMs can stop. This offline analysis must not delay evidence recovery/shutdown. No current formal run, resource allocation or product source is changed; no additional pressure run is authorized.

Exact source90b local extracted file hashes are in PROVENANCE.PUBLIC.json. All line references below refer to that source, not current development branch. Published neutral RESOURCE_WINDOWS.PUBLIC.json shows API17.68/15.14 cores, MySQL3.85/3.31, no measured throttle, and MySQL3207/3200 block writes/s with66.14/65.85MB/s. These are bounded windows, not complete accepted performance or proof of cloud IO throttling. Increasing CPU utilization itself is not the acceptance objective; reducing request/IO waiting at unchanged criteria is.

## 1. Unique-constraint-first idempotency claim (highest diagnostic relevance)

runtime.py155–177 locks the auth session, SELECT FOR UPDATEs the unique idempotency scope, then on miss INSERTs inside SAVEPOINT, then GETs its inserted row. schema_v1.sql343–359 defines nonnull scope columns and UNIQUE uq_idempotency_scope(actor_kind,actor_id,operation_id,idempotency_key). Prior published exact digest mapping identifies INSERT idempotency_requests as the largest sampled SQL statement wait, not a causal attribution for the current p13.

Candidate: preserve authenticate share lock; attempt original fully specified INSERT under savepoint for the new-key common path; on duplicate roll back savepoint then execute original scoped FOR UPDATE lookup and original hash conflict, complete replay, lease expiry, owner fencing rules. This could remove the pre-insert locking read and avoid some empty-range lock acquisition; actual MySQL isolation/gap-lock behavior must be measured with semantic concurrency checks, not presumed from SQLite. Preserve distinct persisted claim transaction and main business transaction: merging them casually loses lease/in-progress visibility and crash semantics. Do not use INSERT IGNORE (can conceal other constraint errors), REPLACE (destroys row identity/state), or unvalidated upsert (can overwrite another owner's claim). Do not introduce retries without explicit error semantics.

Risks: duplicate-heavy workloads incur more work; unique-index contention or AUTO_INCREMENT/disk wait may still dominate; statement ordering alters deadlock/error exposure. Request_hash must still gate replay/conflict; same-key concurrent owner, rollback/CommitUncertain, stale owner and revoked/expired session ordering must remain correct. No speedup is claimed.

Minimum next validation, after any implementation approval: bounded actual local MySQL8.4 semantic cases for same key/same and conflicting payload, distinct keys in same index range, active/expired lease, concurrent revoked session, crash after claim/before main, owner fencing and uncertain commit; verify audit/outbox exactly once, no extra successful business effects and original error precedence. Collect statement counts/lock events as diagnostic evidence, not another formal performance AB.

## 2. Reuse rows already locked inside the same main transaction

runtime.py211–242 takes stable project/dependency locks and then sorted unique-PK task locks, but discards their rows. workflow.py29 immediately reloads the task;43–46 reloads dependencies and predecessor states for START/REWORK/UNBLOCK. authenticate at identity.py77–80 reads member/project, then runtime.py217–221 obtains membership rows under share locks. This is an opportunity to return the locked context to the handler rather than making redundant SQL round trips.

Candidate: a request-local locked-context object valid only in the same main UoW. Retain original ascending unique-PK acquisition and all project/graph/session/member locks; retain full scope, ownership, version, dependency state and audit checks. Reuse fully projected locked rows only while unchanged; invalidate/update cached row after CAS. Do not reuse the earlier prepare transaction's rows, cache across requests/workers, collapse task locks into unordered IN FOR UPDATE, or precompute states outside the transaction.

Risks: MySQL repeatable-read consistent reads differ from locking current reads; substituting current locked rows for later consistent-snapshot reads can alter visibility/error results. Full lock acquisition order and state-machine version/error priorities need explicit review. Missing rows, scope mismatch and dependency changes must preserve exact guards. Potential savings are a few round trips, not an asserted solution to block-write limits.

Minimum next validation: statement trace to identify exactly duplicated same-transaction rows; concurrent graph edits and version changes under real MySQL; deterministic deadlock/lock ordering; membership revocation and scope failures; compare full successful/error contract plus audit/outbox/idempotency state. No blanket read cache.

## Deferred rather than selected

GET prepare/execute opens two UoWs and authenticates twice (runtime.py45–52,253–276; prior local count9 SELECT/2 checkout). Combining them may cut a checkout but changes the second transaction's fresh membership/revocation visibility under repeatable read. Do not delete authentication, pool-reset rollback, pre-ping, durable commit, original audit/outbox, or standalone idempotency claim based on operation counts. There is no proposal to batch unrelated client transactions or reduce400-client/60/600/270ms criteria. CPU could increase or decrease after useful optimization; end-to-end correctness and latency remain decisive.

Status: analysis only; algorithm candidates not implemented/tested/adopted. VM stop is controlled by the root's actual run exit and complete evidence recovery, independently of this offline analysis.
