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

## 1.1容量生命周期合同 checkpoint（尚未新冻结/部署）

D005/D006真实用户选择与bbc限定设计审核后，先交OpenAPI/运行副本/README/design：1.1.0、31paths/38ops、/api/v1、DDL18/226不变；新增assignment/rework的ID30容量分支，全量active owner、capacity1–5/终态6/7与原成员保护1–5+7、项目锁与原幂等/事务顺序均明确。所有请求字段/参数/权限scope及非Meta组件保持，真实规范校验与38操作错误一致性检查通过，证据capacity-v11-contract-validation.*。

当前checkpoint不含新守卫生产实现、未部署，root建立新freeze后再继续；原v1摘要不回填。开发草稿回归旧码11失败/2通过（capacity-v11-before.*），已准备但未暂存的986及service草稿待后续。旧CI362仅属479源，不代新业务回归/真MySQL竞争/独立复测；性能仍暂不运行。

冻结前责任岗增量：精确同步root9aeb40c的frozen-v1.1 metadata，仅修转派description区分无效developer的OWNER_NOT_PROJECT_DEVELOPER与缺capacity的CAPACITY_REFERENCE_INVALID；权威/运行副本一致。旧995设计夹具版本过期造成2个C2失败，改取SPEC.info.version和真实迁移命令后1130检查/38ops/0失败，101收件人等原断言保持，证据capacity-v11-995-before/after.log。仍未提交新守卫，父链freeze由root完成后继续；本次不是产品容量或MySQL测试结论。

## 1.1正式冻结后业务实现

合入189dc4a并核新manifest c95076a及14文件原hash，新增转派capacity守卫/项目锁、changeIteration全量state1–5 owner覆盖、返工前有效developer与capacity守卫；原角色/状态/版本/依赖错误及幂等/事务保持。原成员保护1–5+7不放宽，6/7工时可移出。未改freeze/DDL/输入字段，未部署。

定向开发回归：冻结后21个新HTTP/SQLite项通过；7个新真实MySQL8.4/t44_test项通过，含三类动作各两种锁先后及合法转派后移除原owner双成功。追加版本上限回归先1失败再1通过，最后同源全量交后续CI；终态为明确合成fixture，非完整真实交付旅程或独立验收。严格本地Ruff/Bandit/格式通过；原975更严格SIM117样式失败经root授权只合并context，未降低规则/断言。原始失败、测试XML及冻结后源码hash在agents/backend/capacity-v11-*。新精确CI/独立复测/性能/源码规模尚待，955停止。

精确8f6源39956073530/66523真实全CI失败：391项/2失败/0error/skip，static/frontend绿。两合法UTC候选的500根因是服务把外层1.1.0错误用为冻结内层schema_version.const1.0.0。根采纳本岗按内层冻结const输出的最小修法，未实施曾建议的1.1.1；14冻结文件/APIREADME不改。三category HTTP先3失败，修后加原7个UTC边界共10通过，等待新SHA全CI；原日志/JUnit私密原件与公开脱敏副本SHA、失败关系在capacity-v11-ci-failure-provenance.json。

第二诊断窗口仅public bootstrap成功，45秒服务在跨工具间隙已退出后才发3个sanity，故3ConnectError、0有效业务样本；本岗测量生命周期错误，非产品性能结论。服务正常退出且root已释放窗口；下轮须一次控制器管理全部生命周期并先提交，955/负载现在停止。

精确4c20f32的product39958165108/39958156337已success：394测试/0失败/错误/跳过，contract96/integration63/fault7分别通过；全43个t44文件、无excluded，行2542/2865=88.73%、分支78.55%、综合86.56%。原两个合法UTC及三category修复均在真实CI中，证据capacity-v11-ci-summary.json及该run原件。新1.1开发全量CI通过，不称独立验收、性能或源码规模达标。

955单调用orchestrate控制器已准备，逐次管理3个独立服务的ready/bootstrap/valid sanity/1-8-32矩阵/正常stop，finally清理、全局160s、服务timer120s，实际argv/UTC/PID及import hash记录；生产字节与4c20一致。当前仅静态检查，尚未运行，等root另给quietwindow；原两个诊断失败保留。

## Stage-B 契约校验短诊断 03

