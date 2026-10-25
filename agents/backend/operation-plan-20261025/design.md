# OperationPlan internal-interface probe

Actual author/operator: backend AI. Prompt `ROLE-backend-OPERATION-PLAN-v1`.
Base `f4bd382d4668130793fc553df9ce6363c4656ea6`; supplied application count
5862, limit 5100, gap 762. These supplied numbers are not a new measurement.
The optional API-wire branch is not part of this base or this probe.

The first executable design is an immutable `OperationPlan` containing an explicit
`authorize: Callable[[Call], None]`. Applying it to an original operation callback
produces a normal bound service method with the existing `(gateway, call)` external
service shape. Its only common steps are `authorize(call)` then `call.task(gateway)`;
it passes the resulting transaction-local task row to the original callback.
`RowsGateway`, `Call`, task-row and dictionary-result types are explicit in the
callback/handler aliases. The plan has no row state, request data or mutable cache.
An original callback still receives its original service object, gateway and Call.
`functools.wraps` preserves operation names; no generated SQL, field-expression DSL,
string callbacks, evaluation, dynamic public routing or new persistence API exists.

This deliberately keeps the longest, distinct guard/write sequences in ordinary
Python callbacks. Moving their conditions or dictionaries into a plan would still
count those declarations and need additional state-binding/branch machinery.
The independently ordered review actor check and the opposite CAS/write orders
cannot be merged into a shared state-first/create-first algorithm. The plan does
not move any resource read into the pure domain layer. Runtime, transaction,
fresh authentication, project/member/sorted task locks, savepoints, CAS,
schedule history, independent rejection audit, outbox and idempotency remain
the original owners' byte-identical code.

All code first lives below `tmp/797_backend_operation_plan/`; product files stay
unchanged. Exact base service bytes and SHA256 manifests are archived from git.
Candidate copies remove only the four original authorize/task-load pairs, add
typed task-row callback parameters and four plan applications. Every remaining
callback statement must be AST-identical and ordered as the corresponding base
suffix. The fixed cloc 2.10 count includes both changed modules and the complete
new plan helper, including imports/types; no gain is claimed for test artifacts.

## Type and lifetime boundary

| Object | Input | Output and effects |
| --- | --- | --- |
| OperationPlan | Trusted unbound `Call.manager` or `Call.reviewer` | Frozen authorization policy; callable wrapping a typed callback |
| Handler | Existing service, transaction-local RowsGateway, mutable request Call | Existing result dictionary; raises the original errors |
| Original callback | Same service/gateway/Call plus task row returned after authorization | Original guards, gateway operations, CAS and serialized result |

The plan itself is immutable; the gateway/Call/task are intentionally the existing
transaction-local objects. Freezing or copying them would alter CAS/audit behavior
and is outside this design. No additional task lookup or authorization is allowed.

## Original ordered gates and writes

1. `addTaskDependency`: manager → project-owned task read → prestart / DEPENDENCY_EDIT_LOCKED
   → requested predecessor → edge query / duplicate STATE_CONFLICT → self-reference
   → project-owned task set locked update / RESOURCE_NOT_FOUND → graph cycle check
   → task expected-version/overflow + CAS → create edge with original metadata
   → predecessor read for satisfied flag → original task/dependency result.
2. `removeTaskDependency`: manager → project-owned task read → prestart / DEPENDENCY_EDIT_LOCKED
   → edge read → task/project ownership / RESOURCE_NOT_FOUND → task version/overflow
   + CAS → edge delete → original task result.
3. `createTaskReview`: reviewer role → project-owned task read → independent actor
   / ACTION_FORBIDDEN → PENDING_REVIEW / STATE_CONFLICT → template/artifact baseline
   / REVIEW_BASELINE_MISMATCH → exact unique sections/items / PARAMETER_INVALID
   → passing-verdict evidence / EVIDENCE_REQUIRED → original review create/read
   → task version/overflow + CAS latest_review_id → original task/review result.
4. `createReleaseAssessment`: manager → project-owned task read → PENDING_RELEASE
   / STATE_CONFLICT → four risk perspectives / PARAMETER_INVALID → responsible active
   member lookup / RESOURCE_NOT_FOUND → latest rollback-plan-version query
   → original assessment create/read → task version/overflow + CAS invalidating
   approval references → original task/assessment result.

`Call.task/resource`, `create/insert`, `check_version/cas`, `Tasks.prestart/check_graph`,
`Reviews.review_complete` and all serialization stay unchanged. Faults must abort
at the same gateway event and keep the same before/after audit diff.

## Preliminary net ledger and stop rule

The four pairs remove eight original statements. Four plan annotations, explicit
row parameters, imports and a readable immutable wrapper are expected to add
18–30 effective lines, for an initial net **−18 to +6** (negative means growth).
This is an estimate, not a measured result or an 80–150-line claim. Even a free
wrapper would save only eight lines from this common pair; unique domain guards
and original field construction remain counted. More ambitious create/CAS steps
will not be promoted without a separately measured positive net ledger.

Stop if the complete probe saves less than 20 lines or worsens readability or
verification cost. Keep the failed prototype/evidence under tmp and leave product
bytes unchanged. If it exceeds the threshold, seek exact-source review before
integration; do not broaden to all CRUD on speculative savings.

## Validation before any product promotion

- Exact archived-byte manifest and suffix AST proof, including unchanged non-target
  methods and no string/SQL/eval instructions in the helper.
- Deterministic handler differential: result/error fields, ordered gateway calls,
  created/updated/deleted rows and Call audit diff for valid and combined-invalid
  scenarios; fault injection at each real gateway boundary, keeping original
  failure type and first-failure event.
- Existing, unchanged developer HTTP/contract scenarios with candidate methods
  temporarily installed by a test-only plugin; no expectation or fixture relaxation.
- Real SQLite HTTP fault regression for each of the four operations, proving CAS /
  create / delete and later outbox errors roll back business writes and preserve
  rejection audit / idempotency behavior. This is not MySQL locking proof.
- Pinned cloc SHA `bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83`,
  complete before/after file lists and new-helper cost; targeted Ruff/format checks.

No full CI, cloud, formal performance, MySQL, private acceptance materials or
unpublished independent cases are read or executed. The full-suite evidence
supplied by root remains bound to f4bd, not to this temporary prototype.
