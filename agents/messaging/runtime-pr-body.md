通知 API 现在通过实际 `NotificationFacade()` 执行本人项目范围查询、通知版本 CAS、独立已读和处理记录；消息进程通过现有 OutboxStore 执行持久 Pika confirm/mandatory 投递、DB 提交后 ACK、重投/坏消息隔离和原子降级。

- Agent-Role: messaging
- Prompt-Ref: ROLE-messaging-APPLICATION-v1
- Refs: #5
- 基于 `12f7141`；本岗代码仅 `backend/t44/messaging/` 与 `backend/tests/messaging/`，其余是本岗留痕。
- 本地模块自测28通过（17基础/SQLite/fake/配置、11真MySQL含真实子进程），3真Rabbit用例本机无服务未跑；b5a16e6两次真实Actions中三项实际均通过（原始ZIP/gzip+SHA及job/step见agents/messaging/ci/AUDIT.md）；消息模块语句覆盖84%，Ruff通过。失败的MySQL夹具及修正证据保留在本岗日志。
- 真Rabbit集成测试包含真实连接关闭/redelivery、mandatory return、同event去重/终态降级及新event恢复、DLQ；CI缺AMQP或数据库配置直接失败，不将fake通道称为真实MQ故障验证。
- 数据库 `recover_confirmed` 已接入1602f359并真MySQL验证；实际进程在真实TCP拒绝时完成fallback并SIGTERM退出0。publisher空闲连接心跳与active membership读范围锁已补并回归；真实Rabbit仍待CI。
- 原有contracts回归25通过、1失败、1跳过；失败是“默认应用缺通知依赖”夹具在默认门面已实现后收到200，已报根由BE显式注入故障，未越权改外岗测试或降低503断言。
- 当前后续快照需新真实Rabbit/托管CI；首阶段run整体失败仍保留，不宣称全产品覆盖率、规模、正式性能或独立验收通过。当前AI操作者为消息岗，不冒记人工修改。

最终本地复跑run10曾因共享pending积压使本岗目标event不在首50条而失败；只修dispatch测试批次至夹具事件数+1并断言本次retry尝试，run11恢复28通过/3本地skip，未改生产批次或删数据，原失败保留。
