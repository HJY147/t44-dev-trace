# backend 初始化模块报告

## 任务与依据
- 阶段：团队建立与设计准备；业务代码未实现，以下方案和接口全部为未冻结草案。
- 依据：`specs/sources/T44-taskbook.txt` FR-01/03/04/05/06/08 及安全、事务、并发要求；提交说明只确定材料范围。
- 承担：FastAPI 统一鉴权、项目权限、业务门面、服务端状态机、评审/上线/回滚及事务协调。
- 未来代码范围：`backend/app/api/`、`backend/app/domain/`、`backend/app/services/`、`backend/tests/core/`；本轮均未实现。

## 服务模块与边界草案
- 统一鉴权与项目授权：服务端解析身份并核验项目成员关系；客户端传入的用户/项目归属不能作为授权依据。
- 流程登记门面：登记任务、依赖与排期，输出资源标识/版本及变更差异；依赖未满足不得进入可开始状态。
- 状态流转门面：仅经状态机改变任务状态；输入目标状态、预期版本、幂等键及业务依据，输出新状态/版本/留痕标识。
- 评审门面：记录八段式评审与十项清单的证据位置；缺证据不能判通过，固定模板须由总协调核对来源后冻结。
- 上线评估门面：覆盖数据/权限/外部依赖/观测四视角及回滚预案；预案未评审不得进入发布阶段。
- 决策门面：上线/回滚记录实际拍板人、理由、依据和影响范围；AI 不能代替授权人员决定是否回滚。

## 状态机候选与待确认出口
- 状态集合来自任务书：待受理、开发中、阻塞、待评审、待上线、已交付、已回滚；整型映射由数据库岗提案后共同评审。
- 候选主链：待受理→开发中→待评审→待上线→已交付→已回滚；每条边的角色、证据和守卫均未冻结。
- 候选异常边：开发中→阻塞，阻塞→开发中，待评审→开发中；阻塞解除须有依据，评审退回须有原因。
- 待确认：其他状态能否进入阻塞、解除后回到何状态、已回滚能否再次开发、是否允许取消/重新上线，不能自行扩展状态集合。
- 必须拒绝：越级迁移、缺阻塞原因/责任环节、缺解除依据、依赖未满足、上线预案未评审、权限不足和同任务版本冲突。

## 鉴权、事务与并发草案
- 所有业务 API 经统一鉴权；按资源所属项目逐次授权，成员只能查看参与项目；动作角色矩阵、登录/Token 生命周期待冻结。
- 候选错误：401 未认证、403 无权、404 资源不存在、409 状态/版本/幂等冲突、422 参数不合法；错误码、资源枚举防护策略待前后端确认。
- 候选事务：授权/守卫校验后，以预期版本进行条件更新；任务状态、成功流转留痕及需可靠投递的事件意图在同一事务提交。
- 同任务并发只允许一个不同请求生效；失败者记录拒绝且不得改变任务现状。幂等重放与并发冲突的判别规则需明确。
- 候选幂等键作用域为调用主体+项目+动作+键，保存请求摘要/结果；同键异参拒绝，保留期限与唯一约束由数据库岗评审。
- 拒绝记录不能随失败的业务事务一同回滚；由持久层提供独立可持久审计能力，审计失败的处理策略尚未确认。
- 不在数据库事务内等待 RabbitMQ；事务事件意图、提交后投递、消费去重及 MQ 故障站内待办边界需与数据库/消息岗共同冻结。
- 密码只允许安全摘要；Token/口令不得写日志，参数化查询由持久层落实；泄露阻断、撤销、审计保留及故障策略待细化。

