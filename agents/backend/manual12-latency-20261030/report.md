# MANUAL12 backend diagnosis: transaction lifecycle

Agent-Role: backend. Prompt-Ref: ROLE-backend-MANUAL12-DIAGNOSIS-20261030-v1. Refs: #47.

Source inspected: `90b734f65ce6ee9f5c217e885bc7ea4857e32b48`. No cloud access, QA PRIVATE access, product code change, or new benchmark.

## Measured evidence

From the two published APP telemetry windows, API average CPU is 13.096 cores over 63.109s early and 11.771 over 62.516s late; MySQL is 2.697/2.389 cores. This does not support saturation of the 64 host CPUs. MySQL commits and rollbacks are almost one-for-one: 1596.280/1596.217 per second early and 1483.184/1483.040 late. New row-lock waits are only 4 and 1; aggregate added row-lock times 113 and 46ms; log waits remain zero. Global counters must be interpreted as differences within each window, not per-request latencies.

A real local SQLAlchemy 2.1.6/SQLite DBAPI probe uses the unchanged product UoW and isolates only pool reset policy. With the current `rollback` reset, successful read/write UoWs each issue 1 COMMIT plus 1 subsequent DBAPI ROLLBACK. With reset None, they issue only COMMIT. An exception UoW rolls back twice/current versus once/None. Unclosed Connection transactions roll back once in both; unclosed Session transactions roll back twice/current versus once/None. All failed/unclosed writes remain absent and the successful write remains persisted. This is command/lifecycle evidence only; SQLite does not prove MySQL durability or cloud P95 improvement.

Sequential profiling of unchanged source90b Runtime plus request/response frozen validation confirms:

| Operation | SELECT | Checkouts / commits | Mean local milliseconds |
|---|---:|---:|---:|
| getTask | 9 | 2 / 2 | 3.042 |
| validateContractPayload | 4 | 1 / 1 | 1.581 |
| transitionTask | 20 | 2 / 2 | 9.136 |

The means include cProfile overhead and are not performance acceptance or an estimate of cloud latency. `transitionTask` also executes its savepoint, 3 INSERT and 2 UPDATE operations. This small local CPU time is insufficient to explain the measured >1s cloud tail by itself.

## Candidate and retained semantics

The current engine hardcodes `pool_reset_on_return='rollback'`. After a UoW successfully ends its transaction, SQLAlchemy's connection checkin can issue an otherwise redundant ROLLBACK. Every HTTP class uses at least one UoW, so this candidate spans all four classes. Database owner must map the measured digest wait and validate real MySQL commit/rollback/failure/savepoint behavior before proposing a single-factor change. No reset configuration has been changed here.

GET also authenticates both in prepare and the main transaction, while writes authenticate before/inside the idempotency claim and again under locked scope. Removing live authentication/revocation checks is explicitly rejected. A previously considered GET transaction reduction affects only query, so it is not selected for this four-class failure.

No claim that pool reset is the sole bottleneck or that an index change caused the new P95. No persistence safety setting, worker/pool budget, audit, idempotency, contract, fixture or formal assertion was weakened.

## Reproduction

- `PYTHONPATH=backend <existing-local-venv>/bin/python -B agents/backend/manual12-latency-20261030/transaction_reset_probe.py agents/backend/manual12-latency-20261030/transaction-reset-probe.PUBLIC.json`
- `PYTHONPATH=backend:. <existing-local-venv>/bin/python -B <prior-backend-worktree>/agents/backend/manual11-latency-20261030/local_profile.py agents/backend/manual12-latency-20261030/runtime-baseline.PUBLIC.json`

The prior profiling script is an already-published backend author tool, not independent cases. Its exact source hash is recorded in `provenance.PUBLIC.json`. All data created by those scripts is synthetic and local.
