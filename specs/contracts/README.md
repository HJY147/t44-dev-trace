# T44 API 契约 1.0.0

状态：**v1规格已冻结**。用户D001/D004已采用业务及字段/错误取舍，C1–C4限定技术复审通过。`openapi.json` 为 OpenAPI 3.1 / JSON Schema 2020-12，含31路径、38操作；进入完整实现与联调。冻结不表示HTTP、功能、性能或验收已经通过；冻结摘要见records/spec-freezes/v1.json。

## 依据与范围

- 用户采用的业务出口与通知规则：`../business-rules.md`、`../../records/decisions/D001-business-rules.md`。
- 协调者的开始前编辑范围：`../../records/decisions/D002-prestart-edit-boundaries.md`，不是用户逐条原话。
- 需求与架构：`../requirements.md`、`../../architecture.md`、原始T44任务书；评审内容来自 `../../docs/reviews/review-protocol.md` 及总协调给定稳定ID。
- 技术方案：同步FastAPI、SQLAlchemy 2 / PyMySQL、MySQL、Pika、独立APScheduler进程；数据库岗负责持久实现与DDL。当前授权实现ORM、版本迁移及产品代码，按本规格和审核门禁验证。

三类主接口分别是 `POST /api/v1/projects/{project_id}/tasks`、`POST /api/v1/projects/{project_id}/tasks/{task_id}/transitions` 和 `POST /api/v1/projects/{project_id}/tasks/{task_id}/release-assessments`。辅助操作覆盖登录/撤销当前会话、本人身份、字典、项目/成员、迭代产能、排期差异、开始前负责人及依赖、评审模板/证据、预案批准、经理决策、升级历史、通知已读/处理和项目只读审计。没有通用状态PATCH、无鉴权注册、全局账号枚举或外部自动部署/回滚执行接口。

## 统一表示

| 项目 | 约定 |
| --- | --- |
| 基址 | 同源 `/api/v1`；生产使用TLS，当前不代表已有服务 |
| ID | 正整数，范围1～4294967295，与数据库INT UNSIGNED对齐 |
| 版本 | 正整数至2147483647；任务关联写统一 `expected_version`，成功递增 `task.version` |
| 时间 | MySQL DATETIME(6)共同域：1000-01-01T00:00:00Z～9999-12-31T23:59:59.999999Z，UTC RFC3339仅Z、最多6位微秒；真实FormatChecker验证；页面转北京时间；结束必须晚于开始 |
| 字典 | 状态、角色、动作等整数集中在components.schemas和 `/dictionaries`，名称/标签不作数据库状态 |
| 分页 | `page>=1`，`page_size`默认20、上限100；items/total/page/page_size；只允许列举排序，id打破并列 |
| 成功 | `data` 加 `meta(request_id,server_time,contract_version,replayed,original_request_id)`；不返回凭据摘要 |
| 错误 | code/message/request_id/audit_id/current_version/current_state/original_error_code/violations；无权时不泄露资源版本 |
| 证据 | kind、locator、description，仓库引用另带固定revision；HTTPS引用不由服务端自动抓取；界面安全展示 |
| 版本化扩展 | 评审ID采用R[0-9]{2,3}并按template_version精确验证，v1仅R01～R10；level范围1～255并按rule_version验证，v1仅1/2/3 |
| 幂等 | 业务写必填 `Idempotency-Key`，16～128个允许字符；登录、logout、GET及只读契约校验例外 |
| 内容限制 | 业务对象禁止额外字段；请求体上限1MiB；不接受客户端actor/决定者/状态值覆盖服务器身份与状态机 |

JSON Schema的integer不接受字符串或布尔；JSON数值 `1.0` 在标准语义上是整数，校验通过后可规范化为1，不能默默接受字符串 `"1"`。URL路径/查询参数按HTTP参数序列化规则解析。后续实现必须以同一契约先验证真实请求，再进入业务类型；不得让Pydantic默认转换、额外字段忽略或宽松时间解析放宽契约。响应也须对实际HTTP内容验证。

