# 契约校验只读 UoW 合并候选

状态：内部实现设计草案，待总协调/审核岗比对准入；未应用、未运行，不改冻结规格。依据源 c83f627331acf43fb508fac7e16525a48c0389ab（生产字节仍为绿源4c20f32）。本轮仅静态源码分析和未应用补丁；原诊断03整体RuntimeError/exit1保留。

## 范围与证据

仅 `POST /api/v1/projects/{project_id}/contract-validations` / `validateContractPayload`。其余17个只读操作、login、logout、所有幂等写入及后台进程保持原路径；不泛化全GET，不改池大小、pre_ping、Schema、鉴权规则或冻结14文件。

03诊断每请求平均2次Engine.connect、8.667次SQLAlchemy游标事件；并发增长时连接获取和游标墙钟增长，Runtime线程CPU较稳定。只支持先减少可静态证明的重复往返，不能断言poolwait或数据库锁是根因。原transition/escalation正式P95不因本候选得到解决；没有性能达标或源码规模收益。

## 源码调用链与SQL账本

| 位置（本依据源真实行号） | 实际行为 |
|---|---|
| api.py 203–213、215–229 | middleware先完整收请求流，保存最多1MiB；之后同步endpoint创建Call并调用Runtime |
| runtime.py 40–43、224–227 | 第一UoW authenticate，退出提交/关闭后才validate |
| identity.py 45–85 | 成功人类项目鉴权依次读auth_sessions、users、project_members、projects，各1 SELECT；无身份缓存 |
| runtime.py 235–252 | 本接口不claim幂等；第二UoW再次完整authenticate，仍为普通非锁定读 |
| application.py 107–129 | category1不读任务；category2/3按body.task_id读tasks一次；仅计划纯计算/返回，不写业务记录 |
| rows.py 93–103、150–193 | get委托一次rows；每次rows物化dict并关闭SQLAlchemy Result，不生成第二次隐藏业务查询 |
| uow.py 21–34、87–104 | 每次with新Session；begin是逻辑事务，首个实际SQL才需要连接；成功commit，异常rollback，finally close |

成功category1当前4+4=8 SELECT；category2/3当前4+4+1=9；1:1:1平均8.667，与原始指标一致。候选一次authenticate后原dispatch，预期4/5/5（平均4.667）和1次acquire。**这是静态预测，尚无候选执行结果。** 拒绝路径另需独立审计事务，不能用成功账本覆盖其SQL/连接数。

Engine.connect观测包含QueuePool checkout/可能等待、pre_ping、可能重连/首次TCP/TLS/驱动建连和初始化，不能拆成纯poolwait。engine.py 65–76在每新物理连接通过DBAPI cursor执行3条SET；89–108启用pre_ping、READ COMMITTED、LIFO及rollback-on-return。当前安装SQLAlchemy pool/base.py 1347–1384显示fresh连接跳过ping、复用连接先_do_ping_w_event再触发checkout事件；mysql/pymysql.py 149–155调用DBAPI ping；PyMySQL connections.py 596–630发送COM_PING并读OK。该ping不经SQLAlchemy before_cursor_execute，所以8/9不是总网络roundtrip数。Session.commit/rollback、连接重置也不属于955的SQL游标事件；驱动初始化SET同样绕过该事件。不得将“少4 SELECT”换算为确定延迟收益。

## 选择的最小候选（不新增只读S锁）

在Runtime现有try/except内，只为此operation走一个自有with：普通RC authenticate → 原validate → 使用now()复核会话expires_at → 原business.dispatch → 退出with → 原wire/status返回。API最终envelope/Schema检查保持，内层schema_version=1.0.0、meta.contract_version=1.1.0保持。成功无业务、audit、outbox或idem写；拒绝仍按原独立审计写入。

未应用的可审补丁：agents/backend/drafts/contract-validation-read-uow.patch。只有runtime.py：8行增加/1行替换，净+7物理行，282→289；其中导入now替换一行、单接口分支增加7行。receipt记录原文件和补丁SHA。当前生产实际diff=0；该候选不减行，不能拿删除roundtrip当3500–5100源码范围通过。没有修改Identity、Rows、UoW或公共存储接口。

本阶段先提出session/member FOR SHARE以把在途读和撤销强线性化；随后总协调指出冻结仅要求撤销提交后新请求拒绝，强锁属于写路径。审核岗同意无锁单UoW更贴合最小范围，因此撤回新增S锁方案。这是备选收敛，不是已发现安全漏洞或用户改码。

## 撤销、快照与错误顺序

