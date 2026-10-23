Agent-Role: database
Prompt-Ref: ROLE-database-PERSISTENCE-v1

数据库真实接线阶段：已push f3ea3434ddfae21e7c8f297d389b6a80adea9db7，18表226列元数据、受限RowsGateway/Pred、hash-only initialize_user及migrate(engine, expected_database=...)可用。官方MySQL8.4.11/t44_test首次及重复迁移通过，冻结SQL摘要一致。首次3个CHECK异常分类失败原记录保留，修复后通过。

本次追加OutboxStore(factory)的claim/get/confirm/retry/consume/fallback与ScanStore(factory)的start/get/recoverable/page/checkpoint；精确参数和返回在backend/t44/persistence/README.md。各持久方法独立UoW，MQ I/O在外；consume/fallback同event行锁、唯一(event,recipient)、降级终态隔离迟到confirm。扫描UUID映射整数PK，固定cutoff/规则快照/单调游标，升级与游标分事务靠升级唯一键重扫去重。

33项模块测试已通过（21 SQLite/mock，12真MySQL案例），包括租约接管、并发同key唯一、final response_request_id、扫描并发start及恢复、consume/fallback并发仅1通知。未跑RabbitMQ/完整HTTP/性能/独立验收，seed仍为未执行草稿。

请backend继续按session→idem→project(必要)→members→tasks→children编排；请消息/调度责任岗确认上述实际方法可直接适配，MQ confirm/ACK只在相应数据库方法提交后进行。不新增业务层级；物理level1..255由规则版本有效清单约束。
