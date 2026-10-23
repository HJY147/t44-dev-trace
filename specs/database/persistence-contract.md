# 持久化契约 v1.1人力生命周期演进

本次只同步D005/D006与[已审RFC](../changes/capacity-lifecycle-v1.1.md)的存储语义，实际派工ROLE-database-CAPACITY-V11-CONTRACTS-v1，操作者数据库岗AI。旧1.0.0由父提交`ae60dc3`及[原11项冻结摘要](../../records/spec-freezes/v1.json)保留；本文件和[字段字典](field-dictionary.md)的1.1内容/摘要显式变化，不回写旧manifest或历史验收。最终1.1.0权威/运行API元数据由后端同步，新freeze父链由总协调生成，本轮不声称已完成冻结或产品实现。

结构仍18表226列，不新增列/表/trigger/魔法码；[schema.sql](schema.sql)和打包DDL SHA256仍为`c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4`。既有MySQL/checker修复及原实测不重写，本轮只做文档静态对照，不重跑全套/coverage。MySQL8.4/Python3.12/FastAPI同步/SQLAlchemy2+PyMySQL基线不变。

## 责任与输入输出

- 后端服务拥有鉴权、项目角色、状态机、JSON语义和业务事务编排；持久化模块只执行参数化SQL、锁、CAS、原子写入，不提供“直接改任意状态”门面。
- 持久化输入为已解析的主体、operation_id、请求ID、规范化请求哈希、幂等键、路径项目/资源ID、expected_version及领域命令；禁止口令、Token、Authorization头进入哈希原文、快照、审计或事件。
- 输出为已提交结果快照、成功审计ID和事件ID；失败返回领域错误/冲突，SQL驱动异常不得直出。普通业务ID范围1～4294967295，版本1～2147483647。
- API时间先通过共享UtcTime Schema、FormatChecker和语义校验：仅UTC Z，年份1000～9999，小数秒最多6位，真实范围1000-01-01T00:00:00Z～9999-12-31T23:59:59.999999Z；所有计划、响应和只读契约校验同域。持久入口再次验证可存域后将已确认UTC的aware值去时区存DATETIME(6)，读出补UTC序列化Z，不静默截断小数/年份或接受偏移区。越界输入返回约定422参数/时间错误，拒绝审计遵循独立事务。扫描时间加减用同域饱和上下界/比较，不能在边界溢出后写坏时间。每条连接固定 `time_zone='+00:00'`、严格SQL模式、`READ COMMITTED`；不可依赖宿主时区或默认隔离。小时用Decimal转换四分之一小时整数，禁止float截断。
- MySQL错误1062按命中约束区分幂等竞争/升级重复/消费重复/真实参数冲突；1213死锁与1205超时只有限重试完整事务，保留原key/hash；提交结果不明返回503 `TRANSACTION_UNCERTAIN`，先查询原key恢复结果。

## 四种版本及有效证据

| 计数 | 初始 | 递增/重置 | 用途 |
| --- | --- | --- | --- |
| task.version | 1 | 每个成功的任务关联写+1，包括评审、评估、依赖、负责人、改期、升级；重放不增 | API CAS，禁止客户端指定新值 |
| task.schedule_version | 1 | 改期及回滚返工+1 | 扫描去重与上线评估有效基线 |
| task.delivery_cycle | 1 | 回滚返工+1 | 一次交付/回滚周期，与排期版本分开 |
| task.review_cycle | 1 | 评审拒绝返回开发+1；返工时重置1 | 与delivery_cycle组成完整代码评审基线 |