1. 每个新请求都从数据库普通SELECT实时查session、主体active、项目成员、项目，不复用前一请求Call/身份。READ COMMITTED各SELECT使用各自语句快照；session撤销对session SELECT判定、成员撤销对member SELECT判定。不能声称四表同一原子授权快照或整个HTTP响应与撤销强线性化。
2. session撤销提交后才开始的新请求必须401 TOKEN_REVOKED；成员撤销提交后新请求必须403 PROJECT_ACCESS_DENIED。已在途、已通过鉴权的读取允许完成：删除第二次普通鉴权会少一次观察校验期间撤销的机会，这是需明确准入的在途语义；不承诺原双读所有竞态输出逐一相同。客户端连接复用不允许复用身份结果。
3. 无新session/member/project/task锁，不与CLI session FOR UPDATE形成等待链。原成员写project X→members→tasks和写session→idem→必要project→members→tasks完全保留；该只读分支不调用locked_scope、不后补project/task FOR UPDATE/SHARE。业务dispatch仍只有普通tasks SELECT。撤销可以在暂停的在途read期间提交，不能为了测试绿色让writer等待read。
4. 原鉴权/项目范围先于输入错误、服务身份继续拒绝。validate失败即抛原错误，不执行后续到期复核；valid输入后expires_at与fresh now比较，不用Call.clock。到期保证仅到复核点，不是提交或发送瞬间永不跨过到期。初始已过期仍先于422；鉴权后跨过期且输入非法仍保留原参数错误先发生。
5. users.active仍在authenticate首次真实查询中验证。当前accounts.initialize_user和seed仅创建active=1；CLI init-user/service-token与session撤销没有用户停用更新入口，源中无公开disable账号操作。特权直改数据库不属于当前API/CLI并发承诺；未来增加账号停用入口必须重新审查在途语义，不能把本候选扩为账号缓存。当前即使普通双鉴权也没有锁住身份到响应。
6. Rejected/通用异常/PersistenceError必须先退出该with完成rollback/close，再走现有runtime.rejection新UoW独立审计；不能在活跃只读Session里调用rejection。新UoW/新SQLAlchemy Session不等于必须新物理MySQL连接，pool允许复用连接但事务必须独立。CommitUncertain保留现有503映射；审计不可用仍503 AUDIT_UNAVAILABLE，原脱敏日志策略不变。
7. 网络请求body已经在打开UoW之前完整读取。UoW内只有本地解析/Schema/参数检查、同步数据库读取及纯计算，不await客户端网络、外部服务或流式发送；wire与最终envelope照旧在退出后执行。代价是数据库连接跨越本地校验CPU持有，合法大输入/并发下可能抵消收益，必须实际测量，不能保证吞吐改善。

## 实现准入后的有意义回归计划（尚未编写/运行）

复用既有tmp/backend/contracts/986_http.py、985_mysql_http.py，不新增编号脚本，不读独立用例。

- 三category真实HTTP正例：严格冻结响应、内层/外层版本和只读计数保持；记录成功1acquire及4/5/5 SQL，失败时不能把审计SQL排除后伪称总计。计数来源需与03一致，同时以Rows记录验证会话/主体/成员/项目各查一次，无statement/参数归档。
- session撤销两种时序，真实MySQL：先撤销提交再发新请求→401/audit；读在authenticate后暂停、另一身份/独立事务撤销相同session并确认已提交，再恢复旧读→允许有效200，之后新请求→401。验证撤销不等待只读S锁，使用事件屏障证明先后，拒绝仅靠sleep猜时序。
- 成员撤销两种时序，真实MySQL：用无受保护任务的reviewer作为reader、另一manager撤销成员，保持最后经理/owner规则不变。先撤销提交→新请求403；旧读鉴权后暂停→manager合法撤销提交→旧读可完成→新请求403。两角色与新旧请求ID区分清楚。
- 参数优先级：未鉴权/已撤销/已过期/非成员/服务token+非法JSON分别保留相应认证/范围错误；有效身份非法壳与非法候选继续PARAMETER_INVALID/CONTRACT_INVALID。已有断言保留，只补此优化路径没有覆盖的组合。
- 到期：在有效auth之后、validate中受控推进服务时间，合法输入跨到期→TOKEN_EXPIRED且不dispatch；非法输入保留原422优先；不以Call.clock旧时间放行。保留初始过期测试，不宣称发送时刻保证。
- 独立拒绝审计：在validate/dispatch注入可标识Rejected或PersistenceUnavailable，记录主UoW exit/closed后才创建audit UoW、新Session且审计持久化；明确依赖故障注入不冒充MySQL真实宕机。独立audit再失败仍503，不能当正常422。
- 写路径守恒：原985项目锁、幂等/CAS、独立拒绝审计、outbox与既有撤销测试原断言保持，全量精确新源CI按正常流程执行；不为本候选另造写事务捷径。

## 后续门槛

本RFC/未应用补丁先交审核岗比对，总协调明确准入后才改生产、追加必要回归及真实MySQL专项。若同源CI通过，再协调独占窗口以相同fixture做短对照；不得自动重跑03矩阵，不改正式400/600/4worker条件。transition/escalation和其P95仍待各自证据。其余只读UoW合并、身份active管理、纯poolwait/DB锁细分均列未来独立范围，不在本轮扩展。
