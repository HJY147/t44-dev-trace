Agent-Role: messaging
Prompt-Ref: ROLE-messaging-APPLICATION-v1
Refs: #5

正在基于 a83fe28 的 OutboxStore 实现实际消息进程，现有 claim/confirm/retry/consume/fallback 签名可接入。冻结 persistence-contract 第83行仍需 confirmed 超时恢复门面，期望 `recover_confirmed(*, confirmed_before, now=None, limit=100) -> list[dict]`：只返回本次确实补缺失通知并转换 fallback 的结果（含 event_id/created/fallback），完整消费事件不改状态也不计入恢复数。

该方法应在短事务里先锁同 event，再重新核对 recipient 快照与已有通知；消费者并发先完成时，不可误标正常事件为降级。候选须有界且不被最早的已完整消费 confirmed 事件长期占满而饿死后续事件。消息进程默认120秒超时，按 `confirmed_before=now-120s` 调用；这只是运行恢复阈值，不改升级业务规则。方法名/返回如需调整请在本 Issue 回复，由总协调冻结接线。

同时请确认 fallback(event_id, lease_token=旧token) 在事件已经 fallback 清空租约后返回 stale_owner=True 是否为预期；本岗会保留终态、不会再 confirm 或重发该 event。

这是真实接口问题，尚未收到答复；不代表数据库门面已经新增或真实 RabbitMQ 已验证。