- 评审发布只插入不可变reviews（version恒1），更新latest_review_id及task.version；不自动迁移状态。审核对象必须匹配任务当前artifact_revision、delivery_cycle、review_cycle及模板版本；审批只能引用本轮最新评审。
- 代码评审发布者及批准者不得为task.owner；预案评审者不得为assessment.created_by。仅校验系统责任主体，不声称能从SHA自动证明真实代码作者。模板八个稳定section_id和有效item_id清单按template_version精确覆盖；item_id形状R加2～3位数字，不能把R01～R10硬编码进DDL。
- reject_review清空latest/approved review、approved assessment及提交SHA；开启下一review_cycle，旧评审保留。rework清空同类批准，写新排期diff、返工决定，再检查依赖并进入开发。
- 普通阻塞/解除只改version并保存/清除阻塞字段，不自动增加其他三个计数；解除依据写成功审计。改期不撤销同轮代码评审，但清空approved_assessment引用。
- release_assessments文档内容及rollback_plan创建后不可变；审批只一次从pending_review到approved/rejected，version从1到2；再次提交文档创建新ID，rollback_plan_version按task全历史单调+1（锁task后分配）。
- 上线评估绑定schedule_version和delivery_cycle，符合API；交付还同时校验当前代码评审、当前评估终态/版本、四视角证据及预案。终态评估不可修改，避免历史decision引用漂移。
- decisions不可变；delivery/rollback记录当次delivery_cycle，rework记录新delivery_cycle；type1.target_version映射API release_version。unique(task_id,delivery_cycle,type)防止同一轮重复拍板；决定只能由具有经理角色的实际主体提交。

## 锁序、项目权限及依赖图

1. 先鉴权并验证当前项目参与范围及请求格式；重放仍须当前具备项目访问权，不能因历史快照绕过撤权。
2. 每个写事务先对当前auth_sessions行FOR SHARE并重核有效期、revoked_at及主体active，再锁自己的idempotency_requests行。需要项目级不变量的操作再锁project行；随后按成员user_id升序锁相关membership，再按task.id升序锁任务；最后按ID锁评审/评估/其他子记录。禁止拿到task后补取project或反向取另一任务。会话撤销CLI只对session行FOR UPDATE，不反锁业务行；在途已授权写与撤销以锁提交先后线性化。
3. 同项目依赖新增/删除持有project `FOR UPDATE` 到提交，读图、验证同项目/自依赖/环、写边与task CAS同事务。A→B和B→A不能同时通过互不相见的查环。
4. start、unblock回到开发、rework同样先project锁；在同一锁序内锁目标及全部前驱任务，确认每个前驱state=6，再检查expected_version并CAS目标。前驱之后回滚不自动修改其他任务；该次开始的审计保留当时证据。
5. 负责人/依赖只允许state=1，或state=3且blocked_from_state=1；其余409，拒绝留痕。1.1的changeTaskAssignment在锁成员/任务前新增project锁，与迭代capacity变更串行。依赖编辑与CAS、审计、outbox同事务，禁止半套边关系。
6. 成员角色/撤销先project锁，再 `FOR UPDATE` 锁成员和需检查的负责任务。撤销经理或经理角色必须仍有至少一个active经理；撤销active负责人或开发角色若仍负责state=1–5或7的任务则拒绝；该成员保护不能与1.1仅保护1–5的迭代capacity规则混同。成员仅active=0软撤销，保留外键历史。
7. 除1.1四类人力路径和原本需要project锁的操作外，普通单任务写不必全项目串行，但在task锁前，对操作者/负责人/此次快照经理等相关membership行按user_id顺序 `FOR SHARE`，重验active/roles；成员变更与并发写以锁的先后顺序确定权限。普通路径不得事后补取project锁。
8. 项目创建与创建者经理成员记录同事务。roles_mask为内部位集合，API仍ProjectRole数组；所有查询显式join active membership过滤project_id，经理身份不绕过过滤。通知再限制recipient_id=当前主体。

认证辅助数据仅增加service_accounts与auth_sessions：稳定服务主体ID与用户ID分scope；token只存SHA-256摘要及过期/撤销，服务会话存project_ids/scopes白名单，个人会话实时查项目成员。服务scope不等于经理角色。登录仅首次返回高熵不透明token；日志、命令行参数和URL禁止token原文。

