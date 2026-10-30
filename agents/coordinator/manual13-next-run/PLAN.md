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

## Completed local experiment and selected candidate

The exclusive local redo comparison has completed (database commit26f47fec); no latency benefit was observed, so no redo change is adopted. Global pool reset=None remains rejected. No further AB experiment is planned, per the user's explicit request.

On2026-10-31 the user reported the APP's ESSD changed from PL0 to PL1,40GiB/3800IOPS. This is user-provided console evidence, not an agent live cloud readback. The candidate retains exact source90b, original seven images and applied schema indexes; only storage tier changes. DiskID, effective tier and actual MySQL volume mapping remain to be read back on the next live preparation.

## Next-run preparation

Next identifiers are r30manualp13 / r30materialresume06 / r30restoretransition06. Old grants, inputs and output paths cannot be reused. Deployment prepares SSH authorization headroom and missing wait/checkpoint observation. A fresh independent tester prepares only public p13 interfaces with all execution flags false until current neutral evidence is available. Source/image and database configuration identity remain pending the selected candidate. No previous profile may be renamed as a current approval.

The original400/60/600 measurement,270ms/1000-per-minute/zero-error criteria and every original assertion remain. Prepare locally first; actual SSH, source/image/schema/config identity, real sessions and once-only independent permission must be current before formal trigger. Recover evidence and immediately tell the user both original VMs may economically stop before local result analysis.

## 2026-10-31 material07 offline readiness

User confirmed shutdown after interrupted material06 and requested complete local preparation before another boot. Keep06 prefix; material07/maintenance07 new output, p13 still requires live unconsumed proof. A current400-state2 check can skip repeated UNBLOCK; all material qualification remains. Deployment-only fresh scan wait is900s, whole preparation shares monotonic1800s; original benchmark timing/assertions are unchanged. No automatic VM shutdown/timer is added. Notify user immediately after evidence recovery for manual stop. See agents/coordinator/manualp13-resume07-preparation/DELIVERY.PUBLIC.json.
