# 数据库模块报告：PERSISTENCE-v1阶段2

## 任务与状态
- 岗位database，实际prompt ROLE-database-PERSISTENCE-v1；用户D004采用Q002后v1冻结，已合并ae60dc3及集成6afd13f，不再以“Q002待回复”为当前阻塞。
- 独立树.agent-worktrees/database / codex/database-runtime，PR17保持draft；未操作根索引、共享lock、其他岗源码或独立测试资料。
- 18表226列Core元数据、参数化Rows/Pred、真实版本迁移、hash-only初始化、幂等原语、outbox/通知和持久扫描已实现。
- seed尚未实现生产入口；草稿在agents/database/drafts/，未执行，须补代表状态/评审证据轮次一致性后再验证，不算完成。

## 实际产物与接口
- backend/t44/persistence/schema_v1.sql与冻结schema.sql SHA256 c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4一致，schema.py从它构造元数据，不复制字段清单。
- Engine每连接UTC/严格SQL/READ COMMITTED；UoW每次独立Session、正常commit/异常rollback/总close，提交确认丢失保留CommitUncertain，不能以cleanup rollback宣称未提交。
- RowsGateway rows/get/insert/update/delete/count/savepoint及Pred已与backend直接确认并接线；完整参数/codec规则见产品README。表/列allowlist、绑定值、空where和SQL表达式拒绝。
- migrations.migrate(engine,expected_database=...)真实初始化及重复运行，不破坏数据；t44_schema_migrations只技术例外。DDL隐式commit，中断标记禁止无声修复/drop。
- accounts.initialize_user只接受合法Argon2id hash；非法输入独立新UoW持久脱敏拒绝审计，原口令/原hash不入审计。CommitUncertain仍传播。
- IdempotencyStore提供claim/lock_owner/complete/reject_after_rollback，可供backend选用；并发唯一、摘要先匹配、过期行锁+owner换代、COMPLETE保存最终结果处理者request_id，不清旧key。
- OutboxStore(factory)提供claim/get/confirm/retry/consume/fallback；消费和fallback锁同event，唯一(event,recipient)，降级终态隔离迟到confirm，通知已读/处理状态不被重复消费覆盖。
- ScanStore(factory)提供start/get/recoverable/page/checkpoint；UUID持久唯一、规则快照/固定cutoff、单调游标和重复checkpoint不重复计数，重启可沿原UUID恢复。
- 成功业务/audit/outbox/idem同事务，拒绝先主事务rollback释放后独立会话保存；权限/状态/图查环/升级首次CAS和HTTP错误映射由backend编排，本岗门面不冒称已完成业务全链。
- 锁序session→idem→project(必要)→members user_id→tasks id→children；依赖变更先项目锁串行再查环。裸gateway不自动验证调用者是否遵守锁序。

## 真实验证
- 官方MySQL8.4.11真实t44_test，app账户；未用admin权限，未动acceptance/bench。首次迁移与重复迁移均通过，18表226列无静态结构核对缺陷，SHOW CREATE核对四核心表InnoDB/自增/CHECK。
- 真实连接UTC、strict、RC；真实tasks生成ID/同事务读取；真实CHECK/FK拒绝、savepoint恢复、两线程同旧version CAS只有一次成功。
- 真实非法hash入口独立拒绝审计；PROCESSING response_body为SQL NULL；同key并发唯一/租约换代/旧owner拒绝/最终response_request_id重放。
- 真库并发相同scan UUID仅一行；游标新Store实例恢复与重复计数防护；outbox过期租约、retry/confirm、重复消费及consume/fallback并发仅一通知、迟到confirm拒绝。
- 最后执行：T44_TEST_DATABASE=t44_test T44_TEST_CREDENTIALS=<ignored-private-file> PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/persistence -q，33 passed（run5，0.50s）；其中21 SQLite/mock、12真实MySQL案例。
- Ruff format/check实际退出0。日志persistence-lint-stage2.log、persistence-mysql-tests-run5.log；首次真库3失败26通过的3819分类问题保留run1，修复后29再33通过。
- SQLite只验证可移植夹具/生命周期，mock只验证连接初始化/故障；不替代真库。未跑RabbitMQ网络、完整HTTP跨模块、全局覆盖率、性能或独立验收。

## 对接、过程与后续
- backend已收到可merge阶段8095b6e及f3ea3434ddfae21e7c8f297d389b6a80adea9db7；后者含迁移/accounts/task自增修复。后端公开接线确认见Issue4评论6360456261。
- 本次真实Issue4评论 https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6360580838 ，Issue3 https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6360581522 ，正文persistence-interface-comment.md。
- 消息/调度责任岗目前尚待总协调唤醒直接确认Store接口，未伪称这些岗已接线或MQ通过。当前小阶段优先交可运行门面，以便下游编码。
- 日志agents/database/WORKLOG.md、prompt原文agents/database/prompts/ROLE-database-PERSISTENCE-v1.md，交接records/handoffs/database.json。所有产品改码为AI，本轮用户采用方案与AI实际编码分别记录。
- 需恢复工作：完成seed_demo及同项目DAG/代表状态/轮次证据一致性真库验证；加强结构漂移/项目图锁等模块检查；配合后端/消息/调度真实集成，最终复审与验收另行执行。

- CI入口已改为DATABASE_URL+显式匹配T44_DATABASE=t44_ci，integration标记；CI缺配置fail。本机按相同环境变量入口实际跑12 passed（persistence-ci-env-test.log），不等于GitHub CI通过。
