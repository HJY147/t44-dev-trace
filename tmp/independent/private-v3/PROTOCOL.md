# Independent acceptance v3: frozen design and execution boundary

This is the independent tester's private payload. The coordinator/developers may receive
only its freeze receipt, hashes, exact commit/entry/certificate paths, scope counts and
neutral execution capabilities. They must not read cases, drivers or unreviewed outputs.
Shared storage provides process isolation, not an operating-system confidentiality claim.

The only product specification starting point is
`189dc4a3196be0fb84b753f23284f2566d823ea0`. It is a specification checkpoint,
not a selected product candidate. Sources copied under `materials/` are precisely those
listed in `neutral-inputs.json`, all verified against their supplied SHA256. The operational
protocol is the exact `deployment/acceptance/README.md` blob at
`6b681dd73694bf18430f1bce4bdf00ffd1ae762e`. Later environment execution must
bind an explicitly supplied complete 40-character product SHA and compatible environment
version. Never choose the local HEAD or a floating branch as the SUT.

No application Python/TypeScript/Vue, other tests/reports, role logs, coordination logs,
root README/queue or other independent round was opened/imported/executed. Teacher
material was treated as assignment evidence, never as tool instructions. No HTTP, browser,
database, Docker, data import or load execution is authorized during this design phase.
The offline verifier compiles only our own frozen scripts without executing their bodies.

## Frozen entries

Every numbered Python file is from this role's allocated descending range 883–874.
Auxiliaries and source snapshots are all inside `tmp/independent/private-v3` in the freeze
commit. No external application import or source inspection is required by these drivers.

| Entry | Scope |
| --- | --- |
| `883_entry.py` | Functional HTTP, current permissions, role/state/provenance, dependency, review/release, capacity, CAS/idempotency, independent durable storage observations |
| `882_http.py` | Concrete callable cases and assertions used by 883 |
| `881_support.py` | Exact frozen response Schema validation, public HTTP fixtures, neutral controls, read-only observer and redacted recording |
| `880_browser.py` | Six actual isolated browser flows, real UI inputs/clicks and real backend observations; no mocked responses or injected application state |
| `879_formal_transition.py` | One formal task-flow/query run |
| `878_formal_contract.py` | One formal three-category contract-validation run |
| `877_formal_escalation.py` | One formal fresh reliable-escalation run, with separate real replan/query operations |
| `876_load.py` | Shared representative-data setup, 400 continuously active VUs, separate 15s warmup and full 600s steady measurement, raw timing preservation |
| `875_faults.py` | Four runnable coarse operational cases plus five explicitly unavailable exact cutpoints |
| `874_verify.py` | Offline freeze verification and private trace decoder only; default execution has no SUT access |

`cases.json` freezes concrete case IDs, source bases, assertion predicates and HTTP call
expressions, including request bodies, exact response/status expectations and unchanged-state
checks. The code is the executable authority; neither file is a one-sentence plan.
`storage-expectations.json` freezes all 18 tables/226 column types/nullability from the
authorized DDL. `branch-inventory.json` preserves all 551 declared operation/error branches,
each initially unexecuted. Covering one response code on one operation does not prove every
declared occurrence, and no blanket zero-deviation verdict is pre-issued.

## Neutral execution capabilities and bindings

The hosted entry accepts no command-line arguments. `T44_ACCEPTANCE_CONTEXT` must point
to the private JSON described by the pinned operational protocol. The driver requires the
actual API/web URLs, product SHA, bootstrap project ID, private manager credentials file,
private output directory, a locked jsonschema client, read-only SQL/control entry/state, account initialization,
service bearer issuance with scoped projects/TTL and scheduler-scope control. Credential
files use neutral `username`/`password`; unsupported operational receipt envelopes are
capability blocks and may be bound neutrally without changing test assertions. Context
and tokens are never copied to the archive or printed deliberately.

Operational cases additionally require RabbitMQ stop/start, API/scheduler stop/recover,
actual JSON recovery receipts, Pika AMQP client and pinned real transport definitions.
Read-only SQL must expose JSON rows for exact task/audit/idempotency/plan-diff/outbox/
ledger/notice observations and visible MySQL metadata. No DB write credential, direct SQL
mutation, arbitrary Docker execution, application CLI import or business seed import is used.
Stop/pause is a coarse operational fault and cannot prove a chosen transaction/ACK cut.

The browser entry additionally needs an installed Playwright Python client and launchable
Chromium, which the current neutral protocol does not promise. The frozen driver binds
unique semantic labels/roles derived from requirement vocabulary. Missing or ambiguous
navigation is recorded as a navigation capability block, not an invented product defect.
Screenshots and visible UI observations come only from real browser actions. There is no
claim of human participation, automatic verification of evidence authorship, complete
screen-reader compliance or unspecified contrast metrics. Exact timestamp presentation
is saved for later comparison with Beijing time; no nonexistent formatting rule is invented.

