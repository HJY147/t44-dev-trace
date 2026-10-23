# T44 模块与关键函数输入输出契约（M3可审说明）

Agent-Role: documentation；Prompt-Ref: ROLE-documentation-M3-CONTRACTS-v1。

本说明据集成`074fab7accb1e868bac1d379d6460cca2f6fd2e4`真实源码整理；R001原话来源另合入`5b3bf30`。这是对现有实现的说明，不修改冻结1.0.0，不是测试执行或最终验收。原始签名、行号、源码哈希和38个HTTP操作映射见[M3源码索引](reports/M3-contract-sources.json)。未加类型注解的原函数，以下只描述其函数体实际形态，不伪称已有强类型检查。

## 1 读取顺序和数据形式

先读[需求](../reports/final/requirements-report.md)和[业务规则](../specs/business-rules.md)，再读冻结[OpenAPI](../specs/contracts/openapi.json)、[字段字典/DDL](../specs/database/field-dictionary.md)、[持久化契约](../specs/database/persistence-contract.md)，最后将本说明与[概设/详设](../reports/final/design-report.md)、[M3八图](reports/M3-diagrams.md)及实际代码对照。

| 层次/表示 | 实际形态和约束 | 边界 |
| --- | --- | --- |
| HTTP请求 | path/query/header和JSON；OpenAPI Request Schema，写操作通常含expected_version与Idempotency-Key | 具体必填/例外逐操作读取；login/logout/validateContractPayload不能套一般写规则 |
| HTTP成功 | `{data, meta:{request_id,server_time,contract_version,replayed,original_request_id}}` | data按操作Schema；重放是历史结果，不是当前详情 |
| HTTP失败 | 冻结Error对象、状态码及request_id/audit_id等 | 仅该操作声明的分支合法；不可把内部异常直接回显为驱动文本 |
| 前端TS | `Json`、`Row`、`Promise<Envelope>`、`Intent` | request的Envelope是TS声明/类型断言；不是完整运行时Schema校验器 |
| 后端Call | 可变dataclass，path/query/body为dict，actor/idem等由可信门面补入，clock为UTC datetime | HTTP和Scanner均构造Call；调用者不能把不可信布尔/客户端target_state直接当领域守卫 |
| domain | frozen dataclass/Enum/tuple/frozenset；Decision含source/target/action/command/effects | 内部语义Enum不等于持久整型；转换在services/codes.py显式映射 |
| 持久层 | 允许表/列的dict行，datetime转换UTC，SQL值绑定 | gateway不负责用户鉴权/业务合法边，只有可信调用者可选表和字段 |

服务HTTP身份只有`escalation:write`并限制project_ids。消费者进程负责落通知，人类收件人负责本人read/handle；不能用服务token处理本人通知。

## 2 前端API与页面上下文

