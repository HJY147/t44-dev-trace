# Independent offline audit checklist (frozen before implementation inspection)
1. Verify source hashes and preserve originals; inspect only neutral authorized sources.
2. Compare unchanged load generation: 400 clients, 60 seconds warmup and 600 seconds steady; preserve original metrics and assertions.
3. Compare every original per-task post assertion, 400 final snapshots, complete pagination, 40-second total post budget and schema compatibility.
4. Exercise offline negative cases for timeout/error/incomplete data; no false PASS.
5. Trace load task stop, HTTP sessions, validator processes and output writers through success/failure/timeout.
6. Verify total exit code and ability to seal failed evidence; effective identity includes every changed execution module.
7. Ensure historical records remain untouched. Distinguish static review, local execution and unperformed live acceptance.
