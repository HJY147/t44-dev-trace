# 实际派工 ROLE-scheduler-APPLICATION-v1

来源：总协调实际消息；实际操作者scheduler AI。以下为原文，不把AI技术实施记为用户亲自改码。

开始ROLE-scheduler-APPLICATION-v1完整真实扫描/升级实现。用户D001/D004已采用，v1冻结ae60dc3；当前总协调本地codex/integration整合SHA12f7141026376763086e41a5b4db9ac1e82cfa33，含API47c21f与DBa83fe28，直接merge此共享git SHA到你干净树保留77基础测试/PR19。只写自己backend/t44/scheduling、resources/escalation-rules.json、tests/scheduling及本岗记录，不改BE/DB源码/共享锁。读AGENTS/冻结OpenAPI+backend-design/persistence-contract，以及当前services/application.py、common.Call/Runtime与DBREADME，别沿旧口头接口猜。
必须对齐API默认零参 t44.scheduling.facade.EscalationFacade()，三个方法rules(g,c)、list(g,c)、create(g,c)返回冻结data，create在传入g同UoW执行，Runtime统一鉴权/idem/审计/完成快照，不能私自提交。单任务升级要重验state/expected_version/schedule_version/rule_version/窗口+服务scope；同事务outbox(event_type2)+escalation_events+task.version/escalation_count+audit（audit根Runtime写）+idem快照。硬去重task/schedule/level，rule_version不绕过去重，重复返回created=false不加任务计数/版本，参照DB savepoint避免临时outbox孤儿；snapshot责任人+所有active经理，临期owneronly，递增规则最高优先级。create结果缺audit_id由Business.finalize补，所以data校验顺序注意一致。服务token认证在Runtime/identity已实现，你用真实Call接口不另造JWT。
当前foundation JSON是内部rule_version字符串/levels，不能原样作为冻结GET返回：API要version正整数、selection、rules每项显式start/end含边界+priority+recipient_kinds、effective_at/decided_by；请将一个配置+一个解释模块改成符合冻结结构的真实可扩展规则解释器，不硬switch3级。阈值D001已用户采用；配置结构为AI技术选择，身份metadata如演示ID要标明真实初始化映射/合成边界，不冒称人逐条批准了例值。raw UTF8 hash+snapshot保存且规则变更原/新/时刻/影响/决定者有迹。保留elapsed差值避免1000/9999溢出与UTC微秒支持。
完整进程 python -m t44.scheduling：APScheduler独立单实例/注入60s扫描，keyset分页和持久UUID run/游标/heartbeat/计数、崩溃恢复重扫无重复，API多worker不各起timer。DB已交 from t44.persistence.scans import ScanStore(factory)：start(UUID,*,rule_version,rule_snapshot,rule_hash,cutoff_at=None)，get(UUID)，recoverable(heartbeat_before,limit)，page(UUID,limit)，checkpoint(UUID,*,last_task_id,scanned_delta,created_delta,duplicate_delta,finished,error_code)。OutboxStore也已就绪，消息岗正同时做consumer/fallback，不互写。扫描应通过实际Runtime.execute(Call,validate)的统一服务认证/idem/事务或共用你create(g,c)门面，必须和API保持一次原子升级，不绕audit。直接与BE（当前inactive，可Issue3+root转达）对接构造Call的稳定签名、部署service-token初始化/CLI支撑需求；不编造接口。当前CLI签发服务会话尚缺可提root/BE下一轮实现。
本机真MySQL8.4.11 127.0.0.1:13306，根ignored0600 .agent-worktrees/.runtime/mysql-8.4/credentials.json四键，不打印secret；模块真库可用t44_test但请用自己前缀，不清空其他module数据。APIdev在18080，演示账号根ignored api-demo-credentials.json已给FE。本机无Rabbit，CI有真实AMQP_URL/DATABASE_URL/T44_DATABASE；真库测试支持CIenv，不依赖本机私密JSON、不在CI skip。要实际20条超期全覆盖、重扫/重启不重复、并发同level一个event、改期新版本允许新事件、已回滚/交付排除blocked计时，规则扩展真实diff验证≤1配置+1模块。原失败保留，不能用mock=实库或基础100%=全局；整产品生产有效3500–5100行紧凑实现不填充。每实际阶段自己commit/push同PR19更新scope，Issue6真交流，完成SHA/证据/缺口；不要独立testing消息/资料，容量失败恢复文件不换模型。先可用代码，再紧凑记录。

## 实际纠正与对应

总协调后续实际消息：“你核对得对，直接使用现有service-token CLI；我先前‘尚缺’的描述不准确，以12f7141实际代码为准，不再新增替代签发。请保留这条AI对AI误判纠正事实，不能算用户识别/人工修改。”本岗已读cli.py并使用真实命令发测试服务会话；这是AI对AI事实纠正，没有冒充用户识别或人工改码。

facade.py复用Runtime事务边界；scanner.py复用Call/Runtime与数据库门面；__main__.py组合真实进程；rules.py和唯一JSON解释冻结结构；tests/scheduling、原始日志/覆盖/XML记录模块验证。改进理由：以真实源码签名取代口头猜测，并区分规则采用、AI配置结构、合成身份metadata、真实MySQL和未运行的MQ/独立验收。无另造无意义演进版本。