工具245e56b、生产字节同CI394通过源4c20f32。13:18:49.973–13:19:57.093Z，t44_profile/18083/1worker完成baseline与timings各1/8/32并发10秒及3份profile；18289主样本另3sanity均有效，0业务/HTTP错误。baseline P95=5.444/33.143/149.208ms；timings=4.856/35.185/151.564ms。原38份metadata/JSONL/pstats/日志zip及SHA清单与限定分析见agents/backend/profile-contract-03-*。

整体controller仍RuntimeError/exit1（最后断言错用bootstrap返回值），子阶段有效；三服务exit0、已释放窗口。两行工具赋值修复仅离线检查/Ruff/format/AST，不重跑负载，不能称修后控制器实际通过。cProfile inclusive合计execute35.007/rows27.158/authenticate24.111ms含等待/冷TLS；连接获取与SQL游标墙钟随并发增长，尚无纯poolwait/DB锁因果证据。未改生产pool/授权/guard/契约校验或正式性能条件，不宣称独立性能/规模通过。

## 只读契约校验优化设计（待准入，非实现）

RFC specs/changes/contract-validation-read-uow-rfc.md仅对validateContractPayload合并两个UoW，默认普通RC实时鉴权、验证后fresh-now复核到期，保留已在途读可完成/撤销提交后新请求拒绝的最低语义。原先S锁提议经根/审核讨论撤回；全部写路径、17其它只读及池/安全/Schema不动。SQL8/9/9→4/5/5与2acquire→1仅静态预期；无负载/收益结论。未应用patch净+7物理行，生产delta0，尚未编写/运行新回归。精确源行号、网络/事务边界和986/985撤销竞态测试计划在RFC；原controller exit1、正式性能失败及源码超限保持。

## 单UoW契约校验已实现，等待精确CI

设计父3187后仅runtime.py净+7行实现唯一接口单UoW：默认RC鉴权→原验证→fresh-now到期复核→原dispatch，退出后原异常独立审计。冻结14文件/全部写路径/其余17只读/池/Schema保持。新增回归原目标9fail/9pass，改后18pass（SQLite HTTP11+真实MySQL7）；真库实际4/5/5SELECT、各1acquire，session/member两种撤销时序与新请求401/403通过。原断言仅追加不删改，故障注入不冒真宕机。证据read-uow-validation-summary.json及before/after原日志/XML。此为定向开发验证；精确全CI/全覆盖率待运行，原394只属旧源，尚无性能收益/独立验收/源码规模通过。

精确5dcb源product39970988113四任务全部success：412项/0失败错误跳过，contract114/integration70/fault11分别通过；全43个t44且excluded0，行2550/2872=88.7883%、分支78.7371%。原coverage/JUnit/metadata与summary见agents/backend/read-uow-ci-*。本轮唯一接口交付，evidence-only收尾后释放岗位；没有性能收益或规模达标结论，后续写路径账本/短对照另派。

## 写路径定位静态材料交接

write-path-static-ledger.md给出三次鉴权/3UoW的新写分阶段账本、真实空依赖SQL、success/rejection audit与幂等/提交边界；项目分布和R/M/N未知，不称瓶颈已定位。只提出无守卫依赖读取可跳过的最小候选，现源码/项目X锁/冻14不变。contract-short-compare-plan.md为4c/5dcb同fixture/8并发ABBA、90秒有界待运行方案；930未创建、无负载/新生产改动。因前端调度优先本轮资料提交后释放槽位，后续由根重新授权，不等待窗口。

## 夜间930有界ABBA工具准备

新分支codex/backend-contract-abba保留05623c并合75c，生产仍精确5dcb。tmp/backend/930_contract_abba.py实现独占进程组连续ABBA控制、90秒监督上限、Git/actualimport双身份、相同profile fixture与未包裹API；每阶段3类sanity、均衡120预热、8并发8秒。说明及静态证据abba-tool-preparation.md、abba-tool-static.*；离线11项通过，显式项目Ruff/format通过，首次隐式配置失败原文保留。未启动应用/SQL/HTTP/负载，真实生命周期和收益待根窗口；历史03整体exit1、正式400×600失败、源码6051超限保持。不是新的全量CI/独立性能通过。

## ABBA一次成功执行后的限定解释