账号初始化持久层公开边界 `initialize_user(hash_only)` 必须解析并验证合法Argon2id编码/参数，拒绝非hash或不合法hash，独立提交脱敏安全审计 `SECURITY_INPUT_REJECTED`；失败返回503且不声称已记录。CLI接收口令、在内存哈希后调用该入口属于正常流程；审计只保存请求ID与原因分类，不保存原口令或原hash。DDL的hash形状CHECK只是额外防线；任意恶意直连不被宣称能自动生成独立审计。后续自测必须从真实持久层入口触发此拒绝路径。

## 人力生命周期1.1事务契约

人已选择的范围见[D005](../../records/decisions/D005-capacity-lifecycle-adopted.md)/[U015](../../records/prompts/U015-original.md)、[D006](../../records/decisions/D006-rolled-back-capacity-adopted.md)/[U016](../../records/prompts/U016-original.md)及[限定设计通过报告](../../reports/reviews/capacity-v11-design-bbc4be681f19a386fbca40baf97a63ab902b3f89.md)。这是1.1新增守卫，不倒称旧1.0已有全部行为。

| 操作 | 同一项目锁内的服务层核对 |
| --- | --- |
| createTask | 沿用已有owner匹配迭代capacity守卫；负责人必须是本项目有效developer且在当前所属迭代登记有效工时 |
| changeTaskAssignment | 新增project `FOR UPDATE`；保留原角色/允许状态/版本守卫，目标有效developer检查后核对当前迭代capacity |
| changeIteration | 同项目事务内重读本迭代全部任务，按id有序锁定相关任务；新capacity各项有效/唯一，且包含全量state=1–5任务owner，不只核对旧/新人员差集 |
| transitionTask action9 rework | 保留原经理、状态/版本/证据/排期/依赖守卫，在CAS前重验当前owner是有效developer且已补回当前迭代capacity；state7尚未返工时允许移出capacity |

1. 四操作统一session `FOR SHARE`/idem→project `FOR UPDATE`→相关membership按user_id升序→相关task按id升序；依赖任务/子记录继续原锁序。获得project锁后读取当前capacity及受保护owner，不使用锁前缓存或另一事务预检结果，项目锁持有到提交/回滚。assignment不得先拿task再补project。
2. capacity JSON不增加跨行CHECK、trigger或外键；数据/SQL能力仍由既有持久门面提供，集合及有效developer校验由后端服务在同一事务编排，不隐式创建连接或提前提交。
3. 新capacity保留本迭代state1–5全部owner；6/7可移出，7进入2前先补回有效人力再按原证明/版本/依赖条件返工。项目成员/开发角色移除仍保护1–5+7；D002转派只允许1或从1进入3，不新增状态出口或预算算法。
4. 新人力失败复用422 `CAPACITY_REFERENCE_INVALID`及原稳定审计码30；不改变原权限、状态、版本等错误优先级。失败不递增业务版本、不写plan/plan_version、task/cycle、decision或schedule_changes，主事务先回滚释放，再按下文独立拒绝事务记录审计和原key错误快照；审计失败仍503。
5. 成功的业务变更、审计、outbox和幂等快照仍一次提交。已有COMPLETE成功key先回放原结果，不因当前capacity变化重跑新增守卫或再增版本；访问权重验及同key内容冲突规则不变，提交不明仍沿原key恢复。
6. 并发与移除目标人capacity竞争时，若移除先提交，后续向该人创建/转派/返工按最新快照拒绝；若激活任务先提交，后续移除该state1–5 owner拒绝。先合法将A的可转派任务交给已登记B，再移除不再拥有受保护任务的A，可以依次都成功；不把所有跨资源安全更新一概限制为一次成功。仅为锁原理契约，本轮未做真实竞争测试。

