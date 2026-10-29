# MySQL持久层与内部门面

冻结v1的18表/226列由schema_v1.sql构造SQLAlchemy Core元数据，资源SHA256必须等于specs/database/schema.sql冻结摘要；不维护另一套手工字段清单。生产仅MySQL8.4/InnoDB。SQLite变体只供模块夹具，不能验证MySQL CHECK、锁或隔离级别；未放松生产DDL。

组合根构造MySQLSettings、create_mysql_engine(settings)、SqlAlchemyUnitOfWorkFactory(engine)，进程退出dispose Engine。每条新物理连接UTC、严格SQL、READ COMMITTED；池pre_ping/回收/超时，隐藏参数。with factory() as uow正常commit、异常rollback、总close；工厂每次新Session。CommitUncertain表示提交确认丢失，后续rollback只清理，服务必须沿原key恢复，不重新执行已完成请求。

uow.gateway是RowsGateway。只允许冻结表/列、参数绑定和固定谓词；拒未知标识符、SQL表达式、无where写入。此门面只供可信应用内部，不作为用户可选表名的CRUD API。DATETIME写入要求aware并转UTC naive，读取aware UTC，年份1000..9999；JSON直接dict/list，Python None写SQL NULL。codecs提供to_db_time/from_db_time、hours_to_quarters/quarters_to_hours、uuid_to_bytes/bytes_to_uuid。主键统一INT UNSIGNED，tasks循环FK仍显式生成id。

```python
with factory() as uow:
    g = uow.gateway
    row = g.get('tasks', task_id, lock='update')
    changed = g.update('tasks', {'id': task_id, 'version': old}, {'version': old + 1})
```

- rows(table, where=None, *, columns=None, order_by=('id',), limit=None, offset=0, lock=None, skip_locked=False, predicates=())；get(table,id,*,lock=None)。rows/get返回物化dict，查询结果在事务内关闭。排序字段前缀-代表降序，锁share/update。
- insert(table,values)返回本事务生成整数ID；update(table,where,values,*,predicates=())（别名update_where）及delete(table,where)返回影响行数；count(table,where=None,*,predicates=())返回整数。
- Pred(column,op,value=None)支持eq/ne/lt/le/gt/ge/in/is_null；ne(None)为IS NOT NULL，空IN为[]/0。savepoint()允许预期唯一冲突回滚局部操作；其他未恢复执行失败使UoW只可rollback。
- task_schedule_changes(project_id:int,pairs:tuple[tuple[int,int],...])->list[dict]：固定schedule_changes完整解码行，project_id与iteration_id IS NULL及精确(task_id,to_version) tuple-IN，按task_id/to_version/id排序；空0execute、非空1execute，无LIMIT。输入tuple最多100项（去重前），ID为严格int且1..4294967295、Version为严格int且1..2147483647，拒bool/字符串等StatementRejected。唯一pair键支持最多distinct pair数行；完整列/ID与项目pair范围/iteration/重复pair或id/硬上界违约PersistenceUnavailable且rollback-only。调用方在已授权页的原UoW使用，不另连/锁/提交；业务理由与快照匹配由后端负责，原audit不变。精确契约见agents/database/plan-history/design.md。
- PersistenceIntegrityError.kind为duplicate/foreign_key/check/other，constraint仅从已知约束名匹配；不传出SQL/值/驱动原异常。MySQL3819在PyMySQL属于OperationalError，亦正确分类check。

锁序由服务遵守：session FOR SHARE → idem FOR UPDATE → 必要project FOR UPDATE → members按user_id → tasks按id → children。依赖变更必须先锁project再查环，普通路径不得反向追加project锁。成功业务+audit+outbox+幂等快照在同一UoW。拒绝先rollback并close主UoW，才新UoW保存拒绝审计及错误快照；审计失败不能返回正常业务拒绝。权限、状态机、依赖环、同key摘要、升级首次CAS及通知版本语义由backend编排，不把裸gateway调用声称为业务原子性。

migrations.migrate(engine,*,expected_database)核显式库名、MySQL8.4、冻结摘要、版本、结构；空库执行打包DDL。重复运行不重建数据；不兼容或中断标记拒绝自动修复。MySQL DDL隐式commit，技术t44_schema_migrations记录开始/完成，不能谎称DDL可事务回滚。accounts.initialize_user(factory,*,username,display_name,password_hash,request_id=None)只收合法Argon2id hash；非法入口独立持久脱敏审计，绝不保存原口令/hash。CLI先hash由backend负责。

## 消息与调度可运行门面

OutboxStore(factory)各方法使用独立UoW，MQ网络I/O必须在方法外。

