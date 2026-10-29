# 项目 S + 逐点 X：设计勘误

数据库 AI，root 明确准入工具/设计，生产 Runtime 仍由 BE 负责。原 9e0caf2 的 S+batch 风险结论保留；本次只针对 root 后续修订：三读图 action 项目 S，writers 项目 X；Runtime 原 target+pred 集合统一 sorted(unique ids)，逐个 `g.rows(tasks, {project_id, id: scalar}, limit=1, lock=update)`，全部完成后原 Business 锁后重读。非图本来只有 target，一条点查询；D 个前驱增加 D 条锁 SQL，成本不能省略。

## 正确性边界

- 单条 WHERE 包含全局唯一主键 id 等值与项目归属，至多匹配一行；多个任务 X 请求顺序由逐条语句而非 optimizer 对 IN 的遍历顺序决定。项目/成员/会话/idem 顺序与不升级 S 的约束不变；项目 S 持有期间 graph writer 不能改变这次已发现的依赖集合。
- 同 predecessor 的 reader 仍 X 串行；不同 target 只在全部 target/pred 集合不相交时并行。某个多行集合不是原子一次获得，可能先持低编号行再等高编号；正确性不要求一次获得，但只有全部获取成功后才允许 Business 决策，异常必须由原 UoW 回滚，不能返回部分成功。
- 在当前 Runtime、Tasks、Workflow、Projects 路径审查中未发现此修订新增的结构性反例。该判断不是所有 FK/数据库错误的全域无死锁证明。原非图写无显式 project 门，审计/outbox 的隐式父行锁、既有 writer 路径仍需真实业务 races。没有扩大成全局 Rows 改写，也不顺带修其他旧路径。
- 单点访问也可能涉及 secondary/clustered/FK 内部记录；我们只证明不同任务 id 的显式锁请求顺序，不把这句话扩大为全部数据库资源都有同一全序。

## 工具修订

新参数 `--expected-task-lock-shape batch|point`，分别用于原 X/batch 与新 S/point。在每个真实 Runtime.locked_scope 内只对该 UoW 的 gateway.rows 做透明观察，并在同线程的 SQLAlchemy before_cursor_execute 采实际 tasks FOR UPDATE statement 形状哈希。输入 id 只在内存比较，不输出绑定值。baseline 必须真实一条 batch selector；candidate 必须逐个 scalar/limit1、ascending unique、集合相等；不能凭参数自称执行了点锁。

EXPLAIN 改为对实际捕获的可信参数化 SELECT 与原参数执行，不再构造旧 batch 查询冒充候选；每种形状有界一次，输出仅 shapeSHA 与 plan，SQL/绑定值不写证据。交叉两共享前驱、反向编号不交集、实际 P_S wait resource 断言保留。观察包装始终调用原方法，finally 恢复，不更改锁/结果。

fresh CI fixture 前运行 P_S readiness，权限/表/列错误单列环境阶段，不能算锁竞争失败。最窄表级权限为 SELECT on `performance_schema.data_locks`、`performance_schema.data_lock_waits`、`performance_schema.threads`；不需要 `performance_schema.*`、PROCESS、UPDATE 或 instrument 配置。官方依据：[P_S表权限](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-table-characteristics.html)、[threads不同权限模型](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-threads-table.html)、[等待关系](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-data-lock-waits-table.html)。权限需由 root 在本次 fresh service 授给实际诊断账号，本岗不执行 GRANT。

仍只做同8个工具 guard，新增观察分支通过参数形状与静态检查准备给 root freshCI 实跑；不在本机执行 MySQL、不碰13306。真实两个库的准确名字由 root 决定，未收到前不扩目标allowlist。所有旧封条、失败、报告仍按其原 source 保留，本次另建回执封条。