API路径保持`/api/v1`，契约信息版本由后端同时更新`info.version`与`Meta.contract_version.const`至1.1.0；本岗不代改权威/运行OpenAPI。新版本清单须另记父1.0及差异，不能通过改写原11hash制造“旧冻结未变化”的表述。

## 请求幂等、CAS与成功事务

- 作用域唯一 `(actor_kind,actor_id,operation_id,idempotency_key)`；user/service分开。actor_kind=2的数值ID由部署分配，不与用户混淆。operation_id用OpenAPI稳定operationId，哈希为SHA-256的32字节，内容包括方法、路径资源ID和完整规范化body（含旧expected_version）；JSON键排序、数字规范化及缺省/null语义由后端统一实现。
- 登录、Token签发和只读查询不进入幂等表。API key长度16～128、ASCII区分大小写；scope内相同key异哈希409 `IDEMPOTENCY_CONTENT_CONFLICT`，不得返回旧主体或旧项目数据。
- 短独立事务原子INSERT PROCESSING(status=1)、owner_token、lease_until，response_request_id必须NULL；唯一冲突后锁行比较hash，COMPLETE(status=2)直接回放原HTTP/body，不再验证旧task.version。PROCESSING未完成返回409 `IDEMPOTENCY_IN_PROGRESS` + Retry-After；客户端继续原key。
- 过期PROCESSING只能通过 `SELECT ... FOR UPDATE` 等旧主事务结束后，CAS旧owner_token接管并换新token/租约；旧worker在业务事务开始及提交前校验token。主事务从开始到提交持有幂等行锁，租约到期本身不能让第二worker并行提交。
- 主事务：锁幂等行并核owner → 按上述锁序鉴权/读基线 → CAS task (`WHERE id=:id AND project_id=:pid AND version=:expected`) → 领域子记录/排期diff/decision → success audit → outbox事件 → 幂等COMPLETE快照及response_request_id → 一次COMMIT。response_request_id写生成本次已保存结果的当前处理请求ID；若租约接管，最终完成者写自己的处理请求ID，不沿用首次认领者ID。任一步失败均ROLLBACK；CAS affected_rows必须恰1。
- 不同key持相同expected_version竞争：只有第一次CAS成功，第二次409 `VERSION_CONFLICT`；成功更新与审计/outbox不允许分开提交。只读快照回放不新增成功审计或事件。
- 成功/拒绝快照是当时结果，只存业务data/错误及HTTP状态，不保存旧完整meta或凭据。初次处理 `meta.replayed=false`，当前meta.request_id为当前请求，meta.original_request_id可NULL；重放时 `meta.replayed=true`，当前request_id/server_time重新生成，original_request_id必须读取COMPLETE行的非空response_request_id。此来源不依赖响应data是否有audit_id，也不靠审计反查。前端再GET最新任务，不把旧快照当当前版本。v1不自动清理完成记录；至少保留7天的想法尚未获总协调最终采用，不能默默过期使同key再次执行。

## 拒绝事务、审计与503

1. 非法迁移、版本冲突、依赖拒绝等先ROLLBACK主事务，关闭/释放该Session持有的连接和锁。不得在“已失败但未回滚”的Session继续写，SAVEPOINT不能代替独立拒绝提交。
2. 新建独立SQLAlchemy Session/连接、独立事务（业务连接已释放），锁原幂等行核owner，写outcome=2的audit、错误快照及生成此已保存拒绝结果的当前response_request_id后把幂等行置COMPLETE，一次提交。该ID与成功路径采用同一完成时语义，租约接管亦不固定首次认领ID。不写task、成功审计、outbox或业务子记录；before/after不得伪造发生了变更。
3. 拒绝审计失败：独立事务也ROLLBACK，返回503 `AUDIT_UNAVAILABLE`；不能仍报“409已记录”。保留PROCESSING供租约恢复，必要运维告警仅含request_id及脱敏错误。部署的恢复介质/告警方式仍待确认，不能宣称审计已持久化。
4. 鉴权/格式错误发生在幂等占位之前，可独立写安全审计而不缓存敏感请求。未知项目/资源ID写attempted_*，resolved project_id/task_id可NULL；不以外键失败丢掉拒绝记录，也不向越权者泄露记录。
5. audit的reason_code为tinyint集中映射API ErrorCode；actor_id不设users外键，以容纳service与未识别主体。审计before/after是字段级脱敏白名单，禁止保存密码/Token、原SQL或用户恶意输入全文。SQL只走参数绑定；可疑输入的识别和拒绝由后端完成，不声称数据库识别一切注入字符串。

