岗位 backend；Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1（412CI后静态定位续派）。

基于22647b4/生产5dcb，仅逐源码核写路径账本，未执行SQL/HTTP/pytest/负载或改生产/冻结。正常新key BLOCK22+R SELECT、5DML、2控制，UNBLOCK24+R/5/2；改期20/6/2；服务新事件24+M SELECT、6+N DML、4+2N控制，均3UoW/acquire/成功commit。R为可选approved review读取，M为本级经理users检查数，N为新scan_run；不是正式平均数。GET task9SELECT/2UoW；COM_PING/建连/commit不属于955 cursor计数。完整前缀、replay/拒绝/成功audit和原错误顺序见agents/backend/write-path-static-ledger.md。

最小候选仅按domain guard加载依赖/跳过空前驱SQL，未实现；同主Tx task复用和成功audit scope另需证明，拒绝audit不省查库。所有现有project X/锁序/CAS/幂等/Schema保持，未提出S/X分层，不因未知项目分布就定瓶颈。

agents/backend/contract-short-compare-plan.md给出4c/5dcb精确前后、同t44_profile/18083/1worker、同预热、8并发ABBA四组各8秒、90秒deadline方案，尚未运行/未创建预留930。原controller失败/正式性能失败/源码超限不改写；根因UI调度优先收方案后，本轮材料交接并释放槽，后续工具/安静窗口另授权。
