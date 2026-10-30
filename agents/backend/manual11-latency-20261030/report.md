# MANUAL11 backend local diagnosis and conservative read candidate

- Operator: backend AI. Prompt ID: `ROLE-backend-MANUAL11-LATENCY-20261030-v1`.
- Base/source under diagnosis: `90b734f65ce6ee9f5c217e885bc7ea4857e32b48`; isolated branch `codex/manual11-latency-backend-20261030`.
- Inputs: AGENTS, implementation-layout, frozen v1.2 manifest/contract, PUBLIC MANUAL11 report/conclusion and `DIAGNOSTIC_NEUTRAL.PUBLIC.md`. No PRIVATE, unpublished independent cases, test logs or tester contact.
- Published performance FAIL remains FAIL. This candidate is not evidence that the ~1s four-class P95 root cause is corrected.

## Evidence and hypotheses

The published four classes all exceed270ms. Public app header P95 is already883–966ms; source `api.handle` starts its timer within the synchronous handler, covers Runtime and output schema validation, and evaluates the header before JSONResponse construction. This cannot separate pool, DB, lock, Python scheduling or CPU. LOAD aggregate idle resources cannot establish APP or DB capacity.

`handle` is synchronous; FastAPI/Starlette dispatches it through AnyIO. No project-specific thread limiter or request dependency chain is configured. Installed AnyIO default limiter is40 tokens per process; actual remote process count, worker distribution, pool configuration and DB waits remain unobserved. Settings default pool5+overflow10, engine pre-ping/LIFO/rollback reset; these are source defaults, not confirmed remote settings. No worker/pool increase was made.

Real local SQLite SQLAlchemy events, real Runtime and real jsonschema were used for30 sequential calls per class. They do not model MySQL network/locks/commit latency. Baseline `baseline-v2.json` shows:

| Path | SELECT | Checkout | Commit |
| --- | ---: | ---: | ---: |
| getTask |9|2|2|
| contract validation |4|1|1|
| transition BLOCK / UNBLOCK |20 /22|2|2|

GET repeats session/identity/membership/project lookup before and after request validation. Write prepare authenticates, then `_claim` checks again under shared session lock, then main UoW checks live state again. Rechecks cannot simply be cached or removed without changing invalidation windows. Contract only authenticates once, so duplicate GET SQL cannot alone explain the shared four-class tails.

cProfile baseline30 requests: contract total about45ms, authenticate22ms and schema validation20ms; GET85ms; transitions256ms. These sequential local costs do not reproduce a1s pure-schema hotspot. No sensitivity-damaging cache, schema relaxation or assertion deletion is proposed.

## Minimal candidate and safety

`Runtime.execute` executes GET preparation and data read in one read UoW, preserving both complete live authentication passes on either side of validation, all error auditing and unchanged dispatch. READ COMMITTED remains configured by the existing engine; no persistence or deployment files change. Contract special handling and all write/claim/audit/outbox transactions remain unchanged.

Candidate GET uses9SELECT,1checkout,1commit; both transaction round trips drop2→1. Contract and write event counts are unchanged. Profile means baseline→candidate2.845→2.716ms for GET,1.494→1.466ms contract,8.533→8.290ms transition; these small sequential observations are not controlled performance acceptance or proof of cloud benefit.

Five additional tests exercise real SQLite persistence changes between initial authentication and final dispatch: session revocation, expiry, inactive identity, inactive membership all remain rejected with an audit; initial authentication failure still precedes validation. The same5 pass on original90b Runtime.execute. These tests do not prove MySQL concurrent locks.

## Execution and honest limits

- Local Python3.12.10 venv was created and68 packages installed from frozen `backend/requirements.lock` using `uv pip install --require-hashes`.
- `PYTHONPATH=backend:. .venv-manual11/bin/python agents/backend/manual11-latency-20261030/local_profile.py <baseline-v2.json|candidate.json>` produced raw JSON/cProfile evidence.
- Original144 HTTP/fault/D008/dependency/security tests passed; initial run omitted explicit pytest config and warned of unknown markers. Configured combined149-test rerun recorded separately.
- New5 pass on baseline and candidate. Configured ruff passes. Initial default ruff selected parent config and rejected the repository's numeric test filename; actual project config fixes that tooling invocation without changing policy or tests.
- Initial profiling attempt used `profile.py`, shadowing stdlib profile; renamed to `local_profile.py`. Second attempt used an incomplete synthetic BLOCK body; actual exception log retained and fixture corrected to frozen BLOCK/UNBLOCK schemas. No product fix was made for either harness error.
- Source budget is measured after the product commit with frozen cloc; see follow-up budget record.
- No cloud connection, VM, load, grant, independent retry or remote MySQL/RabbitMQ validation was performed by this role.

## Coordinator handoff

Root cause remains unresolved. Next discriminating evidence: APP per-worker CPU/GIL distribution, AnyIO busy/queue, SQLAlchemy checkout wait/pre-ping, DB statement/commit wait, row locks and growth-sensitive queries. Database/deployment owners receive suggestions only through coordinator. Candidate has no API/schema/DDL/version change. Fresh independent retest is coordinator-owned after root cause work and admission.

## Final measured gates

- Product/evidence commit: `5331b658df6428fafe93a65664bf97b1f92c46b8`.
- Configured combined149 regressions passed in31.58s, one upstream Starlette/httpx deprecation warning; no unknown project markers after correct `-c backend/pyproject.toml`. Baseline invalidation5 passed in1.31s.
- Frozen cloc2.10 application count FAIL:90b baseline5818, candidate5821, net+3, ceiling5100. Exact committed candidate and original90b tree counted with same classifier and pinned cloc. Baseline script binding replaced only rev-parse HEAD with explicit90b, leaving archive/classification/count intact. No source counter/assertion modified. This candidate cannot satisfy the source-size gate; removing unrelated requirements or compressing source to hide this is outside scope.

## Existing core/auxiliary source grouping clarification

Coordinator clarified the already-adopted grouping; verified against committed `6a17d788:reports/final/requirements-report.md` and `docs/reports/FINAL90b-core-runtime-groups.json` (the90b worktree retained older final-report bytes). Applying that exact existing62/3file partition to the candidate's original pinned-cloc per-file output gives:

| Existing category | Files |90b lines|Candidate lines|
| --- | ---: | ---: | ---: |
| Main core runtime |62|5038|5041|
| Offline auxiliary |3|780|780|
| Full original application |65|5818|5821|

All+3lines are in core `services/runtime.py`. Auxiliary CLI147/migrations307/seed326 are unchanged. The main-core figure is within the user-adopted3500–5100 range. The original full `--require-range` FAIL remains unchanged; no teacher approval of exclusions is asserted. Exact group membership and measured sum are in `source-groups-candidate.json`; no statistics script, assertion or threshold changed, and no unrelated historical source-size repair is opened.

GET candidate and regression artifacts are preserved and **not integrated**, pending more direct root-cause evidence. Coordinator relayed a separate database-owner hypothesis concerning growth-sensitive `confirmed_missing` scanning; this role neither verified it nor modified database/consumer paths.
