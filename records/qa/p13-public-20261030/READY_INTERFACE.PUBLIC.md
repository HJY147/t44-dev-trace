# P13 independent PUBLIC offline interface

Status: OFFLINE_PREPARATION_ONLY. No real identity, packet, prepare, independent decision, allow=true grant, cloud observation, SUT action or performance conclusion exists for this round. All execution approvals remain false. User formal-retest authorization does not replace independent current-evidence admission. No SSH/cloud/SUT actions are authorized in this preparation task.

Identifiers: QA `r30manualp13`; neutral material `r30materialresume06`; maintenance `r30restoretransition06`. W remains `/root/t44-final-20261029/QA753MANUAL10`. Local PRIVATE is `tmp/753_p13_independent_20261030/PRIVATE` (not published). Older run `r30manualp12` must never start again.

## Unchanged measurement and tool boundaries

400 clients; 60-second warmup; 600-second steady interval; P95 <=270 ms; every measured minute >=1000 requests; zero business errors; all original tool assertions. No reduced load, worker tuning, bypass, core or assertion change. Existing tools may be reused only if all frozen hashes match and W is complete and exclusive; do not reinstall into existing private_tools. No old PRIVATE, raw results or other roles' cases were read. No new measurement cases were designed or published.

Public wrappers are exact p12 PUBLIC bytes except `r30manualp12` -> `r30manualp13`. OBSERVE bytes are unchanged. ENTRY SHA `d15874c477fef0d92bc68ab77802a5354d15be237c853621b56467005c20d43e`; ADAPTER SHA `a4cbb793ac6ecb292ad6d4c6451052b051a1ea50fbf798ccad4463b92173fc1c`; original tool-manifest SHA `78a0aca6e90b61695338a332f7adb1becb5f7eebd13d0c8bd28d3f6ff4f09a05`. Tool runner image remains the original `sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1`; this is not a claim about the current product image. Frozen measurement core is not accessed or changed by offline preparation.

## Current neutral evidence intake: required before identity

Submit exact originals and SHA256, collection UTC, actual host/container identity and explicit missing items. Source, product image and actual DB state for this round are UNDETERMINED. A renamed old profile is not approval; old schema supplement review is not current approval.

1. Current APP seven owned roles: actual container IDs, immutable image descriptors -> config digests, current source commit and exact source manifest, backend bundle manifest, source-to-image mappings, original or fresh actual import receipt and import provenance. Preserve original bytes; do not rewrite an old receipt. Current package identity must be supported by the unchanged original verifier; incompatible identity blocks admission.
2. Current APP/DB CPU and memory settings, ownership and exclusions; APP64-core/DB budget; current LOAD image, actual CPU/memory and fixed 8 CPU/8 GiB execution budget; current no-other-writer/no-other-run evidence. An observation from a previous round does not establish current facts.
3. Actual isolated schema name, exact DDL/migration SQL and SHA, actual execution receipt/time, real before/after SHOW CREATE TABLE/index/constraint originals and SHA, schema fingerprint, semantic comparison to frozen v1.2 DDL/field/persistence contracts, exact supplemental manifest binding all original evidence. Missing before-state must remain marked missing. Migration is not proof it was baked into an image. Supplement not understood by original V4 is additional independent review, not an original-tool assertion.
4. Four current real sessions: subject, role, project/service scope and actual expiry; secrets only in sealed neutral packet, never in PUBLIC or coordinator-visible plaintext. Current 400-client/800-distinct-task eligibility and project distribution, actual task state/owner/current plan/end, escalation event/schedule/rule, fixture SHA and actual counts, isolation and demo-volume facts.
5. TLS origin/connect IP, exact CA SHA, actual valid certificate and validity; neutral sealed material transport receipt and bindings for this new material/maintenance/QA chain. Fresh opened inputs: `session.private.json`, `ca.pem`, `source-manifest.json`, `backend-bundle-manifest.json`, `backend-import-receipt.json`, each exact byte SHA. Packet runtime original and target/grant V4 identities stay separate and must match original interface requirements.
6. Current collected bytes must support the identity profile's required original format and true observation timestamps. Independent tester then signs `TARGET_PROFILE_753.json` run_id=r30manualp13, phase=p and `APPROVAL_753.json` binding exact target SHA, ADAPTER SHA, and actual supported source. `approved=true` if eventually issued means IDENTITY_ONLY_FOR_ZERO_SUT_PREPARE only; functional_authorized, benchmark_authorized and grant_allow remain false; manual_start_protocol=753-ready-manual-once-v1. Nothing signed now.

