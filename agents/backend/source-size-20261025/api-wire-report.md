# API normalization reuse: narrow performance candidate

Base d63fe18f3227e1779d3951072636efcdb6181550; branch codex/backend-api-wire-boundary-20261025; actual operator/backendAI; executed prompt ROLE-backend-API-WIRE-v1. This phase removes one duplicate traversal. It does not establish consistent whole-response latency improvement, add source savings, or complete formal performance/source acceptance.

## Change and boundary proof

The sole production change is two expressions in api.py. Bind the result of the original response-check `wire(payload)` and pass that same normalized object to JSONResponse. The schema-missing short circuit remains, as do response-schema validation, INTERNAL_ERROR fallback, all meta/trace/header fields, request capture, timer/profiling boundaries and exception placement. Runtime and every other product file are byte-identical tod63. Restoring only these two expressions reconstructs the complete base API AST; this is exercised by a test against its frozen canonical AST hash.

The first normalization already converts datetimes to the existing UTC microsecond spelling, Decimal to float and tuples to lists. A second wire traversal is a fixed point on those transport values; IntEnum/StrEnum remain valid JSON values. The candidate retains that first conversion at exactly the same short-circuited validation position. Invalid plain Enum/nonfinite values still produce the same schema fallback, and permissive-schema JSON encoding failures/unresolvable references still escape at the original boundaries. Existing error fallback is already a primitive dictionary, so schema-missing handling does not need an extra traversal.

## Actual development execution

Twelve new boundary/AST/value/exception tests passed. Then those12 plus the five unchanged HTTP/contract files(986,987,856,859,816) produced155 passes,0 failure/error/skip. A read-only observer compared1648 actual candidate HTTP responses across35 operations and11 statuses(200,201,400,401,403,404,409,413,422,429,503) to the exact base rendering tail given the same captured Runtime result and actual request/meta/timing values. Body bytes and all headers matched,0 omissions/mismatches. This isolates response rendering; it does not pretend to rerun an independent old Runtime/SUT or compare real elapsed durations across hosts.

A separate real in-memory SQLite developer case created100 tasks and requested20/100-item pages plus getTask. It passed and added111 exact response comparisons. Total1759 matched responses. Runtime result objects remained unchanged after rendering. Public payload hashes/counts/sizes are persisted; tokens and response-body plaintext are not. The harness issued no network/database calls outside its explicitly created SQLite/TestClient setup. Two harness warnings remain: imported-anyio assertion-rewrite warning and the pre-existing Starlette/httpx warning.

## Measurements, including unfavorable samples

Matched renderers include real frozen response-schema validation and JSON encoding, exclude Runtime/SQL/network, alternate base/candidate order, disable GC within timed windows, and retain9 raw CPU samples per case. Initial medians(ns/call):

| Actual shape | Bytes | Base | Candidate | Candidate/base |
| --- | ---: | ---: | ---: | ---: |
| getTask | 908 | 431075 | 411500 | 0.955 |
| audit page | 117127 | 40684250 | 39019000 | 0.959 |
| small listTasks | 928 | 466875 | 474250 | 1.016 |
| transitionTask | 7200 | 673200 | 684225 | 1.016 |

The added real page campaign yielded:

| Actual shape | Bytes | Base | Candidate | Candidate/base |
| --- | ---: | ---: | ---: | ---: |
| getTask | 884 | 490400 | 481300 | 0.981 |
| listTasks20 | 14202 | 8537725 | 8460150 | 0.991 |
| listTasks100 | 70125 | 42177333 | 42957167 | 1.018 |

These are mixed whole-render outcomes. The cause of small unfavorable differences is not established; they are not dismissed as proven noise, and no repeated sample was selected to manufacture a speed claim. Do not claim consistent API or endpoint acceleration from these results.

The exact localized work reduction is proved independently: a normal response performs one full payload wire pass instead of two. In five cProfile calls, recursive wire calls were365→185(getTask),5925→2965(20-page),29125→14565(100-page). Wire's own profiled CPU was approximately halved; profiling overhead prevents turning that into an endpoint-latency claim. Inclusive timings are not summed with parent frames. Full schema traversal dominates these observed render costs.

## Source count, scope and status

Pinned cloc2.10 reports api.py244→244, incremental savings0; prior corrected backend scope2363→1993/net370 remains. No credible additional200-line API/runtime structural budget was established. Their same-policy CRUD scaffolding is already thin; preserving the distinct authorization/resource/version/plan/transaction ordering while adding a generic decorator/generator engine would likely only move0–25 lines and add complexity. No such engine is implemented, and no proof of a global lower bound is claimed.

Only a narrow candidate is delivered for coordinator/reviewer choice. Full combined CI, MySQL, frontend, cloud, independent acceptance, formal270ms/400-client/600-second/zero-error performance and whole-source5100 remain pending. No such campaign was started. Stage pushes use[skip ci] to obey the coordinator's no-self-started-fullCI instruction; no workflow or main protection is changed.

Evidence:tmp/811_backend_size/api-wire/validation.json,base-render-manifest.json,all-junit.xml/all.log,http-differential.json,render-cpu.json,page-shapes-* and the raw reference rendering AST. Initial missing-sys import in the added page harness is retained in page-shapes-all.log, then corrected run is page-shapes-all-fixed.log. Helper import/style/SIM findings were corrected; final targeted Ruff/format/diff checks pass. Those harness failures are not product failures. Prior d63 alias-repair evidence is unchanged.
