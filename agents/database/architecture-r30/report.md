# R30结构候选否决：净增15，已恢复原产品

数据库 AI，ROLE-database-ARCHITECTURE-R30-20261029-v1。精确基准7374b3637b06465d448fc2e81952ba18fc676315，独立分支codex/database-architecture-r30。设计bd819c57，实际原型009b7acdbfa0e0497d7cc36bbbae86805283dcfd，撤回4a1acafbc1b895a3df5f6cdbf6e47b59b546fb1d。**不采用009b7acd；当前产品已恢复基准原字节，没有净减产物。**旧R29B封档不改，不代root merge。

本轮读完整个persistence，而不是继续几行注册/缓冲微调。实际编写并提交统一catalog快照：五份固定INFORMATION_SCHEMA查询取表、列、完整索引、CHECK及FK记录；同一TABLES预期投影为同形快照、统一features比较，替代旧Inspector→临时dict→signature及native两套构造。原_index_signature/_foreign_signature中间层确实移除，但新增行形状、类型/默认值、FK、集合/完整顺序和报告标签适配消耗了同样代码。

规范格式后的实际Git差异+185/-169、物理净增16。原cloc2.10/原hash/原source_count对精确009b源码实测应用5895/65文件、migrations385、persistence1672；恢复后精确4a1实测应用5880/65文件、migrations370、persistence1657。候选有效行**净增15**，撤回后相对根**净0**。两个严格范围命令均exit1；恢复后仍超5100上限780。没有找到安全百行方案，没有包装成优化成功。

实际检查与失败：

- 候选py_compile exit0，模块真实导入、TABLES快照构造和feature投影 smoke exit0：18表、226列、146索引行、59 CHECK行、55 FK列行、1286个feature，无构造冲突。这些是行/投影数，不是146个索引或55个FK约束，也不是数据库执行或行为验收。
- 原_check_signature及migrate完整函数字节相同；规格、DDL/hash源、Rows/UoW/seed/scans/accounts/delivery/engine、依赖、全部原模块测试/812断言、计数器与旧R29B封档Git差异零，见candidate-boundary.json。
- 候选Ruff真实exit1，SIM102一项嵌套if，原输出不改。因候选已经净增而被否决，没有为这项风格错误继续制造一个小减行版本，也没有称静态全绿。
- 原794/956尚依赖旧Inspector/native fixture注入点。没有迁移或修改任何原assert/负例；由于量度已否决，不再提交测试输入映射申请，不运行这些已知需迁移的白盒入口来制造无意义红灯，也不靠改期望值变绿。

这不是已验证兼容的新架构。原型的实际MySQL行规范化、缺陷标签/顺序、索引冲突与FK选项等仍需全量差分和真实原生库验证；当前仅证明构造可运行及受保护函数未变。净增已经否决其规模价值，无须再占用root的免费原生CI协调轮次。没有pytest、build、benchmark、coverage、MySQL、HTTP、独立验收或云执行，没有PRIVATE/未公开测试读取或测试岗联系；未安装新依赖。

释放门之前只阅读/设计/编辑（含formatter编辑）；收到root明确释放后才开始计量、Ruff、语法编译及构造smoke。未触碰独立工具进程或其他worktree。原型保存在准确Git提交，撤回只恢复本树migrations.py；没有回写或删除历史候选证据。

其他结构取舍：SQLAlchemy已安装2.1.6；TypeEngine.compile是公开渲染能力，但Table/Column身份比较不能替代所有字段/约束语义，也不能消除native属性检查。UoW自有状态包含单次使用、rollback-only和commit-uncertain/cleanup优先级，不能直接用Session.begin上下文删掉；seed先行插入和后续指针回写对应循环FK，Rows白名单/结果校验不是重复业务功能。本轮没有把这些必要边界删去，也没有引入SQLGlot/其他依赖或改变技术栈。

上下游：最终gateway/UoW/check_schema输入、输出、错误、版本与基准完全相同，无跨岗接口变更，无fixture迁移要求。开放项仅为原严格LOC超780及其他根调度工作；本岗没有可交付的百行减量方案。四件、真实prompt、commands、原输出、计数、边界和GitHub实际交接回执在本目录。