`schedule_version`只随改期递增；`delivery_cycle`标记已回滚返工的新交付；`review_cycle`标记评审退回后的新评审。状态变化、阻塞和解除不让全部证据无条件失效。排期变更保留代码评审，撤销旧上线批准；新上线评估必须绑定当前排期版本和交付轮次。

## 身份、权限与幂等顺序

账号由部署CLI初始化，只存安全口令摘要；已认证用户可创建项目并自动成为经理。经理仅按精确用户名加入已有账号，不提供全局目录。所有业务数据先核验当前项目成员身份；管理员或服务身份不会自动获得其他项目数据。

协调者权限细化：start/submit_review仅任务负责人且具有developer角色；manager身份不能代推。待受理的阻塞/解除仅manager，开发中仅负责人developer，评审阶段reviewer/manager，上线阶段manager，发布/回滚/返工仅manager。代码评审发布者/批准者不能是task.owner，上线评估审核者不能是assessment.created_by；这是AI协调者质量约束，不冒称用户原话，也不声称验证SHA真实作者。项目证据与审计由本项目成员只读；个人通知仅当前收件人且仍有项目资格可访问。服务Token只用于授权项目内的升级入口，前端人类Token不能代用。

请求顺序为：身份及项目权限 → 结构/安全输入校验 → 同主体、operationId、幂等键查找 → 相同摘要回放原结果 → 当前动作角色/责任人/状态/版本/业务守卫 → 事务提交。摘要包括路径ID和规范化完整请求体（含旧expected_version），排除Token、口令及请求追踪头。同键异参409；相同成功请求重试优先返回首次快照，不因旧版本变409；重放响应后必须另GET权威最新任务。

幂等PROCESSING由独立短事务认领，持久owner_token/租约；主事务锁该行再执行并原子完成快照。其他请求仍处理中返回409及Retry-After，不能换键重试。恢复者需加锁等旧主事务终止，再CAS租约所有者；旧worker提交前核对owner_token。拒绝回滚后，独立事务同时写拒绝审计和错误快照。v1提案不自动清理已完成记录，避免无声明重试窗导致二次动作。

C1修订采用持久字段 `idempotency_requests.response_request_id`：COMPLETE结果必须非空，值是**实际生成已保存结果的请求ID**；租约恢复后最终完成时才定格也合法，不一定是首次认领ID。成功结果与该字段同主事务完成，拒绝结果与该字段同独立拒绝审计事务完成；回放 `meta.original_request_id` 取该字段，`meta.request_id/server_time/replayed`按当前请求重新构造。只保存业务data/状态码及该标识，不存整个旧meta、Token或凭据。对应列及成组约束已在v2设计修复并复审；运行验证另行记录。

## 可触发错误与验证责任

各操作response已收窄允许的code，不要求为它不可能发生的错误制造用例。以下是具体触发依据；实际HTTP实现后才执行负向契约与模块自测。

