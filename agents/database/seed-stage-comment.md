Agent-Role: database
Prompt-Ref: ROLE-database-RECOVERY-SEED-v1
Refs: #3 #4

生产checkpoint已push 9aeb69795f67239b04352125f4b7db0427ce1272。seed入口为 t44.persistence.seed.seed_demo(factory, *, projects=40,tasks=6000,dependencies=9000,records=15000,manager_username='synthetic-manager',seed=44,anchor_at=None,template_path=None,rules_path=None,batch_size=250)。现有backend CLI seed-demo可直接调用，真实重复入口退出0。所有SQL继续归Rows，增加固定形状绑定insert_many/update_many；250条批次、一个外层事务。

官方MySQL8.4.11新项目t44_bench真实首次迁移+生成：40项目/6000任务/9000同项目DAG依赖/11400评审+3600决定=15000，另3600预案；已交付2400，其余六态各600。全量引用、冻结JSON、八段十项、四视角、轮次/批准指针、父前驱已交付且排期先于后继、容量核验通过。模板和规则取真实配置原字节SHA256；返回version/seed/anchor与manifest_sha256，不冒称整库密码hash可重现。重复同manifest幂等，不同seed拒绝，不删除或覆盖项目。所有记录/证据明确synthetic，绝非真人review或真实交付证明。

已删除仅旧测试调用的CoreGateway/TableBinding和可选IdempotencyStore，保留factory/Rows/Pred等生产接口；原18项资源/事务/绑定/NULL/标识符断言迁Rows后仍通过，连同seed共23项SQLite模块通过。原幂等并发/接管/旧token/final-request断言改调用实际Runtime并真MySQL通过，未新增纯租约到期拒绝。恢复1602f35及公平性8b60b71已另交消息岗并收到实际接线确认。

本岗没有运行最终跨模块全套/RabbitMQ网络/全局覆盖率/正式性能或独立验收；模块生成耗时不充当压测结论。cloc2.10按公开政策核本checkpoint应用4582行、其中持久Python1500，包含旧FE/未全量MQ的本树快照，不能替代最终整合统计。
