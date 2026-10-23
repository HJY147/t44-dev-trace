# 后端设计草案 v1

状态：v1规格已冻结，进入完整实现和联调；冻结不是运行验收；实际派工 `ROLE-backend-CONTRACT-v1`。业务出口依据用户采用business-rules v1，开始前编辑范围依据协调者D002；下列技术细节须跨岗及审核岗复核。契约见 `contracts/openapi.json` / `contracts/README.md`，数据库DDL/持久契约由数据库岗提供。

## 包、进程与依赖边界

后续统一 `backend/t44/` 包，`PYTHONPATH=backend`。API入口约定 `t44.api:app`，同步FastAPI路由和同步SQLAlchemy2/PyMySQL事务；Pika和APScheduler不混入async数据库访问。依赖定义在 `backend/pyproject.toml`，uv编译固定 `backend/requirements.lock`，CI以pip安装锁文件。本轮这些实现文件尚不存在。

- `t44/api.py`：应用组合根，安装认证、错误/脱敏、body大小及登录限流中间件，注入服务门面；不创建调度任务。
- `t44/domain/`：集中枚举、状态机及守卫；API不能直接改state。
- `t44/services/`：流程、评审、上线决策、幂等/事务与独立拒绝审计协调；仅依赖门面协议。
- `t44/persistence/`：数据库岗拥有ORM、参数化仓储、UoW、锁、幂等/审计/outbox持久能力；服务不构造连接。
- `t44/messaging/`：消息岗的Pika发布/消费/降级门面；独立进程，连接不跨线程共享。
- `t44/scheduling/`：调度岗APScheduler独立进程，每60秒扫描及续扫；API多worker不各起一份调度器。
- `t44/cli.py`：拟统一初始化账号及会话撤销命令入口，由后端提供行为、部署岗提供运行封装；命令设计不代表已实现。

跨模块依赖从组合根注入AuthFacade、WorkflowFacade、ReviewFacade、ReleaseFacade、EscalationFacade、NotificationFacade、UnitOfWorkFactory、IndependentAuditWriter与OutboxRepository。通知查询/已读/处理的领域契约由消息岗承接，API只做适配，不另建通知系统。正式目录责任映射由协调者同步，不能沿用初始化旧目录误改他岗文件。

已读并遵守 `../docs/collaboration/implementation-layout.md`：本岗自测位于backend/tests/backend/，review模板资源归本岗backend/t44/resources/review-template.json；升级规则资源backend/t44/resources/escalation-rules.json归调度岗；依赖锁由后端统一维护，其他岗先提需求。引用该约定不表示已有这些实现文件。

运行配置提案：`DATABASE_URL=mysql+pymysql://...`、`AMQP_URL`、`T44_SESSION_TTL_SECONDS=3600`；不透明Token方案无需JWT_SECRET。API可由 `uvicorn t44.api:app --workers 4` 启动，消息/扫描分别 `python -m t44.messaging`、`python -m t44.scheduling`；这些入口尚未编码。账号CLI拟 `python -m t44.cli init-user --username ... --display-name ... --password-stdin`，CLI只在内存将口令转安全摘要，持久层初始化门面只接收可解析Argon2id摘要，拒绝明文并脱敏审计。健康/就绪采用进程/TCP及数据库直探，不增加无鉴权业务探针。迁移命令归数据库岗明确；pytest标记可对齐contract/integration/fault、入口backend/tests、t44覆盖率至少80%，但无已运行结果。

## 版本与证据基线

| 字段 | 变化与用途 |
| --- | --- |
| task.version | 所有任务关联写CAS，包括状态、排期、负责人、依赖、评审发布、评估/预案及批准；每次成功只增1 |
| schedule_version | 改期递增，升级唯一键使用它；完整旧/新计划、原因、依据、操作者保留 |
| delivery_cycle | 初始1；已回滚返工时递增，旧批准引用清空 |
| review_cycle | 初始1；评审不通过退开发时递增，返工进入新delivery_cycle时重置1 |
| review.version | 不可变发布评审的自身版本；绑定delivery_cycle/review_cycle与提交审核对象SHA |
| assessment.version | 评估/预案及评审的乐观版本；绑定schedule_version/delivery_cycle |

