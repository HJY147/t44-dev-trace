# 90b734f6 official CI evidence review

Reviewed at 2026-10-29T18:21Z. Scope: archive and verify already completed official runs; no rerun, cloud, QA PRIVATE or acceptance action.

Product run [40928297882](https://github.com/HJY147/t44-dev-trace/actions/runs/40928297882), attempt 1, push, exact head 90b734f65ce6ee9f5c217e885bc7ea4857e32b48: static/contracts/coverage/frontend all success. Original JUnit: coverage 797 tests; contract 184, fault 19, integration 102, each errors/failures/skipped 0. Contract groups overlap the coverage suite and are not added to 797. Frontend test-results: 89 passed, zero failed/pending/todo; 15 reported suites, four result files containing 89 assertions.

Backend coverage JSON/XML: line 2485/2754 = 90.23238925199709%; branch 719/852 = 84.38967136150235%; excluded_lines=0. Combined coverage.py percent_covered is 88.85191347753744%, not the line rate. Frontend line 364/390=93.33%, statement 631/712=88.62%, function 206/240=85.83%, branch 821/932=88.09%; all reported skipped counters zero. No test execution, skips, exclusions or assertions were changed by reviewer.

Docker run [40928465279](https://github.com/HJY147/t44-dev-trace/actions/runs/40928465279), attempt 1, pull_request: docker-application success; resume-source-context, cloud-bundle, offline-source-context skipped as the original workflow reports. API head_sha is 90b, but decoded official job log and original result.json prove actual checkout 56217f14568c7cd5ac6e83aaf4d890883e755ef9, PR46 merge with ordered parents bdaa814c4f908cc9f5b5af56d6aee1009b955623 and 90b734f65ce6ee9f5c217e885bc7ea4857e32b48. Git comparison of backend/frontend/specs/deployment/986_http.py is empty between merge and 90b. This is hosted-Linux synthetic Compose evidence on the matching product bytes, not a pure-90b checkout, target APP loaded proof, independent acceptance or pressure result. Docker result passed=true; its expected shared-flock negative step has exit 1 and is retained, not counted as a failed workflow.

Five connector-downloaded original ZIPs verified against official API byte sizes and SHA256 digests; all 128 members hashed in zip-manifest.json. Original XML/JSON and entire ZIP bytes retained. GitHub connector fetch responses are retained as unmodified response content; decoded job log retained separately. First local urllib download failed certificate trust before bytes; system curl with normal TLS verification succeeded, no insecure flags. See initial-download-error.txt.

Evidence: records/ci/90b734f6-40928297882/{product-run,product-jobs,product-artifacts,docker-run,docker-jobs,docker-artifacts,zip-manifest,summary}.json and original ZIP/raw members. No image bundle was downloaded or imported in this task.

Decision: exact native product CI success verified; Docker success verified with explicit merge-checkout qualification. No global reviewer/stage, target/live or release approval.

Archive whitespace check: full staged diff-check exit2 only for seven original decoded job-log trailing-space lines, preserved; excluding that raw log, scoped staged diff-check exit0. No product failure inferred. collection-verification.json records actual collection steps.
