# 后端全量结构研究：一项净37行的跨岗RFC，尚无833行闭合方案

实际设计/分析/工具执行者：后端AI；prompt `ROLE-backend-ARCHITECTURE-SCALE-20261028-v1`。设计先提交57354c71，再作以下评估。本轮**仅设计与只读证据，产品改动0、实际净减0**，不称实现、自测、正式性能或独立验收通过。

## 准确基线与用户边界

独立分支 `codex/backend-architecture-scale-20261028` 从200001087d41113984a3f1a96ad7bdcf66bca90b建立；其全部65应用文件逐字同a12e9e70b963bacafda3242bb6d82e53ee912ff1。既有source_count.py在已提交设计源57354c7188e9ac0cf9addf36d9a40cdca9c70265实际执行：**5933行，上限5100，超833；--require-range退出1**。逐文件固定cloc数为后端43个Python文件4834，前端22文件1099。backend/t44共有51个受跟踪路径，另8个README/JSON/SQL原本在应用计量之外；这是范围澄清，未改变任何计数规则。

用户最新明确“没有补充，继续现有口径”。继续把前端/CSS、迁移、CLI和造数计入现行口径，原排除项不变；400持续活跃请求、270ms、600s协议也不改。费用充足不证明源码或性能方案成立。本岗不删功能，不移到SQL/JSON/工具/生成代码，不把新抽象藏到依赖中，也不改门槛。

已读全部43计入Python模块、4份模块README/合成说明、资源及冻结API/DDL结构。API31路径/38操作/130schemas、DDL18表226列。原始T44任务书及作业要求由现有主树specs/sources只读取得，未复制原件或学生研究正文到分支。职责表、D001/D002/D004/D005/D006/D008与冻结设计用于区分原要求及工程选择。未访问tmp792/private或未发表独立资料，未进行云/运行库操作。

## 不重叠预算汇总

以下均为**设计预算**。只有“片段实量”在普通Ruff100列下用同一固定cloc对未应用的设计片段计量；它不代表完整候选已提交、已回归或真实产品节省。工作包区间尚无可运行实现，只供owner评估成本，不能作为将来节省保证。

| 候选 | 删除/替换依据 | 新增/保留成本 | 预计净值 | 责任/准入 |
| --- | --- | --- | ---: | --- |
| A 统一受信组件Call与通知CAS | Business六操作旧34；通知四方法旧65；CAS旧14 | 新14+47+15 | **37，片段实量** | backend+messaging；必须明确迁移内部Python签名 |
| B 消除插入初态与冻结DDL的重复事实 | escalation._run的6个默认字段；event插入8字段 | 原DDL已提供相同初值，无新框架 | **14，静态逐字段预算** | scheduler+database确认完整存储快照一致 |
| C reject_if/expect公共异常构造 | 仅30个实际短调用点毛省30 | 14个文件import+3行helper | **13，片段实量**；工厂式7 | 各owner；建议低优先级，不做全量替换 |
| D 已物化列表first_or_error | 5处require+取[0]合并毛省5 | 公共3行helper；均可扩展现有common import | **2，静态预算** | backend+scheduler；收益不足单独实施 |
| E UTC/UUID转换复用 | common.now/uuid_text与codecs同义，移除原UUID import及4行函数 | codec alias导入由1变3行，isort已核 | **3，静态预算** | backend；保留common原可调用名字 |
| F 单一规范化schema目录视图 | migrations中四方法共189 | 预计160–210：采集/期望/规范化/诊断映射 | **-21至29，工作包估计** | database；不移除DB新反例，未证明值得实施 |
| G 事务内scan run注册组件 | ScanStore.start27+EscalationFacade._run35=62 | 共享注册/两调用桥接约52–72 | **-10至10，工作包估计** | database+scheduler；保持查询/锁时点才有效 |

A至E设计净预算合计69，未实施；即使全部兑现仍5864行、超764。F/G最乐观再加39，但G与B重复6个默认字段，必须扣除：**本轮所有方案最乐观预算102，5933−102=5831，仍超731**。F/G可能净增；新接口兼容壳、类型/故障校验、导入排版、owner回归发现都可能进一步减收益。不能据此承诺833，也不能把102当所有可能架构的数学上界。当前正式计数仍5933。

## A：统一受信组件调用和现有CAS，交两owner评审

此前只改Business dispatch而保留通知平铺签名，完整预算仅15，已排除。本次不同之处是**同时消除参数搬运与重复CAS算法**：通知门面采用与升级门面相同的(g,Call)输入；Call内actor/project/path/body/clock均由当前Runtime/HTTP校验产生，客户端不能选择组件、方法或表。静态6项映射只包含原有操作。

输入不变量：list仍使用c.actor_id+c.query，按query.project_id做原实时资格检查；写仍使用c.project_id、path.notification_id、body.expected_version与c.clock。输出仍原Notification/分页模型；handle仍不自动mark_read。数据库锁、_projects的当前资格复查、通知行FOR UPDATE、recipient核对、version上界与条件UPDATE完全保留，不创建/提交第二UoW。

**最易遗漏的顺序与审计边界：** 原通知_update在values(row)求值前检查版本。设计保留显式c.check_version(row)，随后Call.cas再做同一纯版本检查；不为了少1行把values回调提前。原通知成功audit.before/after没有版本diff，不能复用CAS后默默新增diff；新增record_diff默认True，仅通知传False，保持原成功audit照常提交。notifications没有updated_at列，Call.cas不会额外写时间；原错误current_state默认None，与Call.cas的row.get(state)相同。所有其它Call.cas消费者保持默认True。

Python内部接口确实变化：NotificationFacade.list/mark_read/handle由平铺关键字参数变为(g,c)。现有消息模块自测和替身需由消息owner迁移调用形式、保留原断言；如果仍承诺支持所有旧Python签名，需增加兼容壳，37预算不再成立。外部REST/OpenAPI/DDL不需要改变，但必须经root及消息owner明确准入，不能靠本报告宣布内部合同已改变。

片段计量为Business34→14净20、Notification65→47净18、Call.cas14→15净增1；合计37。下面只是设计片段，未写入产品模块；dispatch_added_block的def仅为排版/计量容器，正式应插入原dispatch，在计量中已扣除该人为1行。
### A-business

```python
_COMPONENT_OPERATIONS = {
    "listMyNotifications": ("notifications", "list"),
    "markNotificationRead": ("notifications", "mark_read"),
    "handleNotification": ("notifications", "handle"),
    "getEscalationRules": ("escalations", "rules"),
    "listEscalations": ("escalations", "list"),
    "createEscalation": ("escalations", "create"),
}


def dispatch_added_block(self, g, call):
    target = _COMPONENT_OPERATIONS.get(call.operation)
    if target:
        component, method = target
        owner = getattr(self, component)
        require(owner is not None, "DEPENDENCY_UNAVAILABLE")
        return getattr(owner, method)(g, call)
```

### A-notification

