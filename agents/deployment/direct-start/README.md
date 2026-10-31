# APP direct initialization

This is **DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE**, explicitly authorized by the user's changed workflow. It does not claim original full preparation, eligibility, horizon or scanner admission. Production source/authentication/business dates and the independent 400-client, 60-second warmup + 600-second steady measurements remain unchanged.

Transport this directory plus `agents/backend/fast-bootstrap/{bootstrap.py,runtime_support.py}` from corrected backend commitdfef9a825ed2622f894a77187b686164bf162ecf to APP. The entry hashes those two exact files before any Docker command. No image import, pull, rebuild, configuration/PL1 change, seven-role reinspection, maintenance, full-scan wait or cloud/SSH operation is implemented. Existing IDs are the actual bcec deployment IDs retained from the previous run. This entry is only for that retained deployment.

As root on APP, after normal host boot:

```sh
python3 -B /root/t44-direct-start/start.py \
  --backend-dir /root/t44-direct-bootstrap \
  --run-id NEW_DIRECT_RUN_ID \
  --output /root/t44-direct-start-output/NEW_DIRECT_RUN_ID
```

Create the root-private parent `/root/t44-direct-start-output` once when installing the entry. The run output itself must be absent; each invocation needs a fresh run ID/output. `--backend-dir` and `--output` must use canonical absolute paths. There are no hidden environment parameters or host credentials.

Sequence: stop only the two known consumer/scheduler containers first (including workers automatically started by reboot restart policy); `docker --context default start` known MySQL/MQ/TLS/API/web IDs (already-running containers are not restarted); wait at most30seconds for basic read-only connections, then execute neutral backend bootstrap once with original P09 initialized accounts/packet/CA, original receipt provenance, API ID and TLS gateway DNS `tls-gateway`/port8443; check successful current `DIRECT_INPUTS_V1` matching run/source; compare service session to the original CLI `access_token`; install the CLI file's exact bytes by fsynced atomic replace; finally start the known consumer/scheduler IDs. It never waits for business eligibility or scanner readiness and never retries bootstrap/session issuance. Basic cold-start connectivity alone retries before any session operation: API-container SELECT1 plus strict original CA/SNI TLS gateway8443 OPTIONS /api/v1/projects expecting405 with nonempty Allow containing only POST/GET plus exact JSON detail Method Not Allowed. bcec has no /health endpoint; OPTIONS405 stays in the FastAPI router and avoids Runtime rejection auditing (an unauthenticated GET401 would write an audit event). Reject404/503/405 without a valid Allow or exact router body. Internal readiness budget28seconds, container command29seconds plus1second kill grace, outer subprocess30seconds; these bound only the read-only initialization probe, never a VM or benchmark. Timeout fails and preserves the exclusive run output without calling bootstrap.

Token target is fixed `/root/t44-final-20261029/P09/campaign/p/scheduler-secrets/scheduler-token.json`. Preserve its uid/gid and0600; save exact old bytes under the new run's private `rotation/`; fsync backup, temporary credential, rename directory and read back installed bytes. Temporary token is in the same directory as the target. No token is printed; subprocess stdout/stderr remain0600. These guarantees do not make bootstrap issuance, rotation and Docker startup a single transaction. A failure retains partial changes/private backups and stops the chain. No automatic rollback, retry, shutdown or timer exists. The backend's own bounded command execution is unchanged and never shuts down a VM.

Successful stdout is a secret-free `INIT_DONE` JSON with bootstrap output/input paths. Root then transports `bootstrap/current-inputs.private.json` through the existing private transport and hands it to the independent direct runner immediately; this entry does not launch benchmark/claim acceptance. Failed execution returns nonzero with `INIT_FAILED` and no exception text/credential output. `FAILED.PUBLIC.json` identifies the failed phase; inspect retained private stderr only through the authorized private channel. Do not run another initializer concurrently against the same token file.

## Actual offline checks