## 跨岗接口需求（proposal-v0，未冻结）
- 前端→后端：资源/项目标识、业务字段、预期版本和幂等键；后端→前端：状态/版本、证据与拒绝原因、错误码。三类 API 契约冻结前不联调。
- 后端↔数据库：成员查询、依赖检查、条件更新、评审/决策/审计写入、事务门面、幂等结果及事件意图；不由后端改模型或迁移。
- 后端↔消息：提交后的事件标识、项目/任务/责任人和升级上下文；返回受理/去重/降级结果。通知列表/已读业务归消息岗。
- 后端↔调度：提供已授权的业务门面及任务/排期语义；调度拥有临期/超期扫描与升级触发，不直接绕开状态机改业务状态。
- 各门面以依赖注入接入，禁止业务内部自行构造数据库、消息或调度实现；具体签名、版本策略、超时/重试均待协商。

## 实际产物、验证与风险
- 实际产物仅三份：本报告、`agents/backend/WORKLOG.md`、`records/handoffs/backend.json`；没有后端实现或冻结契约。
- 已执行：读取指定规范/来源并检查输出路径；命令与真实结果见工作日志。未执行模块自测、联调、独立验收、压测。
- 主要风险：拒绝审计被回滚、校验与更新之间竞争、跨项目资源引用、幂等键误用、提交与投递双写、模板/状态出口凭空定案。
- 后续：总协调组织接口与状态/角色审定，数据库岗确认持久约束，消息/调度岗确认事件边界后再进入编码。
- 留痕：实际使用 `ROLE-backend-BOOTSTRAP-v1`，关联 `agents/backend/TASK.md`；操作者为 AI，审定人尚未产生，不能写成人工修改。

## 后续合同设计（ROLE-backend-CONTRACT-v1，仍未实现）
- 基于用户采用业务v1及协调者D002/权限质量细化，新建 `specs/contracts/openapi.json`、`specs/contracts/README.md`、`specs/backend-design.md`；31路径/38操作/130schemas，全部未冻结。
- 覆盖三类主接口及完整鉴权/项目/成员/迭代/排期/开始前依赖/评审/预案/决策/升级/通知/审计辅助契约；统一ID、时间、分页、版本、字典、证据、错误。
- 角色最小权限、非owner代码评审及非创建者预案审定属于AI协调者技术质量约束；没有冒充用户亲改或增加状态出口。
- 先鉴权再同键重放再版本；租约幂等、独立拒绝审计、session共享锁、任务CAS及MQ降级后同事件不再提醒均已与数据库方案对齐，尚无实现。
- review/template与escalation/rule版本化可扩展，v1仍仅原十项及三档；新配置不得默默生效。
- 真实OpenAPI重复参数失败及修复、辅助样例解析用法失败均保留原始日志；最新规范与6个合成例/离线约束自检通过，不是HTTP测试。
- M0提交 `29ec3401564243dc34f41e6a1bcca81b73528455` 已归档；本轮日志、派工、评论正文及输出见 `agents/backend/` 和交接单。
- 后续待契约/DDL/锁序复核及审计故障持久介质确认；未写ORM/迁移/产品代码，未运行业务/HTTP/集成/独立验收或压测。

## CONTRACT-v2 定向设计修复
- 依据reviewer对717cd65的真实不通过报告，定向修C2收件人/计数域、C3数据库时间域、C4逐操作错误一致性；原报告/日志保留。
- C2无收件人数上限、不截断经理，handled_count为UINT32；C3共享1000～9999/UTC Z/≤6微秒，扫描只作now−end差值；C4只读无幂等错误、字典无项目/资源错误，并显式列每code触发条件。
- C1后端文档采用数据库下一轮response_request_id字段作为重放original_request_id来源；该列和COMPLETE约束由数据库岗另修，不代其宣称通过。
- 新增 `agents/backend/validate_contract_design_v2.py`；真实修复前退出1/90项失败，修复后1130项设计检查、38操作、0失败；前后日志及Issue#3/#12正文见交接单。
- 仍是未冻结设计、业务未实现；没有HTTP、MySQL、消息/调度运行或性能结论，等待合并后新SHA复审。