阻塞/解除只改变task.version并记依据，不改变轮次。改期不撤销本轮代码评审，但撤销旧上线批准，待上线保持待上线，重新创建并批准当前排期的评估，不新增5→4出口。评审退回/回滚返工清空旧批准并重新评审，不能凭旧记录自动进入待上线或交付。

代码评审先发布不可变证据，递增task.version但不直接改变状态；随后统一transitions引用本轮最新review_id/review_version作通过/退回。提交审核对象SHA须与评审SHA一致。上线评估包含四视角各一项、应对与回滚目标/触发/步骤/影响/验证/负责人/证据；评估评审通过后再由经理决定交付。评审缺证据可记录失败/未验证，但不得将必需项判通过。协调者质量约束：代码评审发布者/批准者不得为task.owner；评估/预案审核者不得为其created_by。最低防线不能声称确认SHA真实作者，其他无自审证据仍由R01逐项判断。

## 允许状态出口与角色守卫

| action | 当前→目标 | 必要守卫与角色 |
| --- | --- | --- |
| 1 start | 待受理→开发中 | 仅负责该任务且有本项目developer角色；经理身份不能代推；依赖全部当前已交付 |
| 2 block | 待受理/开发中/待评审/待上线→阻塞 | 保存原状态；原因/责任环节/证据；待受理经理、开发中负责人developer、评审阶段reviewer/manager、上线阶段manager |
| 3 unblock | 阻塞→阻塞前状态 | 不接受客户端返回状态；同原阶段角色，解除依据/证据；返回开发中重新查依赖 |
| 4 submit_review | 开发中→待评审 | 仅负责人developer；审核对象固定SHA及证据 |
| 5 approve_review | 待评审→待上线 | 评审人员/经理且不能是task.owner；最新本轮通过评审，十项/八段完整且必需项有证据 |
| 6 reject_review | 待评审→开发中 | 评审人员/经理；本轮拒绝评审与理由；review_cycle++，清空旧批准 |
| 7 deliver | 待上线→已交付 | 经理；本轮代码通过、当前排期与交付轮次的评估/预案批准；记录发布版本及人类拍板依据 |
| 8 rollback | 已交付→已回滚 | 经理；原因、影响、目标版本、交付采用的已审预案及证据；保留任务和历史 |
| 9 rework | 已回滚→开发中 | 经理明确返工决定与新计划；依赖全已交付；交付轮次++、评审轮次重置、排期版本++ |

其他迁移一律拒绝并独立留痕。接口无target_state通用入口。负责人/依赖仅待受理或blocked_from_state=待受理时由经理修改，开始后明确409；这是协调者技术范围，不冒称用户原文。任何依赖变化均校验同项目、自依赖和环，不能改变其他任务现状。依赖任务从已交付回滚后，不自动把下游任务状态改回，后续需依赖的开始/回开发/返工守卫重新检查。

## 鉴权、会话泄露阻断与输入约束

部署CLI初始化账号并存Argon2id安全摘要；登录是取得身份的专用例外，不是开放业务接口。拟使用高熵不透明会话Token，数据库仅存摘要/session_id/过期/撤销信息，不存可恢复原文。默认有效期3600秒属于技术配置，不代替撤销。

每次请求都查当前会话及项目资格，不缓存可长期绕过撤销的权限。`logout`只撤销当前会话。泄露处置须有CLI `revoke-sessions --user-id <id>` 撤销目标用户全部会话，或 `revoke-session --session-id <id>` 撤销指定会话；不把原Token放命令参数/日志/URL。撤销提交后新请求返回401 TOKEN_REVOKED；必要时重置口令并重新登录。服务Token单独项目范围及scope，可单独撤销，不具有经理权限。

写请求事务内重新核验会话/成员资格：会话锁后再取业务锁，撤销动作不反向锁业务资源；已被授权在途写与撤销按锁提交次序线性化。该锁策略仍须持久岗复核，不能保证已执行的外部动作可回滚。当前产品只记录发布/回滚决定，不执行外部云动作。

