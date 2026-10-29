# R29B 本地 catalog 注册候选：真实净减4，规模仍超783

数据库 AI；ROLE-database-DRY-R29B-20261029-v1。基准 `a92e5e73da93ba23748c3bab113103036c395d50`，设计 `4e317333eb93f9c7fa768b68fbbaf2096ea69fa3`，产品/测试 `8f29030756139061341e0a636c8774ca790964bd`，分支 `codex/database-dry-r29b`。没有代根合并。

唯一产品改动是 `migrations._catalog_defects` 四项查询注册从 `(label, query, expected)` 序列改为 `label: (query, expected)` 映射，按 `.items()` 原顺序执行。标签静态唯一、Python 3.12 dict 保序；没有增加辅助层，删除四份重复的三元组结构。四份 SQL、预期签名构造、缺陷比较和异常传播逐字不动。不是把多个语句挤到一行，不移动实现到被排除的资源。

原 cloc 2.10、原 hash/分类/范围计数器实测：基准应用5887/65文件，精确产品8f290307应用5883/65文件，净减4；migrations374→370，persistence1661→1657。两次 `--require-range` 均 exit1，仍超5100上限783。没有找到≥798或百行安全去重方案，不能把这个小整理称为规模闭合。

职责约束：完整AST在仅规范化这两处注册/解包结构后逐节点一致。seed、rows、scans、schema、DDL、engine、UoW、依赖、全部原有模块测试与812断言、规格、CI和计数器Git差异为零，见 boundaries.json。CHECK优先级/原生catalog层、DDLhash/版本/锁、SQL白名单、session/事务/幂等/保存点和seed exact数据性质都未删改。

实际验证：

- 首轮新增6个精确父源差分与原794/956/812迁移顺序/claim共56通过，1.25秒。不是新增56项测试。
- 产品提交后，本地新6+原 persistence/812/消息980/扫描990和974联合133通过、43未选、3原警告，52.26秒。包含原975默认6000任务摘要与V2全量关系、角色、指针、时间、重现和批次性质。首轮56与133重叠，不相加。
- 新差分复用本岗公开794 fixture，对比精确a92e源码：成功、四类组合缺陷顺序、每一个查询阶段 OperationalError 的完整SQL前缀及连接上下文退出。不是MySQL反射/原生库执行。
- 限定Ruff/Bandit和产品格式检查通过。首次格式检查对新增临时测试/runner失败；只格式化这两个新增文件后重检，生产migrations从未借格式化减行。

真实失败与修正：第一次定位误用不存在的 services 路径、随后误读不存在的812文件名，均是探索命令exit1/2而非产品失败；真实输出摘录在 exploration.json。首次源码push因 LibreSSL SSL_ERROR_SYSCALL exit128，随后相同命令成功，远端branch指向8f290307。最初Ruff和format两次runner同时读写commands.json使Ruff首轮结构行丢失，原stdout/stderr仍在；runner现额外逐命令写独立JSON，最终顺序重检有完整回执。没有把这些失败隐藏或计入成功。

未做真实MySQL、完整CI、coverage、HTTP、独立验收、云、正式性能或新建数据库连接；没有读取PRIVATE/未公开独立测试，也没有联系测试岗。原43个integration目标未执行，不称其通过。

可审查性和取舍：这是低风险、有限收益的小候选，可由根决定是否采用。seed任务/评审先插入、指针后回写对应循环外键，不能直接删去第二阶段；Rows批量insert/update参数与结果契约不同；反射与native catalog检查互补，不能当重复移除；scan启动幂等保存点和checkpoint锁事务职责不同。没有为扩大数字移除这些门禁或合并不同职责。

封档检查：全量 `git diff --cached --check` 真实exit2，原因是push成功的原始stderr有4行GitHub `remote:` 尾空格；原字节保留，不修剪日志。排除原stdout/stderr/JUnit的源码、说明、JSON暂存检查exit0，两个检查各自原输出归档，不能写成整包diff-check绿。

上下游契约：所有public函数签名、错误文本和冻结接口/DDL不变；无新输入输出或依赖。未解决项仍是严格LOC超783及根对精确源码的review/组合CI决定。完整命令、原stdout/stderr、JUnit、源码绑定和计数见本目录；Issue4真实评论回执单独归档。