| 真实函数/调用方 | 输入 → 输出 | 前后置、错误和副作用 |
| --- | --- | --- |
| [intentFor](../frontend/src/api.ts#L10)；OperationForm | `(operation:string, params:Row, body:Json, previous?:Intent) → Intent`，含JSON.stringify指纹和UUID key | 同operation/params/body复用previous；内容变化新key。只本地生成意图，不发网络，不承诺服务端已成功 |
| [request](../frontend/src/api.ts#L14)；页面、workspace | `(operation, params={}, query={}, body?, intent?) → Promise<Envelope>` | operation须存在于冻结生成映射；编码path/query、Bearer、JSON、可选幂等头，fetch no-store。网络不确定抛status0/NETWORK_UNCERTAIN；非JSON INVALID_RESPONSE；非2xx抛ApiError(status,detail)。非login401清token并回调unauthorized；不会自行重试/修改业务状态 |
| [allPages](../frontend/src/workspace.ts#L8)；bootstrap/context | `(operation:string, params:Row={}) → Promise<Row[]>` | 页大小100，累计items到total或空页；错误向调用者传播。只读取接口，不把前端分页当服务端授权 |
| [bootstrap](../frontend/src/workspace.ts#L17) / [context](../frontend/src/workspace.ts#L22)；页面初始化/项目切换 | `() → Promise<void>`，更新reactive workspace | bootstrap并行读本人/字典/项目；context读项目/成员/迭代及可降级模板/规则，响应项目仍相同才写回。失败保留错误/警示，不伪造模板、规则或项目数据 |

## 3 HTTP适配、Runtime和Business

| 真实函数/调用方 | 输入 → 输出 | 前置/后置与事务、副作用、错误 |
| --- | --- | --- |
| [create_app](../backend/t44/api.py#L150)；ASGI入口/显式DI | `(*, factory=None, settings=None, notifications=_DEFAULT, escalations=_DEFAULT) → FastAPI实例` | 装配Runtime和真实owner门面；显式None可构造依赖缺失故障。注册38路由；不启动扫描器，不自动迁移；默认LazyFactory首次需要UoW才建Engine |
| [validate_request](../backend/t44/api.py#L63)；HTTP闭包传给Runtime | `(request, operation, c) → None`，补`c.path/query/body/key` | 认证后按冻结Schema查未知/重复query、整数/布尔/headers、1MiB、JSON重复键/非法数值、格式与安全输入；抛Rejected，不提交DB。login由自己的Schema和限流处理 |
| [Runtime.execute](../backend/t44/services/runtime.py#L217)；HTTP handle / Scanner._execute | `(call, validate, source="unknown") → (status:int, result:dict, replayed:bool, original_request_id:str或None)` | 先授权再validate，写claim/replay先于版本守卫；login独立限流/会话/审计，logout撤销会话。主UoW锁scope→dispatch→成功audit/finalize/validate→outbox→idem COMPLETE一起提交。返回未包meta的data或Error，HTTP再包装。业务Rejected走独立拒绝审计；CommitUncertain返回503，不自动执行整个事务重试；原key/内容由调用者保留 |
| [Runtime.claim](../backend/t44/services/runtime.py#L120)；execute | `(call) → COMPLETE行或None`，可补`call.idem` | 对path/query/body规范摘要、actor/operation/key作用域；独立短事务先锁会话再锁幂等行，建租约或过期接管。异内容冲突、未过期处理中抛Rejected；COMPLETE供重放，不能借旧token绕过新鉴权 |
| [Runtime.locked_scope](../backend/t44/services/runtime.py#L179)；主写事务 | `(g:活动RowsGateway, call) → None` | 会话→idem owner→必要project图锁→成员顺序共享锁→任务/前驱顺序更新锁。只持锁/补可信上下文，不commit；失去owner/成员范围即Rejected |
| [Runtime.rejection](../backend/t44/services/runtime.py#L69)；execute及Scanner鉴权失败 | `(call, error:Rejected) → 同execute四元组` | 主事务已退出回滚后，新UoW写拒绝audit；仅本owner、status1且error<500才存拒绝重放。审计依赖失效返回503/AUDIT_UNAVAILABLE及audit_id=null，不声称已留痕 |
| [Business.dispatch](../backend/t44/services/application.py#L38)；Runtime | `(g, call) → 操作data dict` | list依赖/评审/预案/决定统一page，其余按已知operation调用handler；g来自调用者活动UoW。业务读写不私自commit，不返回HTTPResponse；Rejected交Runtime |
| [Business.finalize](../backend/t44/services/application.py#L62) / [Business.validate_data](../backend/t44/services/application.py#L68)；Runtime | `(result,call) → result`补audit_id；`(operation,result) → None` | finalize只在该操作data_fields含audit_id时补；validate_data用冻结data_schema，不符抛INTERNAL_ERROR使主UoW失败。普通成功outbox task_id可None；createEscalation不重复生成普通事件 |
| [Business.validateContractPayload](../backend/t44/services/application.py#L107)；dispatch | `(g,c) → {valid,category,validated_operation_id,schema_version,business_guards_executed:false}` | 输入ContractValidationRequest三类payload、可选task范围；校验时间/结构，明确不执行全部状态/权限业务守卫，不创建任务/决策 |

Call和纯领域之间的桥为[Workflow.transitionTask](../backend/t44/services/workflow.py#L61)：输入`g,c`，消费TransitionRequest；读当前task、前驱和已持久证明/轮次，构造typed命令与TransitionContext，调用decide，再CAS应用effects、可选decision/排期diff，返回`{task,decision或None}`，对应TransitionResult。旧版本、跨任务证明、旧评审/预案、非法动作等Rejected；不提交，Runtime统一成功/失败边界。

## 4 纯领域决策

[decide](../backend/t44/domain/state_machine.py#L90)真实签名为`decide(position: TaskPosition, command: Command, context: TransitionContext) -> Decision`。

- 输入是已有合法TaskPosition、九种typed Command之一，以及由服务层读取真实成员/负责人、全部前驱状态、当前轮次/排期和评审/交付/回滚证明构造的TransitionContext。不是客户端传入的“已授权/已通过”可信声明。
- 输出不可变Decision：原/目标位置、动作、原命令、effects集合。start、unblock回developing及rework重查依赖；block保留原态；解除由原态决定；无任意target_state接口。
- 不合业务抛`DomainViolation(Violation)`；非法内部类型/不支持命令为TypeError/ValueError。Workflow显式映射成冻结错误；内部Violation本身不是HTTP错误码。
- 无SQL/网络/文件、无状态修改、无commit；返回Decision不代表数据库已经改变。计数/类型校验见[models](../backend/t44/domain/models.py)，命令字段见[commands](../backend/t44/domain/commands.py)。

## 5 数据库工厂、Rows、UoW与迁移

| 真实函数/调用方 | 输入 → 输出 | 前后置、事务与错误 |
| --- | --- | --- |
| [create_mysql_engine](../backend/t44/persistence/engine.py#L79)；LazyFactory/CLI/进程组合根 | `(settings:MySQLSettings) → Engine` | 可信配置，库名白名单；仅构造连接池，连接建立时执行UTC/严格模式/READ COMMITTED初始化。无建表/迁移，不在每次业务调用时重新造Engine；hide_parameters=True且echo关闭，HTTP/CLI另负责异常脱敏 |
| [SqlAlchemyUnitOfWorkFactory.__call__](../backend/t44/persistence/uow.py#L103)；Runtime/Store | `() → 新SqlAlchemyUnitOfWork` | 每次新single-use UoW，Session工厂共享而事务不跨请求复用 |
| [SqlAlchemyUnitOfWork.__enter__](../backend/t44/persistence/uow.py#L21) / [SqlAlchemyUnitOfWork.__exit__](../backend/t44/persistence/uow.py#L87) | `__enter__() → self`；`__exit__(exc_type,exc,traceback) → False` | 入场begin，正常active出口commit，有异常rollback，最终close。gateway只在active且非rollback-only可用；不得复用/并行跨请求共享UoW |
| [SqlAlchemyUnitOfWork.commit](../backend/t44/persistence/uow.py#L51)；正常上下文出口 | `() → None` | commit确认失败抛CommitUncertain，cleanup rollback不能证明未提交。rollback-only先回滚并抛TransactionStateError；无自动重执业务 |
| [RowsGateway.rows](../backend/t44/persistence/rows.py#L150) / [RowsGateway.get](../backend/t44/persistence/rows.py#L191) | `rows(table,where=None,*,columns=None,order_by=("id",),limit=None,offset=0,lock=None,skip_locked=False,predicates=()) → list[dict]`；`get(table,id,*,lock=None) → dict或None` | 表列/排序/谓词允许表内，锁None/share/update；skip_locked必须有锁；limit/offset非负。参数化、UTC转换；持锁直到调用者UoW结束；无业务鉴权 |
| [RowsGateway.insert](../backend/t44/persistence/rows.py#L221) / [RowsGateway.update](../backend/t44/persistence/rows.py#L250) / [RowsGateway.delete](../backend/t44/persistence/rows.py#L261) | insert(table,values)→int主键；update(table,where,values,*,predicates=())/delete(table,where)→影响行数 | 写值/where非空且允许表列，不能绑定SQL表达式。0行不是自动业务冲突，调用方须核对CAS；执行失败标记回滚（savepoint隔离其失败），不自行commit |
| [Call.cas](../backend/t44/services/common.py#L143)；Workflow/Tasks等 | `(g,table,row,values,*,expected=None) → 更新后的行dict` | 取expected_version，版本相等且未溢出，UPDATE where id+version且行数=1，版本加1/可选updated_at，补before/after。失败VERSION_CONFLICT，仍属调用者事务 |
| [migrate](../backend/t44/persistence/migrations.py#L78)；显式t44.cli migrate | `(engine,*,expected_database:str) → {version,sha256,already_applied,tables,columns,defects,passed}` | 只MySQL8.4且目标库一致，校验打包DDL摘要、GET_LOCK；首次空库建迁移表+18业务表并逐语句提交。失败可能留部分DDL，MigrationError禁止假称可回滚/自动drop修复；重复版本/摘要/状态必须一致 |
| [check_schema](../backend/t44/persistence/migrations.py#L17)；migrate/显式核查 | `(engine) → {tables,columns,defects:list[str],passed:bool}` | 当前基线检查列集合/类型部分属性、nullable/default/主键以及索引/FK/CHECK名称存在；C-P4已证实遗漏约束/索引语义。新checker修复未在本基线发布，不将passed视为全面语义一致或独立验收 |

共同异常见[persistence/errors.py](../backend/t44/persistence/errors.py)：StatementRejected(ValueError)拒绝内部不安全调用；PersistenceIntegrityError带kind供duplicate等处理；PersistenceUnavailable/TransactionStateError/CommitUncertain不泄漏原SQL/密码。数据库错误不是业务参数错误，调用门面选择冻结协议映射。

## 6 消息投递、消费与本人通知

| 真实函数/调用方 | 输入 → 输出 | 前后置/副作用和错误 |
| --- | --- | --- |
| [DeliveryWorker.cycle](../backend/t44/messaging/worker.py#L33)；run循环 | `() → {confirmed,fallback,recovered,retried,consumed,quarantined,errors}`整型计数 | 先超时confirmed恢复，短DB事务claim租约；事务外publish，再独立confirm。发布失败：type2升级终态fallback待办，type1普通事件retry；消费get/consume后计数。计数不是通知已被人读/处理，DB故障仍可抛PersistenceError由run记录并留租约恢复 |
| [PikaBroker.publish](../backend/t44/messaging/broker.py#L67)；worker | `(event:outbox行dict) → None` | 只发UTF-8 JSON三字段event_id/schema_version/event_type，persistent+mandatory+publisher confirm；不是完整通知/明文用户数据。网络/NACK为BrokerUnavailable；不在持DB锁事务里等broker |
| [consume_delivery](../backend/t44/messaging/broker.py#L122)；worker | `(store,channel,method,body:JSON bytes) → "consumed"或"quarantined"` | 精确三整数字段、范围/schema1/事件存在且类型匹配；store.consume成功提交后ACK，ACK丢失允许再投。非法消息reject requeue=false进隔离；PersistenceError NACK requeue=true再抛。不声称网络恰一次 |
| [OutboxStore.consume](../backend/t44/persistence/delivery.py#L105) / [OutboxStore.fallback](../backend/t44/persistence/delivery.py#L138)；consume_delivery/worker | consume(event_id,*,now=None)→event_id/created/fallback dict；fallback(event_id,*,now=None,lease_token=None,error_code="MQ_UNAVAILABLE")→结果dict | 每次自己UoW锁同outbox行，只插缺失收件人，不覆盖已有read/handled；fallback检查type2及可选租约owner，stale_owner无再提醒。终态fallback晚到消费仍不复制通知；提交后才返回 |
| [OutboxStore.recover_confirmed](../backend/t44/persistence/delivery.py#L116)；worker | `(*,confirmed_before,now=None,limit=100) → list[{event_id,created,fallback}]` | 只选confirmed且缺通知的事件，在短事务锁/重查缺失，补降级待办；不让已完整事件吃满恢复limit |
| [NotificationFacade.mark_read](../backend/t44/messaging/facade.py#L82) / [NotificationFacade.handle](../backend/t44/messaging/facade.py#L92)；Business | 输入g与actor_id/project_id/notification_id/version/now，handle另需note/evidence；→冻结Notification dict | 需活动成员、本人收件、版本CAS；handle必须证据。mark_read不设置handled_at，handle不改变task状态；不私自commit，Runtime负责审计/幂等和事务。无记录/越权/旧版本/缺证据Rejected |

## 7 扫描与升级门面

| 真实函数/调用方 | 输入 → 输出 | 前后置、错误、持久副作用 |
| --- | --- | --- |
| [Scanner.run](../backend/t44/scheduling/scanner.py#L102)；CLI一次/定时tick | `(run_id=None) → scan_runs行dict`；UUID可续扫 | _scope实际鉴权服务token，取当前不可变规则；ScanStore.start固定候选cutoff，keyset逐页，业务请求每次用clock。每候选经Runtime，持久checkpoint累计扫描/新建/重复；断点前已提交事件不因重启复制。失败抛ScanFailure，不当全扫成功 |
| [Scanner._execute](../backend/t44/scheduling/scanner.py#L67)；run每候选 | `(candidate:task行,run_id:UUID文本,rules:规则对象) → 升级受理data dict或None` | Call含expected_version/schedule_version/rule_version/scan_run_id，key为run+task+版本摘要。202返回，NOT_ELIGIBLE跳过；仅版本/排期冲突最多3次重读，其他错误ScanFailure；不是Runtime死锁通用重试 |
| [Scanner.tick](../backend/t44/scheduling/scanner.py#L145)；APScheduler | `() → 新一轮scan_runs行` | 先续120秒无心跳且同rule_hash旧运行（最多查询100），再开新运行。单实例flock由进程入口负责；不因多API worker起多个扫描器 |
| [EscalationFacade.current](../backend/t44/scheduling/facade.py#L16) / [EscalationFacade.rules](../backend/t44/scheduling/facade.py#L19) | current()→注入或load_rules规则对象；rules(g,c)→当前或历史snapshot dict | 规则version/hash/effective_at不静默改写；历史版本未找到RESOURCE_NOT_FOUND。规则文件路径/数据域见冻结契约及scheduling/rules.py |
| [EscalationFacade.create](../backend/t44/scheduling/facade.py#L106)；Business.createEscalation | `(g,c) → {event:EscalationEvent,created:bool,task_version:int}`，HTTP202 | 服务scope/project→task锁/版本/排期/规则→当前clock选最高匹配→同task/schedule/level查重。首次outbox+escalation+计数CAS同调用者事务、负责人/全部有效经理去重，重复返回既有事件不增加；失败由Runtime拒绝审计。不能把202写成收件人已读/已处理 |

## 8 部署与管理CLI

| 真实函数/调用方 | 输入 → 输出 | 前后置、事务/外部副作用和错误 |
| --- | --- | --- |
| [main](../deployment/ops.py#L191)；`python deployment/ops.py` | argparse命令/--env-file→退出码0或1及文本 | init-env/build/infra/start/stop/status/config-check/migrate/backup/restore/scheduler-token/seed-demo/account；受控调用指定Docker context/project。失败只出脱敏摘要；解析参数错误按argparse，不能保证一律1 |
| [backup](../deployment/ops.py#L104)；ops backup | `(env_file:Path,values:dict[str,str],database:str,output:Path) → None` | 显式匹配主库，拒绝已有目标/软链、空库/非InnoDB/视图/可编程对象；写dump+0600摘要manifest，排他发布不覆盖。调用方须先停写保证演练一致性；函数本身不自动全系统停写 |
| [restore](../deployment/ops.py#L147)；ops restore | `(env_file,values,args) → None` | 新t44-restore-* project+不同库+confirm_target匹配，校验dump/manifest；默认plan，--execute才创建新隔离卷导入。拒绝既有卷/非空目标；保留实例，不drop/替换活库。函数只比表数量，语义/行数/checksum/应用验证需另做 |
| [issue](../deployment/credential_admin.py#L40)；ops scheduler-token | `(projects:list[int],*,name:str,rotate:bool,credential:Path=CREDENTIAL) → 脱敏session_id/expiry/写入与撤销状态dict` | 私有目录、项目正ID、flock，临时0600文件由真实backend CLI发token，原子发布/fsync；轮换撤销旧session。凭据本体留私文件，不stdout。失败可能已发session，cleanup尽力撤销；不谎称跨DB/文件原子事务 |
| [main](../backend/t44/cli.py#L46)；管理/容器入口 | `(argv=None) → 退出码0/1和JSON摘要` | migrate显式库，seed_demo synthetic，init-user摘要密码，revoke写会话+审计，service-token只escalation:write/项目范围。token O_EXCL0600文件；异常脱敏COMMAND_FAILED。参数解析先于try；不在文档抄凭据或当普通HTTP接口 |

## 9 现有实践与用户建议的未来工作流

本项目确实先有OpenAPI/字典/DDL/持久契约草案，C1–C4审核失败后修正，经D004/ae60冻结再派完整实现；这不等于学生事先亲自写好了Python函数骨架。本文函数I/O是M3据既有实现补充的可审说明，不倒填为编码前产物。

用户本人原话见[R001](../records/reflections/R001-original.md)与[来源归属](../records/reflections/R001-provenance.json)。用户提出未来由人把关结构/封装/重要函数I/O，用def/#todo骨架约束AI，以及需求歧义、测试要求/过程/结果决策要由人把关。该建议是已提供的本人观点，不是“本次已经由本人写骨架/断点debug”的证据。未来若采用，可先由人实际写骨架和契约→AI补全→人审diff和调用链→分层测试→人按结果决定，再记录真实操作者；本轮不制造已发生记录。

## 10 核查边界

只读源码签名/函数体、冻结Schema与已发布报告，不导入应用，不运行pytest/业务HTTP/构建/渲染。当前e01产品审核不通过及C-P4待新证据仍保留；CI317成功不能补成全错误分支/全部语义正确。性能窗口结束前不进行本机执行，最终DOCX及逐页QA待后续授权时段和本人研究正文。M2原记录不改，M3图与提示词材料分别引用实际公开来源。