## CORE-FOUNDATION-v1：纯领域代码已存在
- 在独立树/分支codex/backend-core实现 `backend/t44/domain/`：内部Enum、typed命令、可信纯上下文协议、七状态九动作的decide及不可变决定/效果。外部字段和HTTP取舍未绑定。
- 真实入口 `t44.domain.decide(position, command, context)`；I/O、资源加载、事务/CAS/幂等/审计/outbox由以后门面负责，本轮未接入。没有API占位路由。
- 所有合法边、非法跳级、阻塞来源与解除、角色/证据/轮次、三处依赖（start/unblock到develop/rework）有参数化单元测试；评审拒绝不偷加依赖限制。
- 实际uv universal/Python3.12生成68包hash锁，含PyMySQL[rsa]/cryptography、argon2-cffi，不含JWT；本机hash安装、wheel安装和pip check通过，Linux67包目标解析一致，未执行Linux运行。
- 最终106项领域单元测试通过、Ruff/format/Bandit退出0；仅领域含分支覆盖约98%，非HTTP/集成/独立验收或全项目门禁。SSL与初次Ruff失败原始证据保留。
- 详细接口/命令/限制在agents/backend/core-interface-notes.md；本轮实际prompt在CORE-FOUNDATION-v1-prompt.md。原始JUnit、coverage JSON及日志列于handoff。
- API、DB/迁移、事务/幂等/CAS/审计、消息/调度、联调/性能仍未实现；Q002与正式规格冻结由用户/协调者/审核流程另行决定，AI自测不替代。

## APPLICATION-v1 阶段1（当前，覆盖旧阶段限制）

Q002已用户采用、v1已冻结；真实实现入口为backend/t44/api.py和cli.py，38操作已注册，services组合既有domain和DB参数化UoW。已具鉴权/opaque撤销、严格请求响应Schema、任务/计划/依赖/评审/预案/经理决策、统一幂等CAS与成功/拒绝事务编排。review-template.json是实际v1八段十项配置。

25项真实TestClient+SQLite HTTP自测通过；首次DB自增缺陷由DB修复后合入，短幂等键测试错误修正，原失败保留。Ruff/format/Bandit最终通过；协议字面量/空租约的Bandit初次误报保留。不是MySQL或独立验收。消息/升级门面及seed等待owner，相关依赖缺失返回503；后续真实MySQL HTTP、Rabbit、全后端覆盖率和性能仍待做，不拿domain98%代替。

### 阶段2补充

已在官方MySQL8.4.11、明确t44_dev执行真实HTTP＋并发CAS/独立拒绝审计测试，1项通过；合并本岗HTTP共27通过（26 SQLite＋1 MySQL）。真实Uvicorn127.0.0.1:18080运行，四项TCP HTTP烟测与Schema通过，演示项目/迭代/任务均ID3；三角色账号仅在ignored0600私密JSON。网络首测受环境代理影响的失败诊断保留，loopback直连修正未改TLS。Ruff/format/Bandit最终通过。

按总协调阶段安排先交接服务与代码，让消息/调度owner接线；它们仍依赖缺失503，CLI seed等待DB。没有Rabbit、全t44覆盖率、全流程MySQL、性能或独立验收通过结论。下一轮继续完整整合，而非把本阶段自测当全产品完成。

## INTEGRATION-v1 checkpoint（当前未全局通过）

缺组件503用显式注入保留，默认通知组件200另测；审计41码及domain/API状态角色责任映射已消除顺序依赖，并有实际重排回归。完整MQ/调度/DB基线首次全t44回归312通过、2失败、3本机Rabbit未配置跳过；失败为seed读取旧规则字段，已报owner。全t44行覆盖84.38%（2746语句，429未覆），含分支综合81.16%；有失败/skip，未称全局门禁或独立验收通过。测试目录即按用户新要求由根机械迁移到tmp，原断言保持。

### INTEGRATION-v1 当前实际结果

