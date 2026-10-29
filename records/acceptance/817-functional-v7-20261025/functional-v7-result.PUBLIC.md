# Independent functional v7 — PUBLIC result

Overall: **NOT_PROVEN**. One admitted functional run; no retry.

12 PASS / 1 FAIL (F08) / 1 NOT_PROVEN (F11). 1,027 actual SUT HTTP requests; all 1,027 had complete durable HTTP responses. Original completed-postcondition counter: 89; assertion results: 9,703 pass and 1 fail.

F08 observed HTTP 409 / ASSESSMENT_BASELINE_MISMATCH at the failing frozen assertion; private construction and oracle remain withheld. Nine prior completed postconditions remain preserved. F11 made zero SUT requests because an expired-token credential input was absent.

Started 2026-10-25T09:44:41.231180Z; ended 2026-10-25T09:47:18.923213Z, before the 09:50 UTC deadline. Process exit 0 is not an acceptance pass.

The new encrypted journal was finalized and fully authenticated: 15,923 records, 15,925 frames, no partial tail; all request begin/end sequences match. Frozen inputs and four authorities remain unchanged.

| Case | Original status | HTTP requests | Complete HTTP | Original completed postconditions |
| --- | --- | ---: | ---: | ---: |
| F01 | PASS | 15 | 15 | 1 |
| F02 | PASS | 15 | 15 | 2 |
| F03 | PASS | 82 | 82 | 6 |
| F04 | PASS | 213 | 213 | 17 |
| F05 | PASS | 79 | 79 | 6 |
| F06 | PASS | 38 | 38 | 3 |
| F07 | PASS | 47 | 47 | 3 |
| F08 | FAIL | 122 | 122 | 9 |
| F09 | PASS | 106 | 106 | 8 |
| F10 | PASS | 34 | 34 | 2 |
| F11 | NOT_PROVEN | 0 | 0 | 0 |
| F12 | PASS | 119 | 119 | 20 |
| F13 | PASS | 14 | 14 | 1 |
| F14 | PASS | 143 | 143 | 11 |

Error branches: 28 observed of 551 declared; 523 NOT_PROVEN. Direct DB/MQ requests, fault phases, performance phases and complete formal 400-client/600-second groups: 0. Scheduler scope replacement and retained neutral preflight data remain declared limitations.

Detailed public result: /Users/yang/Desktop/nothing/软件开发大作业/tmp/817_independent_execution_v7_20261025/PUBLIC/functional-v7-result.PUBLIC.json
