# 下一步如何测：bc5纯静态交接（一页）

后端AI；固定bc5aef9c62393134582affb7a690acb33ac2b833、DDL c0e740b2（18业务表226列）。本轮未测/未改产品、用例或资源。实际operationId为`listTasks`，派工的listProjectTasks是名称简称，不是缺接口。S=SQLAlchemy SELECT含锁读，U=正常UoW/commit；仅有效人类、正常成功、无重试。P=返回页行数≤100（默认20），不把S当全部网络往返。

| 操作→函数I/O | 静态S/U | 规模与现有访问边界 |
| --- | --- | --- |
| `listTasks`→Tasks.listTasks→common.page；项目/筛选/排序入，Task页出 | 10/2＝两次项目auth各4＋页SELECT/COUNT各1 | task_model纯转换，无逐task依赖查询；COUNT随匹配行、OFFSET随深页、排序/JSON/响应随P增长。 |
| `validateContractPayload`→Runtime专用分支→Business.validateContractPayload；候选JSON入、valid/Schema版本出 | 4或5/1（带task_id加1） | 验Schema/局部计划时间，不执行依赖/状态业务门禁；成本随候选和Schema遍历，不随全任务图自动增长。 |
| `listEscalations`→EscalationFacade.list/page→event；项目/筛选入，状态/recipients/handled_count页出 | **10+3P/2** | 每event另查outbox PK、全部notifications(event_id)、scan_run PK；最多310 S。通知行/recipients无每页100截断，CPU/字节随各事件通知总量增长。 |
| `listMyNotifications`→NotificationFacade.list；当前用户+可选project/read/handled入，页/total/unread/unhandled出 | 无project 9/2；有project 10/2 | global auth各2；业务1或2次member/project读＋页1＋COUNT3。未指定project会读全active membership并S锁至U退出；成员项目数、匹配通知、深OFFSET/JSON均是变量。 |
| `listTaskDependencies`→Business.dispatch/page/dependency_model | 11+P/2 | 另task读1，每边再按PK读前驱1；返回页有限，原读取/真假satisfied语义不能省略。 |

**写预检（当前A已合，不照搬旧3U账本）：** Runtime.prepare先auth→输入验证→_claim再实时auth/idem。fresh key的人类项目请求为10S＋1INSERT＋2 SAVEPOINT/RELEASE、1U；服务升级为8S，余同。已完成同key重放9S/7S、1U、无业务写。主事务locked_scope前缀人类普通task7S、图锁task9S、服务升级6S；随后handler/成功audit/outbox/COMPLETE同U原子提交。BLOCK全程22+R S/5DML/2控制/2U，R为实际读review时1；版本/权限/重放/失败分支不能套这个数。成员全项目S锁、图边/前驱加载会随M/边数增长；Workflow即空依赖仍发前驱SELECT，graph编辑check_graph读项目全图并本地遍历。失败须先退出原U再独立audit，连接不可用/ACK不明保留原503分类，不移检查优先或project X锁。

**索引≠已选计划：** session token唯一，membership(project,user)唯一及(user,active,project)；tasks有(project,state,id)/(project,owner,state,id)/(project,iteration,id)，没有(project,planned_end,id)/(project,updated_at,id)专用排序索引。dependencies有(project,task,predecessor)与反向索引，Workflow只按task_id读边无显式task_id前导索引；escalation有(project,task,id)，通知有(event,recipient)唯一及(recipient,project,id)/(recipient,read_at,id)/(recipient,handled_at,id)。组合筛选、排序、COUNT/深OFFSET的真实扫描/锁须以后自有合成库EXPLAIN/同次指标，当前未执行。

**未来仅待准入的观测：** 不重复既有低并发profile/5+10↔15+0短ABBA。用自有固定fixture分开P=1/20/100、浅/深页、少/多成员/通知/依赖；一次只变一个维度。按request_id关联：①派发→线程进入与body-read分段（非纯队列）；②queue获取、物理connect/初始化、pre_ping、checkout、commit/reset分别记次数/耗时（engine.connect非纯poolwait）；③安全SQL形状/次数、execute与fetch/codec分段、同次服务端rows/锁指标；④每次实时auth单独计时，不缓存身份；⑤model/wire/Schema/JSON编码同线程CPU及输出字节。只存code/脱敏错误类和计数，不记SQL参数/Token/自由正文；cProfile inclusive不能加总当CPU份额。DDL/池/锁/错误优先保持；所有阶段只是建议、未测，不推原正式或其他运行根因。

**升级记录batch议题（非实施）：** 授权页确定后保留原id升序（通知列表另为-id），去重仅作用数据库ID集合；outbox/通知始终同project＋授权event IDs，scan_run无project列，只能用授权页派生ID。必须保留每event**全部通知**、所有recipient含额外行的handled_count、recipient原顺序与空通知/nullable handled_at、原disposition优先级；缺outbox/run不得补默认/忽略（原错误/独立audit边界不变）。RC各语句快照不改成“原子快照”或加锁。未来回归至少空页/共享run/多项目/多收件人>100/全与部分送达/空通知/null/缺引用及并发delivery-read-handle，原页序/total/认证/错误优先与不可变行保持，测0页0附加/非空3批读及全量输出；预测13S仅静态议题，不声称节省/收益。详细源位置和边界见static-perf-path-receipt.json；后续需根及scheduler/DB owner独立设计准入。
