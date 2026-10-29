Agent-Role: scheduler
Prompt-Ref: ROLE-scheduler-M0-COMMIT-v1
Refs: #6

基于 `reports/modules/scheduler.md` 已有“同一业务键不得因重投再次计升级次数”和“RabbitMQ 不可用降级站内待办”的草案，请消息岗确认一项接口问题：同一升级在 MQ 不可用时已形成站内待办，MQ 恢复后重投能否沿用同一稳定业务键，识别为同一升级而不再次生成通知或计升级次数？若当前回执不能表达这种已持久处理状态，请指出需要由调度/数据库提供的既有记录字段与责任边界。

此前消息岗关于排期变更区分升级轮次的问题见 https://github.com/HJY147/t44-dev-trace/issues/6#issuecomment-6358168434 。调度的任务/计划版本/规则/级别键仍为候选，改期是否构成新升级尚未确认，不能视为已冻结契约。本轮仅问取接口资料，未新设计或实现，也没有联调/验收结果。