root操作者在已协调窗口单次执行tool974，整体exit0/39.88秒，18083由root观察关闭；本岗只离线复核072bc4e的36份原件和15557主请求，0错，SHA/actualimport/fixture/config均一致。A两阶段P95=31.206/31.358ms，B=23.974/23.390ms，三个payload类别同向；完整解释contract-abba-interpretation.md/json。支持唯一契约校验单UoW在本次短条件下改善，不能证明池/SQL因果、transition/escalation收益、正式400×600/独立验收或6051规模达标。后续静态RFC待审，不启动新负载/产品修改。

## 减少往返RFC：待准入、生产不变

specs/changes/runtime-roundtrip-reduction-rfc.md和三个独立未应用patch给出可复核静态Tx/SQL与净LOC预算。推荐只先A：保留authorize普通读和claim session S两次实时鉴权，但同一首UoW；18幂等写3→2事务，SELECT不减少、主锁/成功原子/拒绝独立/commit-ACK不明保护不变。校验跨普通连接及read-commit故障点移除明确列为语义差异，需定向真MySQL证据。B依赖按需+空集合跳过净+6、C根解析evolve净-10独立候选不混用；A仅净-1，未解决6051超限。草案AST/Ruff/format、patch匹配和14hash通过，无候选运行/HTTP/SQL/新负载；精确CI/性能待实现准入后另排。

## A设计调用者勘误（先设计，修正未应用）

原A的25新定向绿未覆盖scanner真实authorize入口，扩检原988/974两项因AttributeError真实红。原RFC无其它调用者判断错误，root审查亦遗漏，AI纠错不是学生发现。root816ba60窄准入恢复authorize原4行并保留claim(call)薄包装→_claim(g,call)，prepare直接同UoW调_claim；不改调度或DB断言。修正patch/预算preflight-caller-correction-design.json先归档，尚未应用；runtime实际草案有效270→276(+6)，旧净减1不能再作当前结论。

## A已实现：保留真实caller，等待精确CI

勘误5a19f80后仅runtime.py恢复authorize与claim(call)薄包装，prepare直接_claim同UoW；原scanner/DB988均不改，B/C/14冻结不动。有效源码净+6而非减1。旧5dcb新增目标14结构红/11语义绿→精确原A25绿（11SQLite HTTP+14真MySQL）→扩caller2红→修正后原caller2+新账本5绿；同次CAS场景查询隔离1红保留，改为实际两keys、不预筛状态、恰2COMPLETE并对应两HTTP request_id，plan先→CAS后2绿。阶段明细preflight-validation-summary.json及原log/xml，不冒当前完整CI通过。RC实连接/实时撤销/独立审计/真实commit后ACK受控注入范围明确，没有时延或设备故障证明；严格静态通过。root组合6102基准+A6仍超5100，待合根后精确数，未解决规模。新源CI/限定审核及独立性能均待。

## A精确7584 CI归档与PR29

精确7584（产品153、先行勘误5a）product40012517513四任务成功：437/0failure/error/skip，markers139/84/17重叠；43文件集合与生产Git完全相同、excluded0，行88.881167%、分支78.663239%。原件/SHA见preflight-ci-40012517513及preflight-ci-summary.json；固定cloc6108超5100计1008。新草稿PR29绑定此实现，旧PR16仅历史；root指定review_backend_preflight对7584 COMMENT，未APPROVE或全局通过。后续纯证据[skip ci]经root允许、产品/测试/配置字节仍7584，不冒称新metadata HEAD另测；未运行任何新性能负载。Issue28只有设计对接，另阶段。

## Issue28理由出口设计（尚未实现）

独立分支codex/backend-plan-reason从已集成A的9826233开始；RFC specs/changes/plan-history-reason-projection-rfc.md及plan-reason-design-examples.json使用现AuditEvent.after理由条目，无冻结API/DDL/版本变化。新schedule audit拟在原成功事务保存原文；旧task audit只有精确project/task/排期版本、task版本、actor/time、完整前后计划和evidence均可唯一核对才投影，不修改原audit。旧iteration缺定位信息、changeIteration没有任务批改，不能猜或串入任务历史。重复/满50条/缺失/2000字符及前端raw-text与局部缺失提示边界均列明。

当前RowsGateway缺有限tuple-pair谓词，向DB owner提出最多100精确pair、空集0SQL/非空1批、完整rows/稳定排序/明确异常的固定门面；旧/database消息未送达，根另派DB，尚未确认/交付。前端真实需求来源Issue28的6373333383，现通用RecordView不能保证理由原文显示，须后续frontend owner执行。

