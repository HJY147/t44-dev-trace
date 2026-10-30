# MANUAL12 database diagnosis — bounded telemetry and local probes

Issue: https://github.com/HJY147/t44-dev-trace/issues/47

Source is exact runtime `90b734f65ce6ee9f5c217e885bc7ea4857e32b48`; source equality was checked for engine, UoW, schema and service runtime. No cloud login, SUT HTTP, QA PRIVATE read or product change occurred. Two public neutral sample groups each contain 12 observations; measured spans are 63.109s and 62.516s, not the full formal 600-second window. Inputs are SHA-bound in the output.

## Measured findings

- API averaged 13.10 / 11.77 CPU cores; MySQL 2.70 / 2.39. CPU cgroups report no throttling; no OOM. The process projection only lists a supervisor, so it is not evidence of a single worker.
- MySQL `STATEMENT_DIGEST` on a separate local MySQL8.4.11 server mapped the exact static statement shapes: `78ceeee…` is the original nine-column INSERT into `idempotency_requests`; `f2b9be5…` is COMMIT; `6ebc715…` is audit INSERT; `3e67fa9…` is ROLLBACK. No cloud SQL text was exported; map SQL is synthetic product-source shape only.
- Idempotency INSERT delta: 32193 calls / 5091.06 aggregate SQL wait seconds (mean 158.14ms) early; 29591 / 2234.83s (mean 75.52ms) late. Concurrent wait totals may exceed elapsed time and are not end-to-end request time. This is the strongest observed SQL hotspot.
- COMMIT mean 15.73 / 16.41ms. Audit INSERT mean 15.52 / 17.48ms. ROLLBACK mean 0.0245 / 0.0236ms server-side. The near one-to-one commit/rollback count is real, but server rollback wait is not the largest component; unmeasured network RTT remains possible.
- Original confirmed-missing query `91fd940…` has real interval increments: each group adds 25 calls and 400000 examined rows (16000 rows/call), zero sent. Mean 35.66 / 43.06ms. The new index did not eliminate this scan under actual event-type distribution; the earlier 100k ordinary-event local case is insufficient to establish cloud benefit.
- Redo fsync rate 459.72 / 491.64 per second; `Innodb_data_written` about 24.8 / 24.2 MB/s. `Innodb_log_waits` and buffer-pool wait-free remain zero; row-lock wait increments only 4 / 1, totaling 113 / 46ms. Reads are about 1–2 physical pages/s. Effective durability remains flush-at-commit=1 and sync_binlog=1.
- Actual redo capacity is 104857600 bytes with about 2.5–2.7 MB/s redo production. This suggests checkpoint/IO pressure worth probing; checkpoint age / auto-inc / actual wait-event breakdown were not collected, so neither small redo nor any insert contention cause is proved. No redo change is proposed as accepted without a controlled local reproduction.

## Rejected shortcut: global pool reset=None

`native_pool_probe.py` uses real SQLAlchemy/PyMySQL against an owned local socket-only MySQL, with synthetic rows. Both variants preserve managed Connection.close rollback, exception UoW rollback and integrity-failure cleanup. Normal UoW commit has commit1+rollback1 with current default, commit1+rollback0 with reset=None.

However raw DBAPI return without rollback exposes an uncommitted row on the next checkout with reset=None (visible=1), while the existing rollback fallback gives visible=0. Therefore changing global pool reset unconditionally removes a safety property. The candidate is rejected, not merged. Product configuration stays unchanged.

## Evidence and reproduction

- `analyze_samples.py` and `telemetry-deltas.PUBLIC.json`: counter deltas, rates, gauges, truncated-top20 limitations and input hashes.
- `render_static_sql.py`, `static-statement-shapes.PUBLIC.json`, `native_digest_probe.py`, `native-digest-map.PUBLIC.json`: exact-source static SQL shapes and real server digest mapping.
- `native_pool_probe.py`, `native-pool-result.PUBLIC.json`: ten actual variant/case outcomes including the unsafe counterexample.
- All MySQL probes start only this task's separate `manual12-digest-mysql-v2`, skip-networking/mysqlx-off socket; own process is shut down in finally. No deployment credentials are loaded. Local data/key/log files remain under ignored runtime.
- Initial local init failed because a log was inside the target datadir; preserved failed runtime directory, then used a fresh datadir with outside log. Initial DML digest calls lacked a default database and were rejected; the final run uses an isolated synthetic database and all 15 mapping calls succeeded. These were local setup failures, not cloud or performance failures.

Open: reproduce the INSERT wait with exact DDL, original claim transaction and accumulated synthetic row volume; inspect real local wait-event/IO/checkpoint evidence before selecting a fix. This analysis and rejected shortcut are not a performance improvement or formal acceptance.

## Accumulated-row native claim probe

