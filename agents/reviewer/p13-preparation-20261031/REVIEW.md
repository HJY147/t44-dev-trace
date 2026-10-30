# P13 PL1 preparation code review

Scope: local preparation review only. No independent black-box acceptance, QA PRIVATE, cloud, SSH, Docker or SUT access. No grant issued. Prompt reference: parent review_p13_preparation task, exact scope retained in handoff.

Reviewed final runtime bundle `.agent-worktrees/.runtime/p13-pl1-ready-20261031`: 32 manifest files, tar SHA256 `3c0b6548f9aefbe6299bd0834cba563806ba78d122febadfebf6bfd4fa788e25`. Continuation manifest SHA256 `78469dc7122f8864d11e382e20c2f475abbf6e4edf5582100b887f03f2ec6a65`; wrapper SHA256 `4f7c9b5b8c698dd2e741a33cf61626f2fc791b7603e81d181404d007bcbe0ab7`.

No blocking preparation defect found in reviewed bytes. This does not authorize live preparation or formal execution.

- verify_bundle.py completed with archive_bytes_verified=true, files=32, cloud_requests=0, benchmark_started=false. It checks exact file set, bytes/SHA, Python 3.10 syntax, shell syntax and archive bytes.
- Coordinator dispatch/observe compared to launch-ready-20261030: only r30manualp11 -> r30manualp13 changed. Original ENTRY SHA remains d15874c477fef0d92bc68ab77802a5354d15be237c853621b56467005c20d43e. Dispatch requires default-false original grant, exact grant equality with only allow changed, new output and an exclusive once-only channel. Failed attempts retain channel; no retry loop.
- New wrapper compared with manual12 wrapper: only exact maintenance06/material06 binding, output stage/path labels and p13 summary field changed. Original 11-tool pins and maintenance helper pin unchanged. Original800, service scope, schema layout/index, counts, restore-before-material, final health and preservation-on-failure guards remain.
- Builder requires source90b, three new run IDs, unexecuted and no-accounts/tokens/keys public declarations; checks every input file SHA; refuses existing output/archive and writes files exclusively. Public manifests/README describe remaining gates. Secrets declaration is provenance, not proof of live credentials absence; reviewed source includes only public metadata, templates and code, no literal credential/key material observed.
- Original measurement stays 400/60/600, P95 <=270ms, >=1000 requests per minute, zero business errors and original assertions. No benchmark or AB experiment ran. p12 references in new documentation explicitly forbid replay; wrapper enforces06.

Commands/results: diff -u old/new coordinator (two run-only differences); diff -u manual12/manual13 wrapper (changes above); python3 -B -m unittest discover -s agents/deployment/manual13-retest -p test_prepare.py (19 tests, OK, pure local mocked seams). An initial diff used deployment worktree for coordinator paths and failed with missing path; rerun from correct integration worktree succeeded. A subsequent rg of wrapper in integration worktree likewise had missing path, corrected to deployment worktree. No failed command interpreted as evidence.

Reviewer negative fixtures copied only public bundle into temporary directories. changed-run -> EXACT_P13_RUN_BINDING_REQUIRED; changed-file -> FILE_DIGEST_MISMATCH:READY_AFTER_BOOT.md; extra-file -> EXACT_FILE_SET_REQUIRED; symlink -> SYMLINK_NOT_ALLOWED. All four rejected, fixtures removed.

Live gates outstanding: effective PL1/disk ID/MySQL volume mapping, SSH authorization window, original seven actual identities and resources, current sessions/TLS, restore/material receipts, independent zero-SUT prepare and unique formal grant. User-reported40GiB/3800IOPS is not live verification. FINISHED is not PASS. This review binds only exact bundle bytes above.
