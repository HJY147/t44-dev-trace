D008 now returns `ASSESSMENT_BASELINE_MISMATCH` when a DELIVER request reaches the existing failed approval-reference check and its assessment delivery/schedule baseline is stale. A valid baseline with a missing approval still returns `RELEASE_APPROVAL_REQUIRED`; matching references continue through the original domain guard order.

Exact source candidate: `0dfb55c2191200d947c5423fd9ee74bb0812cc5a`, based on prior specification freeze `d5307551d6b467f84e8254abd0245cdf22bc0a70`. All15 frozen inputs match. Production diff is only workflow.py’s error argument; domain/auth/lock order/SQL/CAS/idempotency/audit/outbox/DDL/pool/front remain unchanged.

Validation: identical856 HTTP tests produced3fail/8pass before and11pass after. Four unchanged986 adjacent cases passed separately. Cases cover actual schedule double-failure, approval-only rejection, request/task version and assessment ownership, matched-reference domain priority, persisted error and success replay metadata, and new assessment→different compliant reviewer→manager delivery. Cycle mismatch and matched-reference inconsistent rows are explicitly controlled SQLite fixtures, not actual rework or real legacy observations. Rejections retain unchanged business snapshots and one independent audit; replay creates no new business/audit. Ruff/format two files passed.

Public old failure log/XML redact only ephemeral in-memory fixture sessions; exact raw hashes and private0600 originals retained. Assertions/failure/counts are unchanged. Source commit includes test command/hash/log/XML evidence and code-checkpoint.json. The existing TestClient deprecation warning remains.

Actual pinned cloc at this source is6310, +3 from prior6307, outside3500–5100 (exit1). No count-policy change or claimed size pass.

New exact-source product run40060857352 is in progress; Docker will run from this draft PR with actual merge checkout provenance recorded later. No borrowed old510/89 or performance/independent-acceptance claim. Later role/CI evidence will be on separate `codex/backend-d008-implementation-evidence` without moving this source head. Draft only; root will arrange independent code review. No local external DB/server/load or protected independent data access.

Agent-Role: backend
Prompt-Ref: ROLE-backend-D008-IMPLEMENT-v1
Refs: #3
