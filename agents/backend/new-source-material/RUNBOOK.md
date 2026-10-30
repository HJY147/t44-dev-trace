# Material08 dual-source transition interface (offline prepared only)

Old material packets and prior p13/07 outputs remain untouched. This is not a product source change or QA approval. Candidate identities are p14/material08/maintenance08; actual paths must be absent and independently reviewed. Existing DB/campaign,800 IDs/counts and original roles/eligibility remain. Only material runtime files are derived from the immutable old6owner files; process_guard/runtime_support/refresh_runtime HTTP eligibility loops remain except explicit new source checks.

## Sources and inputs

Old session.private.json remains source90b and exact original raw SHA/binding; it supplies historical original task/subject/scope/count provenance. Do not rewrite it to13ac. New source-manifest and bundle-manifest come from verified locked-task-13ac build, exact raw SHA pinned in refresh_core. New actual backend-import-receipt is produced on APP by immutable e523 final-image-bundle.py import_bundle; local CI proof is not an APP import receipt. New reference must contain actual original_path/observed_at/raw SHA, not copied old values. Actual API ID/config and revision are read by host_runner, container-side all backend_runtime_files raw SHA are checked before credentials.

Populate authorization.TEMPLATE.json only after current neutral admission: default root_approved=false, no nonce/oldpacketSHA/identity/receipt/time has been preissued. Full new_identity explicitly supplies git13ac/sourceSHA/bundleSHA/config766701.../OpenAPI; packet runtime is legacy81e046... transportation identity, NOT v5.2 execution core9cf747.... LOAD identity is fixed4f3... but still needs actual current host/image verification. QA profile/grant9cf remains independently issued by QA. runtime/source/manifests and fresh receipt chains are separate.

Missing live originals: new actual import+observation, original800 current versions/states/owner/role/plan/event/rule and stable horizon, DB schema/index/count/fingerprint, current7service container/config resources and no-other-writer, actual CA/service certificate current validity, LOAD actual image/8CPU budget, real4session issue/expiry/scope, scheduler credential rotation and completed post-rotation scan proof, exclusive new output/no consumed prefix. These cannot be marked true offline.

## Executable local preflight

```
python3 -B /BUNDLE/backend/check_inputs.py --old-packet /HISTORY/inputs/session.private.json --authorization /CURRENT/material08-authorization.json --ca /CURRENT/ca.pem --source-manifest /CURRENT/source-manifest.json --bundle-manifest /CURRENT/backend-bundle-manifest.json --import-receipt /CURRENT/backend-import-receipt.json --import-observation /CURRENT/backend-import-receipt.json.observation.PUBLIC.json --remote-import-receipt-path /root/ACTUAL_CURRENT/backend-import-receipt.json
```

Runs no Docker/network and releases no session; default false template refuses. Real credentials stay in files, not stdout. No preflight can prove supplied receipt is a true current APP observation without separate owner/independent verification.

## Later admitted APP material generation (NOT executed now)

```
python3 -B /BUNDLE/backend/host_runner.py --api-container ACTUAL_CURRENT_API_ID --expected-api-image-id sha256:766701c81ee873258930346b1fa30986035dd341810ad170a2bcca271ee088fc --discover-maintenance-gateway --old-packet /HISTORY/inputs/session.private.json --accounts /HISTORY/accounts.private.json --authorization /CURRENT/material08-authorization.json --ca /CURRENT/ca.pem --source-manifest /CURRENT/source-manifest.json --bundle-manifest /CURRENT/backend-bundle-manifest.json --import-receipt /root/ACTUAL_CURRENT/backend-import-receipt.json --import-observation /root/ACTUAL_CURRENT/backend-import-receipt.json.observation.PUBLIC.json --output /NEW/material08
```

Root/private staging, bounded GNU timeout/process exit proof, partial prefix preservation and exclusive output behavior are inherited. On any failure preserve everything; no overwrite/retry. Host emits only original safe material summary; runtime private stdout stays root-private. Fresh packet identity/schema/new receipt reference are rebuilt explicitly, historical identity retained only in additional provenance; original inventory/4sessions/800disjoint/canonical binding gates retained.

This tool does not install the new product, change seven-service identities, perform cohort repair, rotate scheduler file, prove full scan, seal CMS, sign QA identity/grant or start QA. Deployment owner must explicitly adapt current exact source pins and complete those original phases. In particular old maintenance helper pins old host_runner bytes: do not replace them under its old manifest.400/60/600/all original assertions remain. No live authorization is issued here.

## Offline checks

python3 -B offline_checks.py:7 pure synthetic checks using real source/bundle originals and a synthetic receipt; positive dual chain/old-byte preservation, default false and consumed IDs, history source mismatch, changed source/bundle/import raw bytes, wrong config/runtime and stale receipt reference. All runtime Python parsed under3.10 grammar. These do not prove live file permissions/session/scan/import truth, full end-to-end material08 or acceptance. No cloud/SSH/Docker/SUT called.

## Reviewed reference binding correction

a60b2d28 had a verified preparation-tool defect: new receipt bytes could be combined with arbitrary /root/ reference and a future timestamp. The reviewer synthetic reproduction remains historical evidence; original OFFLINE.log7check report is retained, not rewritten. This fix adds producer observation as an explicit input. APP host requires actual receipt canonical path==auth reference==producer receipt_path; original actual file sha/bytes/uid0/mode0600/mtime_ns must match observation and all three observation times must agree. Core additionally requires legal UTC and nonfuture observed_utc, without a maximum-age policy. New reference path cannot be historical packet receipt path. All checks run before Docker/session issuance.

Local downloaded copy preflight uses mandatory --remote-import-receipt-path and verifies reference/producer path+raw SHA/bytes; it explicitly does not equate local copy path/mtime/ownership to remote original. The original positive host filesystem observation cannot be proven on this macOS local copy; actual APP stat remains pending.9 synthetic checks now cover legal actual13ac source/bundle with a fake import observation, wrong old path/ref/hash/size/uid/mode/mtime, host rejecting a local path, future/nonUTC/malformed timestamps, wrong source/config/runtime and default false/consumed IDs. No real import or source08 material was created. All8 scripts parse Python3.10.