## 扫描、升级与唯一性

- 每60秒扫描，固定本轮cutoff_at为UTC；按ID keyset分页覆盖state=1～5且planned_end≤cutoff+24h。阻塞继续计时；同一任务只计算本时刻最高级别：`end-24h ≤ now ≤ end`临期1，`end < now < end+24h`超期2，`now ≥ end+24h`严重3。
- API scan_run_id UUID映射scan_runs.run_key(BINARY16)，表PK仍统一INT；升级记录scan_run_id关联内部PK。run状态1running/2completed/3interrupted，heartbeat/cursor/计数留痕，不靠APScheduler内存游标保证正确性。
- 单任务升级短事务按会话/幂等/成员/任务锁序重验state、expected_version、schedule_version、有效rule_version；snapshot当前owner及所有active经理，临期只owner；去重recipient列表。
- 同事务创建outbox(event_type=2)、escalation_events、更新task.version/escalation_count、成功审计及幂等结果。硬约束 `UNIQUE(task_id,schedule_version,level)`；rule_version不进入去重键，规则更新不对同排期同级再轰炸。
- 先同key重放，再验证task expected_version；不同key持旧版本409。版本有效但唯一键已存在时回读原event，返回created=false及当前task_version，不增加task.version/count，不创建额外outbox，仅完成本请求幂等快照和去重审计。唯一冲突须回滚新建临时outbox等副作用，不能留下无ledger的额外通知。
- DDL level只约束1～255，实际合法值/匹配窗口/优先级/收件角色由当前有效版本规则决定。v1仍仅原3档，不授权新业务级别。解释器按规则数组取最高priority；不能写固定switch(level=1/2/3)迫使新增规则改DDL/API/前端。扫描候选时间窗口也从规则配置推导，不固定未来必须24h。
- 规则配置必须带version/effective_at/decided_by；scan_runs和escalation_events保存完整rule_snapshot及SHA-256 rule_hash。模板以不可变配置文件归档原文、版本/生效/决定者及hash，reviews保存template_version/template_hash。配置变更审计保存旧/新值、影响范围和决定者；文件归档目录/部署加载由后端与部署冻结，不新增独立规则库。SHA对明确的UTF-8原文计算，不能把JSON重排后的hash冒充原文hash。
- 任务改期只增schedule_version并写before/after；旧ledger与通知保留，新排期允许新级别事件。扫描cursor仅在对应业务调用结果确定后前移；崩溃后可从持久游标续扫，也可重开run从0重扫，唯一约束保证不重复升级。
- 一轮扫描O(N+E_r)，N为本轮候选任务/查询访问量，E_r为实际收件人展开；每页B条，内存O(B+R_max)。幂等/消费查重通过唯一索引；不得据此宣称270ms/P95或400并发已经达到。

## outbox、MQ confirm与fallback边界

