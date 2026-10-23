冻结v1后，后端需要真实可运行的数据库事务、迁移与消息/扫描门面。本PR实现18表226列Core元数据及受限参数化Rows/Pred，MySQL8.4版本/摘要迁移和重复运行，hash-only初始化拒绝审计，幂等租约原语，OutboxStore消费去重/降级和ScanStore持久游标。代码评审/权限/状态转换与完整事务编排由backend接线。

真实官方MySQL8.4.11/t44_test首次/重复迁移通过，冻结SQL摘要一致；33项模块测试通过（21 SQLite/mock + 12真实MySQL），涵盖CAS、同key并发/租约、最终response_request_id、独立拒绝审计、consume/fallback并发只一通知及扫描恢复。CI DATABASE_URL+T44_DATABASE入口也用本机真库实际运行12通过，无skip；这不是GitHub托管CI通过。Ruff通过。首次CHECK错误分类3失败26通过记录保留后修复，没有降低DDL。

仍为draft：seed只有agents/database/drafts/未执行草稿，无生产seed_demo；尚需代表状态/轮次一致性及有效规模数据验证。消息/调度需责任岗接线，RabbitMQ网络/完整HTTP/性能/全局覆盖率/独立验收未在本岗宣称通过。下一阶段继续本PR，不把本次小阶段当完整项目完成。

Agent-Role: database
Prompt-Ref: ROLE-database-PERSISTENCE-v1
Refs: #3 #4
