Agent-Role: messaging
Prompt-Ref: ROLE-messaging-M0-COMMIT-v1
Refs: #5

消息岗 M0 阶段说明：仅完成职责与接口需求初始化，业务未实现，设计草案未冻结。

实际产物：
- `agents/messaging/WORKLOG.md`：真实执行日志及文档岗问答。
- `reports/modules/messaging.md`：责任、事件需求、幂等及 MQ 降级恢复边界。
- `records/handoffs/messaging.json`：结构化交接与未确认项。
- `agents/messaging/github-stage-comment.md`、`agents/messaging/github-interface-question.md`：本轮评论原文。

本岗负责 RabbitMQ 投递/消费、通知去重、故障降级和站内列表/已读业务；调度负责扫描规则，数据库负责唯一一套通知模型，前端负责页面，后端负责统一鉴权入口。

尚未冻结：调度事件及稳定业务幂等键、升级计数与投递意图的原子落库、MQ 确认/重试/恢复、列表/已读请求与错误码。向调度 Issue #6 提问仅为待确认问题，不代表形成约定。

未写产品代码或 DDL，RabbitMQ/数据库/服务未启动，模块测试、集成验证和独立验收均未运行。仅确认本岗记录存在及交接 JSON 格式，不作业务通过声明；未联系独立测试岗。

初始化提示词 `ROLE-messaging-BOOTSTRAP-v1` 关联 `agents/messaging/TASK.md`；本轮提示词用于如实问答、评论与阶段提交，不是业务实现或契约冻结授权。
