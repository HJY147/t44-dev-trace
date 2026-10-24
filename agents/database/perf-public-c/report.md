# 公开C短窗失败：数据库路径审查与离线可重放回执

数据库AI，ROLE-database-PERF-PUBLIC-C-v1。仅指定839公开md先核SHA c35b37f47d822ef82b4f05627627a2b1f42eb7388c4f2a83d6c13493c5350d4a后读取；未读其余839/独立私有输入/资源/用例，不向839或测试实例传开发信息。公开任务组400在途短窗流转P95 3645.763385ms、查询3315.969690ms/10814稳态1个502；校验组7273预热2个502/稳态0；完整正式组0。原观察保留。资源采样未公开，**当前不知道502产生层级或延迟根因**。

## 身份与实施边界

独立树codex/database-perf-public-c基root6d02cf1d3b99b15556c5d74e007cb4d8d546bbf9；当前生产根与被测C0dfb55c2191200d947c5423fd9ee74bb0812cc5a差异为空。先设计80e9d67、协调限定离线补充cacd0af，后写工具d75866f0d4077dd0399672f6dc914a82de6b9399并提交，再唯一离线执行。工具13份实际C源逐字/hash拒绝漂移。当前不改生产/DDL/API/隔离/锁/池/认证/幂等；本阶段没有修复公开性能失败或准入正式验收。

root明确两机本阶段只保全证据，不再准入SQL/HTTP/负载；838仅本地临时SQLite。没有加载私有云env/口令/DSN，没有MySQL/HTTP/服务/负载/pytest/CI运行。模块自测结果不替代MySQL锁/CAS或独立验收。

## 索引与查询路径（当前C）

|路径|确认的当前行为|可评估项/不能省的边界|
|---|---|---|
|authenticate/runtime preflight|session token unique、用户PK、membership(project,user) unique、project PK；正常project read两次实时auth；fresh write2UoW/3次auth|不能缓存身份或跨事务复用授权。旧5dcb三UoW账本不用来算C|
|Workflow:72 deps|已经带project_id+task_id，符合uq_dependencies_edge(project,task,pred)前缀|已在C中，不能再次记成优化。按guard装载候选由BE负责|
|Tasks.addTaskDependency:139 existing|仅task_id+depends_on_task_id，缺project前导|与Workflow是另一处；目标task已核项目+图锁，同project谓词是可单独审查候选，现有Rows足够。未修改/无收益证明，也未证明本次短窗触及此操作|
|listTasks/common.page|Rows LIMIT/OFFSET加独立COUNT，Task模型无逐task依赖查询|当前不是N+1；匹配数/深OFFSET/排序/JSON输出可变，但需新MySQL计划/同次指标才能判断实际成本。不能删total|
|task_dependencies列表|每条依赖另按PK取前驱，正常project请求11+P SELECT/2UoW|1+P业务配方确有N+1；候选batch须保页序/全部前驱/缺引用失败，RC每句快照不能改称原子|
|escalation列表|正常project请求10+3P SELECT/2UoW，每event取outbox、全部notifications、scan_run|可单独做授权页内3批读；不能截断通知/忽略多收件人/改disposition优先或吞缺引用。不是已确认本次task组根因|
|locked_scope members|全project成员按user_id共享锁，直到mainU退出|一次SELECT但物化O(M)，不是N+1。它保护成员撤销/责任人/人力并发不变量，不能未经新设计改成只锁actor|
|graph与task锁|session→idem→project必要X→有序member S→有序task X；graph path预读当前task依赖再锁目标/前驱|project锁串行图变更与依赖开始检查，不得直接删；BE仅考虑同U内复用已锁task，不能跨U缓存或忽略CAS后更新|
|create/add依赖check_graph|读取同项目全图并迭代查环；只在图编辑等路径|成本随项目边数；不是所有任务流转全图扫描，不可笼统归因|
|listMyNotifications|跨项目时读全部active membership再页/total/unread/unhandled，成员S锁不被页大小截断|收件人/项目/未读/处理索引支持部分前缀，筛选组合/深页需实测；不删额外COUNT|

静态冻结键签名和函数行号/hash在static-path-receipt.json。tasks有(project,state,id)/(project,owner,state,id)/(project,iteration,id)，scan另有(state,planned_end,id)；没有专用(project,planned_end,id)/(project,updated_at,id)。这是显式元数据而非当前云SHOW结果，不能据此排除InnoDB自动FK键；历史本岗t44_profile只读回执5948cf8已实际见tasks/notifications自动键，但该历史计划不冒充本轮部署计划。当前未提出或执行DDL变更。

## CAS、事务与池

- tasks PK(id)确定单行后version谓词CAS：无需为id+version追加冗余索引。Call.cas仍校版本、更新rowcount==1、版本加一；不同key同旧version只能一个成功是MySQL并发安全要求，本轮未重测该并发。
- 幂等scope唯一(actor kind/id,operation,key)；session先锁、idem FOR UPDATE等待旧主事务结束，再owner换代。COMPLETE owner_token CAS/response_request_id快照保持；单纯租约过期不自动判旧worker不能提交。不能因rollback清理声称CommitUncertain原事务没提交。
- 成功业务/audit/outbox/COMPLETE同main事务；拒绝先回滚释放原连接再独立会话记录，审计失败503。不能把独立拒绝并回原事务或减少实时认证换吞吐。
- 源默认每engine pool_size5/max_overflow10/timeout10/recycle1800、pre_ping/LIFO/rollback reset。默认峰值15是源码配置，不是本轮运行中worker/engine总预算的证据；运行覆盖值/连接数/资源仍未知。初始化3条SESSION SQL及dialect握手/ping/commit/reset不包含在普通Rows SELECT计数中，不能把acquire inclusive叫纯池等待。当前不调整池/线程/超时/全局设置。
- DB异常在当前Runtime经PersistenceError/CommitUncertain分类通常走503；源码不能证明客户502由谁产生，不能用状态猜代理/DB/CPU根因。