本轮离线8/8审计数据形状、14hash/31path38ops通过，见plan-reason-design-static.json；无关联算法/HTTP/真库/CI/负载验证，无产品/测试/配置改动。KeyError离线检查笔误如实保留。净LOC预算仅待实现+66..121，不能解决原6108超限。Issue28评论6373605774逐字回读一致；等待根设计准入、DB入口及必要986/985红绿、前端阶段和独立复测，不把旧437CI移植为本设计执行结果。

## Issue28后端0549：开发目标通过，组合检查待执行

源码0549ea89ce218ecb945cd4346671f20d46fad215已push，新history.py和两个既有接线点实现理由同原事务保存，以及当前授权页严格旧task历史投影。现API/14冻结、DDL、runtime/DB门面原字节不改；旧iteration/缺失/歧义/非原生产字形不猜，不更新immutable audit/旧重放结果。已有reason优先；相关重复字段拒绝关联，无关原条目保留。单页≤100，0/1参数化批读，无N+1。

最终18开发目标通过（11 SQLite HTTP含1原计划回归、7真实MySQL HTTP），原失败与摘要位于agents/backend/plan-reason-implementation。原sort=-id夹具422、修正后旧源2红、三类新writer旧源红、AI草稿字形/无关重复两组红均保留；不拿旧12/16重复相加，不记学生亲改。真MySQL仅自有t44_test，100pair单SELECT/空页0读、原行不变、三类新写2000字/幂等重放、写失败全回滚及GET退出后独立拒绝audit等边界有目标证据。无UI/完整CI/性能/独立验收通过声明。

严格静态通过，14hash一致，原986/985断言前缀保持；本岗生产固定cloc实测净+95，高于RFC后端预算，6186基线仅派生6281且仍超5100，未重跑全局计数。新生产文件需纳入下一组合全覆盖分母，旧43文件百分比不沿用。源码checkpoint先提交给前端，依赖/迁移/配置均无需新增；本次证据随后独立提交，完整同源CI/专审/UI由根接续，未启动任何新runtime或负载。

## HISTORY-EVIDENCE-01窄修：源码bcb0，目标7绿

AI专审员在42243/0549真实SQLite HTTP确认合法audit.kind1与schedule.kindtrue因Python容器相等被错误关联；正常新写原Schema已拒绝true，问题在旧历史候选。原审查不通过保留，旧504 CI绿色不能替代未覆盖反例。后端先设计ad6a9b3归档，再原986无mock实际JSON/HTTP得2红4绿，窄修源码bcb0e1bbb1440df958a04e87afea0e5b015d2f17改为双方EvidenceRefs合法+JSON精确类型/原文值比较；6案+1原正常历史回归7绿。证据agents/backend/plan-reason-evidence-type/summary.json，均属AI开发/审核行为，不是学生纠错或独立验收。

无冻结/DB/runtime/正常写/输入normalization/依赖配置变化，旧行不写回；对象键序无关、array有序、字符串不正规化，历史1与1.0保守不猜。严格静态通过/14hash一致/原986前缀保留；单源文件净+4，本Issue后端累计+99，规模继续未过。此轮没有MySQL/全套/浏览器/性能重跑；新源44生产文件全CI、专审和独立复验待根安排，不能沿用旧43分母或旧504结果称通过。

## N07与870离线C：有限观察，生产不改

隔离codex/backend-source-budget-profile基cee7，应用固定bc5。N07读取原6307/缺1207并交一页n07-source-budget-one-page.md：已实施净省0；旧C静态-10未应用，假设未来全可落也6297超1197；扫描run14字段/通知分页重叠不等于净省，尚无1207可信解。不改功能/类型/守卫/审计/统计根或3500–5100，重大选择留人。

设计84fee744先行、工具964f4bb随后，只执行一次870纯合成诊断，exit0/main墙0.350673s/CPU0.350167s。19样本错误签名/全错误数一致/无效ref failclosed，570独立iter jobs每模式3450错误/30异常，输入/SPEC不变；不证明全38HTTP/线程安全。构造CPU3.670/0.438ms、iter95.267/87.347ms，构造只占此混合两段3.7094%；105错误样本偏重、固定顺序/未统计重复，不推真实P95或SQL/线程瓶颈。relative inclusive热点及原始JSON见agents/backend/source-budget-profile/{raw.json,summary.json,result.md}。原工具静态失败保留、import不跑基准，无HTTP/SQL/凭据/私密输入；生产/B/C/锁/14冻结/口径均未改。

