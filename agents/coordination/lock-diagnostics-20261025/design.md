# Fresh MySQL lock candidate verification design

2026-10-25; coordinator. This is development verification, not independent acceptance.

The application baseline is ade5e4c1998b4c2f014afde8c011645c6c5a7412. Candidate application bytes must equal backend C c8cea7e82805de5283ce67501769fa9a4efc1047. Only Runtime differs: graph readers use project S, graph writers retain X, and all original task lock sets use ascending unique scalar primary-key queries. The candidate is isolated here pending review and real MySQL verification; integration/main remain unchanged.

Three fresh GitHub Actions jobs each receive their own disposable MySQL 8.4 service. Baseline and candidate low-level jobs each use exactly t44_diagnostics; candidate HTTP races use exactly t44_gate_http. Baseline Runtime is restored from the exact baseline commit in its job and is explicitly reported as that source, rather than mislabelled checkout HEAD. All other application files must be byte-equal to the selected reference. Exact driver/observer hashes, workflow identity, request limits and loopback database identity are checked before migrations or application work.

The app principal has only schema-local CRUD. Setup uses the disposable root principal to migrate the named fresh schema and grant SELECT on performance_schema.data_locks, data_lock_waits and threads to the disposable diagnostic principal. No PROCESS or global privileges, real account, production database, or port 13306 are involved. Permission readiness is separate from lock case results.

Each low-level run has its own 120-second internal/150-second external limit, six controlled cases and reserved non-overwriting JSON. The HTTP driver has seven controlled cases, five-second diagnostic lock waits and an outer 180-second limit. Artifacts retain stdout, JUnit, metadata and service logs on failure. The baseline and candidate run independently; a failing baseline cannot skip candidate evidence. The workflow has no performance workload and cannot establish HTTP P95, 400-client acceptance, deployment capacity or release approval.

The coordinator will validate guards locally without network/database work and obtain peer review of the exact candidate and workflow before one push-triggered run. The ordinary product CI also runs on that exact pushed source. Any failed run is retained and corrections receive a new source/run identity.