`native_claim_probe.py` runs the original source90b `Runtime.prepare`/`_claim` and `Runtime.complete` on a separate synthetic schema with the exact frozen DDL and active constraints. Each variant uses 64 clients and 1280 operations. Empty baseline INSERT mean/P95 is 7.32/13.11ms; with 501280 accumulated synthetic rows it is 6.87/11.58ms. Fragment end-to-end P95 is 211.45/169.10ms. This short native case does not reproduce the cloud INSERT75–158ms and does not support row count alone as the cause. It excludes HTTP and the complete main audit/outbox transaction and uses local hardware; it is not a formal load result. Own server was shut down afterward.

A subsequent controlled redo comparison is running separately, with two initially identical cloned synthetic datasets (502560 rows and identical actual extended checksum1696289492), source90b frozen DDL, 64clients,20s warmup/180s measured per phase,100MiB versus1GiB,2s sampling. The pre-run plan is posted in Issue#47 comment6526405915. No outcome is asserted until it completes. Fixed AB order/cache, local buffer1GiB versus cloud8GiB and fragment scope will remain explicit.

## Kernel versus InnoDB IO scope

The analyzer now also differences cgroup `io.stat` for common actual devices, leaving unmatched/empty projections explicit. For MySQL device259:0: early kernel writes are49869956B/s and2073.33 write operations/s; late48642312B/s and2067.10/s. These are block-layer counters. The earlier24–25MB/s `Innodb_data_written` is an InnoDB-layer counter and must not be substituted for kernel bytes; doublewrite/redo and other file paths may contribute. No current cloud disk size/tier/cap was observed in this task, so a historical purchase record cannot establish the live cap or prove throttling. Next actual cloud diagnostic should capture diskstats/await/queue, IO pressure and the relevant P_S wait-event deltas alongside exact current volume/tier/limits, without exporting SQL text or credentials.

## Controlled native redo result — negative for adopting a fix

Both original frozen-schema clones initially had502560 rows, min/max id1/502560 and actual CHECKSUM TABLE EXTENDED1696289492. Two phases used the same original source90b prepare/claim+complete fragment,64clients,20s warmup+180s measurement, pool320/maxconnections384/buffer1GiB, flush-at-commit1/sync_binlog1; only redo capacity changed. Each phase used a clean restart of this exclusive socket-only server and enabled the same local wait instrumentation.

| Capacity | Measured operations | Client INSERT mean/P95 | Fragment client P95 | Actual server INSERT mean | Actual server COMMIT mean |
|---|---:|---:|---:|---:|---:|
|100MiB|77385|7.13/12.03ms|173.40ms|0.054ms|0.118ms|
|1GiB|67578|8.17/13.78ms|200.43ms|0.065ms|0.131ms|

Both phases had0 transaction errors and0 sample failures. The100MiB phase's bounded samples cover178.88s,187.18MB redo (1.785× configured capacity),26 distinct checkpoint advances, checkpoint age9.66–16.97MB,0 log waits. The1GiB phase covers178.99s,163.85MB redo, age22.45–97.48MB,0 log waits. InnoDB data-write rate drops8.48→3.20MB/s with the larger capacity, but INSERT/fragment latency does not improve. These results do not support adopting redo size as an established fix.

Native server INSERT0.054–0.065ms and COMMIT0.118–0.131ms are far below cloud server INSERT75–158ms and COMMIT16ms. Native client INSERT7–8ms includes Python scheduling/transport overhead and must not be compared as if it were server statement time. Native redo rate≈1MB/s is lower than cloud2.5–2.7MB/s; the full main audit/outbox transaction is excluded. Fixed AB order, OS cache and appended warmup/test rows remain confounders despite identical initial clones. Thus the experiment neither proves a cloud cause nor excludes cloud storage/checkpoint pressure. It rejects a speculative fix without the needed live wait/disk evidence.

`native_redo_probe.py`, two `redo-*.PUBLIC.json` files, `native-redo-comparison.PUBLIC.json`, `derive_redo.py` and `native-redo-derived.PUBLIC.json` preserve the run and2-second samples. The local runner completed, disposed pools and shut down its own process; the task socket no longer exists. No cloud, product settings, constraints, original tool or durability policy were changed.

## Deployment observer dictionary compatibility check

The exact received static query bundle for observer52c3e785 is retained as `observer-dictionary-queries.received.PUBLIC.json`. `observer_dictionary_probe.py` independently permits only non-locking SELECT/SHOW over global configuration/status or performance_schema; no INSERT/UPDATE/SET/DDL/privilege statement is accepted. On the owned no-network MySQL8.4.11 (port0), status/config/waits all returned0, with raw `mysql --batch --skip-column-names --raw` stdout and a separate second read of resultset column names preserved in `observer-dictionary-result.PUBLIC.json`. Status exposes37 available variables plus four aggregate resultsets, config12 variables, waits coverage plus20 rows. Absent version-specific fields remain absent; they are not fabricated zeros.

No pressure, SUT, business SQL, setup_instruments update or global-configuration change was performed. The local server was cleanly shut down and socket absent. This proves local dictionary/column compatibility only, not cloud permissions, meaningful live counters, Linux block metrics or deployment parser correctness. Root will forward the raw stdout to the deployment role for parser checks. Original stderr is excluded. The query input hash and observer source hash are bound in the receipt.
