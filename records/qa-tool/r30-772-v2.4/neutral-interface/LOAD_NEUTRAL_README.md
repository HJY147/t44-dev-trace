# Neutral package adapter for the existing LOAD (772-v1)

This is a public transport/input/authorization adapter. The sealed benchmark source, cases and metrics remain unchanged. No UI, cloud or SUT action has been taken by this tester. The root-coordinator receipt confirms private installation of the original seven-file capsule; it does not constitute a benchmark result.

Run LOAD_NEUTRAL_ADAPTER_INSTALL.sh through the coordinator's cloud-assistant UI. It installs only two PUBLIC generic files and performs a --network none platform probe, reporting the actual Python version, Linux architecture, SSL and cgroup ceilings. It reads no neutral/private input and no installed private source. Only a received Linux receipt can establish Python 3.12 compatibility; local syntax/synthetic-input checks alone do not establish that. PUBLIC_LINUX_READ_ALLOWLIST.json names the exact public reports root may read. The platform probe is not the grant-consuming benchmark preflight.

After the package is READY and the tester receives the separate path/tab authorization, prepare with:

```sh
sh /root/t44-r9/independent772/public/LOAD_NEUTRAL_ENTRY.sh prepare --neutral-opened-dir /root/t44-r9/neutral-opaque-load-r29-01/opened-neutral --run-id NEW_RUN_ID --origin https://ACTUAL_STRICT_TLS_ORIGIN
```

The adapter reads only inputs/session.private.json and inputs/ca.pem from that supplied directory. It supports schema (or kind) NEUTRAL_772_INPUTS_V1 and the sessions/inventory/additional_neutral_snapshots/counts/fixture_sha256/source_sha/binding_sha256 fields. The inner session and inventory shapes are the already frozen ENVIRONMENT_SCHEMA.md shapes; an omitted inventory schema is normalized to 772-inventory-v1 without changing snapshots. Additional neutral snapshots are preserved privately. The explicit --origin is only necessary if the neutral packet does not carry origin. APP private connect IP is the provided 172.21.182.245. Preparation is --network none, creates only private input copies plus a default-false grant, and performs no SUT calls.

Identities are distinct: env.identity.source_sha256 is the actual source manifest SHA256 3368534aececbb5441225e7859338aa3079b6e41798e38673bd8f337f8993577; the separate Git commit is f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f and 53-file proof hash b208b86abe657570b3125944274e45f1ecd806537985bea1c34b7deea8e5d5d6. env.identity.image_digest is SUT image sha256:a7d3dde54efda1405bbd7d9f5f5b7c5a6439f1afd1dc8c50b2ed8b37625fa5da. The executing source-free Python container remains LOAD image sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1. No SUT source file is inspected to establish those neutral identities.

Only after the separate explicit one-time SUT authorization, execute:

```sh
sh /root/t44-r9/independent772/public/LOAD_NEUTRAL_ENTRY.sh execute NEW_RUN_ID --authorize-once NEW_RUN_ID
```

This writes exactly one true grant bound to the private environment bytes and frozen runtime digest, then execs the installed private runtime once. Existing grant/receipt blocks a second invocation. There is no login, session extension, retry, restart or successor run. Each actual session expiry is rechecked against the complete new window.

The new window is at most 900 seconds, ends by 2026-10-29T04:54:49Z (90 seconds before the fixed cost stop), and must still contain at least 780 seconds for setup + 60s warmup + full 600s steady + bounded drain/postchecks. At this cost stop the latest eligible start is approximately 04:41:49Z; a later invocation gives NP before any SUT request. The 600-second steady period is never shortened to fit. Expiry after 04:56:19Z covers any eligible new window. Root reads only the public aggregate receipts listed in PUBLIC_LINUX_READ_ALLOWLIST.json; input accounts, IDs, source and evidence remain private.
