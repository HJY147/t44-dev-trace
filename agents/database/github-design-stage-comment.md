Agent-Role: database
Prompt-Ref: ROLE-database-DESIGN-v1
Refs: #4 #13

本轮仅归档已完成的数据库设计和真实过程记录，未扩展新业务设计。提交范围为 `specs/database/field-dictionary.md`、`schema.sql`、`persistence-contract.md`，以及本岗日志、静态自查、实际派工归档、Issue评论正文、模块报告和handoff；不含总协调共享台账或其他岗位文件。

现有静态自查：18表225列、35外键、94命名约束、41显式原因码映射；设计及当轮OpenAPI SHA均复核一致。与backend确认见[责任岗回复](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358617437)。会话→幂等→项目（需要时）→成员→任务的锁序、首次升级CAS及level可扩展范围均已对齐。

仍是待审核的设计提案：未执行DDL、未迁移、未写模型，未进行MySQL语法/约束运行、事务并发、MQ故障、续扫、性能或验收验证。静态检查不是审核通过；四核心和辅助表逐表审核、消息/调度边界及迁移版本/运维恢复仍须补齐。本轮只在获独占时段进行本岗commit，不push/checkout/merge，不发布reviewer通过状态。
