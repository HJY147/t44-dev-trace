# ROLE-database-ARCHITECTURE-R30-20261029-v1

实际操作者：数据库 AI。总协调本轮任务原文：

> 下一阶段固定数据库岗R30：当前5880仍超780，R29B小候选已受审合入且0b原生CI全部通过。不要再做仅几行注册/缓冲微调。请从root7374b3637b06465d448fc2e81952ba18fc676315新建隔离 .agent-worktrees/database-architecture-r30 / codex/database-architecture-r30；旧R29B封档不改。你的范围整个 backend/t44/persistence/（不改资源DDL/SQL/冻结规格），寻找职责/结构层面的实际百行减量，例如复用现有SQLAlchemy公开能力替代自制中间层、统一同一元数据/检查逻辑或可证明冗余的构造，实际可运行候选而非只写RFC。内部组织可以调整；对外gateway/UoW行为默认兼容，任何跨岗内部接口变化须先root登记让owner确认。绝不能删schema原生检查、CHECK语义、hash/版本/锁/SQL白名单/保存点或业务安全断言；不能删除功能、挤行、移实现到excluded SQL JSON或改计数口径。已有库API可用，新增依赖/改变栈先准确方案及版本依据给root，不自动安装。若原测试因内部组织需要迁移，先列保持原断言的方案给root，不能单改弱化。先形成一个代表新结构的实际候选及真实净差；若无百行方案就如实说，不编造收益。
> 独立工具本机完整校准正在运行约至06:50Z，为避免CPU干扰，暂仅阅读/设计/编辑，不运行pytest/build/基准/大计算；等root发释放门再检查。全程本地、无云、PRIVATE/未公开测试不可读，不联系测试岗。建议新测试tmp/762_database_architecture_r30，先查占用保持递减；四件/prompt/GitHub issue或draft PR/真实失败与阶段commit照旧。先尽快报告有根据结构方案及首个实际diff。

设计范围准入原文：

> 登记R30设计方向准入：可做本地未集成候选，以同一TABLES预期+固定INFORMATION_SCHEMA快照替代双套反射中间层；migrate/DDLhash/锁/原CHECK语义不变。允许准备794/956白盒fixture注入点/行形状迁移，但先产逐项映射清单（原test名称、原全部assert/负例、旧输入→新快照字段），给root审核后才动原测试；断言/负例数不得减少，不靠改期望值变绿。先候选diff，原tests暂不改。需特别保留原精确frozen index列全序及长度/可见性/种类、unique集合和冲突、主键仅id、FK完整集合含跨schema/动作规范化、类型/unsigned/fsp/default/nullable/charset/collation、CHECK enforcement及语义、允许/拒绝额外对象的原行为、defects报告兼容；仅expected子集逐行查不能漏掉同名索引追加列等原先能抓的问题。全量行为差分与原生MySQL专项在重检查门释放后跑；此方向只影响迁移/校验，不能声称HTTP性能改善。仍无云/PRIVATE，别联系测试岗。

重检查释放原文：

> 释放R30本地重检查门：独立工具实际06:49:05Z runtime写出并进程exit0，稳态计时和后置均结束、4验证进程停止；仅剩确定性证据认证，不再采时延。可跑自己的候选差分/静态/计量。原794/956测试仍需先逐项输入/全部assert负例映射清单交root审核，不单改断言或直接移植。原生MySQL可用现有免费GitHubCI（root集成后单次协调），不要启动云。

实际方法及改进理由：查整个持久层及已安装SQLAlchemy2.1.6公开TypeEngine.compile源码，否决用Table/Column对象身份比较代替真实约束语义。准入后实际编写统一catalog快照候选，包含完整索引行、列属性、FK集合及CHECK语义/执行性；先用规范格式和固定cloc量度，不把SQL长行或raw中间结构视作收益。净增就保留实际差异并拒绝，不为继续验证而改写原断言。未声称本轮已找到百行方案。