## 838唯一离线执行

命令：

```sh
PYTHONPATH=backend /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/backend/.venv/bin/python tmp/838_database_public_diagnostics/838_database_public_diagnostics.py --run --output agents/database/perf-public-c/offline-run1.json
```

工具源码d75866f...，输出tool_git_commit/工具SHA/13实际源SHA；导入只stdlib、无输出/数据库或网络模块。CLI无--run、试图覆盖原结果均真实拒绝exit2，不再次执行配方；这些是预期边界，不是产品失败。

本地内存SQLite使用从生产列类型复制的三张**专用合成表**，仅id主键，未装生产FK/CHECK或其余唯一/非空约束，未改生产metadata。它只验证生产Rows参数化SQL执行/配方输出，不是合法完整业务fixture、MySQL兼容或锁证明。固定项目1/2、依赖0/4/32、成员3/32和页1/4/32，未复制任何独立caseID/请求比例。SQLite表建立/填充及清理只在本进程内存库，不是云库操作。

|配方|实际Rows语句数|物化行/输出观察|
|---|---|---|
|C deps+前驱IN，度0/4/32|2/2/2|0/8/64；空IN仍Session.execute|
|未应用skip-empty前驱配方|1/2/2|固定输入输出相同；非全局Rows行为修改|
|未应用不消费依赖guard配方|0/0/0|只是候选控制配方，没执行生产动作/没证明错误优先|
|全project成员S锁配方，M3/32|1/1|物化3/32，MySQL方言编译LOCK IN SHARE MODE；SQLite不执行该锁|
|C依赖页P1/4/32，逐get|2/5/33|1+P查询|
|未应用依赖页batch配方|2/2/2|固定数据的输出/顺序与原配方完全相同；缺前驱两侧均失败、不默认satisfied|
|listTasks rows20+COUNT|2|33条同项目合成task，页20；未执行HTTP/model完整Schema|
|有序task X锁配方|1|MySQL编译FOR UPDATE，SQLite只验证读取|

共19个计数配方、71次Rows._execute（69 SELECT、2个顺序version UPDATE，另含缺引用失败路径读），不是71个验收测试或HTTP真实trace。顺序version更新rowcount1/0后rollback，只证明这个合成SQLite谓词，**不是并发CAS**。最终Session关闭/本地engine dispose。源码调用者由静态hash/行号链接，不把手写配方叫实际C端到端请求。

初次Ruff I001/B023三项工具错误原log保留，修为显式绑定loop默认参数并整理import，格式化仅838；Ruff再检通过后工具先commit再唯一执行。首个离线执行exit0，无重跑矩阵/负载刷数。

## 与后端的真实对接和下一阶段

BE已确认现有Rows rows/get/count/update/锁与ID列表绑定足够，无需新SQL门面；其独立候选5cc856d6fa94b1fdde32605543b53822f9747f00只改Workflow guard-specific加载，不动Runtime/Rows/global empty-IN/任何锁。BE自行报告模块红绿结果，本岗没有代跑/代称其MySQL/RC或正式通过。

优先顺序：先由BE复审guard不消费依赖动作的权限/状态/错误优先和空集合边界，root集成精确SHA后仍须单独回归；后续Tasks.addTaskDependency补project谓词/依赖列表batch/升级3N批读各自小设计，不能捆成无证据大改。DB当前生产净变更0，未声称已经降低公开P95或消除502。

真正MySQL阶段须先另冻结开发诊断配置/明确独立schema/源与fixture摘要、授权范围和资源窗口，再执行有限plainEXPLAIN及同次请求SQL/锁/池/资源关联；不用当前两机或839环境。正式400×600复测由独立流程另派，不让838替代。报告/Issue4只提出公开接口需求，不向839发送开发信息。

## 阶段收口与未来最小采样

root随后明确：两份资源文件已全部回收，由839独立联合复核；实例和系统盘于19:01实际释放，当前没有新云动作窗口。本岗未读取这些未具名公开的资源文件；不据此改变原失败/根因未知结论，不再扩大本地测试。

优先验证候选而非归因：①BE guard-specific仅减少无关动作deps/前驱读，静态局部成本明确；但契约校验特殊分支不经过Workflow，故它不能覆盖该组公开2个502或证明全局修复。②全project成员物化、必要project X/有序task X和事务持锁时间，必须控制同项目/同task热点维度才能判断。③池获取/新连/初始化/ping/commit/reset及worker总预算，不能把源码5+10等同运行值或用inclusive计时猜纯等待。④依赖/升级列表N+1是独立候选，不知道本次私有请求是否触及，不作为本次根因。

未来开发诊断要另冻结配置与独立schema，按request_id关联以下同次有限样本：入口→同步线程进入/线程active，认证各次、execute与fetch/codec分段，statement形状/次数/结果行数（不记自由正文/绑定值），事务开始/锁获取/commit关闭、当前schema的阻塞/锁等待与活跃连接，实际worker/池配置和物理connect/ping/close阶段计数，客户端完整状态/原错误及服务端日志关联，CPU/内存/网络与请求/响应字节。一次只改动作/依赖度/页大小/成员数/同task热点中的一个维度；初始化/预热/失败不隐去，before/after准确SHA。没有窗口与配置前不执行，不使用私有runner或被释放环境，不将SQLite/单请求结构差异写成云P95收益。