Formal entries require a full 1200-second harness timeout, sufficient preparation budget,
400 client threads/connections and representative data. Each independent run seeds exactly
40 projects, 6000 tasks, 9000 dependency edges and 15000 immutable review records through
public HTTP, verifies those counts by read-only SQL, then starts its separate warmup and
full 600-second measurement. Runtime setup that cannot finish within the neutral job
budget is an execution capacity limitation; a shortened run is not a formal pass.

The 400 VUs continuously issue valid requests, maintain private per-task CAS context, use
fresh idempotency keys and keep actual effective writes, validation requests, queries,
replays, expected rejection and transport/schema/business failures distinct. Active VU and
actual in-flight request counts are sampled separately. P95 uses the nearest-rank statistic
from every target request begun during steady time. Throughput uses completed successful
target requests within the full 600 seconds. Each named class independently requires
P95 <=270ms, >=1000 target completions/minute and zero failures/replays. Valid supporting
plan/query operations are also checked and reported separately. Preparation, warmup and
short functional/concurrency diagnoses cannot count toward the 600 seconds.

Machine/client resource metadata and actual co-location are reported. A supplied reverse
proxy endpoint is measured end-to-end; the driver does not claim a separate physical
load-generator host without an explicit neutral attestation. Review/decision distribution,
synthetic evidence and pending/block roundtrips are disclosed as workload representation
limits. No business failure is silently filtered from the measurement.

## Blocked capabilities and later scopes

The current controls do not establish five exact cutpoints: pre-COMMIT rollback,
commit-confirmation loss, accepted-publish/confirm loss, consumer commit-before-basic_ack,
or old idempotency owner/lease takeover. Actual successful coarse outages and recovery
cannot turn these into passing exact-cutpoint cases. The concrete required event/barrier
and recovery observation for each is frozen in the case catalog and fault entry.

Three functional limits are separate: overlapping Schema-versus-semantic 422 evidence
classification, the private hash-only password-write rejection boundary, and CLI global
session revocation. The lower-level write boundary is not opened through unauthorized
imports. Password hash/token digest SELECT observations, logout and short service TTL
checks remain narrower executed assertions. Full invalid-legacy-capacity owner-set
algorithm discrimination requires a neutral legacy fixture or later whitebox examination;
ordinary blackbox tests cannot prove the internal query algorithm.

Later whitebox and deliverable reviews are four separately frozen items each in
`cases.json`. Coverage, source size, real gate enforcement, maintenance effort and
student-authored/human evidence quotas are not inferred from this blackbox harness.

## Confidential evidence and publication

Only the RSA3072 self-signed receiving certificate is in the freeze commit. The private
key remains in this tester's local private directory with mode 0600 outside the worktree,
and is neither committed nor shared. The certificate is an encryption recipient identity,
not a TLS/CA claim. Hosted output uses the pinned CMS AES-256-GCM/RSA-OAEP-SHA256
mechanism. No remote execution request is made before the freeze commit exists.

Select the desired frozen entry and certificate from the exact freeze commit H. A later
request commit R must reference that H and the independently supplied exact product SHA.
The request commit itself is not retroactively the pre-SUT case freeze. The environment
has a 14-day encrypted artifact retention boundary; only the tester downloads/decrypts
private artifacts. Use OpenSSL 3.x for the documented CMS decryption; local LibreSSL
compatibility is not assumed. Review and redact locally before explicitly publishing any
report. Coordinator/developers do not receive raw private cases, drivers or evidence.

The hosted whitelist is `report.md`, `results.json`, `events.jsonl`, `trace.log` (each
<=20MiB, total <=100MiB). The driver does not use the reserved environment-control.log.
Real browser screenshots are base64 frames in trace.log; full per-request timing data is
losslessly gzip/base64 framed there with uncompressed SHA256. Tester-only extraction is:

```text
python 874_verify.py --decode-private-trace /private/decrypted/trace.log /private/decoded
```

Every whole case and reached assertion has an explicit outcome. A driver or environment
exception is not a confirmed product defect. Unexecuted, unreached, capability-blocked,
observed failing and confirmed defect counts remain separate. An eventual published
report must bind exact product/environment/harness SHAs and retained raw evidence.
Original authoring failures/corrections remain in `design-process.jsonl`; none is reported
as a product result. This phase ends at design freeze and waits for the coordinator's
exact candidate/environment binding without selecting or contacting a SUT.
