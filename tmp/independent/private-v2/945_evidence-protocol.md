# Frozen independent harness interface and evidence protocol

No SUT has been supplied; these are future commands and capability requests. Execute none at freeze stage. The independent directory is private. Root/developers may read only metadata expressly published by tester. Frozen assertions/recipes/scripts are never submitted for developer review. Local private key is never committed or copied to the hosted runner.

## Binding and immutable inputs

Required exact40-character product SHA and environment implementation/runner SHA, run URL, actual environment-check result with its precise scope and raw redacted capability receipts, fresh isolated context/credentials, original neutral packet SHA and unchanged authoritative spec/DDL hashes. A qualified environment has real MySQL8.4/RabbitMQ, four API workers, consumer, APScheduler and frontend/reverse proxy, no mocks replacing those integrations. Its success does not claim acceptance. Neutral documentation was read at2d09ea8ec6d3b7b81ce83260fe66e4ff686a2c56 only; future final environment SHA must be disclosed and syntax/capabilities may be independently inspected after binding.

Harness entry949_harness.py loads only sibling950_cases.json and independent947/948. It never imports product modules. It reads T44_ACCEPTANCE_CONTEXT and outputs private report.md/results.json/events.jsonl/trace.log. Context required neutral fields follow the documented protocol; manager_credentials_file supports flat username/password or access_token/token and nested credentials/session forms. Credential values stay private and are never passed as command arguments. init-user password goes stdin. Account and project IDs are actual returned IDs, never guessed. control_state passed only via T44_ACCEPTANCE_STATE.

Additional neutral context knobs are execution selection/adapters, not changed assertions:
- independent_phase: blackbox/fault/performance; also T44_INDEPENDENT_PHASE. Default blackbox.
- independent_fault_case: scan20, mq-fallback, api-restart, db-down, mq-duplicate; one bounded real scenario/job.
- independent_service_credentials_file: valid scoped service Token for tester-created project set, supported token/access_token key; no artificial manager privilege.
- independent_mq_topology: actual synthetic queue name and routing/wrapper metadata sufficient to identify a safely captured original message. This describes environment wiring, not expected test results.
- independent_performance.mode=prepare constructs independent API-only dataset (may take hours, separate from formalrun). No workload until separately authorized.
- independent_performance.fixture_file points tester-private prepared results load_fixture, same exact product SHA; dataset_counts_independently_verified=true only after tester inspects SELECT count outputs; cannot be set by developer to assert pass.
- independent_performance.run_kind=mixed/transition/validation/escalation selects one frozen400VU×600s steady run after60swarmup; run_kind cannot change thresholds. Need actual persisted scan_run_id for escalation, not a guessed UUID.
- independent_performance.server_resource_telemetry_file contains real server CPU/RAM/network/DB contention; hash retained, raw file separately encrypted via adequate approved evidence transport. Client /proc samples captured.

Unknown adapter syntax is a BLOCKED capability, not a failed SUT assertion. A later syntax-only adapter requires a versioned supplement preserving this freeze and all assertions; never edit these original bytes.

## Capability needs and outstanding limitations

Public API account/role/project/iteration/task setup; synthetic manager credentials; password stdin initialization; login/logout and revocation/expiry support; service escalation:write credentials with controlled project scope and revocation. Currently documented scheduler-scope rotates internal credentials but does not promise exposing a tester service Token: coordinator must provide neutral capability or mark service-only branch/performance blocked. No new product endpoint is invented for test convenience.

Read-only SELECT/SHOW/EXPLAIN over target schema, SHOW CREATE, safe target metadata in information_schema, transactions/session settings, raw rowset JSON with schema documented, scan_runs/outbox/events/notices/idempotency/audit access. Read-only audit connections are not used to mutate seed/state. DDL integrity later includes actual CHECK/unique/FK/index constraints; no disabling checks or writeSQL.

Leased stop/pause/recover controls for mysql/rabbitmq/api/consumer/scheduler/web,1–120s, explicit structured recovery_completed receipt and actual restart timing. Broker queue/connection metadata and real synthetic AMQP operations. A clean stop/start does not prove a mid-batch crash recovery; a lease that expired before observation does not prove fault active.