输入先按共享JSON Schema拒绝字符串冒整数、bool冒整数、未知字段、非法枚举和非UTC时间；JSON数值1.0按标准整数语义规范化后入严格业务类型。ID/排序/枚举选择器拒绝明确攻击模式，普通标题/说明中的引号不误判；所有查询仍参数化。错误统一去除Pydantic errors中的input、ctx敏感值、口令、Bearer、原始完整body和SQL；只持久化request_id/主体/项目/动作/脱敏字段错误。

## 成功事务、拒绝审计与幂等恢复

```text
authenticate_and_project_access()
validate_schema_and_safe_selectors()
claim_or_read_idempotency(subject, operation_id, key, canonical_request_hash)
if same_completed_request: return original_result_snapshot
if different_hash: independently_audit_and_reject(409)
if other_owner_processing: reject(409, Retry-After)
begin main UoW; session FOR SHARE and recheck live session
  lock own idempotency row; verify owner_token
  acquire project(if needed)/memberships/tasks in fixed order; recheck memberships
  check expected_version, role/ownership, legal state edge and evidence
  CAS task and write associated review/assessment/decision/dependencies
  write success audit; if escalation, write event+outbox and count once
  write completed idempotency result; commit together
on business rejection:
  rollback main UoW
  independent UoW commits rejection audit + completed error snapshot
  if that fails: 503 AUDIT_UNAVAILABLE, no false audit_id, retain PROCESSING
on commit confirmation lost: 503 TRANSACTION_UNCERTAIN; retry original key
```

幂等scope为(actor_kind,actor_id,operationId,key)，摘要包含规范化path/body和expected_version。幂等快照存业务data/状态码，重放时重新构造当前请求meta；原task快照不会冒充现在的版本。认领短事务+owner_token/lease避免拒绝回滚与审计落库间被同键重执；恢复者先锁行等待旧事务结束，再CAS换代，旧worker不能过期后提交。v1不自动清理完成记录。

C1采用 `idempotency_requests.response_request_id` 作为重放溯源持久来源，COMPLETE时必须非空；保存实际生成已存结果的请求ID，可以是owner恢复后的最终完成请求，不强行使用首次租约认领ID。成功与完成快照同主事务定格该字段，拒绝与错误快照/审计同独立事务定格；重放original_request_id读取它，当前request_id/server_time/replayed现场构造。不保存整个旧meta或凭据；DDL列与CHECK由数据库岗下一轮落实，本轮不改数据库文件。

拒绝审计是独立数据库事务，和成功事务分开但不改任务现状；独立审计失败返回503、audit_id=null并脱敏告警。持久故障介质/补偿恢复仍待部署确认，不能声称单数据库宕机时拒绝审计仍一定落库。普通查询与输入/越权失败也需相应安全记录。

锁顺序：会话认证保护 → 自身幂等行 → 项目行（仅需要图/成员/依赖一致性的操作）→ 成员行按id → 任务行按id → 关联业务记录。加删依赖、开始、解除回开发、返工先锁project；读取并锁前驱任务后验state=已交付；同项目A→B/B→A串行查环。普通单任务写不额外串行整个项目，以成员FOR SHARE重核资格后锁task；成员撤销走project→membership FOR UPDATE→活动负责任务。任何路径拿到membership/task后不能再追加project锁。数据库岗对上述固定序和CAS提供统一门面。

## 升级扫描、outbox与降级

```text
every 60 seconds, UTC:
  keyset-read non-delivered/non-rolled-back tasks; blocked still timed
  for each candidate:
    service POST escalation(expected_version, schedule_version, rule_version, scan_run_id)
    reload current plan/time/rule in transaction
    elapsed = server_now_utc - planned_end_utc
    elapsed_us = (elapsed.days*86400 + elapsed.seconds)*1000000 + elapsed.microseconds
    compare elapsed_us with rule second offsets * 1000000
    choose only highest currently eligible level
    unique(task_id, schedule_version, level): existing -> no new count/event
    new -> persist event + recipient snapshot + outbox + success audit atomically
publisher uses Pika confirms; consumer commits inbox before ACK
unique(event_id, recipient_id) prevents repeated notice or repeated fallback
MQ failure -> atomically create marked in-app todo and mark event fallback_terminal
late confirmed/consumed same event -> retain existing notice, no second reminder
new events after recovery -> normal MQ delivery
```