## bc5当前契约路径短诊断（生产无改动）

设计08f8050d→工具231445d→唯一原批exit1；原baseline3766/0失败有效，timings包装与FastAPI keyword相撞导致工具500/连接异常、0进runtime。根明确准入未完成观测续跑，先44b9e8c设计/位置专用修复，再真实FastAPI/AnyIO离线一次证明，随后显式续跑exit0，3416 timings+3 profile全有效，不重复baseline/bootstrap/sanity。原失败和两个时间窗/方法/原49份gzip及SHA见agents/backend/bc5-contract-diagnostic/{result.md,summary.json,continuation-summary.json}；不是原批被改绿。

bc5应用实际hash匹配；t44_profile/18083、单worker/40token/pool5+10保持，两次前后端口空/本库其它连接0，全部自有server正常退。baseline1/8/32 P95=3.681/24.383/87.779ms，timings4.199/25.010/89.705ms；逐request_id3419观测恰1acquire/auth/派发，三候选cursor SELECT4/5/5/0错。并发32 runtime wall28.630ms/threadCPU1.766ms、SQL wall9.239ms、acquire14.525ms、dispatch-to-entry6.123ms均值是重叠观测，不能加总/冒纯poolwait或锁等待。新连1/69/211是下一步可核生命周期观察，非已定位正式根因；schema构造约0.04ms/请求不支持立即C。

未复现503、未跑transition/escalation、无MySQL server锁等待字段，不能解释已发表托管400×600三正式失败。没有优化生产、改池/锁/资源/阈值、重seed/清库或新全CI；14冻结和统计口径不变、固定6307/超1207保持。结论只是开发诊断，下一阶段由根另准入。

## pool默认15+0候选的后端静态兼容意见

本轮只读ac826cb9 RFC与8处构造点，范围先提交e534dee；一页交接agents/backend/pool-retention-compat/caller-handoff.md。Settings→API/CLI/MQ/scanner采用默认，显式factory不覆盖；993的partial override由3+10变3+0，旧930硬5+10保持历史，不改测试凑绿。CLI无显式dispose/MQ及scanner有finally dispose的生命周期事实列入额外预算，未新测。

两默认之外auth/401角色逻辑、撤销/锁序/CAS/幂等/audit/outbox/commit-ACK异常应原样；池/DB不可用仍可能在auth或拒绝audit完成前503，不能保证原错误分布。标准6池峰90相同，温态保留上界30→90，内存/FD/其它连接及滚动实例代价未知。Issue4具体兼容输入6376569009/Issue3总结6376597757已发表回读，DBowner真实确认当时只有诊断、无默认候选SHA。只认静态无API接线阻断，不作候选CI/专审/性能或合入批准；本机0SQL/业务HTTP/负载/套件，生产bc5/旧ff7/14冻结/6307缺口保持。

## db87准确候选CI归档（无生产准入）

本岗AI仅归档两次托管开发run：product40039282322/Docker40039333270均success，五官方ZIP实际先digest验证再选18+33新原件及双hash/roundtrip；不复制旧结果、不触发CI/读独立材料或本机业务。新汇总records/validation/composite-db87-pool-ci.json。

JUnit520/0failure/error/skip，其中86910离线池/Settings实际收集、9300case不代表旧对照跑过；marker162/93/19重叠。全44Python精确Git分母、excluded0，行89.2120%/branch79.9757%分别；FE89/20TSVue精确Git，行93.33%/branch88.09%。Docker实际checkout经官方git log原行证实400a5cac（API head db87只是PR头，result源是事件SHA）；merge父70f4b7+db87，完整明确运行roots166文件候选↔merge字节相同。实际4workers、扫描16created/2completed、19表恢复counts/checksums同，原schema18/226、第二scanner flock预期exit1均保留。仅此准确CI范围，不宣正式性能/独立验收/资源预算实测通过；root生产bc5、6307超1207保持。

## 固定bc5静态I/O与下一步测量交接（没有新运行）

范围先0a84ff6；一页agents/backend/static-performance-next-measurement.md及13源文件hash/前提static-perf-path-receipt.json。项目列表实际operationId=listTasks，10S/2U；契约4或5S/1U；升级列表10+3E S/2U（每event额外outbox/全部notifications/scan_run，E≤100）；通知9或10S/2U；依赖列表11+E S/2U。当前A fresh写预检10/8S在首U、主写第二U，不能套旧3U；SELECT与实时鉴权不减。以上是静态成功分支公式，不是本轮SQL或延迟证据。