Beyond current neutral protocol: selective hold/release immediately before business commit, independent rejection-audit failure while auth/query DB works, COMMIT acknowledgement loss, expired idempotency owner takeover, publisher ambiguous confirm and consumer/fallback interleavings, controlled clock or strict UTC bracket. These are required to claim all declared conditional fault branches. Whole-service stop cannot substitute for selective fault. If unavailable, mark precise cases BLOCKED/NOT_RUN with no overallpass rather than inventing500/503 branch evidence.

Actual browser capability for UI; later explicit product-source/CI/coverage/merge-control/artifact review authorization. This freeze itself grants none. For formal performance, independent qualified load machine sustaining400VUs, server/client telemetry, sufficient disk, representative dataset preparation without900sjob truncation, four separate steady runs (at least44min plus setup) and longer/separate job scheduling. Never squeeze four runs into one900/1200sjob. Formal raw trace uses gzip binary trace.log; decode magic/struct as documented in948. Per-file20MiB archive limit is checked; if exceeded, preserve evidence and request adequate encrypted capacity before claiming formal reproducibility. Do not sample/drop failures or silently truncate raw traces to fit.

## Planned execution and local evidence hygiene

After tester receives exactbinding and neutral capability proof, verify942manifest hashes against local files, then later create isolated codex/independent-harness-v2 branch/worktree for an H commit containing only frozen public harness payload and certificate. Exclude943_recipient-private.pem even from git index. Root/developer may use only H metadata, not open contents. Actual H must be full40SHA and predates request R. No push or worktree is performed during this stage.

Future request R follows authorized neutral syntax only:
{"version":1,"mode":"harness","product_source_sha":"<exactSUT40>","harness_ref":"<frozenH40>","harness_path":"tmp/independent/private-v2/949_harness.py","recipient_certificate_path":"tmp/independent/private-v2/944_recipient.pem","harness_timeout_seconds":1200}

The runner request is a deployment JSON, not another testscript. It does not authorize altering the product or mainbranch rules. The independent tester may select bound phase knobs through a documented neutral context adapter/environment; if runner cannot supply them, defaultblackbox works and other phases are blocked pending capability. No source mutation to smuggle new assertions into H.

Only encrypted CMS artifact is public, certificateSHA and non-sensitive environment/control metadata permitted. Download within14days; private key stays local0600, directory0700. Certificate valid >=1h at run; expiry requires a separately versioned certificate supplement, never silently replace frozen certificate. OpenSSL CMS decrypt locally using944certificate and943privatekey; inspect tar listing/path traversal before extracting under a new private directory. Extracted files stay private and are not confused with originally frozen materials.

Review secrets/redaction and distinguish original failures/retries, exactSHA and environment state, reached/unreached preconditions, audit contents, missing operation positives/branch coverage and testharness errors. Reconcile raw schema logs and independent SQL; a code observed in response does not prove semantic branch assertions. Current script deliberately returns nonzero if phases remain not accepted and explicitly lists missing cases. A partial scriptedsubset is not the entire frozen plan; tester follows remaining frozen recipes under later capabilities. A PASS recorded by one subroutine means its executed assertions passed, not product acceptance.

Per-request formal trace includes every measured request; query and extra reschedulingpreparation writes are separated. Successful preparation HTTP calls are aggregate hash-chained/count/timing to avoid oversized private output; initial setup/error/case/control/SQL evidence remains explicit. Measured latencyraw samples are retained in trace.log. Pair four runs with exact reproducible commands, fixturehash/counts, servertelemetry and no threshold changes.

Only after complete independent review does tester explicitly publish a redacted report. Until then root/developers cannot open private cases/logs/scripts/outputs. The report has PASS/FAIL/BLOCKED/NOT_RUN/SPEC_AMBIGUITY/UNREACHABLE_BY_PUBLIC_API/SETUP_FAILED/HARNESS_ERROR, mandatory AC table, reproducible exactbinding commands and evidence hashes. Private artifacts remain unread even after reportpublication unless separately released.
