# 公开C短窗性能失败：数据库路径审查与可重放诊断设计

数据库AI；ROLE-database-PERF-PUBLIC-C-v1。独立codex/database-perf-public-c，基root6d02cf1d3b99b15556c5d74e007cb4d8d546bbf9；生产根相对被测C0dfb55c2191200d947c5423fd9ee74bb0812cc5a差异为空。先设计commit，再实现/运行阶段。

仅明确获授权的839_PUBLIC_MINIMAL_FACTS_v1.md已核sha c35b37f47d822ef82b4f05627627a2b1f42eb7388c4f2a83d6c13493c5350d4a后读取；不读取839其他文件、私有用例/输入/原始资源，不向839/测试实例传开发信息。公开事实：400在途峰值；任务组短窗流转P95 3645.763385ms、查询3315.969690ms，10814稳态1个502；契约组预热7273中2个502、稳态0；完整正式组0。资源采样待具名公开，502层级/CPU/池/DB等根因均未知。

## 先行路径审查

1. 只读当前生产SQL门面与调用者，固定每文件Git/hash/行号；区分SQLAlchemy SELECT、UoW/commit、物理连接初始化/ping与实际网络往返。按函数列出索引支持、N+1/全量读取、CAS/锁顺序和池默认配置，不用旧5dcb的3UoW账本解释当前C。
2. C已有Workflow依赖where project_id+task_id，用已有复合键；不能再宣称是新优化。两次实时read认证、fresh write2UoW/3次auth、session→idem→project(必要)→成员有序→tasks有序和同事务audit/outbox/COMPLETE、独立拒绝事务/CommitUncertain语义保持。
3. BE负责guard-specific依赖加载与同事务重复task读取候选，DB只给安全绑定/索引与门面边界，不改services。scheduler/MQ的列表附加读须各owner设计，不能自动截断收件人/漏COUNT/更改RC快照/错误优先。当前不改DDL/索引/池/隔离/锁/认证；无反例/收益前不写推测修复。

## 可重放诊断（独立开发夹具，非839复现）

- 先实现纯静态SQL-shape/调用记录器与原生MySQL EXPLAIN路径，使用现有RowsGateway/Core元数据，不造业务存储，不记录Token/口令/自由正文/绑定业务值。工具仅显式运行，导入零连接/负载。新文件编号先报root分配；诊断工具放tmp，不进生产口径，业务SQL若优化仍须owner实现并计数。
- 夹具使用自有开发库/新隔离项目schema（root确认准确库与资源窗口后才SQL/HTTP）；不访问独立数据。独立构造有限项目、成员、同项目DAG/状态/证据，不复制私有caseID或请求比例。每次输出sourcehash/fixturehash/schema/index/参数维度/SQL计数/错误/资源采样同次关联。
- 基线形状：listTasks页20/100及COUNT，依赖0/少/多，BLOCK与真正需要依赖的START/UNBLOCK-DEVELOP/REWORK；分别给页大小/成员/图规模，避免把P95从不同操作混起来。先有限单请求SQL次数和plainEXPLAIN，不带ANALYZE；然后有界开发并发仅root给窗口才运行，不能替代400×600正式验收。
- 优化至少先保留旧源对等自有输入/输出/错误/审计/幂等/版本/锁序与安全负例；有完整设计且DB源码确有可消重复SQL再实现。旧断言不减，不用mock/SQLite冒称MySQL或性能；before/after均精确SHA，不把初始化/预热成本隐去。

当前阶段是设计与静态审查，不运行任何数据库/服务/HTTP/负载/测试，不读取或操作root工作区文件（仅获授权public单文件只读和Git对象读取）。后续实际诊断目标和新工具编号由协调调度，不因缺私有资料自行扩大权限。所有原失败、未验证/待资源项保留，GitHub Issue4公开具体对接并精确GET读回。

## 协调明确本阶段准入与工具838

root实际回复：“诊断工具使用新编号 tmp/838_database_public_diagnostics（最新号递减）。本次两机只保全证据、19:00自动释放，不再准入SQL/HTTP/负载。可先做源码shape计数与本地自有临时SQLite/合成schema诊断，严禁连接私有云env或私有独立用例。真实MySQL执行需另冻结开发诊断配置/独立schema再跑，不把SQLite/静态视为云数据库证明。现阶段先保真实可重放设计/静态证据与backend对接。”

因此本轮838只实现显式CLI、零网络/零env/零凭据、临时内存SQLite的生产RowsGateway观测与MySQL方言编译，不实现HTTP/负载/MySQL连接模式。工具在tmp/838_database_public_diagnostics/838_database_public_diagnostics.py；导入不建连接。SQLite专用合成表只为查询shape/行物化计数构造，不装生产FK/CHECK，绝不改冻结元数据或冒称MySQL约束/锁/CAS实测。

固定有限维度：依赖0/4/32，比较当前生产deps+IN(empty仍execute)二读配方与BE候选的不需要依赖动作零读配方（只说配方，未接生产动作）；成员3/32的同project全量读；依赖页1/4/32的逐前驱get(1+P)与仅作为候选的batch(2)；listTasks页20+COUNT形状；CAS version谓词MySQL编译，锁SHARE/UPDATE编译。捕获SQLAlchemy statement形状和SELECT数/物化行数，不保存绑定参数，不测/宣称耗时收益。

工具验证范围：导入无输出/连接、源码对象hash、固定小夹具输出/顺序与缺引用失败、分页/排序/predicate及empty-IN语义；数据仅本次内存库，事务清理总dispose。所有诊断配方在报告标“静态/SQLite/未应用候选”，不把模拟调用数写成HTTP真实trace；源码实际调用者/锁序由静态receipt链接。不会自动测试839私有输入或解释502层级。BE guard-specific实现和新MySQL窗口另由协调推进。