分页/COUNT/排序、全membership/依赖图、每事件通知/JSON规模及索引前缀列为待测维度，建议以后逐request_id分离派发/连接生命周期/SQL execute-fetch-codec/auth/Schema-wire-JSON CPU；未重复profile/池短样本，不推正式或其他运行根因。未来batch必须保留项目/原序/全通知/null/缺引用/RC及独立audit语义，列明有限并发/跨项目/多收件人回归，未实现/未测试/未准入。Issue3全文GET核对；本轮源码/用例/DDL/锁和统计口径均未改，无服务/HTTP/SQL/负载或独立私密接触，阶段结束释放。

## 依赖边项目条件候选（未集成）

设计ed2737d先于唯一应用74a；固定C=b66fa36a317145afec350d7f61ca374959b2eaf7、DraftPR42。合法FK读集等价依赖全局taskPK+edge复合FK+Call.task核项目；仅Workflow查边加project_id，其它SQL/守卫/锁/CAS/事务/审计/outbox/幂等/ACK与旧5+10池保持。DB公共5948的EXPLAIN仅估9216→1并有filesort，非收益。

原986同18目标旧/候选各通过；74a全CI510绿但整体因部署测试样式红失败，旧Docker实际d74 checkout绿，见records/validation/composite-dependency-query-74a-ci.json。owner17e两处样式摘取后C新CI40047832510/40047836840仍待终态另封，不冒称全绿。C实cloc6307/exit1仍缺1207。细节/原失败/来源/限制agents/backend/dependency-query-candidate/report.md。后证据分支独立、PR头固定；无本地外部SQL/服务/负载、无独立资料。根条件门槛及专审未完，不自动合并。


准确C终态补充：新product40047832510四job和Docker40047836840均success；全510/0失败错误skip、44Python行89.212039%/分支79.975728%且excluded0，FE89/20TSVue行93.33%。Docker actual9b53812父dde39+C、169相关运行文件等同，4workers/19表恢复通过。原74a static红仍在原汇总，固定cloc6307仍失败。准确C新汇总records/validation/composite-dependency-query-b66-ci.json；E仅证据，不改变PR42产品C或冒充E另测。专审/根门槛与性能/独立验收仍另决，本阶段结束释放。

## 859：全部非空前驱交付后允许开工（新增开发覆盖）

从根f986、应用字节同C=b66fa36；设计536162c先于测试，原应用/规范/旧用例不变。root分配tmp/backend/contracts/859_dependency_delivered.py，真实SQLite/TestClient/RowsGateway走两前驱完整评审发布；0/2及1/2拒绝且下游快照不变，2/2才允许开发开工/version+1并保留边。新案+原986相邻拒绝案仅2pass，非bug红绿/实库/全套覆盖/独立验收。

原format一处换行失败保留，AST相同的格式修正后静态通过，未重复pytest；执行时/最终test SHA均留。无本机MySQL/外部HTTP/服务/负载/CI/新cloc，正式FAIL与6307超1207保持。性能中文摘要分已知线索/未知瓶颈/人需决定的大范围选择，已先交root。报告agents/backend/dependency-delivered-regression/report.md，性能performance-summary.md，Issue3 6379240354全文GET。本阶段后端AI完成，释放槽位。

## D008设计候选（尚无实现）

RFC specs/changes/release-error-priority-rfc.md基root14b57c6，明确双失效先BASELINE再新评估/批准，保留原批准引用匹配后的domain顺序及鉴权/资源/请求版本前置。仅原失败槽错误选择为建议，不改全状态机；晚期state/经理角色/代码评审与双失效组合范围交限定审核，不自创全局总序。建议1.2.0外层元数据/两OpenAPI一致，内层candidate schema1.0不改，旧v1.1/F08历史保留。列准确同步文件及新回归计划；纯设计，14hash保持，无应用/测试/DDL/suite/SUT/CI动作。作者AI，用户真实业务选择非改码证据。

## D008 1.2草稿同步（等待新freeze）