| HTTP / code | 触发依据 |
| --- | --- |
| 400 INVALID_JSON | 有JSON请求体的入口收到语法错误JSON |
| 400 SECURITY_INPUT_REJECTED | 明确攻击模式出现在仅允许ID/枚举/排序等选择器位置，或禁止控制字符；规则必须精确、脱敏留痕，不能把普通标题引号判攻击 |
| 401 AUTH_REQUIRED / TOKEN_EXPIRED / TOKEN_REVOKED | 缺Token、超时、已撤销；登录错误账号或口令统一INVALID_CREDENTIALS，避免确认账号是否存在 |
| 403 PROJECT_ACCESS_DENIED / ACTION_FORBIDDEN / SERVICE_SCOPE_REQUIRED | 非项目成员、角色/任务责任人不符、owner自审/批准代码、评估创建者自审、人类Token调用内部服务入口或服务范围不符 |
| 404 RESOURCE_NOT_FOUND | 已授权范围内资源不存在；跨项目已知引用拒绝403且不回显其他项目数据 |
| 409 VERSION_CONFLICT / STATE_CONFLICT | 不同请求争抢旧任务版本；当前状态没有该出口；失败不得更改任务 |
| 409 IDEMPOTENCY_CONTENT_CONFLICT / IDEMPOTENCY_IN_PROGRESS | 同键内容不同，或原请求PROCESSING尚未完成 |
| 409 DEPENDENCIES_UNSATISFIED / DEPENDENCY_CYCLE | 开始/回开发/返工时依赖未全交付；依赖变更形成环 |
| 409 DEPENDENCY_EDIT_LOCKED / ASSIGNMENT_EDIT_LOCKED | 已开始后的依赖/负责人编辑；仅待受理及从待受理阻塞允许修改 |
| 409 REVIEW_NOT_PASSED / REVIEW_BASELINE_MISMATCH | 引用未通过、非最新或旧交付/评审轮次的评审/审核对象 |
| 409 RELEASE_APPROVAL_REQUIRED / ASSESSMENT_BASELINE_MISMATCH | 预案未批准，或评估版本/当前排期版本/交付轮次不符 |
| 409 LAST_MANAGER / MEMBER_IN_USE | 移除最后经理，或移除仍负责活动任务的成员/其开发角色 |
| 409 NOT_ELIGIBLE_FOR_ESCALATION / SCHEDULE_VERSION_CONFLICT / RULE_VERSION_CONFLICT | 服务端时刻尚未触发、任务已终结，或扫描携带过期排期/规则 |
| 413 PAYLOAD_TOO_LARGE | 有body入口超过1MiB；中间件/反代须输出约定错误，不能由未统一的默认HTML替代 |
| 422 PARAMETER_INVALID | 类型、枚举、未知字段、范围、重复模板ID、缺必要字段等结构约束失败 |
| 422 EVIDENCE_REQUIRED / TIME_RANGE_INVALID | 通过项无证据，阻塞/解除/决策缺依据，或结束不晚于开始 |
| 422 DEPENDENCY_SELF_REFERENCE / OWNER_NOT_PROJECT_DEVELOPER / ACCOUNT_NOT_INITIALIZED / CAPACITY_REFERENCE_INVALID | 自依赖、负责人无本项目开发角色、账号未初始化、产能引用非本项目成员 |
| 422 CONTRACT_INVALID | 契约校验入口的候选主请求不符合对应结构或时间/固定集合约束 |
| 429 RATE_LIMITED | 仅登录的真实限流器：默认同源IP+账号每进程60秒10次，附Retry-After；多进程不冒称全局限流 |
| 503 DEPENDENCY_UNAVAILABLE | MySQL/必需持久能力不可达；MQ故障而outbox已提交不属于该HTTP失败 |
| 503 AUDIT_UNAVAILABLE | 拒绝审计独立提交失败；audit_id=null，不伪称已留痕，脱敏请求ID关联故障告警 |
| 503 TRANSACTION_UNCERTAIN | 提交确认丢失，不能断言成功/回滚；客户端沿用同键查询/重试恢复 |
| 500 INTERNAL_ERROR | 未预期异常的统一脱敏兜底；不输出堆栈、SQL、原始body、Token或Pydantic错误input |

SQL注入防护始终依赖参数化查询、整数ID及排序白名单；明确选择器攻击拒绝并记录。自由文本可含正常引号和SQL讨论，不能依赖关键词黑名单替代参数化。所有拒绝路径的安全记录需排除口令、Authorization和完整原始body。

C4修订：每操作 `x-business-error-codes` 等于其response允许code扣除通用认证/输入/基础设施错误的集合；`x-error-cases`逐码提供适用HTTP及触发条件，并与response的code枚举精确一致。GET和只读契约校验没有幂等头/幂等错误。`/dictionaries`没有项目范围、资源ID或可验证输入，不声明PROJECT_ACCESS_DENIED、RESOURCE_NOT_FOUND、422；403 ACTION_FORBIDDEN仅用于已识别服务身份访问人类专用入口，不伪造项目拒绝。

