# MANUAL12 failure diagnosis and next retest

User instruction: 继续检查问题然后修改好，重新启动测试；你每次的debug和改进都需要在github上面同步。

GitHub tracking: https://github.com/HJY147/t44-dev-trace/issues/47

## Confirmed baseline

The single prior r30manualp12 ran the400-client cohort with60s warmup and600s steady. P95 exceeded270ms in all four classes; postconditions incomplete, independent acceptance NP. All encrypted evidence is recovered locally. No retry or successor has occurred.

Independent response-header analysis places most measured latency inside the server. Two application telemetry windows do not show CPU saturation. Exact local MySQL digest mapping attributes the largest sampled statement wait to the idempotency_requests INSERT; this is evidence about sampled SQL time, not a complete causal explanation of end-to-end P95.

## Rejected hypotheses and unchanged safeguards

- Global pool_reset_on_return=None: rejected after real local MySQL raw-connection cleanup counterexample. Current rollback fallback stays.
- Async endpoint directly blocking its event loop: source90b endpoints are synchronous and FastAPI uses its threadpool; no offload patch justified.
- Per-request engine rebuild: LazyFactory is cached perworker; not supported by source.
- Table row count alone:64-client local claim baseline at0 versus501280 synthetic existing rows did not reproduce the cloud wait.

## Current bounded local experiment

Exclusive local MySQL8.4; exact frozen schema and equal synthetic table clones,100MiB versus1GiB redo capacity;64 clients,20s warmup plus180s measurement each,2s checkpoint/IO samples. Flush-on-commit1 and sync_binlog1 stay unchanged. AB ordering, host cache effects, local1GiB buffer versus cloud8GiB, and omission of HTTP/audit/outbox from the claim fragment must be reported. A capacity change is not an adopted cloud fix until results support it.

## Next-run preparation

Next identifiers are r30manualp13 / r30materialresume06 / r30restoretransition06. Old grants, inputs and output paths cannot be reused. Deployment prepares SSH authorization headroom and missing wait/checkpoint observation. A fresh independent tester prepares only public p13 interfaces with all execution flags false until current neutral evidence is available. Source/image and database configuration identity remain pending the selected candidate. No previous profile may be renamed as a current approval.

The original400/60/600 measurement,270ms/1000-per-minute/zero-error criteria and every original assertion remain. Prepare locally first; actual SSH, source/image/schema/config identity, real sessions and once-only independent permission must be current before formal trigger. Recover evidence and immediately tell the user both original VMs may economically stop before local result analysis.
