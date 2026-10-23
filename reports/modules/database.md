# 数据库模块报告：Issue28有限精确pair读取（设计阶段）

- Agent-Role database；Prompt-Ref ROLE-database-PLAN-HISTORY-v1；基线02c4b2a59cdcc3b3dc6bc7981735f4c1b74f181a；独立codex/database-plan-history。
- 本阶段只做真实DDL/RowsGateway/codec/异常/UoW复核与接口设计，产品净改0，未宣称实现、独立验收或全局通过。
- 真实schedule_changes12列，uq_schedule_task_version(task_id,to_version)支持每精确pair最多一行；无需DDL/API/14冻结件修改。
- 精确接口RowsGateway.task_schedule_changes(project_id:int,pairs:tuple[tuple[int,int],...])->完整codec解码list[dict]；输入≤100（去重前）、合法uint ID/Version，bool/串拒绝StatementRejected。
- 固定project_id+iteration_id IS NULL+精确tuple-IN，稳定task_id/to_version/id排序；空0execute、有1execute、无LIMIT/跨乘积/N+1/连接或提交。
- 结果完整列、ID/项目/pair/iteration范围、重复pair/id、硬bound违约显式PersistenceUnavailable并rollback-only；计划/理由/evidence业务匹配由后端拥有。
- 下游只从授权audit当前页提取pairs，在原GET UoW读取；后端matcher/UI不在本岗实现范围，故障不能转成缺理由成功。
- 生产预算因严格输入/结果校验上修净+35..50 cloc；最终以实测为准。原source_count.py+cloc2.10对基线实测6124行，仍超5100；不压行或改口径。
- 详细设计/输入输出/回归范围见agents/database/plan-history/design.md；基线计数见baseline-cloc.json。
- 自测将仅复用本岗993/988，先旧源真实红，再SQLite和真MySQL有限t44_test自有fixture；不清表/停库/读独立资料/跑完整CI或负载。
- 实际Issue4/28正文已用connector读取；阶段发布/精确读回在实施后归档，不提前写成功。
- 过程与真实prompt/交接已更新；AI修改不计学生亲改。精确源码审核与最终组合CI由root另调度，main仍保护。