`python3 -B agents/deployment/direct-start/offline_checks.py`: seven groups pass, including full mock subprocess path, real temporary filesystem atomic replacement/ownership/mode/backup, stop/infra/readiness/bootstrap/worker failures with no retry, replace failure stopping workers, mismatched service credential, wrong tool SHA and existing output rejection. A local temporary TLS server and generated test certificate validate delayed TLS/API availability, exact OPTIONS method/CA/hostname checks, wrong404/missingAllow rejection; mock DB first refuses then succeeds. Fake-clock deadline and late success fail closed; readiness failure traces show no bootstrap/session operation. No Docker daemon, SSH, VM, real MySQL or pressure call occurred. Python3.10 AST parsing passes. `ruff` is absent from PATH; no Ruff result claimed.

First local check run had four passing groups and one test fixture error (expected ValueError for a missing source file; actual FileNotFoundError). The fixture now writes a wrong-source file and verifies hash rejection before any command; seven groups pass. No production failure was hidden or retried.

Review fix: cold-start readiness and reboot-auto-started workers were missed in the first entry. Explicit stop precedes bootstrap/rotation; bounded read-only connectivity precedes the unique bootstrap. Initial local proposal used GET401; root identified rejection audit writes before any live execution, so final probe uses router OPTIONS405/AllowPOSTorGET. No production/API source was modified.


## Live failure retained; narrow route-method correction

Root reported the first real direct invocation stopped at readiness before bootstrap/pressure: read-only SELECT1 and original TLS/CA succeeded, but the production OPTIONS response was405 `Allow: POST`, body `{"detail":"Method Not Allowed"}`. The earlier probe incorrectly requiredGET. Its local TLS stub echoed that assumption and missed real router ordering. The old failure prefix stays unchanged; this deployment agent did not connect remotely for diagnosis or rerun it.

Actual bcec API SHA256 `974ede3d838b1cd865dd1af863a2a7a44ba12c2c26973d5397d16ddf86ba73b4` matches its Git blob. Cached local FastAPI0.161.1/Starlette1.9.0 TestClient shows real bcec route orderPOST thenGET, and405 reports only the first partial match. `router_checks.py` uses that exact API and asserts no Runtime.execute call, then tests actual FastAPI both registration ordersPOST/GET andGET/POST. The final probe permits a nonempty Allow method set confined toPOST/GET and the exact standard router405 JSON. It still rejects noAllow,404,503,DELETE and arbitrary/malformed405 bodies; all TLS checks/deadlines are unchanged. A response alone is connection readiness, never image/source or performance acceptance proof.

Executed entirely locally:

```sh
python3 -B agents/deployment/direct-start/offline_checks.py
# seven groups PASS, including the existing deadline/late-success checks
/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/database-scale-r29-venv/bin/python -B agents/deployment/direct-start/router_checks.py
# three real router groups PASS; cached TestClient emits its existing httpx deprecation warning
```

No SSH, real Docker/VM, bootstrap/session issuance, production mutation or benchmark was executed. API/identity/thresholds remain unchanged. These checks fix the reproduced readiness false rejection; they do not claim a successful live restart.


## Canonical UTF-8 helper synchronization

The first live legacy helper failed historical packet binding when Chinese data was encoded with its ASCII-escaping canonical serializer. Root's subsequent successful run used a new exclusive `utf8-tools` start.py derivation pinned to the corrected helper. It was not the unchanged original deployment package succeeding directly. Original failure and successful derived-tool evidence remain under root's actual run records.

The formal entry now pins corrected backenddfef9a82 `bootstrap.py` SHA256 `cc94bea2ba0699cf0c81b3cf5ac6c5ffe3277ee2a6b78e100885cee7c5475d27`; runtime support stays byte-identical. Historical canonical binding remains UTF-8 `ensure_ascii=False`, sorted compact JSON plus trailing newline; the separately recorded original_packet_sha256 hashes the entire original file bytes including its binding field. Neither check is removed or substituted.

`python3 -B agents/deployment/direct-start/unicode_checks.py` passes two integration tests: real direct entry→real corrected host bootstrap main using a complete synthetic historical400-client packet containing Chinese→one mocked container execution→actual host output rawhash→actual temporary-file atomic token rotation. A Chinese-text mutation with unchanged binding fails before any container/session invocation, retains failure prefixes and does not rotate/start workers. Only the external container execution is mocked; this is not live authentication or benchmark evidence. The backend's existing public complete fixture is used locally by this regression, not QA private data. Existing seven direct-entry groups and three actual bcec router groups pass with the new pin. AST Python3.10 parsing passes. No SSH/cloud/real Docker operation or request to boot was made for this change.