临期为0≤结束时刻−now≤24h；超期为0<now−结束时刻<24h；严重超期为差值≥24h。首次跳级只生成当前最高级别，不补低级；过往已发生级别保留。业务去重键不加rule_version来绕过同排期同级一次规则。通知按事件与接收人去重，已读/已处理独立。新事件成功CAS task.version并增加升级计数，和event/outbox/audit同事务。不同键旧版本409；同键优先原快照；业务重复且版本有效返回created=false，不再增加count/version。通知已读/处理仅notification.version，不占任务版本。事件+outbox接受的HTTP 202只覆盖可靠提交，消息送达延时另测。fallback_terminal是处理语义，最终存储编码与消息岗确认，不新增任务状态。

C2收件人必须包含负责人和全部有效经理去重，不静默截断，也不新增人数上限；event.recipient_ids无数组长度上限，handled_count覆盖INT UNSIGNED域，创建/历史嵌套响应引用同一Schema。C3所有请求、响应及只读候选时间先经UtcTime限制1000～9999年、UTC Z、微秒≤6并用FormatChecker核对真实日期，再比较起止。调度按上面的now−end差值比较窗口，禁止计算planned_end+24h；9999年末仍可作差，不能因构造超出9999年的阈值而溢出。已通知总协调将该约定交给后续调度岗。

扫描使用计划时间索引/主键续扫，N任务、K本批候选时一次完整扫描最坏O(N)，事件唯一查询O(log E)或索引查找、收件人数R时生成通知O(R)；不能把每批索引提取成本冒称整次扫描O(1)。依赖环检查按项目图DFS为O(V+E)，使用project锁防并发写破坏结果；开始检查D个前驱为O(D)数据检查并按主键批量锁。实际SQL计划和性能仍未验证。

## 配置扩展

ReviewItemId使用R[0-9]{2,3}，有效template_version精确规定当前必需项，v1为R01～R10。升级level使用1～255，规则数组用相对计划结束秒的起止/包含边界、收件角色和priority描述，最高匹配；scan_interval_seconds配置范围5～3600，v1为60。v1仍只启用原三档和24小时阈值。新增条目不改硬编码枚举或DDL，配置版本记录原/新值、时刻、影响和决定者，正式采用/审核后才能启用；尚未用真实diff验证一个配置加一个模块的维护指标。

## 验证、跨岗交接与未完成

契约规范校验的真实失败与成功分别保存在 `../agents/backend/openapi-validation-failure.log`、`../agents/backend/openapi-validation-success.log`。实际失败是生成器共享参数列表造成重复幂等头，现已按操作隔离参数并复验通过；这是AI草案实际缺陷，由AI修复。

后续必须使用真实HTTP做请求/响应Schema验证，覆盖合法流转、非法跳级、同版本竞争、同键重放/异参、证据缺失、跨项目/撤权/泄露撤销、参数注入、拒绝审计失败、MQ故障/晚到重复、扫描重启。规范文件可解析不能替代实现一致性或独立验收。三类性能入口和统计口径见contracts/README.md；未运行任何业务测试或压测。

数据库对齐：INT UNSIGNED ID、四计数cycle命名、阻塞原状态、迭代产能/计划diff、独立拒绝审计、租约幂等、事件/outbox和通知唯一键；scan_run_id对外UUID，持久层映射scan_runs整数PK。消息/调度岗须复核事件字段、fallback_terminal与服务调用口径。待审项包括审计故障持久介质、所有DDL/API字段和锁序一致性；无自审最低机器防线不能代替真实作者/证据内容判断。没有新增业务状态出口，没有产品实现或冻结声明。

总协调最后收口：DB完全不可用时不能宣称DB审计成功，返回503，部署承接脱敏stderr/文件运维记录及后续恢复；不为此增加第二套审计系统。实现和实际故障验证仍未开始。

CONTRACT-v2只修审核C2/C3/C4和C1后端来源说明；C4新增逐操作错误/HTTP/触发条件一致性检查，GET与只读校验无幂等错误，字典无虚构项目/资源错误。验证脚本位于agents/backend/validate_contract_design_v2.py，真实修复前/后输出独立留存；没有执行实际HTTP、MySQL、消息、调度或性能测试，原不通过报告仍有效直至新SHA复审。
