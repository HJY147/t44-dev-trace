# 公开 F08 后端顺序修复候选

操作者/作者：backend AI。Prompt-Ref：ROLE-backend-ACCEPTANCE-FOLLOWUP-20261025-v1。产品候选提交：`935ab5b93bea788672c2b4a088c79cfeed848954`；本报告是开发交接，不改写独立验收结论。

## 结论和公开事实边界

最初只获F08的409/ASSESSMENT_BASELINE_MISMATCH观察时，不能据此判断错误。在总协调追加公开最小交接后，已知当前有效developer无manager执行action7，收到上述基线错误，冻结断言要求较早的403/ACTION_FORBIDDEN。源码和自行构造的开发HTTP场景能定位该顺序差异。公开报告没有证明越权发布成功，且失败点后的业务不变/审计未验；本轮新开发验证不能补写为原独立F08已完成的后置条件。

## 四权威依据和精准位置

- 原任务书第4节FR-01要求资源/状态/参数等错误按契约区分；FR-05要求评审后发布；FR-06要求拒绝非法及并发迁移且不改任务；第5节安全要求统一权限和拒绝留痕。原docx只读提取，未复制或提交原文。
- `specs/business-rules.md:37`：先鉴权及项目权限、再请求/重放；`:59`：D008只细化原批准引用失败槽，不能覆盖更早权限，批准引用匹配继续原顺序。
- `specs/requirements.md:53-56`：双失效先评估，单批准失效仍原批准错误；任务和请求评估版本等更早校验保留；拒绝不得推进状态、版本或业务历史。
- `specs/contracts/openapi.json:11884-11893`，transitionTask description / x-role-scope：deliver只限manager，不前移覆盖原state/role/代码评审；x-error-cases的ACTION_FORBIDDEN声明有效身份角色不符为403。D008两个错误条件见`:12543-12549`。
- 四份输入hash逐字匹配公开最小交接，见`verification.json`。当前spec开头仍含草稿状态描述；本轮不回写该状态，不把它当新授权或验收结论。

## 定位及窄修

原`Workflow.transitionTask`在解析任务及评估后，于批准id/version不匹配时直接抛基线/批准409；`domain.state_machine.decide:143-167`的state→manager→证据/代码评审→评估/预案/防自审守卫尚未执行。D008的两个409选择本身符合双失效/单失效要求，但该提前拒绝会遮住原发布状态与manager守卫。

候选仅将`backend/t44/services/workflow.py:113-130`该一个失败语句改为限定分支：已存在、归属正确且请求文档版本已验证的action7，若原批准引用不匹配，先要求任务为PENDING_RELEASE，再调用既有`Call.manager()`，再按原D008基线选择409。状态先于manager沿用领域发布分支已有相对次序；没有把所有动作/所有角色检查全局前移。批准引用匹配仍进入原`decide`；任务版本、请求assessment_version、归属校验位置保留。因此本修复不声称所有错误组合均改为role优先。

73个已跟踪`backend/t44`及`frontend/src`文件逐字比较主树，唯一变化是workflow.py；将该单个批准失败语句恢复后整模块AST等于主树。Runtime、认证、幂等认领/完成/重放、CAS、事务、审计、其它动作、契约及DDL未改。创建评估`Reviews:101-106`和改期`Tasks:112-119`清批准引用、评审`Reviews:132-150`写CAS后的评估版本等原逻辑保留。

## 最小开发回归与实际结果

`tmp/backend/contracts/816_acceptance_followup_20261025.py`只使用既有开发HTTP辅助函数；全部项目、任务、评审、评估和改期在内存SQLite中通过自己的API调用产生，无独立私有ID或构造。

| 目标 | 原产品真实结果 | 候选结果 |
| --- | --- | --- |
| 当前未批准评估，developer发布 | 409 RELEASE_APPROVAL_REQUIRED | 403 ACTION_FORBIDDEN |
| 评估批准后改期，developer发布 | 409 ASSESSMENT_BASELINE_MISMATCH | 403 ACTION_FORBIDDEN |
| 改期后合法block到状态3，manager发布 | 409 ASSESSMENT_BASELINE_MISMATCH | 409 STATE_CONFLICT |
| 同状态3，developer发布 | 409 ASSESSMENT_BASELINE_MISMATCH | 409 STATE_CONFLICT |

新4项在旧源码真实4失败，候选4通过。前两项在最终错误码断言之前检查任务/评审/评估/决定/排期变化/outbox全不变、单条持久拒审计、request ID关联、同键重放原结果且不增审计；候选还确认持久reason_code=6。后两项检查业务不变及单拒审计。必要邻接为既有856完整11项，全部通过，覆盖manager双失效→新评估→独立批准→发布、历史重放、仅批准失效、早期版本/归属/缺失及批准引用匹配的state/role/review/baseline顺序。共15唯一SQLite目标，0失败/错误/跳过；没有把重复执行累加。

