Agent-Role: backend
Prompt-Ref: ROLE-backend-M0-COMMIT-v1
Refs: #3, #5

根据 `reports/modules/backend.md` 的消息事务边界 `proposal-v0` 及用户已采用的 `specs/business-rules.md` v1，请消息岗确认一个具体接口问题：某升级事件已因MQ故障转成带降级标记的站内待办后，是否以持久化的事件投递处置状态和 `(event_id, recipient_id)` 去重约束，阻止恢复后的同事件再次提醒？请说明后端同事务保存的事件/待发送意图，与消息岗“转待办/恢复后跳过该事件”之间的输入、返回结果与原子性边界，尤其是发送确认丢失或重复消费场景。

事件字段、唯一键和处置状态仍未冻结，本岗未实现投递或通知表。这是接口问询，不表示已取得双方约定或测试结果。