基398c3d3仅4件合同/设计：info+成功Meta1.2，两JSON同，candidate_schema1.0；草稿状态明确，最小原批准失败槽基线优先及R2重放边界写清，原1.1历史完整保留。原995规范/1130项通过，45叶值白名单、31/38/130/错误enum/其它Schema不变；真实hash/日志agents/backend/release-priority-spec-draft。Workflow/测试/DB/DDL/旧freeze均未改，没有应用suite/SUT/CI/服务/负载。root另同步根需规并freeze，之后才实施；用户选择非用户改码，旧F08等历史不回写。

## D008 1.2实现候选（待准确源审核/CI）

先冻结d530/15hash→计划9bab→856旧3红8绿→仅workflow既有批准失败槽错误选择→同11绿，另原986相邻4绿/两文件Ruff格式通过。C=0dfb55c2191200d947c5423fd9ee74bb0812cc5a、DraftPR43固定；不改其它生产/原测试/859。新规业务由人选择，改码/开发自测为AI，原F08/1.1历史不回写。

真实schedule/恢复评估批准发布及success/error重放、版本/归属和匹配引用原domain已覆盖；cycle/异常引用为controlled SQLite，不冒真实rework，未新注入5xx/owner/audit故障。原失败合成session值仅公件脱敏/私密原件hash留，报告/命令/JUnitagents/backend/release-error-priority-implementation。实测cloc6310净+3/超1210仍失败；新product40060857352/Docker40060980119终态/全覆盖/actualcheckout待后receipt。只有内存HTTP自测，无本机外部DB/服务/负载或独立材料；代码审核与新源CI后root另决，不宣正式通过。


C准确新托管结果：product40060857352/Docker40060980119成功；实际522/0失败错误skip（85611）、marker174/93/19重叠。44Py全Git集/excluded0，行89.212039%/分支79.975728%；FE89/20TSVue行93.33%。Docker实际f8c0428父3fa+C、171相关文件相同、4worker/19表恢复通过，官方五ZIP/18+33原件全digest/双hash回读。总结records/validation/composite-D008-0dfb-ci.json。PR43 exactC COMMENT已读回，root已开发集成da2d308、main不动；这些是限定开发验证，不抵销cloc6310/超1210或正式性能/独立验收缺口。E纯证据不再推动C，本阶段封档暂停。

## 中性synthetic账号worker

原产品C不变；root跨目录授权仅新增deployment/synthetic-fixture.py和850本地测试，04f1ef8先设计。固定UID10001/DBt44/CLI及公开recipient/helper摘要，严格readonly输入/0700私有输出；pending密文先于原CLI匿名stdin创建，三名任一存在/业务非空/部分失败或未知结果即停止，不重置、不重试、不删用户，最后只发账号密文，不seed或创建session。worker完整hash/参数/风险见agents/backend/synthetic-fixture/report.md。

最终20项纯合成guards/真实本地已知数据加密解密通过，CLI/DB为明确替身，无实际库/云/容器/HTTP/负载。原Ruff SIM105红保留→AI窄样式修正后两文件静态通过；只读三份已公开物流原件，不读独立私密。运行前还需root核准确C镜像/RO挂载/UID权限并单独授权实际初始化；部分提交和全局预检并发边界不冒原子保证，源码规模/正式性能历史不变。

root续准固定C宿主launcher，91d2bfb先设计后新增deployment/fixture-launcher-cloud.py，不改worker/C/既有部署。固定两份-f+原ops.load_env内存、原TLS校验和四挂载，原admin继承UID10001/capdrop/RO；白名单回执/私有0600日志，失败不重试不seed。T44_DATABASE由原C compose继承MYSQL_DATABASE=t44，无需额外覆盖。仅850新增4静态目标通过/旧20不重跑、Ruff通过，未运行launcher.main或任何云/服务/SQL。准确hash/命令/未核范围见agents/backend/synthetic-fixture/launcher-report.md，实际执行归root。

新中性service worker/host launcher先4ab5e7d设计，原C/既有工具不改，仅原admin唯一新cohort私有bind。notification-cohort/40scope/TTL5400，只原credentialadmin/CLI初发；实际主体/时间/会话摘要只读核验后按root给定852-neutral-service-credential-v1在内存加密，origin从host私密env经stdin，不公开实际IP/Token。新extended TLS helper固定ea1b5873，准入依赖根专审。首9/后3(1重复)离线目标均绿、共11唯一新例，Ruff绿/原SIM300样式红保留；无DB/CLI/云/main执行。报告agents/backend/service-fixture/report.md，运行和接收方解密仍待root审后执行，不冒真实通过。
