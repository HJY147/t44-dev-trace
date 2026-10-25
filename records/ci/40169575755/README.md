# Linux/MySQL sequential diagnostic: preserved official artifact

GitHub Actions run [40169575755](https://github.com/HJY147/t44-dev-trace/actions/runs/40169575755), job 121097508425, completed successfully on exact checkout `81c909ad753aee7179ee0c464349a07273092fc0`. Application source bytes equal baseline `ade5e4c1998b4c2f014afde8c011645c6c5a7412`. Reviewer admitted the tools/workflow before execution; no product code changed in this run.

Official artifact 12589763159, 123428 bytes, SHA-256 `3de3e3bcef1952f0736da762fcbe76f045eccf9e014a1ab90aba1e7bb80e8650`. The downloaded ZIP was size/hash verified before extraction. Extracted `mysql-before.json`, 1387070 bytes, SHA-256 `b17f0fd502f9342ec11f9ae12064edccb11f139b3a90997c6be022f5ec333a9e`. ZIP also preserves admission metadata, console and MySQL service logs. Original bytes are retained.

This was 56 sequential TestClient/ASGI requests with a real fresh MySQL service: four warmups, 48 measured requests and four separately profiled requests. It did not exercise Uvicorn, Nginx, external network latency, simultaneous clients or a 600-second acceptance window.

| Operation | Measured samples | Client wall median, ms | Handler thread CPU median, ms |
| --- | ---: | ---: | ---: |
| getTask | 12 | 10.881364 | 6.997921 |
| listTasks (20 rows) | 12 | 24.904759 | 20.507875 |
| transitionTask | 12 | 25.356698 | 17.260684 |
| validateContractPayload | 12 | 6.148877 | 3.226141 |

Response-only list schema validation consumed median 11.711 ms CPU; constructor work was about 0.136 ms total on that path. Transition SQL cursor wall/CPU means were 8.796/4.720 ms; these are inclusive observations and cannot establish that the difference is lock waiting. Nested Rows, Session and cursor timings overlap and must not be summed.

The run establishes useful CPU/SQL attribution for this finite diagnostic, not formal performance acceptance, cloud root cause or release approval. The separate ordinary product CI on this exact checkout, run 40169575729, has four successful jobs: static, contracts, coverage and frontend. That CI result also does not close the independent acceptance, source-size or 400-client gates.