所有计划先验证共享UtcTime的数据库时间域，再比较起止；只读契约校验与写入使用同域，不能只因0001/0999年的起止有序就判为有效。升级事件完整包含负责人和全部有效经理，不截断、不新增人数上限；recipient_ids不设maxItems，handled_count为0～4294967295，创建响应及历史分页嵌套共用该事件Schema。事件分页大小100是每页事件数，不是项目人数或单事件收件人数上限。

## 三个真实性能入口

| 测量类 | 入口 | 测量到哪里 |
| --- | --- | --- |
| 任务流转 | `POST .../tasks/{task_id}/transitions` | 反代、鉴权、幂等/守卫、CAS、任务和成功审计提交后的完整HTTP往返 |
| 契约校验 | `POST .../projects/{project_id}/contract-validations` | 鉴权、归属、对应主请求真实Schema及跨字段验证；不执行写入或业务状态守卫 |
| 升级通知 | `POST .../internal/projects/{project_id}/tasks/{task_id}/escalations` | 服务鉴权、规则/版本/业务去重、事件+outbox+审计持久提交；202不表示消息送达 |

使用约40项目/6000任务/9000依赖/15000评审决策的合成数据，独立发压端经真实反代及鉴权访问。三类分组统计，400并发稳态10分钟，P95目标270ms、吞吐至少1000次/分钟，预热另计。有效任务写、查询、幂等重放和预期拒绝分别统计，不能用缓存重放或固定成功冒充有效写。消息投递、消费、降级与恢复延时另测；队列断开时API成功持久化事件不算已送达。首次升级事件与计数、task.version同增；重复业务事件不增加，通知已读/处理仅notification.version。尚未编写发压脚本或取得任何结果。

## 配置扩展与版本生效

规则返回版本化数组：level/label、相对截止秒起止及包含边界、recipient_kinds、priority；最高优先级匹配，扫描间隔范围5～3600秒，v1值60。新评审项或升级规则只需集中配置及至多一个解释模块，不改固定枚举/DDL；必须先记录原值、新值、生效时间、影响、决定者并审核发布新版本。范围放宽不自动启用新业务规则。此为可扩展设计，尚无真实变更diff/人日验证。

## 规范自检与待审

实际规范校验使用根 `.venv/bin/python` 的 `openapi_spec_validator.validate`。初稿因共享参数列表导致Idempotency-Key重复，失败输出保留 `../../agents/backend/openapi-validation-failure.log`；修复后实际通过，成功输出在 `../../agents/backend/openapi-validation-success.log`，同时核对operationId/参数唯一、业务写幂等头恰一个及GET无此头。该缺陷由AI草案生成造成，由总协调指出、AI修复，不计为用户人工改码。

仍待审核：审计不可用的持久故障介质、幂等恢复实现、字段/DDL与API一致性；证据内容真实性与SHA真实作者仍是明确的机器核验限制。尚无产品代码、HTTP验证、集成、独立验收、覆盖率或性能结论。

## CONTRACT-v2 修复自检

原审核 `reports/reviews/design-v1-717cd65ef73560fde7ff5bca2821c9fe2b20d68a.md` 的不通过结论原样保留。新增可重复运行 `.venv/bin/python agents/backend/validate_contract_design_v2.py`：真实FormatChecker检查0001/0999拒绝、1000/9999边界接受和≤6位微秒；校验101名收件人的事件、创建/历史嵌套及UINT32计数域；逐操作检查错误注解、response Schema、HTTP、触发条件和只读无幂等错误。修复前后的输出另存本岗 `contract-v2-before-fix.log` / `contract-v2-validation.log`，不覆盖v1证据。这些是设计/Schema验证，不是业务HTTP、MySQL或调度运行测试；仍须新SHA复审，不能据此宣称冻结或产品通过。
