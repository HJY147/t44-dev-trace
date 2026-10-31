# Posttools v1 independent offline audit

Conclusion: BLOCKED — candidate is not approved. This is an offline tool audit, not a pressure run or acceptance result. No server, SSH, HTTP or SUT access was performed. Historical results were not modified.

## Independence and scope

A new independent auditor received neutral frozen source metadata, original/candidate source and authorized neutral response replay only. No developer logs, reports, test scripts, explanations or prompt records were read. No developer contact occurred. The checklist was frozen before implementation inspection; its SHA256 is 23d4a5148dfb1dff643fcdc9892607533a7feb5c05aa7742af835bae81d3d8ac. Internal cases, private responses, credentials and keys are excluded from this publication.

## Blocking finding AUDIT-POST-001

Priority P1: compiled_post.py Compiled.compile lines 7–11 memoize by id(schema), without retaining the schema object. Python may reuse that ID after a temporary deserialized schema is released. The persistent validator process and global compiler allow a later different schema to resolve to the first compiled validator. The serialized-string cache in post_runtime.validate_compiled does not retain the input schema object either.

Executed reproduction used the frozen TaskEnvelope and AuditPageEnvelope schemas and an authorized response in memory: compile a temporary TaskEnvelope reference, release it, allocate an AuditPageEnvelope reference at the reused ID, then compile and validate. Candidate accepted the task response under the audit schema; original Validator rejected it. Only aggregate booleans are published in id-reuse.PUBLIC.json. A separate synthetic integer/string reference reproduction also accepted the wrong type. These are direct execution evidence of schema-compatibility failure, not a prediction based solely on static inspection. This can cause either false rejection or validation against the wrong contract; exact end-to-end incidence was not measured. Fix must preserve schema identity safely across object lifetimes, then receive fresh independent review.

## Other checks and evidence

All supplied original/candidate source hashes and the authorized replay hash were verified. Original runtime.py and openapi.json are byte-identical. Static comparison confirms inherited load loop, 400 clients, 60-second warmup, 600-second steady state, ten throughput buckets, four class P95 thresholds, request errors and per-client coverage gates remain. Per-task transition, contract and escalation assertions remain inherited. Final task field checks, audit scope, actor/outcome/operation filters and required audit-ID subset checks remain; the candidate explicitly requires all pages before audit completion and both 400 counters for combined success.

Executed offline checks compared original and compiled acceptance on 138 evenly sampled replay responses and 828 structural mutations; all compared outcomes matched in that stable-schema test. This passing sample does not override the independent object-lifetime defect. Four synthetic postcondition scenarios exercised two-page success, wrong scope, missing expected ID and expired budget. Fourteen combined-exit mutations rejected errors, incomplete counts, timeout/deadline, undrained ownership, pending validation, incomplete writer/pool shutdown and non-PASS metrics. Full 11-minute timing replay was not performed.

Static lifecycle review: dispatch uses the original 40-second deadline. Additional 30-second drain grace is for admitted work, with post-dispatch checks preventing late completion from counting as success. Client-owned sockets close in client finally; global closes follow draining. Validation jobs are tracked, pending jobs force non-PASS, pools close/terminate then join, and writer shutdown is reflected in combined verdict. The inherited outer supervisor provides a process-group hard bound. Exceptional failure results are saved and the writer is closed in finally; failed runs can retain encrypted evidence, but a hard kill is not guaranteed to yield a finalized seal. These lifecycle statements are static evidence, not an executed full failure/timeout matrix.

Effective runtime result identity includes base runtime, post runtime, compiled validator and boot module hashes and a binding hash. Original benchmark identity and result schema fields remain, with additive combined verdict/identity fields. Source history was read-only and no prior result was rewritten. No candidate readiness, live performance, complete concurrency lifecycle acceptance or formal project acceptance is claimed.

## Limitations and next step

No cloud access, physical environment, full 400-client timing execution, spawn-pool deserialization timing test, signal interruption matrix or encrypted-writer fault injection was performed. The demonstrated frozen-schema lifetime defect is sufficient to block approval; root must route the finding to the responsible developer. A corrected frozen source requires a fresh independent audit.
