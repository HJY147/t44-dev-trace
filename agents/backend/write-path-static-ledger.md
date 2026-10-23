# 写路径静态账本：未运行负载、未改生产

依据：22647b4eef87f7486293c64dc6d0b3d6809b1a53中的生产文件（同5dcb73cc10c38deb14fae68d33318b04d538fecf）。本轮只读源码/当前安装SQLAlchemy和PyMySQL实现；没有SQL执行、pytest、服务或负载。已发布报告的请求模型由根转述：每轮GET后block或unblock；升级轮次GET→经理改期开新schedule_version→服务建事件；400独立任务，项目分布、经理数、scan_run复用方式未知。未读取私有脚本/数据库推测这些参数。

下表均是**明确正常分支的源码逐调用计数，不是本轮SQL trace或性能瓶颈实测**。假设认证/Schema/角色/证据/状态/版本全部有效，新幂等键、无唯一冲突/租约恢复/连接失败，正常提交。R=当前任务有approved_review_id而实际额外读取reviews时为1，否则0；M=本级规则含经理时，对active项目成员中的manager逐一读取users的次数（即使该user不active也算查询），否则0；N=本次scan_run不存在需插入时为1，存在为0。

## 正常成功账本

SELECT包含锁定SELECT，DML包含claim/业务/audit/outbox/idem；控制语句为SAVEPOINT/RELEASE。955的cursor计数包含这些控制语句，**不含**DBAPI COM_PING、commit/rollback、物理连接初始化等。

| 请求 | SELECT | DML | SAVEPOINT/RELEASE合计 | cursor事件 | UoW/acquire/正常commit |
|---|---:|---:|---:|---:|---:|
| 人类GET task | 9 | 0 | 0 | 9 | 2/2/2 |
| 人类BLOCK，新key | 22+R | 5 | 2 | 29+R | 3/3/3 |
| 人类UNBLOCK，新key | 24+R | 5 | 2 | 31+R | 3/3/3 |
| 经理changeTaskPlan，新key | 20 | 6 | 2 | 28 | 3/3/3 |
| 服务createEscalation，新key/新事件 | 24+M | 6+N | 4+2N | 34+M+3N | 3/3/3 |
| 服务createEscalation，新key/事件已存在 | 21 | 3 | 2 | 26 | 3/3/3 |
| 人类已完成同key重放 | 9 | 0 | 0 | 9 | 2/2/2 |
| 服务已完成同key重放 | 7 | 0 | 0 | 7 | 2/2/2 |

各阶段来源（源码行号按依据源）：

- `identity.py:45–85`：人类项目鉴权session/users/member/project共4 SELECT；服务升级是session/service_account/project共3，服务scope不查成员。没有跨事务身份缓存。
- `runtime.py:40–43,233–245`：第一authorize UoW完成后原validate；第二claim UoW重新鉴权，查idem，fresh键SAVEPOINT→INSERT idem→RELEASE→GET idem。因此claim为人类6 SELECT/服务5 SELECT、1 INSERT、2控制语句。已完成重放只鉴权+查idem，不运行主事务/audit/任务版本检查；新请求身份/输入仍先检查。
- `runtime.py:186–222`主locked_scope再次鉴权→idem FOR UPDATE→必要project FOR UPDATE→全部project_members按user_id FOR SHARE→tasks按id FOR UPDATE。BLOCK/改期人类为4+1+1+1=7 SELECT；UNBLOCK当前对所有返回环节均走graph_lock，另project读与依赖边读，合计9。升级服务为3+1+1+1=6。即使依赖为空，锁任务查询仍有目标id，确实发SQL。
- `workflow.py:62–86,229–256`：重新c.task 1 SELECT，之后无条件依赖边1、前驱tasks 1（空ID列表也执行），可选review R；CAS UPDATE1，BLOCK/UNBLOCK不写decisions，无返回再查。`common.py:153–166`已直接合并row/values，**没有CAS后GET**；不能虚列这种可优化查询。
- `tasks.py:102–122`改期：manager本地检查→c.task 1 SELECT→CAS UPDATE→`projects.py:173–200` INSERT schedule_changes；计划差异/版本写公开before/after是纯计算。输入、状态、CAS等错误顺序保持现状。
- `scheduling/facade.py:106–217`新事件：c.task FOR UPDATE1、查existing event1、查active members1、manager users M、查scan_run1、新event读回1、event序列化的outbox/notifications/scan_run共3，即8+M SELECT；outbox/event两INSERT、任务CAS UPDATE，新scan_run另INSERT N。外层SAVEPOINT一对、new scan_run内层再一对N。事件已存在直接task/event及序列化5 SELECT，不扫收件人或新run，不增task.version/count。
- `runtime.py:45–74,266–278`成功audit：GET project1、查目标task归属1、INSERT audit1；普通写另INSERT outbox1，升级由facade已写outbox而runtime跳过；COMPLETE UPDATE idem1。成功业务、审计、outbox及快照仍同主事务原子提交。`task_model`、Schema/wire、本地规则/ReviewGate计算不另读数据库。