```python
def list(self, g, c):
    actor_id, query = c.actor_id, c.query
    where = {
        "recipient_id": actor_id,
        "project_id": self._projects(g, actor_id, query.get("project_id")),
    }
    predicates = tuple(
        Pred(column, "ne" if query[key] else "is_null", None)
        for key, column in (("read", "read_at"), ("handled", "handled_at"))
        if key in query
    )
    result = page(
        g,
        "notifications",
        where,
        {**query, "sort": "-id"},
        notification,
        predicates=predicates,
    )
    for name, column in (("unread_count", "read_at"), ("unhandled_count", "handled_at")):
        result[name] = g.count(
            "notifications",
            where,
            predicates=(Pred(column, "is_null"),),
        )
    return result


def _update(self, g, c, values):
    self._projects(g, c.actor_id, c.project_id)
    row = g.get("notifications", c.path["notification_id"], lock="update")
    require(row and row["project_id"] == c.project_id, "RESOURCE_NOT_FOUND")
    require(row["recipient_id"] == c.actor_id, "ACTION_FORBIDDEN")
    c.check_version(row)
    changed = c.cas(g, "notifications", row, values(row), record_diff=False)
    return notification(changed)


def mark_read(self, g, c):
    return self._update(g, c, lambda row: {"read_at": row["read_at"] or c.clock})


def handle(self, g, c):
    require(bool(c.body["evidence"]), "EVIDENCE_REQUIRED")
    return self._update(
        g,
        c,
        lambda row: {
            "handled_at": c.clock,
            "handling_note": c.body["note"],
            "handling_evidence": c.body["evidence"],
        },
    )
```

### A-common_cas

```python
def cas(self, g, table, row, values, *, expected=None, record_diff=True):
    expected = self.check_version(row, expected=expected)
    values = {**values, "version": row["version"] + 1}
    if "updated_at" in row:
        values["updated_at"] = self.clock
    require(
        g.update(table, {"id": row["id"], "version": expected}, values) == 1,
        "VERSION_CONFLICT",
        current_version=row["version"],
        current_state=row.get("state"),
    )
    if record_diff:
        self.before = [{"field": "version", "value": str(row["version"])}]
        self.after = [{"field": "version", "value": str(values["version"])}]
    return {**row, **values}
```

### A的等价证据与owner变更方案

现阶段证据是逐参数/原语句顺序对照、正常排版计量及notifications DDL无updated_at字段的静态核查，**没有运行结果**。backend应只改Business静态委托与Call.cas的默认保持型参数；messaging只改门面签名/内部版本更新和开发调用适配；调度模块不需要产品改动。不得先跨岗修改再要求owner追认。

未来准入后应逐项比较原/新：列表授权项目范围、read/handled四筛选/total与未读未处理全范围计数；已读/已处理各自CAS及旧键重放；错误优先(资格/归属/收件人/版本/值构造)；最大版本；handle不等于read；全部通知audit.before/after、outbox和COMPLETE快照逐字段相同；缺组件503与独立拒绝审计；outbox失败回滚通知/版本；commit不明沿原key恢复；真实MySQL同通知并发只一次生效。原SQL/锁/UoW账本应保持，不能为新实现盲改数值断言。随后全开发回归/覆盖率、精确源码固定计量、审核和独立验收各自绑定新SHA。此候选没有性能通过证据；多一次纯版本检查可能抵消少一层适配的CPU收益，需另测。

## B：冻结DDL是插入初态唯一事实，不删验证

`scan_runs`的last_task_id/scanned_count/created_count/duplicate_count均DEFAULT0，finished_at/error_code允许NULL；`outbox_events`的schema_version/status/attempts为DEFAULT1/1/0，lease_token/lease_until/confirmed_at/fallback_at/last_error_code允许NULL。EscalationFacade._run与create初次insert中共14个逐字段赋相同值可省略，依赖现有冻结DDL与完整迁移审计保证同值。不是把代码移到新SQL，不改DDL、不新增默认、不删除任何检查或状态转换字段。

task、review、assessment的delivery_cycle等**不能**从seed通用context直接删：这些字段并非所有表都有相同DEFAULT，部分是NOT NULL无默认。seed的326行并非默认字段堆叠；这轮未找到可正当删去的大块。

owner须比较完整实际落库行、重复扫描、冲突/savepoint回滚、raw规则hash和API输出，确认SQL绑定字段减少不改变错误路径。B不影响初态以外的confirm/fallback/retry/完成转换，终态/租约清空字段不能套用省略规则。原七类DB反例必须继续通过。G若采用相同省略，重叠6行只能算一次。

## C/D/E：公共验证与已有基础函数的真实小收益

C设计只抽取“单if、无else/elif、单bare raise、全局异常类、一个静态字符串消息”的点。condition在原语句位置求值一次，异常实例只在失败时构造；动态message/显式cause/多语句失败分支保留。没有用布尔短路代替语句。工厂式更严格保留异常表达式本身惰性；异常类+常量message式仅提前取得稳定的类对象与字符串，不提前构造异常。

```python
def reject_if(condition, exception_factory):
    if condition:
        raise exception_factory()


def reject_if_static(condition, exception_type, message):
    if condition:
        raise exception_type(message)
```

两种是替代设计，不能同时相加。94个符合形式的点全改反而增131/160行；只取短点工厂式23处毛省23−13文件import−3helper=7；静态式30处毛省30−14import−3=13。实际Ruff100列会把复杂条件和长错误消息展开为多行，helper没有数百行潜力。新公共helper需要root明确归属，不能让持久层反向依赖services。为了13行引入跨21模块新抽象维护成本，不建议优先于A。初次工具把1个elif当独立片段导致解析失败，旧输出保留；v2排除了该点，未改产品。

D仅合并**已物化**列表的非空校验与取首项，不包装/提前执行SQL：identity两处、Projects两处、EscalationFacade.rules一处。现有require的业务异常不变、查询及锁发生在原处。3行first_or_error包require，五处各省1，实际净2；DB的StatementRejected分支不能为了复用改成HTTP Rejected。无缺失即返回None的路径不能接这个helper，login的dummy hash防枚举也不能改成“无用户立即错误”。

E可保留服务内部now/uuid_text名字，使用现有codecs.utc_now/bytes_to_uuid作为alias；两实现逐语义同义，无I/O。原共6行(import+两函数)变3行alias导入，现有isort确认不会强行合并为长块，预算3。它是已有业务库的复用，不是新依赖或迁出计量。需核内部函数签名/注解/猴子补丁兼容；若有不变支持承诺则保留原函数，放弃这3行。

## F：单一schema目录视图，仅交DB作有限RFC

当前migrations374行并非374行重复：CHECK保序语法签名80、迁移生命周期98，其余四方法189。可能重复的是期望metadata既被投影为Inspector的column/index/FK/CHECK签名，又被投影为native engine/collation/extra/index visibility/enforcement签名。可研究一个统一的`SchemaSnapshot`与分面差异映射，同时读取当前库native事实，保留冻结TABLES作为期望唯一来源；**不**另建生成JSON、shadow schema或外部检查工具来扣行。

替换的189行仍需要：期望事实遍历40–50、native目录读/分组45–55、类型/字符集/排序方向/索引前缀/方法/可见性/FK动作及schema/default/CHECK规范化40–55、同顺序诊断标签/集合对照35–50。合计160–210，预算净-21至29，尚无实现。这是工作量估计，不能报成已测29。保留原CHECK parser、migrate库名/8.4/checksum/advisory lock/中断标记/DDL隐式提交/不自动修复全部阶段，保留缺表和额外unique/FK/CHECK检测、现有diagnostics兼容及新七类反例。全收敛到一个目录层才可能省；只把旧遍历封进类会净增。

