Agent-Role: database
Prompt-Ref: ROLE-database-M0-COMMIT-v1
Refs: #4

数据库岗本阶段实际产物为：

- `agents/database/WORKLOG.md`：已读资料、执行事实、本次文档岗问答及Git状态记录。
- `reports/modules/database.md`：四核心表与必要辅助数据的职责范围，以及后端/消息/调度待确认项。
- `records/handoffs/database.json`：未实现状态、未冻结接口、产物、命令与限制。
- `agents/database/github-stage-comment.md`、`agents/database/github-backend-interface-question.md`：本岗GitHub评论的实际正文。

业务实现为未实现，`draft-db-v0` 全部未冻结；没有模型、DDL、迁移或产品代码。仅做资料自检，未运行数据库、模块自测、联调、性能验证或验收，不构成审核通过。

后端需确认状态/版本冲突、请求幂等、错误码、项目权限及成功/拒绝审计事务边界；消息需确认事件与消费幂等、通知持久化及降级；调度需确认扫描窗口、规则版本、升级幂等、计划变更及重启续扫。后续须由总协调汇总冻结，字段字典与DDL逐表评审后方可另行授权迁移。

本阶段使用同一授权GitHub身份，`Agent-Role` 表示实际AI分工，不代表独立真人账号。初始化派工引用 `ROLE-database-BOOTSTRAP-v1`；本轮仅资料问答、GitHub问询与阶段提交。
