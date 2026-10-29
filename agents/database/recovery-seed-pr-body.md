冻结v1后，后端和消息/调度进程需要可直接运行的SQL边界。本PR实现18表226列Core元数据、参数化Rows/Pred、MySQL8.4版本/摘要迁移、hash-only初始化拒绝审计、outbox/通知与持久扫描；后端负责权限、状态与业务事务编排。

本轮补齐confirmed超时恢复：先排除完整通知再限量候选，同event锁内重新比较收件快照，只在确实补缺时转换fallback；正常完整消费不误降级。真实复现低ID重试导致后续事件饥饿后，claim改按ready/lease时间及id排序，沿既有索引/锁序/SKIP LOCKED/token fencing，不改冻结DDL。

生产seed_demo已由真实CLI接线：新t44_bench生成40项目、6000任务、9000同项目DAG依赖、11400评审+3600决定（合计15000），另3600预案；七态覆盖，所有记录/证据明确synthetic，不能作为真人评审或实际交付证明。250条绑定批次在一个事务，重复同描述幂等、不同描述拒绝，不覆盖现有项目；保存真实配置raw hash与seed/version/anchor描述摘要。

实际证据：官方MySQL8.4.11首次/重复迁移，恢复14项回归，公平性修前真实失败/修后通过，全量数据JSON/轮次/批准引用/DAG/时间/容量核验及CLI重复exit0。删除无生产调用的CoreGateway/TableBinding与可选IdemStore，原18项安全/事务断言迁Rows后保留，连同Rows/seed当前23项通过；幂等断言转测实际Runtime并真库通过。原失败保留，没有用SQLite替代MySQL或弱化断言。

仍为draft：最终整合SHA全套/全局覆盖率/正式压测/独立验收未由本岗执行，RabbitMQ网络结论由消息岗独立提供。cloc2.10核本树产品checkpoint9aeb697应用4582、持久Python1500；旧FE/未全量MQ快照不能替代最终整合总计。不把模块生成耗时当性能门槛通过。

Agent-Role: database
Prompt-Ref: ROLE-database-RECOVERY-SEED-v1
Refs: #3 #4 #5
