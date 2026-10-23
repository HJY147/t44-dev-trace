# 实际完整持久实现派工

发送者为AI总协调，执行者为database AI。用户实际采用Q002在D004/U006另记；AI编码不是用户亲自改码。以下为本次实际消息原文，不是事后优化版。

> 用户现已真实采用Q002“采用推荐方案，继续开发”。D004/U006及v1freeze在ae60dc3（codex/team-bootstrap已push），manifest records/spec-freezes/v1.json，业务字段不变仅phase/version1.0.0。开始ROLE-database-PERSISTENCE-v1完整实现，不停通用基础：你干净独立树merge ae60dc3，保留基础PR17并随最终scope重写标题正文。实现冻结18表SQLAlchemy Core/ORM元数据、真实MySQL版本迁移（空库初始化+重复运行无破坏、核版本/摘要，技术迁移版本表可注明例外）、参数化持久门面、索引约束/CAS/锁/幂等认领完成/独立拒绝审计所需能力、outbox/通知/持久扫描，及有效合成seed约40项目6000task9000依赖15000review/decision（不要假证据冒真人），四核心表规范检查实际代码。后端负责业务语义/事务编排，你必须先在几分钟内直接跟backend确定真正可编码的门面签名和测试stub/Protocol，Issue3/4真实对接，不只写文档。可用泛化信任内部参数化Rows/get/insert/update+锁/计数/分页与图查询门面，所有SQL归你；依旧采用SqlAlchemyUnitOfWorkFactory/CommitUncertain，支持并发锁序session→idem→project(必要)→members升序→tasks升序→children，不把缺锁实现称原子。后台MQ/scheduler稍后接入，要暴露可用outbox租约/消费去重/fallback同event终态、scanrun持久游标门面并与owner确认。成功业务/审计/outbox/idem快照同事务，拒绝rollback释放后独立新会话保存，不确定commit不可当rollback。UTC/严格SQL/READ COMMITTED，PyMySQL[rsa]已锁，schema是MySQL8.4。你可本机SQLite做可移植夹具且如实限定；不要为SQLite放松生产MySQL约束。真实MySQL/Rabbit后由root集成GHA执行，需要提供seed/迁移CLI可复用函数给backend CLI适配。你只改自己产品路径backend/t44/persistence/、backend/migrations/、tests/persistence和本岗记录；不改后端共享lock/pyproject或其他岗源码；新依赖问BE。全产品有效3500–5100行需紧凑实用，禁止填充；无需生成重复巨量样板。每实际阶段自己显式commit/push PR17，完整范围必要自测/真实失败原样处理，标清哪些未跑，不能把mock=MySQL、模块=全局覆盖、AI编辑=人工改。禁止接触独立testing私有资料。容量失败从本树恢复不换模型。

实际追加：官方MySQL8.4.11在127.0.0.1:13306就绪；仅app权限连接明确选择的t44_test/dev，acceptance/bench留后续。不输出或提交ignored凭据/连接串，绝不读或用admin文件。

实际阶段收口指令原文：
> 目前消息/定时调度完整编码排队等你的OutboxStore/ScanStore稳定可运行门面。请下一小阶段优先补它们必要真实MySQL测试并commit/push给SHA+精确签名，然后可暂结束本轮释放槽位（seed/最终报告如果还未做完如实列缺口，后续再恢复，不要伪称完成）；先让下游写真实代码优于全部报告收尾才交接。seed若已在做可同阶段完成，但别用治理文档延迟可用接口。合成数据最终需同项目无环依赖/状态证据轮次一致，覆盖有代表性的状态分布；15k仅是合成夹具，不能假称真人评审。不要为凑数量写无效数据。

产物对应：18表元数据/Rows与codecs、migrations/accounts、delivery/scans/idempotency、真实MySQL模块测试与原失败记录；seed阶段未完成，草稿只归档于agents/database/drafts/，不提供占位生产成功入口。改进理由：由冻结后的完整实现任务收敛为先交可运行下游门面的小阶段；不抹去剩余工作，也不伪造同prompt六版演进。
