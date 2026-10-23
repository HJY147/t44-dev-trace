Agent-Role: messaging
Prompt-Ref: ROLE-messaging-APPLICATION-v1
Refs: #5

PR20 的第二阶段已将 DB 原始提交1602f359（本worktree cherry-pick为76000e2）精确recover_confirmed接入默认worker；仅缺失通知超时补fallback、完整事件不改标、重跑不二提醒，均用真实MySQL验证。publisher现维护空闲心跳并清理失效channel；列表在当前成员共享锁范围内读取，真MySQL撤权并发验证通过。

本轮最终消息模块自测28通过（17基础/SQLite/fake/配置，11真实MySQL），3真Rabbit本地未执行。实际python -m t44.messaging子进程在真MySQL+真实拒绝TCP连接时完成专属event的站内fallback，无凭据输出并SIGTERM退出0；这不是RabbitMQ正常投递或broker服务重启通过证据。局部语句覆盖84%，Ruff通过；原先85%是较早快照，未改写历史。

真实Rabbit的mandatory return、连接关闭后redelivery、重复消息、终态fallback迟到消息与新event恢复、DLQ用例已实现，需有AMQP_URL+MySQL的CI执行；CI缺配置fail，不skip。原BE缺失依赖夹具的1失败仍由BE负责显式注入故障修正，原文保留。全产品规模/覆盖率/性能、独立验收未给通过结论；根已实测规模超5100，后续须实际重构并复测，不能改计数分母。

PR：https://github.com/HJY147/t44-dev-trace/pull/20；DB实际回复：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6360999718。操作者是AI消息岗，无人工亲改记录。
