# Functional v5 run 29165d4935db2789 — PUBLIC facts

Outcome: **NOT_PROVEN — TOOL_TRANSPORT_EVIDENCE_BLOCKED**. The single admitted functional invocation completed; it was not a successful acceptance run.

- Frozen tool: `50408b5315df42c0d1240132c597a2a016130aa0c3d35ab5a1b1c633f79a6324`. Native source metadata: `c8cea7e82805de5283ce67501769fa9a4efc1047`.
- Planned: 14 functional cases. Prior controller-only offline checks: 36 passed. Actual SUT requests: **12**.
- Observed HTTP status: **201 for all 12**, followed by local `OSError [Errno 9] Bad file descriptor` while receiving body. Complete HTTP responses: **0**.
- Original case records: **0 PASS / 12 FAIL / 2 NOT_PROVEN**. Those raw results are retained. Complete business cases/postcondition checks/formal performance groups: **0 / 0 / 0**.
- No scope handoff was emitted. No provider, scheduler-scope limitation, SUT business rejection or rollback is established as the cause. Exact root cause remains unproved.
- The 12 write calls may have taken effect. Incomplete reception does not prove rollback, and this report does not establish cleanup targets.
- Automatic reruns, extra diagnostic requests, faults, performance and deletion/cleanup: **0**. All raw credentials/headers/bodies/errors remain in private authenticated encrypted evidence.

| Case | Raw recorded status | Actual SUT requests | Complete postconditions |
|---|---|---:|---:|
| F01 | FAIL | 1 | 0 |
| F02 | FAIL | 1 | 0 |
| F03 | FAIL | 1 | 0 |
| F04 | FAIL | 1 | 0 |
| F05 | FAIL | 1 | 0 |
| F06 | FAIL | 1 | 0 |
| F07 | FAIL | 1 | 0 |
| F08 | FAIL | 1 | 0 |
| F09 | FAIL | 1 | 0 |
| F10 | FAIL | 1 | 0 |
| F11 | NOT_PROVEN | 0 | 0 |
| F12 | FAIL | 1 | 0 |
| F13 | NOT_PROVEN | 0 | 0 |
| F14 | FAIL | 1 | 0 |

The JSON fact report binds the exact grant, native runtime, PUBLIC receipt/status and private ciphertext hashes. A zero process return code is not an acceptance verdict. Raw FAIL rows caused by this evidence blocker do not establish SUT business nonconformance.