因此单轮GET→BLOCK为38+R cursor、5个UoW；GET→UNBLOCK为40+R、5个UoW。升级轮次GET→改期→新事件为71+M+3N cursor、8个UoW（SELECT53+M、DML12+N、控制6+2N）。这些是分支合成账本，**不是已知正式平均数**，不能假定R/M/N或项目分布。

## 空依赖与真实网络边界

`rows.py:61–90,150–193`把空列表编译为IN谓词，仍调用_execute/Session.execute，没有空列表短路；因此workflow里的空前驱确有一次SQL。SQLAlchemy dialect默认do_begin是pass（DBAPI隐式事务），SAVEPOINT/RELEASE则通过Connection.execute发出，进入955 cursor hook。UoW成功路径调用一次Session.commit；当前PyMySQL commit发送COM_QUERY COMMIT，不进SQLAlchemy cursor hook。

Engine.connect包括checkout/可能等待、pre_ping或建连/重连、TCP/TLS/认证和初始化。当前fresh连接跳过pre_ping，复用连接走PyMySQL COM_PING+OK；可能失效重试，所以不能把3acquire机械等同3COM_PING。新物理连接的项目connect事件有3条DBAPI SET，dialect/驱动还可做初始化；commit与pool reset rollback也不能从cursor账本推成总网络次数。当前没有纯poolwait/DB锁数据，不调整池。

## 拒绝、幂等竞争与错误优先

- 主事务拒绝先rollback/close，再`rejection`新UoW。有效主体+有效项目/目标task+已认领idem时，独立审计是session SHARE1、idem UPDATE1、项目存在1、task存在1，共4 SELECT；INSERT audit1，若4xx且owner仍有效则另UPDATE idem完成错误快照1。5xx不完成idem，审计不可用仍503，不能称单库故障时必落库。
- 示例：新key BLOCK版本不匹配在workflow第一task读后失败，依赖/证据读取尚未发生：总22 SELECT、3 DML、2控制=27 cursor，4acquire，3commit+1主rollback；UNBLOCK同类为24/3/2=29。若是版本上限，原流程先域守卫再CAS上限，不能套此早失败账本或前移上限改变优先级。
- 参数/越权可能在claim前失败，actor/project可能尚未赋值，FK安全检查按实际上下文短路；claim内容冲突/PROCESSING未拥有idem时不完成它。不能对所有错误套4 SELECT常数。成功缓存重放不再审计/写task，拒绝独立audit不能因复用旧授权context而省略。
- 唯一冲突会加ROLLBACK TO SAVEPOINT及重查，具体前缀依冲突位置而异；租约恢复UPDATE owner，提交不明走原TRANSACTION_UNCERTAIN/DEPENDENCY_UNAVAILABLE。未执行这些分支，不给编造平均次数。

## 最小候选与影响（均未准入实现）

优先候选仅按纯域实际使用加载依赖：start、unblock返回develop、rework需要；BLOCK及unblock返回其它环节不需要。需查边时若ID为空，跳过无效前驱SELECT。保留workflow最先版本检查、原review/assessment读取和域角色/证据/状态优先、CAS、全部锁、成功/拒绝事务。正常BLOCK可少2 SELECT，需依赖但空列表的UNBLOCK可少1；这是静态潜力，未写代码/未测收益。不能以此删除graph_lock的边读/有序任务锁或project X。

第二候选是同主事务已经FOR UPDATE取回、当前代码丢弃的完整task行，替代紧随其后的c.task再次读取；不是保存authorize/claim结果。需要明确gateway/事务绑定、结束及异常清空、同project同id完整行、同等锁强度，资源缺失仍在原handler位置报错（不能抢manager/version等优先）。这可静态少1 SELECT，复杂度高于第一候选，未实现。

成功audit的两次FK存在读也可能由**同主事务持锁且已验证**的scope证明替代，但必须独立传递受信证据、限定成功，不能改变拒绝audit的重新查库/attempted引用界限。否则会退回IAT03非法引用审计失败；本轮只列议题，不优化audit。三个事务之间仍须实时鉴权，不能拿Call里的actor/member/project当跨事务缓存。

project X确会让同项目相关操作互斥，但400任务的项目分布未知，不能据此宣布瓶颈。本轮不提出/实施S/X分层；当前冻结设计和1.1容量/图变更锁序完全保留。若未来考虑project SHARE，须独立新RFC证明与capacity/图/成员编辑X及有序任务锁相容，显式设计增量，不改写冻结14原件。鉴权多表join尤其不能直接加FOR SHARE（优化器访问/锁顺序可能变化，缺失身份/项目错误优先也须重建）。

后续任何实现先由根选唯一候选并审查，保留真实before/after账本、依赖满足/不满足/空集合、角色/版本/状态/证据优先、同key重放与拒绝独立审计回归。本阶段无代码、测试或性能结论。