已有官方SQLAlchemy2.1.6的Inspector支持get_multi_*，可能统一采集形状，但不证明MySQL执行一次SQL或覆盖缺失字段。[官方反射接口](https://docs.sqlalchemy.org/en/21/core/reflection.html#sqlalchemy.engine.reflection.Inspector.get_multi_columns)明确按表返回事实；[MySQL反射说明](https://docs.sqlalchemy.org/en/21/dialects/mysql.html#mysql-mariadb-unique-constraints-and-reflection)说明unique index/constraint的表示差异。已核本岗venv和锁均2.1.6；实际get_check_constraints仅回name/sqltext，get_indexes不回visibility，不能删native审计后宣称官方库等价。CHECK文本的sqltext也不是保序语义比较器。新依赖不能替代缺失的安全事实或作为隐藏自写代码的容器。

F由DB owner先确认每一原事实到新snapshot字段的全覆盖矩阵，再做原合法库及逐项坏库/七新反例差分；不仅要求passed相同，还应明确defect类别/顺序合同。未知语法/缺目录字段继续fail closed。此项位于冷迁移/检查入口，不改善每次API的P95；不应因为大文件或29乐观预算而抢在热路径性能工作前改写已修复审计。

## G：ScanStore.start与EscalationFacade._run的重复生命周期

两处都写run_key/rule_version/snapshot/raw_hash/cutoff/start/heartbeat，保存点处理唯一冲突并核同UUID配置。但不是相同事务：Store.start拥有独立UoW且insert-first，duplicate后以UPDATE锁回读；Facade._run已经在Runtime主事务及外层savepoint中，先查存在、成功只需id，原已有行无UPDATE锁，冲突映射RULE_VERSION_CONFLICT。它不能调用会自行开UoW/提交的Store.start。

可设计DB owner的事务内注册原语，输入同一已授权g及规范化run_key/原文快照/hash/clock，返回(id,existing-row-or-none)；两owner保持各自外层UoW/查询顺序/锁模式/错误映射，不能无理由增加读回SQL或提前commit。62旧行的共享体约24–32+Store桥12–18+Facade桥15–20+import1–2，正常格式约52–72，净-10至10；B已覆盖其中6默认行，不重复计。这说明职责相关不等于可以把两段全部删除。没有达到值得先实施的完整正收益预算，列为研究后备。

## Rows、seed、Runtime/API为何没有大块可删除

- Rows293：_fields的字段/表达式递归拒绝与时间域转换，_clauses谓词编译，rows排序/列/limit/offset/锁模式白名单，_execute失败状态和脱敏，savepoint与有界schedule-history完整返回合同是不同入口。SQLAlchemy参数绑定本身不替代这些边界。行历史专门读的每项检查防错误project/pair/重复/上界，不能因DB“应当正确”删除。现有统一_fields/_execute已经集中共同职责。
- seed326：配置raw hash/manifest与重复/错版本拒绝、空项目数据约束、独立合成身份、七态/八段十项评审/四视角预案/版本批准指针、时间拓扑及DAG、固定规模分配、批量FK顺序和一次事务分别服务可复现演示/负载输入。改为逐条调用业务API会新增编排、真实audit/outbox和SQL成本，并改变数据分布及15000约束；不能把它当省326的方案。
- Runtime284：预认证/输入/短claim，主事务会话和owner fencing，project/member/task锁序，成功audit/outbox/COMPLETE，以及主回滚后的独立拒绝audit/可完成4xx是不同生命周期。合并成一次鉴权或一次事务会损失撤权线性化、同键恢复或拒绝审计；重放不能重新业务。authorize/prepare/locked_scope并非可删重复认证。
- API244：HTTP选择器解码/攻击模式、重复JSON键与NaN、body大小和媒体类型、oneOf选择及EVIDENCE_REQUIRED/CONTRACT_INVALID优先、成功meta/动态头、真实响应Schema校验分别有外部错误行为。换默认FastAPI/Pydantic转换不保JSON整数/布尔/额外字段/错误细节与安全边界。没有已证等价的官方单函数可消除整层。

## 来源映射：原任务与工程选择均不能擅自删

| 能力 | 原始T44/明确选择 | 当前工程实现与支持承诺 | 若删除或简化的外部变化/风险 |
| --- | --- | --- | --- |
| 三类接口、统一错误与鉴权、项目范围、安全拒绝记录 | FR-01、FR-06及安全条款明示 | 38操作、精确错误次序/响应校验是冻结设计细化；D004由用户采用 | 改API或错误分支会违反AC-01；删鉴权/输入/审计违反安全与并发要求 |
| 状态机/依赖/排期差异/八段十项/风险预案 | FR-03–06明示；D001采用具体状态边 | domain/Workflow/Review/Tasks及历史版本绑定 | 删除其中一层门禁会允许非法开始、自审或失效发布；不是便利功能 |
| 迭代capacity生命周期和D008提示次序 | 原FR-04/06原则；D005/D006/D008为用户明确新增 | project锁、owner集合、1–5与7区分、批准失败槽次序 | 回退会改变用户已采纳业务，并发后可留非法人力或错误优先级 |
| 幂等、一次并发成功、事务留痕、MQ故障待办、调度重启 | 原可靠性、FR-06/07、AC-06/07明示 | opaque会话、租约owner、PROCESSING/COMPLETE、outbox/ledger/cursor是工程方案，已入冻结合同 | 可以未来研究替代实现，不能删除结果保证；跨事务合并/缓存鉴权破坏安全与恢复 |
| 造数体量与复现 | 原性能条款明示40/6000/9000/15000，AC-08复现 | seed CLI、manifest/随机不可逆口令/时间拓扑/批量插入属于工程细化并公开支持 | 删除seed会失去当前可复现生成入口；把同功能移出计量被本次口径明确禁止 |
| DDL字段、类型、逐表评审与迁移 | FR-02/AC-02明示；D004采用字段方案 | 程序化迁移、GET_LOCK、版本标记、重复迁移、运行时目录完整审计是防御/运维设计 | 即使原文未逐项指定，也已在持久契约且近期明确要求DB反例安全；删会接受错库/半迁移或不兼容结构 |
| Token泄露阻断/明文拒绝 | 原安全条款明示 | Argon2id边界、会话撤销CLI、受限服务token是工程机制 | 换机制须等价阻断，删CLI/服务范围不是免费省行；必须保独立记录与认证需求 |
| 规则扩展、raw版本与生效追溯 | 原可维护条款+第12节明示变更留痕 | Rules DTO、选择器、immutable raw snapshot/hash和历史规则查询 | 不能硬编码三级换掉扩展能力；DTO形式可研究，校验、版本和追溯不能删 |
| legacy audit reason投影 | FR-04要求前后差异；旧数据的安全关联投影是工程兼容细化 | history96与Rows有界读取公开合同，原audit不改 | 删会改变旧GET审计可见信息；不能自动视为“非原文即可删”，须明确支持策略及新冻结 |
| Python helper/别名/导出 | 多数是工程内部或公开包接口，并非原任务逐名要求 | README、__all__和开发调用形成可见支持面 | 仅未被当前入口调用不证明没有支持承诺；优先复用/alias，不能删除后靠改测试掩盖 |

用户已明确继续现有范围，因此本轮**不提出通过删seed/migrations/CLI/历史或改计量解决规模的可执行方案**。用于人的边界判断：即使假设把整个seed326和migrations374全部删除，也仅700，还缺133；且会丢上述明确入口/安全和复现能力。当前不能以“老师没有写具体机制”视为已授权降级。这不是上限不现实的结论，而是本轮找出的具体方案不足833；未来任何更大替代架构应先给完整职责/错误/安全等价设计及准确净预算，保持门槛继续失败。

## 入口、动态注册与遗留路径审计

遍历全部43 Python产品文件的**301个def/class/嵌套方法**，按名称加载引用及字符串注册线索做定位，再核四类真实入口：t44.api:app/create_app；cli.main命令分支；messaging.__main__.main→DeliveryWorker/Broker/OutboxStore；scheduling.__main__.main→Scanner/Runtime/EscalationFacade/ScanStore。下方完整清单给每个定义位置和同名引用数。**同名统计不是完备调用图**，注入对象及同名不同receiver可能过近似；不能用它证明函数可删。

| 静态看似少引用的项 | 实际证据 | 结论 |
| --- | --- | --- |
| Business/Projects/Tasks/Reviews/Workflow的命名API方法 | contracts.OPERATIONS38项→API closure→Runtime.execute→Business.dispatch的getattr；四collection额外注册 | 全部是产品动态入口，不能据没有Name Load删 |
| capture、__post_init__、__enter__/__exit__、__repr__ | FastAPI decorator、dataclass构造、with协议及脱敏repr | 框架/语言隐式调用，非死代码 |
| quarters_to_hours、bytes_to_uuid | README明确列codecs转换支持；后者可供现有uuid_text复用 | 非可无条件删的废代码；只建议保名字复用 |
| ScanStore.recoverable | 当前Scanner.tick用更精确hash+heartbeat直接查询，但README仍明确公开此方法 | 有公开支持承诺，未找到废弃决定；不删8行 |
| Runtime.claim | 当前生产入口用prepare/_claim；988_mysql开发真库恢复/租约/冲突断言调用claim | 只能称非入口路径直接可达，不能证明废弃；不把包装搬到测试规避计量 |
| WindowMatch.code/recipient_roles及规则别名属性 | 包导出WindowMatch；991_rules保留基础返回约定 | 旧调用/公开对象面，未有废弃批准；不删属性或测试 |
| update_where、两个__all__(13+11行) | README明确update_where别名；包导出与可能外部star import是支持面 | 未见生产star调用不等于无接口语义；24行不计节省 |

本轮没有发现已证无产品行为且无支持承诺的大块历史残留。未覆盖、仅测试调用、receiver名称匹配不构成删除证据。完整清单也保留未知/动态边界，不伪称全程序可达性证明。

## 已执行与未执行

执行：固定计量、65应用文件对20000108/a12字节比较、完整产品/冻结API/DDL diff空、51路径/301定义和动态注册核查、94异常点两种RFC片段普通Ruff/cloc、A完整片段Ruff/cloc、DDL14默认字段对照、现有官方SQLAlchemy2.1.6实现/文档查证、JSON证据可解析。设计片段从未导入或应用为产品代码，没有新增tmp项目文件或编号。

未执行：新产品测试、完整开发CI/覆盖率、MySQL/RabbitMQ、前端、云、正式性能和独立验收。没有新增834之类开发数量，也没有修改任何测试。初始猜测specs/database/README.md、旧分支source-count路径及D004文件名不存在，均随后定位实际路径；一处elif碎片工具失败保留，v2结果更正，不归因产品。

建议root先将A以37行**设计RFC**交backend/messaging owner作内部接口决定，再由owner实现并新SHA审核；B可由scheduler/database确认14行是否值得附带实现。F/G不能为减数急改。任何实现都不构成833闭合，仍需后续有具体证据的新方案。规模5933/5100失败继续保留，性能实验另行按原协议，不能相互替代。

## 固定输入、预算原件与SHA256

- `/tmp/t44-architecture-base-count-20261028.json` SHA256 `7238cc5d58e0367c51e78c4ae454d93b627b6095ce5b54456618f1596698aea2`。
- `/tmp/t44-architecture-component-budget-20261028.json` SHA256 `2ecbb53e655b79aabb2df8a856272f17c08eb5b5dd8e45814c0f374e89ccea0b`。
- `/tmp/t44-architecture-guard-budget-v2-20261028.json` SHA256 `240fe73f517cdf9469c6b7bf989b515abb857359d8067071d7b82d9146763756`。
- `/tmp/t44-architecture-def-reference-inventory-20261028.json` SHA256 `058f70d719e2534e1f8705c1b32943592316514f75578a4728c83a4c480fdb8e`。
- `/tmp/t44-architecture-scope-budget-20261028.json` SHA256 `a10aa15771ba016d1ef04673d402b32007f211dd8c3ded5588ded41996111295`。

计量命令：

```sh
python3 scripts/metrics/source_count.py --cloc /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/cloc-2.10.pl --output /tmp/t44-architecture-base-count-20261028.json --require-range
```

固定cloc SHA256 `bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83`；脚本SHA256 `7749021256e1fa295419ded8eee094ea21ed9db783fd08ec704a2c72cd45f434`。原输出commit57354c71/application_code5933/within_range=false；返回1是规模出口失败，不是基础设施故障。

## 43个计入后端文件与51路径核对

| 文件 | 固定cloc产品行 | SHA256 |
| --- | ---: | --- |
| `backend/t44/__init__.py` | 0 | `e572411e3ef110b4976da10aee2744cc33c2fa864f1d6a9f4005c49275643c38` |
| `backend/t44/api.py` | 244 | `2db431218d7c182dd114b7e616442478539396dcf86cccca42a537250356075e` |
| `backend/t44/cli.py` | 147 | `da88377aed1131fb82aea31ef2783e02af01c6b620518f3d1b9e8b01175112db` |
| `backend/t44/contracts/__init__.py` | 56 | `30d3f2acdb2ce5adb49e47065fd684e5d06825d08f32eb6e06cc2375fb6f4688` |
| `backend/t44/contracts/openapi.json` | 原口径另列 | `6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478` |
| `backend/t44/domain/__init__.py` | 0 | `6aae9b1fb4fcc87a0766c807ed8f036f09629811544c8b7db50485634cc4348e` |
| `backend/t44/domain/models.py` | 111 | `67406cec4592a1d113ec68eb93ee952127b701688db5950340a779dacf983547` |
| `backend/t44/domain/state_machine.py` | 164 | `65a743e2f30e3459568491dfb25e3db387bfb019db5a05dd7125c07fcd1ec9a8` |
| `backend/t44/messaging/README.md` | 原口径另列 | `33e08d59a9e3a3b8eec58b68ff5d331c997cb2410405ffc94181becb03bb0b1b` |
| `backend/t44/messaging/__init__.py` | 0 | `0223fc2eea2e0bc490de900bcac14f7b17bf7ce8d83d4bbc02bbe11d569a8a63` |
| `backend/t44/messaging/__main__.py` | 49 | `356ef3c0eeb5be3750df311fa2dd33cb420e3bf8218eedf9dd86e03ebe32493c` |
| `backend/t44/messaging/broker.py` | 126 | `41e3d755b556f508d9adfdd2af30f2817edbb67fdbd01f6907bfa67f1320f15a` |
| `backend/t44/messaging/facade.py` | 85 | `e111c6e28e9f90e3e494ef224ae33ba8a10bcd2a16c63740c4cc27d555d141d5` |
| `backend/t44/messaging/worker.py` | 84 | `266b39185b946484599584f0e49a1dfb6b14cde2566cc7efb73f5386cc86648b` |
| `backend/t44/persistence/README.md` | 原口径另列 | `eb924187015bc4db73ae9a21159994cc4ac1791be40a9489adc710a7d058c7e3` |
| `backend/t44/persistence/SYNTHETIC-DATA.md` | 原口径另列 | `c6e4002baa3b90861d37fef82c07a1d08310669ef09319e494fc3e7259f9dfd9` |
| `backend/t44/persistence/__init__.py` | 24 | `3a114365e08b4154ec9d5c4399559ee1d512d3cf1e9adeadb5bb9f10bc93d071` |
| `backend/t44/persistence/accounts.py` | 61 | `6717761266ad853fd861ba041e13e56aa30fe4e4d0c286302a14081de869df2b` |
| `backend/t44/persistence/codecs.py` | 27 | `67ce7fe9d9492f8e92c66aa4080203114aaa578702663681c3d88d4a5b6b1c4e` |
| `backend/t44/persistence/delivery.py` | 159 | `c9d6d704096aef55a81a61563eee90a8bebbe4de8000efbb8f4e50c745d1d6cb` |
| `backend/t44/persistence/engine.py` | 93 | `f7ec591dad711e3755aeda2606cee8dcaa023b416d8c51592b7b87684121ab9d` |
| `backend/t44/persistence/errors.py` | 9 | `76fabd26e20706ba606a8904c23ebaef5b9306e0b65b4757c7d9d999f9156248` |
| `backend/t44/persistence/migrations.py` | 374 | `cf2e6b30c6284148afc24b039ee483f744e9fa8af0fbe5f0982f67fb42371ca5` |
| `backend/t44/persistence/rows.py` | 293 | `417b32a7d9ac29ecd7ce9c301d8fd530ecc0086a43d0926053c733e9964bd76b` |
| `backend/t44/persistence/scans.py` | 103 | `479fd65effbcc476654c2e76994d4573bb17f34c430ac5cc75e4c12646ec146b` |
| `backend/t44/persistence/schema.py` | 117 | `cd1465fc7560c0f13bb80216507b237e297e2177eccf280d8802651f0458e4bd` |
| `backend/t44/persistence/schema_v1.sql` | 原口径另列 | `c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4` |
| `backend/t44/persistence/seed.py` | 326 | `7fe5f623d56c0e16ea8395edd67fdd961563a04a8d73661d78133fe4f80ac141` |
| `backend/t44/persistence/uow.py` | 86 | `3063b8b29a07dd29f188720df637d4e31e0fbc9e8b401be1f2ecbc3188d5897f` |
| `backend/t44/resources/escalation-rules.json` | 原口径另列 | `63bda0d3931bb7d34b3fd745c8a9ba14f489f7288badbf422dfc7ba4f6bc8f41` |
| `backend/t44/resources/review-template.json` | 原口径另列 | `4fdaad483abe00a41335546f11dda58f8b87da66cf5d158521c24c125d99f199` |
| `backend/t44/scheduling/README.md` | 原口径另列 | `86db4a1cde2a0371b28ea0aaa0fe426157d0f176c9d554ab7a0ee12c9a192bcf` |
| `backend/t44/scheduling/__init__.py` | 21 | `13546feadd8867b987928a9178a984c1d96aae3e85f66ef6fe71662fb935f21b` |
| `backend/t44/scheduling/__main__.py` | 96 | `66743cc75f1558356c2c605690803310f5c9ecec0abdac579afe21c23fdbefbe` |
| `backend/t44/scheduling/facade.py` | 205 | `17e293ec0389020f9269e75dbf9dd927eee877426181165c46cd7951c68f8ab6` |
| `backend/t44/scheduling/rules.py` | 140 | `4b182e8f531f22f86e8bfd019a84ce9a844ef29eca1a58ed341d38e86e1d1428` |
| `backend/t44/scheduling/runtime.py` | 39 | `19ccc353d794fb7d22ab39a3c2ad720d435c0e3fe0760ce508a2918b08fe3778` |
| `backend/t44/scheduling/scanner.py` | 141 | `6c724d7f0360128e9474cce631f9b2b9bf282072e8aeb9876457f9a720401ed4` |
| `backend/t44/services/__init__.py` | 0 | `f9adfcf32ee8df41e7ff3e330b17ba03fbca641dd5c55a8ffdb8b03954dc7df0` |
| `backend/t44/services/application.py` | 167 | `158fd13d7b0765b085a8dfa14beb6ccd441c55b2d7cfb0e8938cc3e5a5e61e75` |
| `backend/t44/services/codes.py` | 11 | `bab51291d86feb0575796eab666cdd4170c2e6efcfc9a1c6d34b05d42ddea104` |
| `backend/t44/services/common.py` | 140 | `39180236fb89536f3b068ddcf82ce7ba43cb92ea12ec21f0fdc50875d499c186` |
| `backend/t44/services/errors.py` | 28 | `95148fc2086e6ff924a7077beb0be8ef282db54a084410be426fe0394408ded7` |
| `backend/t44/services/history.py` | 96 | `36b2fb1aed476bff3d852e113da4584e1906b53f1f5e3d476b730f9f8a1d98ae` |
| `backend/t44/services/identity.py` | 107 | `9ec1537da5cad83ae99ec68872be5ea4ad8477f99519a03d0bf8439317132985` |
| `backend/t44/services/projects.py` | 169 | `0cdadc0710d15ea837e5285f8e6ea278703f954d5afb4b09fe6aa9ca02f03a30` |
| `backend/t44/services/reviews.py` | 140 | `688183095865d119e77dd8a7aa5db965bf1d0ca2ff81ff19e5188225a8234d92` |
| `backend/t44/services/runtime.py` | 284 | `a8b6a6711f2a88249f760e05badd80c911ead6e25824e9d4400d8b3b1844a239` |
| `backend/t44/services/tasks.py` | 136 | `2b47b84e281f022231adf863e116b82aade3e4174968ff2f68fe7ed5ee2638da` |
| `backend/t44/services/workflow.py` | 140 | `e30455418a474eaf9a82809327c9567508610162cd3dc67dbed801f1d29c4d3c` |
| `backend/t44/settings.py` | 36 | `1c998fa935c2c63891278982cac859fe76899a1e1791f5d7641433416002beea` |

## 301定义定位清单

以下“引用”是全产品同名Name/Attribute加载数，不含定义；它不能区分所有注入receiver。API动态注册与隐式协议单独标识，不据数字0删代码。

| 文件与行 | 定义 | 同名静态引用数 | 动态/隐式说明 |
| --- | --- | ---: | --- |
| `backend/t44/api.py:29` | `_security` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:41` | `_unique_object` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:50` | `_schema_type` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:56` | `_parameters` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:63` | `_body_schema` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:79` | `_body_error` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:88` | `_body_error.evidence_only` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:104` | `validate_request` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:169` | `LazyFactory` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:172` | `LazyFactory.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/api.py:175` | `LazyFactory.__call__` | 1 | 语言/框架隐式协议 |
| `backend/t44/api.py:190` | `create_app` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:204` | `create_app.capture` | 0 | 语言/框架隐式协议 |
| `backend/t44/api.py:215` | `create_app.endpoint` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/api.py:216` | `create_app.endpoint.handle` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/cli.py:18` | `_parser` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/cli.py:46` | `main` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/contracts/__init__.py:19` | `validator` | 6 | 有静态名称线索，receiver需辨别 |
| `backend/t44/contracts/__init__.py:27` | `_absolute_refs` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/contracts/__init__.py:38` | `violations` | 13 | 有静态名称线索，receiver需辨别 |
| `backend/t44/contracts/__init__.py:49` | `normalized` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/models.py:11` | `_dictionary` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/models.py:29` | `DomainViolation` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/models.py:30` | `DomainViolation.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/domain/models.py:35` | `_counter` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/models.py:41` | `Transition` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/models.py:55` | `Transition.__post_init__` | 0 | 语言/框架隐式协议 |
| `backend/t44/domain/models.py:124` | `Decision` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/models.py:128` | `Decision.__post_init__` | 0 | 语言/框架隐式协议 |
| `backend/t44/domain/state_machine.py:36` | `_require` | 25 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/state_machine.py:41` | `_present` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/state_machine.py:45` | `_stage_role` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/state_machine.py:55` | `_review` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/domain/state_machine.py:73` | `decide` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/__main__.py:17` | `main` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:15` | `BrokerUnavailable` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:20` | `BrokerSettings` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:25` | `BrokerSettings.__post_init__` | 0 | 语言/框架隐式协议 |
| `backend/t44/messaging/broker.py:32` | `PikaBroker` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:33` | `PikaBroker.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/messaging/broker.py:38` | `PikaBroker._operation` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:45` | `PikaBroker._channel` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:75` | `PikaBroker.publish` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:99` | `PikaBroker.get` | 110 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:106` | `PikaBroker.keepalive` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:111` | `PikaBroker.close` | 12 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/broker.py:121` | `consume_delivery` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/facade.py:8` | `notification` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/facade.py:12` | `NotificationFacade` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/facade.py:13` | `NotificationFacade._projects` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/facade.py:28` | `NotificationFacade.list` | 24 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/facade.py:54` | `NotificationFacade._update` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/facade.py:72` | `NotificationFacade.mark_read` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/facade.py:82` | `NotificationFacade.handle` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/worker.py:16` | `DeliveryWorker` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/worker.py:17` | `DeliveryWorker.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/messaging/worker.py:33` | `DeliveryWorker.cycle` | 6 | 有静态名称线索，receiver需辨别 |
| `backend/t44/messaging/worker.py:83` | `DeliveryWorker.run` | 22 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/accounts.py:12` | `PasswordHashRejected` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/accounts.py:16` | `AuditUnavailable` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/accounts.py:20` | `initialize_user` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/codecs.py:8` | `utc_now` | 13 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/codecs.py:12` | `to_db_time` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/codecs.py:21` | `from_db_time` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/codecs.py:25` | `hours_to_quarters` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/codecs.py:34` | `quarters_to_hours` | 0 | 公开/测试/动态边界另核，非可删证明 |
| `backend/t44/persistence/codecs.py:38` | `uuid_to_bytes` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/codecs.py:42` | `bytes_to_uuid` | 0 | 公开/测试/动态边界另核，非可删证明 |
| `backend/t44/persistence/delivery.py:11` | `OutboxStore` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/delivery.py:12` | `OutboxStore.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/persistence/delivery.py:15` | `OutboxStore.get` | 110 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/delivery.py:19` | `OutboxStore.claim` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/delivery.py:52` | `OutboxStore.confirm` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/delivery.py:68` | `OutboxStore._notices` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/delivery.py:97` | `OutboxStore.consume` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/delivery.py:108` | `OutboxStore.recover_confirmed` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/delivery.py:130` | `OutboxStore.fallback` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/delivery.py:154` | `OutboxStore.retry` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/engine.py:19` | `validate_identifier` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/engine.py:26` | `MySQLSettings` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/engine.py:40` | `MySQLSettings.__post_init__` | 0 | 语言/框架隐式协议 |
| `backend/t44/persistence/engine.py:66` | `initialize_mysql_session` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/engine.py:79` | `create_mysql_engine` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/errors.py:4` | `PersistenceError` | 9 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/errors.py:8` | `PersistenceUnavailable` | 8 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/errors.py:12` | `PersistenceIntegrityError` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/errors.py:15` | `PersistenceIntegrityError.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/persistence/errors.py:20` | `CommitUncertain` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/errors.py:24` | `TransactionStateError` | 6 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/errors.py:28` | `StatementRejected` | 28 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:12` | `MigrationError` | 8 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:16` | `_check_signature` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:51` | `_check_signature.pop` | 12 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:59` | `_check_signature.peek` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:62` | `_check_signature.arguments` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:71` | `_check_signature.parse` | 7 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:104` | `_index_signature` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:119` | `_foreign_signature` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:142` | `_catalog_defects` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:215` | `check_schema` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:230` | `check_schema.signature` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/migrations.py:304` | `migrate` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:23` | `Pred` | 9 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:29` | `RowsGateway` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:30` | `RowsGateway.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/persistence/rows.py:34` | `RowsGateway._table` | 7 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:39` | `RowsGateway._fields` | 7 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:45` | `RowsGateway._fields.safe` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:59` | `RowsGateway._clauses` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:85` | `RowsGateway._execute` | 10 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:122` | `RowsGateway._failed` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:129` | `RowsGateway.savepoint` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:143` | `RowsGateway.rows` | 78 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:184` | `RowsGateway.get` | 110 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:188` | `RowsGateway.task_schedule_changes` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:193` | `RowsGateway.task_schedule_changes.integer` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:223` | `RowsGateway.task_schedule_changes.unavailable` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:257` | `RowsGateway.confirmed_missing` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:283` | `RowsGateway.insert` | 20 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:289` | `RowsGateway.insert_many` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:298` | `RowsGateway.update_many` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:312` | `RowsGateway.update` | 26 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:323` | `RowsGateway.delete` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/rows.py:329` | `RowsGateway.count` | 18 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/scans.py:10` | `ScanStore` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/scans.py:11` | `ScanStore.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/persistence/scans.py:14` | `ScanStore._run` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/scans.py:20` | `ScanStore.start` | 20 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/scans.py:48` | `ScanStore.get` | 110 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/scans.py:52` | `ScanStore.recoverable` | 0 | 公开/测试/动态边界另核，非可删证明 |
| `backend/t44/persistence/scans.py:61` | `ScanStore.page` | 11 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/scans.py:79` | `ScanStore.checkpoint` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/schema.py:28` | `ddl_text` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/schema.py:35` | `_parts` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/schema.py:48` | `_type` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/schema.py:68` | `_foreign_key` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/schema.py:77` | `build_metadata` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/seed.py:32` | `_snapshot` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/seed.py:37` | `_populate` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/seed.py:69` | `_populate.add` | 12 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/seed.py:79` | `_populate.annotations` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/seed.py:253` | `seed_demo` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/uow.py:13` | `SqlAlchemyUnitOfWork` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/uow.py:14` | `SqlAlchemyUnitOfWork.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/persistence/uow.py:21` | `SqlAlchemyUnitOfWork.__enter__` | 0 | 语言/框架隐式协议 |
| `backend/t44/persistence/uow.py:36` | `SqlAlchemyUnitOfWork._require_active` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/uow.py:44` | `SqlAlchemyUnitOfWork.gateway` | 30 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/uow.py:48` | `SqlAlchemyUnitOfWork._mark_failed` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/uow.py:51` | `SqlAlchemyUnitOfWork.commit` | 8 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/uow.py:66` | `SqlAlchemyUnitOfWork.rollback` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/uow.py:76` | `SqlAlchemyUnitOfWork._close` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/uow.py:87` | `SqlAlchemyUnitOfWork.__exit__` | 0 | 语言/框架隐式协议 |
| `backend/t44/persistence/uow.py:99` | `SqlAlchemyUnitOfWorkFactory` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/persistence/uow.py:100` | `SqlAlchemyUnitOfWorkFactory.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/persistence/uow.py:103` | `SqlAlchemyUnitOfWorkFactory.__call__` | 1 | 语言/框架隐式协议 |
| `backend/t44/scheduling/__main__.py:26` | `read_token` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/__main__.py:37` | `single_instance` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/__main__.py:48` | `main` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/facade.py:12` | `EscalationFacade` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/facade.py:13` | `EscalationFacade.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/scheduling/facade.py:16` | `EscalationFacade.current` | 8 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/facade.py:19` | `EscalationFacade.rules` | 29 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/facade.py:28` | `EscalationFacade.event` | 51 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/facade.py:58` | `EscalationFacade.list` | 24 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/facade.py:70` | `EscalationFacade._run` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/facade.py:106` | `EscalationFacade.create` | 9 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:16` | `RuleConfigurationError` | 6 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:20` | `TimestampError` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:25` | `EscalationWindow` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:37` | `EscalationRules` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:46` | `EscalationRules.rule_version` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:49` | `EscalationRules.snapshot` | 8 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:54` | `WindowMatch` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:61` | `WindowMatch.code` | 30 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:65` | `WindowMatch.recipient_roles` | 0 | 公开/测试/动态边界另核，非可删证明 |
| `backend/t44/scheduling/rules.py:69` | `_unique_object` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:78` | `load_rules` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:137` | `parse_utc_timestamp` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/rules.py:153` | `select_window` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/runtime.py:15` | `build_scheduler` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/runtime.py:44` | `run_scheduler` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/scanner.py:15` | `ScanFailure` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/scanner.py:16` | `ScanFailure.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/scheduling/scanner.py:21` | `validate_call` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/scanner.py:39` | `Scanner` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/scanner.py:40` | `Scanner.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/scheduling/scanner.py:47` | `Scanner._scope` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/scanner.py:67` | `Scanner._execute` | 10 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/scanner.py:102` | `Scanner.run` | 22 | 有静态名称线索，receiver需辨别 |
| `backend/t44/scheduling/scanner.py:145` | `Scanner.tick` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/application.py:32` | `Business` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/application.py:33` | `Business.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/services/application.py:36` | `Business.status` | 27 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/application.py:39` | `Business.dispatch` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/application.py:63` | `Business.finalize` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/application.py:69` | `Business.validate_data` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/application.py:72` | `Business.outbox` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/application.py:84` | `Business.getMe` | 0 | operationId动态注册 |
| `backend/t44/services/application.py:87` | `Business.getDictionaries` | 0 | operationId动态注册 |
| `backend/t44/services/application.py:108` | `Business.validateContractPayload` | 0 | operationId动态注册 |
| `backend/t44/services/application.py:131` | `Business.listProjectAuditEvents` | 0 | operationId动态注册 |
| `backend/t44/services/application.py:151` | `Business.listMyNotifications` | 0 | operationId动态注册 |
| `backend/t44/services/application.py:155` | `Business.markNotificationRead` | 0 | operationId动态注册 |
| `backend/t44/services/application.py:166` | `Business.handleNotification` | 0 | operationId动态注册 |
| `backend/t44/services/application.py:179` | `Business._escalation` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/application.py:183` | `Business.getEscalationRules` | 0 | operationId动态注册 |
| `backend/t44/services/application.py:186` | `Business.listEscalations` | 0 | operationId动态注册 |
| `backend/t44/services/application.py:189` | `Business.createEscalation` | 0 | operationId动态注册 |
| `backend/t44/services/common.py:16` | `now` | 42 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:20` | `wire` | 19 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:32` | `time` | 8 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:36` | `roles` | 8 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:40` | `mask` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:44` | `model` | 15 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:49` | `plan` | 11 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:59` | `plan_values` | 6 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:73` | `task_model` | 11 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:77` | `page` | 11 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:96` | `Call` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:114` | `Call.project_id` | 51 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:118` | `Call.actor_id` | 24 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:121` | `Call.manager` | 13 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:124` | `Call.reviewer` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:127` | `Call.task` | 46 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:130` | `Call.resource` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:135` | `Call.members` | 17 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:140` | `Call.create` | 9 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:143` | `Call.insert` | 20 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:154` | `Call.check_version` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:164` | `Call.cas` | 13 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/common.py:180` | `uuid_text` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/errors.py:12` | `Rejected` | 11 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/errors.py:13` | `Rejected.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/services/errors.py:21` | `Rejected.payload` | 32 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/errors.py:34` | `require` | 99 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/history.py:11` | `_snapshot` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/history.py:57` | `_matches` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/history.py:93` | `project_reasons` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/identity.py:21` | `token_digest` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/identity.py:25` | `LoginLimiter` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/identity.py:26` | `LoginLimiter.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/services/identity.py:30` | `LoginLimiter.check` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/identity.py:45` | `authenticate` | 6 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/identity.py:87` | `login` | 1 | operationId动态注册 |
| `backend/t44/services/identity.py:103` | `issue_session` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/projects.py:8` | `Projects` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/projects.py:9` | `Projects.project_model` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/projects.py:12` | `Projects.member_model` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/projects.py:21` | `Projects.createProject` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:36` | `Projects.listProjects` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:47` | `Projects.getProject` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:50` | `Projects.listProjectMembers` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:59` | `Projects.addProjectMember` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:74` | `Projects._change_member` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/projects.py:106` | `Projects.changeProjectMember` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:109` | `Projects.removeProjectMember` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:112` | `Projects.capacity` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/projects.py:122` | `Projects.iteration_model` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/projects.py:125` | `Projects.createIteration` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:130` | `Projects.listIterations` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:133` | `Projects.changeIteration` | 0 | operationId动态注册 |
| `backend/t44/services/projects.py:160` | `Projects.schedule_diff` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/reviews.py:16` | `Reviews` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/reviews.py:17` | `Reviews.getReviewTemplate` | 0 | operationId动态注册 |
| `backend/t44/services/reviews.py:23` | `Reviews.review_complete` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/reviews.py:28` | `Reviews.createTaskReview` | 0 | operationId动态注册 |
| `backend/t44/services/reviews.py:64` | `Reviews.createReleaseAssessment` | 0 | operationId动态注册 |
| `backend/t44/services/reviews.py:103` | `Reviews.reviewReleaseAssessment` | 0 | operationId动态注册 |
| `backend/t44/services/runtime.py:31` | `_audit_integer` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:35` | `Runtime` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:36` | `Runtime.__init__` | 4 | 语言/框架隐式协议 |
| `backend/t44/services/runtime.py:40` | `Runtime.authorize` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:45` | `Runtime.prepare` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:54` | `Runtime.audit` | 30 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:85` | `Runtime.rejection` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:119` | `Runtime.complete` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:136` | `Runtime.claim` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:140` | `Runtime._claim` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:197` | `Runtime.locked_scope` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/runtime.py:244` | `Runtime.execute` | 10 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/tasks.py:8` | `Tasks` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/tasks.py:9` | `Tasks.owner` | 5 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/tasks.py:13` | `Tasks.capacity_owner` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/tasks.py:20` | `Tasks.iteration` | 9 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/tasks.py:23` | `Tasks.prestart` | 3 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/tasks.py:28` | `Tasks.dependency_model` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/tasks.py:32` | `Tasks.check_graph` | 2 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/tasks.py:52` | `Tasks.createTask` | 0 | operationId动态注册 |
| `backend/t44/services/tasks.py:82` | `Tasks.listTasks` | 0 | operationId动态注册 |
| `backend/t44/services/tasks.py:89` | `Tasks.getTask` | 0 | operationId动态注册 |
| `backend/t44/services/tasks.py:92` | `Tasks.changeTaskPlan` | 0 | operationId动态注册 |
| `backend/t44/services/tasks.py:114` | `Tasks.changeTaskAssignment` | 0 | operationId动态注册 |
| `backend/t44/services/tasks.py:124` | `Tasks.addTaskDependency` | 0 | operationId动态注册 |
| `backend/t44/services/tasks.py:143` | `Tasks.removeTaskDependency` | 0 | operationId动态注册 |
| `backend/t44/services/workflow.py:27` | `Workflow` | 1 | 有静态名称线索，receiver需辨别 |
| `backend/t44/services/workflow.py:28` | `Workflow.transitionTask` | 0 | operationId动态注册 |
| `backend/t44/settings.py:12` | `Settings` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/settings.py:19` | `Settings.__post_init__` | 0 | 语言/框架隐式协议 |
| `backend/t44/settings.py:24` | `Settings.from_env` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/settings.py:30` | `Settings.mysql_settings` | 4 | 有静态名称线索，receiver需辨别 |
| `backend/t44/settings.py:45` | `Settings.__repr__` | 0 | 语言/框架隐式协议 |

## 94个异常抽象片段预算定位

完整保留设计选择位置；正数表示少行，负数表示增加。这里只是片段排版预算，不是产品修改。工厂/静态两方案互斥。

| 文件与起始行 | 原代码行 | 工厂式净值 | 静态message式净值 |
| --- | ---: | ---: | ---: |
| `backend/t44/api.py:44` | 2 | 1 | 1 |
| `backend/t44/cli.py:66` | 5 | 0 | -1 |
| `backend/t44/cli.py:76` | 2 | 1 | 1 |
| `backend/t44/cli.py:90` | 2 | 1 | 1 |
| `backend/t44/cli.py:109` | 2 | -2 | -1 |
| `backend/t44/cli.py:117` | 2 | -2 | -1 |
| `backend/t44/cli.py:128` | 2 | 1 | 1 |
| `backend/t44/domain/models.py:36` | 2 | -2 | -1 |
| `backend/t44/domain/models.py:56` | 9 | 0 | -1 |
| `backend/t44/domain/models.py:65` | 5 | -5 | -6 |
| `backend/t44/domain/models.py:70` | 4 | -3 | -4 |
| `backend/t44/domain/models.py:82` | 2 | -2 | -3 |
| `backend/t44/domain/models.py:84` | 4 | -2 | -3 |
| `backend/t44/domain/models.py:88` | 2 | -2 | -3 |
| `backend/t44/domain/models.py:109` | 6 | 0 | -1 |
| `backend/t44/domain/models.py:78` | 2 | 1 | 1 |
| `backend/t44/domain/models.py:104` | 5 | -5 | -6 |
| `backend/t44/messaging/__main__.py:25` | 2 | -2 | -3 |
| `backend/t44/messaging/broker.py:26` | 2 | -2 | -3 |
| `backend/t44/messaging/broker.py:28` | 2 | -2 | -3 |
| `backend/t44/messaging/broker.py:96` | 2 | 1 | 1 |
| `backend/t44/persistence/codecs.py:13` | 2 | -2 | -3 |
| `backend/t44/persistence/codecs.py:16` | 2 | 1 | 1 |
| `backend/t44/persistence/codecs.py:26` | 2 | 1 | 1 |
| `backend/t44/persistence/codecs.py:29` | 2 | -2 | -3 |
| `backend/t44/persistence/delivery.py:21` | 2 | 1 | 1 |
| `backend/t44/persistence/delivery.py:72` | 2 | 1 | 1 |
| `backend/t44/persistence/delivery.py:102` | 2 | 1 | 1 |
| `backend/t44/persistence/delivery.py:135` | 2 | -2 | -3 |
| `backend/t44/persistence/engine.py:21` | 2 | -2 | -3 |
| `backend/t44/persistence/engine.py:42` | 8 | 0 | -1 |
| `backend/t44/persistence/engine.py:58` | 2 | -2 | -3 |
| `backend/t44/persistence/engine.py:60` | 2 | -2 | -3 |
| `backend/t44/persistence/engine.py:62` | 2 | -2 | -3 |
| `backend/t44/persistence/migrations.py:306` | 2 | -2 | -3 |
| `backend/t44/persistence/migrations.py:55` | 2 | -1 | 1 |
| `backend/t44/persistence/migrations.py:289` | 2 | 1 | 1 |
| `backend/t44/persistence/migrations.py:315` | 2 | -2 | -3 |
| `backend/t44/persistence/migrations.py:323` | 2 | 1 | 1 |
| `backend/t44/persistence/migrations.py:337` | 9 | 0 | 1 |
| `backend/t44/persistence/migrations.py:347` | 4 | -2 | -1 |
| `backend/t44/persistence/rows.py:35` | 2 | -2 | -3 |
| `backend/t44/persistence/rows.py:40` | 2 | -1 | 1 |
| `backend/t44/persistence/rows.py:42` | 2 | -2 | -3 |
| `backend/t44/persistence/rows.py:174` | 2 | -2 | -1 |
| `backend/t44/persistence/rows.py:178` | 2 | -2 | -3 |
| `backend/t44/persistence/rows.py:196` | 2 | -2 | -3 |
| `backend/t44/persistence/rows.py:198` | 10 | -2 | -3 |
| `backend/t44/persistence/rows.py:259` | 2 | -2 | -3 |
| `backend/t44/persistence/rows.py:285` | 2 | 1 | 1 |
| `backend/t44/persistence/rows.py:294` | 2 | -2 | -3 |
| `backend/t44/persistence/rows.py:304` | 2 | -2 | -3 |
| `backend/t44/persistence/rows.py:314` | 2 | -1 | 1 |
| `backend/t44/persistence/rows.py:325` | 2 | 1 | 1 |
| `backend/t44/persistence/rows.py:46` | 2 | -2 | -1 |
| `backend/t44/persistence/rows.py:68` | 2 | -2 | -3 |
| `backend/t44/persistence/rows.py:134` | 2 | 1 | 1 |
| `backend/t44/persistence/rows.py:166` | 2 | 1 | 1 |
| `backend/t44/persistence/rows.py:171` | 2 | -2 | -1 |
| `backend/t44/persistence/scans.py:16` | 2 | 1 | 1 |
| `backend/t44/persistence/scans.py:90` | 5 | -4 | -5 |
| `backend/t44/persistence/scans.py:44` | 2 | -2 | -3 |
| `backend/t44/persistence/schema.py:30` | 2 | -2 | -3 |
| `backend/t44/persistence/schema.py:52` | 2 | 1 | 1 |
| `backend/t44/persistence/seed.py:49` | 4 | -2 | -1 |
| `backend/t44/persistence/seed.py:233` | 2 | -2 | -3 |
| `backend/t44/persistence/seed.py:267` | 11 | 0 | 1 |
| `backend/t44/persistence/seed.py:280` | 2 | -2 | -3 |
| `backend/t44/persistence/seed.py:319` | 2 | -2 | -3 |
| `backend/t44/persistence/seed.py:340` | 2 | -2 | -1 |
| `backend/t44/persistence/seed.py:122` | 2 | -2 | 1 |
| `backend/t44/persistence/seed.py:313` | 5 | -1 | 0 |
| `backend/t44/persistence/seed.py:324` | 2 | 1 | 1 |
| `backend/t44/persistence/uow.py:22` | 2 | 1 | 1 |
| `backend/t44/persistence/uow.py:37` | 2 | -2 | -3 |
| `backend/t44/persistence/uow.py:39` | 2 | 1 | 1 |
| `backend/t44/persistence/uow.py:67` | 2 | -2 | -3 |
| `backend/t44/scheduling/__main__.py:28` | 2 | -2 | -3 |
| `backend/t44/scheduling/__main__.py:31` | 2 | -2 | -3 |
| `backend/t44/scheduling/__main__.py:40` | 2 | -1 | 1 |
| `backend/t44/scheduling/__main__.py:58` | 2 | -2 | -3 |
| `backend/t44/scheduling/rules.py:87` | 4 | -1 | -2 |
| `backend/t44/scheduling/rules.py:97` | 2 | -2 | -3 |
| `backend/t44/scheduling/rules.py:146` | 2 | -2 | -3 |
| `backend/t44/scheduling/rules.py:148` | 2 | 1 | 1 |
| `backend/t44/scheduling/rules.py:102` | 13 | -1 | -2 |
| `backend/t44/scheduling/rules.py:140` | 2 | -2 | -3 |
| `backend/t44/scheduling/runtime.py:23` | 6 | 0 | -1 |
| `backend/t44/scheduling/scanner.py:41` | 2 | -2 | -3 |
| `backend/t44/services/codes.py:12` | 2 | -2 | -3 |
| `backend/t44/services/identity.py:107` | 2 | -2 | -3 |
| `backend/t44/settings.py:20` | 2 | -2 | -3 |
| `backend/t44/settings.py:32` | 2 | -2 | -3 |
| `backend/t44/settings.py:35` | 2 | -2 | -1 |