串行nice10运行约4.4秒，仅开发TestClient/SQLite，零活动SUT HTTP/外部DB请求。Ruff/format按`backend/pyproject.toml`对两文件通过。初选主.venv缺pytest已留`initial-env-no-pytest*`；首次未显式Ruff配置误继承外层命名规则并有格式差异，原日志保留，后用项目配置并格式化测试。旧红长traceback暴露本次内存SQLite临时token，原log/XML已移至本机/tmp专用0700目录、文件0600；提交件仅精确脱敏派生，原始和派生SHA见`before-redaction.json`。首次脱敏标记含尖括号导致派生XML解析失败，已只改为XML安全标记；原件及失败结果不变。后续使用短traceback。

## F11：真实短TTL human token建议，仅代码阅读

现有`cli.py:18-43`没有human-token命令。`init-user:63-87`只建用户；`service-token:130-136`传service_account_id而非user_id，产生actor_kind=2，不能代替人类令牌。`Settings:20-27`允许`T44_SESSION_TTL_SECONDS=60`，更短值非法。真实`identity.login:91-104`校验口令和有效用户，调用`issue_session`以user_id签发actor_kind=1，数据库只保存摘要/created_at/expires_at。

未来由总协调在新获准隔离campaign schema上置备：已有有效human可直接登录，否则先用既有`init-user --username ... --display-name ... --password-stdin`私密建立fixture用户（display-name长度1..100）；在同准确源码的单独一次性认证进程设置TTL60，并显式选择**与待测SUT相同的获准隔离schema**，经真实`POST /api/v1/auth/login`取得token及expires_at。可用`create_app(settings=Settings.from_env(), notifications=None, escalations=None)`配真实MySQL LazyFactory和进程内TestClient（base_url设`https://fixture.invalid`，无网络明文传输）；若建立真实临时监听，须使用TLS并限制只接受登录。不能使用另一schema、手写/修改会话到期时间、mock时钟或service-token。正常SUT认证只比较会话行expires_at与真实UTC(`identity.authenticate:45-63`)，不要求其自身TTL也变成60，故不必重启或修改冻结SUT。等待该expires_at自然过去后，将原令牌作为中性凭据输入交总协调规定的安全通道；不logout/CLI撤销它，因为撤销先于过期检查。普通日志/Issue只记签发/到期时间和不含secret的回执。

环境字段是`DATABASE_URL`（必须mysql+pymysql且指定database）、可选但若给出须同database的`T44_DATABASE`、`T44_SESSION_TTL_SECONDS=60`；不要把带凭据的URL放argv/普通日志。API请求JSON严格只含`username`、`password`，不接受TTL/user_id等额外字段：username长1..64、模式`^[A-Za-z0-9_.-]+$`；password长1..128。登录端点无Idempotency-Key参数，无注册接口。正常200外层`data`含`access_token`（32..512）、`token_type=Bearer`、`expires_at`（UTC）、`user`，不含session_id；`meta`和X-Request-ID可用于无secret回执。所有响应/异常必须在捕获token前后阻止原body/credential被print或pytest长traceback输出；令牌落盘应预留0700目录、用O_EXCL/0600且不进入Git。`auth/me`无需项目归属，适合未来独立执行者在其自选冻结用例中验证凭据类型/到期，但本岗不向独立测试者传递断言或构造。

这是静态可行方案，本轮未建立用户、令牌、认证进程或DB连接，未执行CLI或调用liveDB。若禁止任何额外进程接同schema，可使用现有SUT正常login并等待其原TTL自然过期；代价是等待更长，而不改SUT设置。F11仍NOT_PROVEN，须有获准真实凭据和新独立执行。

## 待项

总协调/审核岗需审准确源码，再组织MySQL/完整CI和新独立复测；本岗未自行触发workflow。原F08 FAIL、F11 NOT_PROVEN和公开总结果保留。活动C8、性能数据和.runtime未触碰，运行中的400client/600s不受本补丁替换。原产品规模6326超过5100的失败仍开放，本轮未新cloc且新增守卫不声称节省。相邻missing assessment现走原RELEASE_APPROVAL_REQUIRED，而OpenAPI RESOURCE_NOT_FOUND条件泛指请求引用不存在；D008又明确missing原分支不变，本轮不擅改该既有语义，作为独立规范澄清项交总协调，不归因为F08。