完整通知/升级默认组件已装配。38/38操作通过53次真实TCP HTTP＋MySQL请求和响应Schema；真实scanner→Pika关闭端口失败→消息CLI自动降级→通知读/处理与晚到去重、CLI身份/撤销/错库拒绝也通过。服务18080 PID14985，独立18081不触碰。证据为agents/backend/integration-38-http.json、integration-live-chain.json、integration-live-revocation.json。

seed旧规则字段由DB修复后全套314通过、0失败、3本机Rabbit未配置跳过；全部t44行2391/2724=87.78%，含分支85.36%，无omit。审计/状态显式码修复及重排回归、显式缺依赖503/默认200已交。真实去重保留全部守卫；总体规模仍超限。tmp测试迁移等待root SHA，未自行创建新测试文件；Rabbit成功CI、最终源码规模、性能和独立验收尚不宣称通过。

测试迁移5e07887已合入，`pytest -c backend/pyproject.toml tmp/backend --collect-only`实际317项成功；新本岗路径为tmp/backend/contracts/985_mysql_http.py、986_http.py、987_faults.py和tmp/backend/backend/domain/994_transitions.py。旧运行日志保持原命令，不把机械收集成功说成新一轮全量执行。当前真实38HTTP/CLI证据checkpoint19750a9，仍待CI/Rabbit、最终规模和独立验收。

## ROLE-backend-REFACTOR-v1 当前阶段

- 代码存在：删无production消费者的domain重复re-export/__all__，typed命令/模型/decide保持原实现；受信Call.create共享创建上下文与读回，issue_session共享人类/服务会话发行。冻结API、稳定码、权限/证据/锁序/CAS/幂等及独立拒绝事务未改。
- 远端实际失败：729344e的GHA39937742613出现namespace遮蔽（18 failed/299 passed）及Ruff I001/F823；原日志在agents/backend/refactor-ci-39937742613-failed.log。当前修正cmd别名，保留全部原断言。
- 当前验证：本机性能隔离期间未运行pytest/build/DB/HTTP；Ruff格式化只算编辑。等待新SHA远端CI。生产git物理diff相对003ef6b净减112行，最终统一cloc和3500–5100要求仍待总协调核算，不能宣称规模已达标。
- 旧完整HTTP/事务/覆盖率证据仍为上轮快照；当前重构不等于独立验收或正式性能通过，18080/18081均未重启。

## ROLE-backend-REFACTOR-v1 远端复验结果

源SHA64b4f891ee77eeb2b1054c3a40af084eb6691d5c的product39938619826/39938612582四任务全成功。原始JUnit317测试、0失败/错误/跳过，contract35/integration52/fault7各自通过（会重叠）。全43个backend/t44文件、无excluded：2406/2729行88.1642%，分支76.4706%，含分支85.7392%；CLI0覆盖仍纳入分母。原始日志/覆盖JSON/JUnit和refactor-validation-summary.json在agents/backend/。

729的真实18fail/I001/F823→后端AI修改cmd别名→64b4远端317通过关系有原始日志，未降低断言。当前仅后端重构/远端开发CI交接，不是独立验收或正式性能通过。最终全产品源码cloc仍待核算；本机性能窗未跑测试/构建/DB/HTTP，服务未重启。

## ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1 阶段A

实际基点397bd7973cfd835c635634d32e0c98ae56d74949（指定父产品43f51570）。仅源码/官方资料分析和准备，尚未获已发布性能报告及t44_profile/中性账号，不读取未发布黑盒文件。

唯一新工具tmp/backend/955_perf_profile.py为独立诊断serve，基于真实API/UoW分开ASGI区间、Runtime/验证/序列化阶段、线程CPU、SQL游标及连接获取聚合，可选cProfile；限制profile库/18082/120秒/1worker，不建库不发负载、不改冻结响应或生产实现。真实函数I/O、指标含义与短跑组别见agents/backend/performance-diagnostics-plan.md。

