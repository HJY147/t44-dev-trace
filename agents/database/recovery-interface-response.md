Agent-Role: database
Prompt-Ref: ROLE-database-RECOVERY-SEED-v1
Refs: #4 #5

已实际读取messaging评论6360793043并实现精确签名：OutboxStore.recover_confirmed(*, confirmed_before, now=None, limit=100) -> list[dict(event_id,created,fallback)]。

候选由固定MySQL JSON_TABLE + NOT EXISTS先排除通知完整事件，再按id取limit并FOR UPDATE SKIP LOCKED锁同outbox行。锁内重新比较recipients与通知集合，只在确实新建缺失通知时status3→4并返回结果；完整事件不改状态、不占候选limit。消费/普通fallback相同event→children锁序，已存在通知不修改已读/处理信息。旧token在终态已清空租约时返回stale_owner=True为预期，迟到confirm不得回退。

官方MySQL8.4.11/t44_test真实14项持久回归通过，新增验证3个旧完整事件不饿死后续缺失、重跑不重复恢复、consumer持锁与并发恢复跳过、consumer提交后不误标降级。首轮2失败12通过源于共享库既有缺失事件被正常优先恢复，保留原失败后隔离夹具时间窗，不删除他岗数据；第二轮14通过。未改冻结DDL，未把这些模块验证当RabbitMQ网络或独立验收。

消息岗可直接按该方法适配，本次先交恢复小阶段；seed后续继续，尚未称完成。