- outbox.id就是稳定event_id；event_type=1 business.changed，2 escalation.created，schema_version=1。升级payload含task/schedule/rule/level/UTC时间、标题正文，recipients是去重后的用户ID快照；不包含Token或口令。普通变更事件recipients=[]，不凭空新增用户提醒需求。
- 事件status：1pending，2leased，3confirmed，4fallback。业务事务只写pending；发布者短事务 `FOR UPDATE SKIP LOCKED` 领取并写lease_token/lease_until，提交后才调用RabbitMQ。不能一边持业务事务锁一边等待网络。
- 发布使用durable exchange/queue、persistent消息、mandatory路由与publisher confirm；只有confirm ACK且未被return才在新的短事务锁该outbox、核lease_token并置confirmed(status3)。网络ACK不等于DB已标记、也不等于消费者已提交。
- 发布超时/断连可能已入队，不能假定“未投递”。升级事件转fallback时，在一个DB事务锁outbox，按recipient顺序插入缺失notifications(fallback=1)，保留已存在通知及read/handled字段，最后置status4、fallback_at，清空租约。失败则整个fallback事务回滚，记录仍待恢复，不能标成已降级。
- 消费者先验证event_id/schema及数据库权威event，锁outbox；若status4，只核对已存在的完整fallback通知后ACK，不再提醒。其余状态对快照收件人插入notifications(fallback=0)，同事务提交后才basic_ack。重复消息命中 `UNIQUE(event_id,recipient_id)` 后回读已有行，禁止REPLACE或清空已读/处理状态。
- consumer与fallback都先锁同一outbox，再按recipient_id升序处理，因此不会两套通知并存。若confirm响应丢失但consumer先提交，fallback只补缺失人并标记event降级；已存在通知保留原fallback值。迟来的consumer/ACK不得把status4改回confirmed。
- confirmed后消费者迟迟未完成时，恢复者核对recipient快照与通知集，可同样事务补缺失站内待办并将status3→4；防止只凭publisher ACK宣称用户收到。何时触发超时与重试阈值由消息/调度配置版本决定，当前待消息岗确认。
- 过期leased恢复依然核token并加行锁；可重新投递原event_id，消费唯一键兜底。已fallback为终态，MQ恢复不重发同event；新event正常投递。非升级business.changed发布失败保持pending/重试，不伪造无收件人的站内待办。
- handled_at/handling_note/evidence与read_at分别写入、各次成功更新notification.version；处理通知不解除任务阻塞、不改变task.state。消息/调度代码必须通过数据库门面，不自行建第二套通知表。

## 迁移、运行与审核门禁（v1历史设计记录）

以下“本轮/当前未运行”指1.0设计轮当时状态，保留原记录；既有运行证据见模块记录。本次1.1文档同步不执行DDL或重写MySQL/checker验证。

- schema.sql是可供MySQL 8.4执行的完整DDL提案，选择空schema后按文件顺序建18表和补循环外键；本轮未执行。没有DROP/数据库创建/种子数据/DDL事务回滚承诺。
- SQLAlchemy模型必须逐字段实现本规范并走评审，不得在应用启动时create_all偷偷迁移。迁移另行派工、逐表审核、备份和恢复预演后进行；InnoDB、外键检查和CHECK不可关闭以绕过错误。
- 外键统一整数类型，只引用显式主键/唯一索引；默认RESTRICT，不物理删除有业务历史的用户/项目/任务。列级CHECK只守单行范围，不替代状态机、查环、角色、JSON证据完整性和基线校验。
- 需真实验证后才能放行：MySQL8.4建表/SHOW CREATE TABLE及信息模式检查、参数化/CAS/拒绝独立连接、同key争抢/租约接管、双向并发加边、撤权/撤最后经理、扫描重启、MQ模糊确认/fallback/consumer竞争、存量与恢复、性能。当前这些均未运行。
- 当前跨岗确认来源与GitHub链接记在本岗日志及handoff；消息/调度事务和阈值仍需相应责任岗确认，最终字段与错误码取舍由总协调组织用户/授权责任人审定。本稿不得自行记为“审核通过”。

技术语义参考：MySQL 8.4 [CHECK约束](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html)、[外键约束](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html)、[日期时间类型](https://dev.mysql.com/doc/refman/8.4/en/datetime.html)与 SQLAlchemy 2 [事务管理](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)。仅用于校核设计语法与事务概念，不是本项目已运行的证据。
