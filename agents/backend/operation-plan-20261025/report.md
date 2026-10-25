# OperationPlan probe: stop, no product promotion

The actual immutable-plan prototype **grows application source by 14 lines**.
The coordinator's minimum-20-line stop rule applies. All product files remain
byte-identical to `f4bd382d4668130793fc553df9ce6363c4656ea6`; the application
remains **5862 lines, 762 above 5100**. The optional API-wire candidate remains
held. Actual author/operator is backend AI, not the student or independent tester.

## Design and actual net ledger

Design and ordered type/guard mapping were committed first as `31924c4d` and pushed
with `[skip ci]`. The complete code is under `tmp/797_backend_operation_plan/`.
The immutable typed `OperationPlan` captures only the trusted authorization
callback, authorizes, loads the transaction-local task once, then calls the
original Python body. There is no mutable request/row cache or instruction DSL.

| Fixed cloc 2.10 effective source | Exact base | Temporary candidate | Net saved |
| --- | ---: | ---: | ---: |
| Tasks | 136 | 135 | 1 |
| Reviews | 140 | 139 | 1 |
| New plan, complete types/imports/wrapper | 0 | 16 | −16 |
| Application, same classifier | 5862 / 65 files | 5876 / 66 files | **−14** |

This is an executable virtual product tree, not a merged or committed production
candidate. `prepare.py` archives the exact two base modules, proves statement
preservation and materializes the same 65 application files selected by the
existing classifier; only the two candidate modules and new helper differ.
The pinned tool SHA is checked before use. Both full by-file raw outputs and
lists are retained; generated whole-tree copies are reproducible and ignored.
The prototype helper is counted at its real proposed product path. Tests, reports
and the base oracle are not counted as product savings or runtime dependencies.

The preliminary −18…+6 estimate was an estimate; the actual result supersedes it.
The common prefix is only eight removable statements across four operations.
Four plan applications plus imports consume six of them before the 16-line
wrapper. Unique evidence/ownership/graph guards and original record construction
still have to exist. CAS precedes dependency writes but follows review/assessment
creation; independent review actor precedes state. A shared create-first or
state-first skeleton would change error/rollback semantics. This narrow probe
does not establish a mathematical lower bound or rule out all larger designs;
it establishes that this proposed common plan is not a useful size change.

## Executed developer verification

- **153 passed**, zero failures/errors/skips: unchanged original 143 SQLite HTTP /
  contract cases plus 10 new probe cases. A test-only plugin installs just the
  four candidate methods on the existing service classes; original tests, fixture,
  Runtime, gateway, schema validation, REST and DDL are unchanged.
- One new actual-gateway test compares **45** valid/combined-invalid scenarios
  and **22** injected gateway failure positions, using the exact archived base
  and candidate callbacks in rollback-only savepoints. It compares returned data
  or full rejection fields, complete ordered gateway calls/arguments, actual
  tasks/dependencies/reviews/assessments state and Call before/after audit diffs.
  Scenarios cover role before missing resource, cross-project, blocked origin,
  duplicate/self/missing/cyclic dependency before version, stale/overflow version,
  review independence before state, baseline/shape/evidence order, responsible
  membership and four risk perspectives. This is not every possible input.
- Eight real HTTP faults cover all four operations, each at the business write
  following CAS / CAS following create, and at later outbox insertion. Assertions
  require whole business/outbox state rollback, one independent rejection audit,
  empty rejection before/after values, failed key remaining incomplete, subsequent
  successful new-key retry and completed-key replay without new business/audit
  writes. A separate case checks immutable plan policy without captured row data.
- Narrow AST proof: every remaining statement in each original callback is
  identical and ordered after removing only authorize/task-load; all other methods
  in both copied modules are identical. This does not prove whole-program
  equivalence. All product and original selected test bytes are separately hashed
  against f4bd, so transaction/freshness/locks/history/audit/outbox/Runtime code
  has no change in the proposed product or the actual worktree.

Initial standalone differential: one receipt-writing failure and one pass; all
comparisons had reached receipt serialization, where the static review-template
hash was bytes. The raw log/JUnit remain. The receipt was narrowed to last-event
method/table; the full in-memory comparisons were unchanged. The corrected two
cases passed, then the complete selected 153 passed. This failure is not a product
defect or a green first run. Existing Starlette/httpx deprecation warning remains.

Ruff check passed initially and finally. Initial format check requested four
helper/test formats; applied formatting has an explicit all-nine-file AST
identity proof. Candidate module/helper bytes were already formatted. The full
153 was not repeated solely for AST-identical formatting. Final targeted Ruff /
format checks are recorded. The first staged whitespace check found existing
trailing spaces in raw failure tracebacks/XML and a second final newline in the
raw count console log. These exact originals were preserved in lossless gzip
archives, with raw/gzip hashes and verified byte-for-byte round trips; no raw
content was stripped. The failed check is also archived. Final staged whitespace
check passes. No original test assertions changed.

## Reproduction and evidence

Use the authorized existing Python environment, `PYTHONPATH=backend:.`, and this
worktree as cwd:

```text
python tmp/797_backend_operation_plan/prepare.py
python tmp/797_backend_operation_plan/run.py
python tmp/797_backend_operation_plan/receipt.py
```

The runner writes `candidate-junit.xml`; its captured first complete run log is
`candidate-initial.log`. This deliberate repeat would overwrite current receipts,
so copy the evidence or use a fresh clone before reproducing. Other artifacts:
`source-manifest.json`, `ast-proof.json`, `differential.json`, `count.json`,
`baseline-cloc.json`, `candidate-cloc.json`, `format-ast-proof.json`, and
`validation.json` bind actual bytes, comparisons and count. Original scripts and
test-only base/candidate modules are retained, with no product import path to tmp.
`differential-initial.log.gz`, `differential-initial.xml.gz`, `count.log.gz` and
`diff-check-initial.log.gz` preserve the exact raw files. Their local unpacked
copies are ignored; `raw-archive-manifest.json` binds both byte representations.

No full CI, Docker, MySQL, cloud, performance measurement or independent
acceptance was run. The parent-supplied 695/89/Docker green remains evidence for
its exact original source, not new performance or size acceptance. No private
independent materials, other runtime accounts or cloud diagnostics were read.
Pushes use `[skip ci]` to honor no-new-full-CI; no workflow or main protection is
changed. The next architecture route belongs to coordinator scheduling; this
failed probe is stopped and not extended merely to manufacture the remaining 762.
