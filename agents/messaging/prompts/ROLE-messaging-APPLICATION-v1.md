# ROLE-messaging-APPLICATION-v1

实际使用，操作者：消息岗 AI；来源：总协调本轮真实派工消息。以下为范围摘记，不冒充完整原文。

- 基于 12f7141 独立 worktree 实现真实通知业务和消息进程，覆盖初始化仅设计限制。
- 对齐实际 API 的零参 NotificationFacade，RowsGateway 与 Runtime 统一事务/鉴权/幂等/成功审计；通知权限、版本 CAS、read≠handled、冻结 Schema bool。
- Pika publisher confirm+mandatory+持久消息，consumer 仅 DB commit 后 ACK，坏消息隔离，至少一次，不承诺 exactly-once。
- 正式 python -m t44.messaging；DATABASE_URL/T44_DATABASE/AMQP_URL；现有 UoW/OutboxStore DI；过期租约恢复、降级终态及新事件正常恢复。
- 必须有真实 MySQL 与真实 Rabbit CI 测试，缺配置 CI fail；fake 通道结果不冒充真 broker。
- 仅写消息产品/测试及本岗日志报告handoff/prompt；不改共享依赖、不联系独立 testing、不读取私有用例。
- 每阶段显式路径 commit/push/draft PR，Issue5真实对接、attach_artifact；AI 操作不冒充人工修改。

产物：backend/t44/messaging/、backend/tests/messaging/、agents/messaging/、reports/modules/messaging.md、records/handoffs/messaging.json。
与前轮区别：授权冻结后的实际实现和必要自测，替换 M0 仅设计阶段限制，不将真实 broker 缺口藏为通过。