## Deferred zero-SUT prepare

Paths: public scripts `/root/t44-manual13-public`; independent identities `/root/t44-manual13-identity`; opened packet `/root/t44-material-r30manualp13/opened`. Do not execute before independent current identity review. `--check-only` checks public bindings and new paths only; not packet or installed tools or cloud.

```sh
python3 /root/t44-manual13-public/PREPARE_REUSE_753.py --workspace /root/t44-final-20261029/QA753MANUAL10 --identity-dir /root/t44-manual13-identity --packet-opened /root/t44-material-r30manualp13/opened
```

Wrapper verifies original ENTRY/ADAPTER SHA and fresh runs/results/phase/history paths. It verifies installed frozen tools using original runner with network none, preserves both prior public identity originals under `identity-history/r30manualp13-before-bind`, then calls original ENTRY prepare. Existing history/results/grants stay untouched. No cleanup or automatic retry after partial failure.

Return original PREPARED_DEFAULT_FALSE stdout, full default-false grant and SHA, environment file SHA only, five input hashes/bindings, resource/exclusion evidence and new-output/unconsumed metadata. No tokens/private test content. Re-review exact current schema supplement/fingerprint against identity record and actual facts after prepare.

## Independent one-time grant and execution

Only independent tester may form decision status INDEPENDENT_CURRENT_NEUTRAL_REVIEW_APPROVED_ONCE with current run_id, exact default_false_sha256, environment_sha256, reviewed_utc, minimum_real_session_expiry, latest_trigger_before_utc, and all seven reviewed=true keys named by ISSUE_ONCE_753.py. Also bind current schema supplement SHA/fingerprint and exact reviewed evidence in decision audit. Coordinator cannot self-attest this decision. Current identity/source/image/schema/sessions/input/exclusion changes invalidate admission.

```sh
python3 ISSUE_ONCE_753.py grant.default-false.json independent-decision.json grant.r30manualp13.approved-once.json
sh /root/t44-final-20261029/QA753MANUAL10/public/ENTRY_MANUAL_753.sh execute /root/t44-final-20261029/QA753MANUAL10 r30manualp13 /root/t44-manual13-identity/grant.r30manualp13.approved-once.json
```

Not executed now. Original default false allow alone changes to true; no other grant fields change. Trigger strictly before four-session minimum actual expiry minus 900 seconds and independent decision deadline. Original V4 rechecks actual expiry/input; old packet window is provenance. Consume once, no retry/successor/relaunch, no rewriting old packet/grant. Public execution stdout only run_id/metrics_verdict/full_cohort/independent_conclusion; stderr PRIVATE.

## Public phase, sealing and return

```sh
python3 /root/t44-manual13-public/OBSERVE_PHASE_PUBLIC_753.py /root/t44-final-20261029/QA753MANUAL10 r30manualp13
mkdir -p /root/t44-sealed-manual13
sh /root/t44-manual13-public/SEAL_753.sh /root/t44-final-20261029/QA753MANUAL10 /root/t44-sealed-manual13/r30manualp13.753backup EXITED_ALL_WRITERS_STOPPED
```

RUNNING400 means readiness barrier released, not simultaneous HTTP/current live400/600-second completion/PASS. FINISHED is not PASS. Seal only after actual original process exit and all W writers stopped, including operator-channel/evidence-neutral. Third argument is truthful operator declaration; wrapper alone cannot prove all writers stopped. Original backup CLI `backup.py workspace output` runs network none with W read-only and output external; includes old evidence without deleting it. Return only cipher and `.753backup.receipt.json`; never private key/results.

In new independent PRIVATE only, frozen verify tool with same-directory runtime and original key validates exact receipt SHA/bytes, decrypt footer/compressed stream and every file SHA. Extraction path must not exist:

```sh
python3 /independent/PRIVATE/verify_backup.py /independent/PRIVATE/r30manualp13.753backup /independent/PRIVATE/backup.key --extract-dir /independent/PRIVATE/recovered-r30manualp13
```

Successful decryption proves integrity only. Independent tester assesses original p13 results and all cohort/measurement assertions; publish complete-cohort, performance and independent conclusion separately. No original tool implementation, cases, raw result or secret published.
