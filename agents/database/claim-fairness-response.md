Agent-Role: database
Prompt-Ref: ROLE-database-RECOVERY-SEED-v1
Refs: #4 #5

按总协调要求先复现再修改：官方MySQL8.4.11/t44_bench无网络案例中，batch=2，两个旧低ID普通事件每轮失败后retry再次到期，后来同样ready的升级事件在3轮均未被claim。原默认id顺序存在真实饥饿反例，原失败记录claim-fairness-before.log保留。

已将pending按next_attempt_at,id，过期leased按lease_until,id排序，沿用现有索引、同事件锁序、SKIP LOCKED与token fencing，不改DDL。相同真库案例改后3轮内claim后来的升级事件，临时fixture仅按明确ID删除，未改6000任务业务数据；证据claim-fairness-after.log。此为DB候选公平性回归，不是RabbitMQ网络/吞吐结论。
