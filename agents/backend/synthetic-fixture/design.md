# Synthetic account fixture worker — design before implementation

Author/operator: backend AI. Local prompt reference: ROLE-backend-SYNTHETIC-FIXTURE-WORKER-v1. Base integration 6df6b3cd3bd026ebd9bb00f86a71f071724cac1f; application source C 0dfb55c2191200d947c5423fd9ee74bb0812cc5a remains unchanged.

Only deployment/synthetic-fixture.py is added as the worker; no host operations wrapper, product/CLI/Compose/lock/frozen changes. Pure local tests use reserved tmp/backend/850_synthetic_fixture.py. No database, cloud, HTTP, service or acceptance execution in this development phase.

## Inputs and trust boundary

- Explicit --database t44, --expected-source C, --certificate, --envelope-helper and --output-dir. UID must be 10001. Both T44_DATABASE and the parsed original C Settings database must equal the explicit t44 selection before connecting.
- Certificate and helper are public logistics artifacts, not acceptance cases. Only the three expressly published 852 files were read. Pin certificate PEM SHA 496ded07649d49078d9e20cebf4fbd80f989d5d2b777573857eb090d1b38af69, DER fingerprint f78e169a626c9eb3978428016996c2370ffd170b3f0cc83f3e96ba4bf199d19e and helper SHA 6a5ddf1226b7e08623a6d8131dbbf742a28359584a34a0e2cf4daa770c2966f7.
- Require absolute non-symlink paths, root-owned input files/parents not writable by this worker or group/others; private output directory owned by current UID, mode0700. Open directory descriptor and create only fixed basenames with O_EXCL/O_NOFOLLOW/mode0600; fsync files and directory. Existing pending/final/status files cause fail-closed before DB access. No overwrite or destructive cleanup.
- Expected source is a declared input, not proof of the full image. Additionally verify installed t44.cli file SHA da88377aed1131fb82aea31ef2783e02af01c6b620518f3d1b9e8b01175112db. Root delivery owns full image/mount provenance.

## Execution boundary (not executed here)

1. Validate all public inputs/output/source/database first. Use only original C persistence factory/Gateway read methods for preflight: all business tables empty and all three exact usernames absent. Users/sessions/service accounts are not classified as business fixture rows. No internal account writes are called by worker.
2. Generate three independent token_urlsafe(32) passwords in memory. Encrypt a neutral-environment pending recovery package using the exact public helper before any account creation. Include source/username/password/role labels, explicitly pending/not an initialized environment. Do not print plaintext or key material.
3. Sequential subprocess argv is sys.executable -B -m t44.cli init-user --username ... --display-name ... --password-stdin. Password is supplied only as anonymous subprocess stdin; stdout/stderr stay captured in memory. Accept only exit0 and exactly one valid positive user_id object. Never retry; unique failure or uncertain outcome stops. Previously confirmed accounts remain; no reset/delete/skip.
4. After all three confirmed creations, encrypt a new final package including returned IDs. It contains no sessions and makes no seed/project claims. Pending recovery ciphertext remains. Create a separate safe status receipt and print only sanitized stage/error/exit/public IDs/hashes. Seed and scheduler scope issuance are separate later authorized operations.

There is no single transaction across three CLI invocations and the output filesystem. Partial creation or lost commit ACK cannot be rolled back by worker. Pending ciphertext is the recovery record; final encryption/publication failure does not undo users. Python memory clearing is best-effort, not protection against server root inspection. No private recipient key is available or read.

## Local validation plan

Use synthetic temporary files and a freshly generated local test certificate/private key entirely in memory, never tester private key. Tests cover pinned-public input rejection, symlinks/modes/owner/O_EXCL, strict declared database/source, empty/existing-user preflight with synthetic Gateway, success/partial/ambiguous CLI replies, stdin-only secrets, pending-before-CLI ordering and final decryption/absence on failure. Simulated dependencies are explicitly test-only; no claims about actual MySQL/CLI/container execution. Save any original failures and final exact commands/results. Do not rerun unrelated suites, CI or load.
