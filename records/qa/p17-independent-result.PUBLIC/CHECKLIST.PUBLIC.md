# P17 independent frozen verification checklist
Frozen before opening result ciphertext or result records. Offline only; no SUT/network/re-run.
1. Verify receipt/ciphertext length and SHA256, authenticated decryption, member inventory, hashes and raw authentication.
2. Bind run r30posttools17, product bcec3326b40814fdb1922bbfea7c29473b47ba47 and manifest runtime base/post/compiled/boot identities.
3. Require actual 400 clients and 60 second warmup plus 600 second steady observation; four operation P95 <=270ms, each of ten completed steady minute buckets >=1000 and zero steady errors.
4. Require 400 final snapshots and 400 complete audits under original 40 second budget; distinguish outer exit, threads, phase, actual measurement and post verification.
5. Locate actual exception and timeline; incomplete measurement is NP, observed failed gate is FAIL, only evidenced satisfied gates PASS. Do not infer unavailable metrics.
6. Publish redacted evidence, conclusions and duties; never publish key/token/private payload/cases. Preserve originals.
