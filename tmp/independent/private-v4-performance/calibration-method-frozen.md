# Independent V4 driver calibration — frozen before execution

Authorization: root message and exact neutral authorization file at 027d759853a88a756735b0aa1ee0f786e53b3e91. This is a local tester-tool calibration, not a SUT or CI acceptance request. Original H2 source bytes and criteria remain unchanged.

Four sequential, single-observation cases, fixed before execution:

| case | logical users | scheduling cap s | maximum reserved request calls | fixed stub delay s |
|---|---:|---:|---:|---:|
| small immediate | 4 | 4 | 1000 | 0 |
| large immediate | 400 | 8 | 2500 | 0 |
| large bounded delay | 400 | 8 | 2500 | .05 |
| large timeout boundary | 400 | 7 | 800 | 5.2 |

The sum of schedule caps is27s and request reservations6800. Completion drain occurs within a separately enforced55s client-lifetime wall cap, including imports/startup. Independent supervisor hard alarm150s plus owned-child cleanup is below180s. It starts only an owned ephemeral127.0.0.1 stub and a separate client; on limit it terminates only its Popen-owned PID handles. No app, DB, MQ, scanner, accounts, runtime controls, project listener, CI or SUT is accessed. No retries or automatic follow-up cases.

Isolation: parse the original H2 harness text as AST, verify its whole-file SHA25640136e5d8fb152cbbfa35cca2fb489e1fa82503e8524c6b0f60d945395b31c65, and compile only Evidence and the four methods key, validate_response, request, sampler. Never import/execute the harness module, Driver initialization, fixture or control methods. Configure a fresh HTTPx client to the exact owned stub port, preserving original800 connection/keepalive settings,5s asynchronous request timeout, successful response metadata and all-response schema validation (mode867) plus original gzip evidence/sampler overhead. Use only a fixed synthetic contract-validation envelope from the frozen neutral OpenAPI. No original private fixture or business-case payloads are sent to another service.

Client records: reservation and returned-call counts separately from trace-recorded HTTP attempts; original per-request trace/status/failure/elapsed, phase start and trace origin serialized separately; original1s sampling, loop lag, CPU and getrusage RSS with actual platform units; full cycle start/finish including response validation; validator count and method segment hashes. macOS /proc/meminfo failure remains unavailable. Independent stub process records actual parsed requests, reply socket writes, active request peaks and per-case counts, plus100ms samples and its CPU/RSS. Parent records independent client/stub PID ownership and monotonic wall limits, exit and cleanup. Reply write does not prove client receipt, active requests do not prove kernel/server-SUT execution concurrency.

Assess observations without importing H2 pass/fail: counts and hard bounds must be reported, with discrepancies preserved. Expected immediate/delayed200 and timeout-path behavior are diagnostic conditions, not a new relaxed acceptance threshold. A5s async timeout may or may not match a5s wall deadline; record actual result, do not clamp. Original H2 minute/P95 oracle, negative-response semantics, write-state recovery, full workloads and600s Linux CI validity are not tested here. macOS, selected response size/schema, third-party versions and local scheduling differ from CI. No outcome can establish either SUT performance or explain its exclusive cause. A setup/runtime failure remains failed/not measured without an unplanned rerun.

Runtime chosen before execution: project-local private venv, Python3.12, httpx0.28.1 and jsonschema4.23.0 with resolved dependency inventory. Private raw outputs stay under ignored0700 .tester-local. Only safe aggregate summary MD/JSON and freeze metadata will be released.
