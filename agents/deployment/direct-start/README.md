# APP direct initialization

This is **DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE**, explicitly authorized by the user's changed workflow. It does not claim original full preparation, eligibility, horizon or scanner admission. Production source/authentication/business dates and the independent 400-client, 60-second warmup + 600-second steady measurements remain unchanged.

Transport this directory plus `agents/backend/fast-bootstrap/{bootstrap.py,runtime_support.py}` from backend commit53acbb28 to APP. The entry hashes those two exact files before any Docker command. No image import, pull, rebuild, configuration/PL1 change, seven-role reinspection, maintenance, full-scan wait or cloud/SSH operation is implemented. Existing IDs are the actual bcec deployment IDs retained from the previous run. This entry is only for that retained deployment.

As root on APP, after normal host boot:

```sh
python3 -B /root/t44-direct-start/start.py \
  --backend-dir /root/t44-direct-bootstrap \
  --run-id NEW_DIRECT_RUN_ID \
  --output /root/t44-direct-start-output/NEW_DIRECT_RUN_ID
```

Create the root-private parent `/root/t44-direct-start-output` once when installing the entry. The run output itself must be absent; each invocation needs a fresh run ID/output. `--backend-dir` and `--output` must use canonical absolute paths. There are no hidden environment parameters or host credentials.

Sequence: `docker --context default start` known MySQL/MQ/TLS/API/web IDs (already-running containers are not restarted); execute neutral backend bootstrap once with original P09 initialized accounts/packet/CA, original receipt provenance, API ID and TLS gateway DNS `tls-gateway`/port8443; check successful current `DIRECT_INPUTS_V1` matching run/source; compare service session to the original CLI `access_token`; install the CLI file's exact bytes by fsynced atomic replace; finally start the known consumer/scheduler IDs. It does not poll health or scan readiness or retry startup/bootstrap. If boot services are not ready, normal bootstrap can fail; that is an initialization failure, not an invented performance result.

Token target is fixed `/root/t44-final-20261029/P09/campaign/p/scheduler-secrets/scheduler-token.json`. Preserve its uid/gid and0600; save exact old bytes under the new run's private `rotation/`; fsync backup, temporary credential, rename directory and read back installed bytes. Temporary token is in the same directory as the target. No token is printed; subprocess stdout/stderr remain0600. These guarantees do not make bootstrap issuance, rotation and Docker startup a single transaction. A failure retains partial changes/private backups and stops the chain. No automatic rollback, retry, shutdown or timer exists. The backend's own bounded command execution is unchanged and never shuts down a VM.

Successful stdout is a secret-free `INIT_DONE` JSON with bootstrap output/input paths. Root then transports `bootstrap/current-inputs.private.json` through the existing private transport and hands it to the independent direct runner immediately; this entry does not launch benchmark/claim acceptance. Failed execution returns nonzero with `INIT_FAILED` and no exception text/credential output. `FAILED.PUBLIC.json` identifies the failed phase; inspect retained private stderr only through the authorized private channel. Do not run another initializer concurrently against the same token file.

## Actual offline checks

`python3 -B agents/deployment/direct-start/offline_checks.py`: five groups pass, including full mock subprocess path, real temporary filesystem atomic replacement/ownership/mode/backup, infra/bootstrap/worker failures with no retry, replace failure stopping workers, mismatched service credential, wrong tool SHA and existing output rejection. No Docker daemon, SSH, VM, TLS/MySQL or pressure call occurred. Python3.10 AST parsing passes. `ruff` is absent from PATH; no Ruff result claimed.

First local check run had four passing groups and one test fixture error (expected ValueError for a missing source file; actual FileNotFoundError). The fixture now writes a wrong-source file and verifies hash rejection before any command; five groups pass. No production failure was hidden or retried.