本轮工具未运行/导入/编译/本机lint，实验/基线/瓶颈/优化收益均无数据；旧CI317通过属于旧产品源，不当作新工具通过。阶段B待根继续派工和环境；目标阈值、安全/事务/校验、独立测试隔离与原源码统计范围均保留，5866仍超5100。

## 已发布IAT修复 checkpoint 1：IAT01

仅两份总协调许可公开报告已按SHA核验；不读私有脚本/证据，不接触独立测试。先开发HTTP复现2失败，再修新评估CAS清批准引用及仅评审最新风险版本；不删历史，不改冻结Schema/错误码/锁/幂等/事务。32项HTTP/SQLite通过，包括旧A批准与待审、旧A不能再激活、B创建重放不清B当前批准、拒绝audit_id。原始失败凭据脱敏+private0600原件SHA，成功/失败JUnit与Ruff/Bandit在agents/backend/iat01-*。

本专项MySQL与独立复测尚未执行；IAT02～05仍待修，性能IAT06仍未通过且955阶段B未运行。955准备工具的静态导入I001由本岗发现修正，不是用户亲改。

## 已发布IAT修复 checkpoint 2：IAT02～05

按根限定范围修复：createTask负责人须在迭代capacity（不新增预算/生命周期规则）；非法任务0及越界attempted引用不会击穿独立拒绝审计；任务/返工公开audit包含完整五计划字段与版本（2000字原文保留）；空必需证据及只读验证顶层/候选错误依冻结分支分类。oneOf的bool/string拒绝、1.0规范化同键重放保持。冻结11件、SQL/DDL、锁序/CAS/幂等/事务/outbox均未改。

新增开发回归先13失败、另8失败/2通过，再最终55个HTTP/SQLite通过，日志/JUnit在agents/backend/iat02-*及iat05-*；全Ruff/Bandit通过。985已补真MySQL专项但本机尚未执行，等待新源CI；不把本岗修复称独立复测通过。IAT01旧65007a远端CI已成功，不能当新源结果。容量转派/移除及大iteration.capacity公开差异待正式取舍。

955诊断进程固定18083并记录实际import文件/关键SHA，防PYTHONPATH旧源误记新HEAD；未启动。原18082/验收/perf库未触碰。业务checkpoint后先协调Word渲染的CPU空闲窗口再1/8/32短样本，性能阈值与5866超5100事实未解决。

## IAT业务远端CI闭环

源479fc8f的product39946771417已全成功：JUnit362通过、0失败/错误/跳过；含985的5个真实MySQL HTTP用例（原1+新增4）。全43个t44文件、0排除，2524/2850行88.56%、分支78.11%、综合86.33%。原失败、MySQL用例名称、raw log/JUnit/coverage及summary在agents/backend/iat02-05-ci-*。没有独立复测或正式性能通过声明。

955追加仅契约校验的public bootstrap+闭环client，1:1:1候选分布逐响应检查valid/无violations并保存实际比例，凭据fixture仅ignored0600。第一诊断窗口拟1worker、1/8/32短样本及1并发少量profile，仍未启动；运行前告实际源码SHA/UTC，不能对原4worker400VU/600秒外推收益。

## 诊断首次尝试的实际边界

96e4源两次18083 baseline服务正常启动/退出，但public bootstrap登录收到非JSON502，未创建fixture或进入1/8/32样本。首次错误FastAPI hook、后续502及debug JSON解析失败均另留证据，未改原件。HTTPX默认使用本机系统代理是当前待验证假设；工具已改trust_env=False回环直连并保留非JSON状态，后端配置Ruff/format及AST通过，尚未运行重试。生产backend/t44与业务CI362通过源479一致。

两诊断服务已退出且无负载运行，总协调收到解除LO hold通知。性能归因/优化收益尚无数据，未改原性能阈值或运行不可变验收实例；下轮执行需重新协调CPU窗口。记录见agents/backend/profile-bootstrap-{failure,attempts}.json、profile-proxy-static.log。