- claim(*,now=None,limit=100,lease_seconds=30)返回已提交的event行列表；FOR UPDATE SKIP LOCKED认领pending或过期leased，每行新lease_token(bytes16)，attempts递增。
- get(event_id)返回行或None；confirm(event_id,lease_token,*,now=None)仅当前leased token进入confirmed，返回bool；fallback终态后迟到confirm为False。
- retry(event_id,lease_token,*,now=None,delay_seconds=5,error_code='PUBLISH_FAILED')将仍归本token的leased行回pending，返回bool。
- consume(event_id,*,now=None)返回event_id/created/fallback；fallback(event_id,*,now=None,lease_token=None,error_code='MQ_UNAVAILABLE')同样返回创建数，旧token返回stale_owner=True。两者锁同outbox行，唯一(event_id,recipient_id)，fallback终态与通知在同事务；重复或迟到消费不再提醒。已存在正常通知保持原处理/已读状态。消费提交后消息岗才ACK。
- event_type=1为business.changed，无站内升级通知；event_type=2须有同事务提交的escalation_events ledger，收件人取已冻结recipients快照，无100人截断。层级取ledger，不把物理1..255当新增业务规则。

ScanStore(factory)：start(run_id,*,rule_version,rule_snapshot,rule_hash,cutoff_at=None)返回持久行；run_id字符串/UUID映射run_key bytes16与整数id；相同UUID并发唯一，同UUID改版本/hash拒绝。get(run_id)、recoverable(*,heartbeat_before,limit=100)取未完成旧心跳行。page(run_id,*,limit=200)按id返回state1..5及快照窗口候选，固定cutoff，id大于游标。checkpoint(run_id,*,last_task_id,scanned_delta=0,created_delta=0,duplicate_delta=0,finished=False,error_code=None)单调推进并返回持久行；相同游标不重复计数、逆向拒绝。进程崩溃status1可用原UUID重启续扫；升级提交与游标分开，崩溃重扫由unique(task_id,schedule_version,level)去重，不能假称两次HTTP与checkpoint一个事务。规则判定/HTTP调用/定时器由调度岗负责。

幂等事务统一由backend Runtime使用Rows编排；已移除没有生产调用的可选IdempotencyStore以及早期CoreGateway/TableBinding，原并发/租约/final-request断言迁到实际Runtime，原18项基础安全/事务断言迁到Rows，保持全部验证意图。

## 实测边界

本机T44_TEST_CREDENTIALS指向ignored app凭据文件且显式T44_TEST_DATABASE=t44_test时：`PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/persistence -q`。仅t44_test；不触及acceptance/bench。CI使用DATABASE_URL+匹配T44_DATABASE（t44_ci），无本机私密文件依赖，CI缺配置直接fail；测试模块标记integration。本机实际复跑该环境变量入口12项通过，非GitHub托管CI结果。当前33项通过，其中21项SQLite/mock、12项真实官方MySQL8.4.11案例。首次真库29项中3项错误分类失败保留原日志，修复后通过。真库覆盖首次/重复迁移、SHOW CREATE核心表、UTC/strict/RC、约束、生成ID、并发CAS/幂等租约、独立拒绝审计、outbox降级并发与扫描恢复。不等于RabbitMQ网络、API全链、性能、全局覆盖率或独立验收通过。

seed.seed_demo(factory,*,projects=40,tasks=6000,dependencies=9000,records=15000,manager_username="synthetic-manager",seed=44,anchor_at=None,template_path=None,rules_path=None,batch_size=250)已实现，CLI现有seed-demo直接调用。单UoW绑定批量插入/主键更新，空项目集限定、重复同manifest幂等、不同描述拒绝，真实配置raw hash及seed/version/anchor入manifest，首次返回全部统计。默认40/6000/9000/11400reviews+3600decisions/7态，另3600预案；历史VERSION1的真MySQLbench已全量核引用、JSON模型、批准指针/轮次/容量及DAG/当前前驱；当前VERSION2仅完成开发SQLite性质/再现验证，真实MySQL与组合CI待根调度，不继承旧结论。全部synthetic，见SYNTHETIC-DATA.md。旧agents/database/drafts只历史未执行版本，不是当前生产入口。

recover_confirmed(*,confirmed_before,now=None,limit=100)只返回本轮真正补缺并从confirmed转fallback的event_id/created/fallback字典。固定MySQL JSON_TABLE+NOT EXISTS在候选阶段排除完整通知事件，完整旧事件不占limit；FOR UPDATE SKIP LOCKED与consumer/fallback锁同事件，锁内复查后created>0才变终态。默认超时由消息进程传入，不新增升级规则；已齐通知不误标降级，旧token仍stale_owner，迟到confirm不回退。

Rows新增insert_many(table,values)与update_many(table,values)：同形绑定参数批量，update每行必须有id与非空变更，不提供无条件批量写。seed使用batch_size分批但一个外层事务，不逐行建事务。
