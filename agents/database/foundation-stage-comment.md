Agent-Role: database
Prompt-Ref: ROLE-database-FOUNDATION-v1
Refs: #4

本岗在codex/database-runtime独立树完成通用Engine/UoW/CoreGateway基础；公开入口位于backend/t44/persistence，工厂/CommitUncertain接口已与backend确认。测试位于backend/tests/persistence：最终18 passed，Ruff通过；首次七项风格失败原日志保留。

这是字段无关的真实资源生命周期与参数化执行逻辑，不是18表ORM/迁移或业务仓储。SQLite测试只建临时玩具表，mock只验证MySQL初始化与敏感错误脱敏；没有MySQL实库、项目DDL、业务CAS/图锁/审计/幂等/MQ或API联调结果。Q002人的取舍仍待回复，不能把技术设计复审当作用户字段/错误码审定。详细边界、原始日志和实际prompt见本岗WORKLOG、模块报告及handoff。拟以独立分支draft PR交总协调，不自行审核成功或合并。
