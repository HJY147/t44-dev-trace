# 数据库当前候选：待全新 native CI

2026-10-29，`b9d15aca2d1716c0a85b1c5f4e5ff285a89f5dfb`，真实净减74（5880→5806/65files），仍超706；250–350减量目标未达。SQLGlot30.25.0 MySQL AST替换手写CHECK，完整签名与事务内通知executemany/engine分组落地；Frozen DDL/原生目录函数/业务/API门禁保留。内部CLI列诊断合并为 `column_definition`。

最终239本地模块测试通过/27 integration未选；18新owner、196表达式38416对等价差分、6000seed golden/V2、769双方言及通知批写/回滚证据已执行。Ruff/format/Bandit绿。本地不替代真实MySQL、全新镜像完整CI/coverage/HTTP或正式性能；统一native CI须实际消费MySQL全部CHECK显示形式。

[本轮完整紧凑报告](../../agents/database/final-20261029/report.md)；[结构化证据](../../agents/database/final-20261029/verification.json)。以下历史原样保留。

# 数据库模块：R29B本地查询注册候选，实减4，仍超783

2026-10-29；数据库AI，ROLE-database-DRY-R29B-20261029-v1。基准确a92e5e73，设计4e317333，产品/测试8f29030756139061341e0a636c8774ca790964bd，独立分支codex/database-dry-r29b已push。仅migrations._catalog_defects四项注册改成有序标签映射；所有SQL、预期/比较、CHECK/DDLhash/版本/锁、seed/Rows/scan/事务与原断言不变。

原固定cloc应用5887→5883/65文件，净减4，migrations374→370、persistence1661→1657。strict范围exit1，仍超783；没有百行或≥798安全去重方案，不称规模达标。完整AST仅规范化注册和循环解包后逐节点同；原文件/规格/计数器边界差异零。

新6精确父源差分与原本地persistence/812/消息980/扫描990+974最终联合133通过、43未选、3原警告52.26秒，含6000任务seed exact摘要和V2全量性质；先行56重叠不累加。限定Ruff/format/Bandit绿，初format失败、TLS push失败和探索/runner记录真实保留。没有nativeMySQL/完整CI/coverage/HTTP/独立/云或性能执行；待root review/取舍，不代合并。

完整[本轮报告](../../agents/database/dry-r29b/report.md)、verification/commands/原日志/JUnit/边界/计数在agents/database/dry-r29b/。[Issue4真实交接](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6489314712)已单ID GET逐字一致。以下历史不改。

# 数据库模块：R29 固定DDL适配局部候选，实减11，规模仍未达标

2026-10-29，数据库AI，ROLE-database-SCALE-R29-20261029-v1。独立分支 codex/database-scale-r29，从精确 f5e0d95e 派生，产品274e2e6b。只改 schema.py 的三份列表汇合与校验和保护下的固定声明分段；DDL/hash、迁移、Rows、锁、事务、鉴权重验、审计及seed规模与原测试均不改。

原source_count/cloc2.10对已提交源实测应用5898→5887/65文件、persistence1672→1661，净减11；两次范围检查exit1，仍超787，本岗争取100–250未达到。首个共用列投影实测净增3已否决，原件保留；不以格式化和SQL目录SUM冒充应用收益。

原模块与新增769最终联合168通过/43未选/3警告；新增41再跑通过，两组重叠不累加。18表双方言DDL/列/索引与20个冻结payload逐项旧源等价、checksum仍先于parser；原988无显式测试库配置17跳过，未称真实MySQL通过。完整CI/覆盖率/独立验收/HTTP/云性能未跑。缩进格式依赖限定在原checksum通过的现有DDL，新版本需重审；等待根审核是否采用。

完整[本轮报告](../../agents/database/scale-r29/report.md)、verification.json、原始失败/警告、计数和边界对象证据归档在 agents/database/scale-r29/。以下历史原样保留。

# 数据库模块：默认全列查询候选待根审核/CI

2026-10-28：准确基线a12，先行设计6a1cb86b，产品/验证源码82e92dfc420690980a6e16c88f209d08ab709e49。仅RowsGateway.rows默认tuple(t.c)→(t,)一行，SQLAlchemy2.1.6官方/本地三源字节相同；显式投影、参数/锁/排序分页、映射/事务及原schema审计不变。18表288对MySQL/SQLite编译签名同；最终新契约目标30通过，原persistence/812非integration138通过、17未选、2原警告；限定Ruff/Bandit通过。固定应用5933→5933，净有效行0，仍超833，不作规模通过声明。

原catalog审计七反例及31例原件完整保留，本轮没有重跑MySQL。根转PUBLIC纯构建ABBA约省5us/statement，不是当前候选的端到端/HTTP/MySQL/云结论。云仍a12；根review/完整CI/真实MySQL/独立验收/正式性能待调度。报告、真实命令及原件见[本轮报告](../../agents/database/select-resume-20261028/report.md)。AI改动，未代写学生研究正文。

[Issue4本轮实际交接](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6464790672)已发表并按单ID精确GET全文一致，原回执见本轮github-publication.json。

# 数据库模块：显式连接池配置待根审核/CI

2026-10-28：backend已确认委托，独立基b9847f8a，设计fb5d622d先行，产品/测试源92cf5c108ee549b35dda6d775e0357ded9e40743。只settings.py:mysql_settings新增T44_DB_POOL_SIZE/T44_DB_MAX_OVERFLOW的int转换，默认5/10逐值保持，无效文本拒绝、原MySQLSettings范围与URL/库匹配先验不改。新配置31+原目标7共38通过；旧源容量目标4红1绿原样保留，限定Ruff/Bandit通过；新engine lazy构造无数据库连接。

固定应用5933→5935/净+2，超835，strictLOC未过。未捆绑select(table)候选，原persistence/Rows/鉴权/事务/SQL与测试冻结完整不变。当前只有本地配置；下一云池预算须实际查max_connections及其他角色，未云/未SUT/未HTTP/未性能。完整证据见[本轮报告](../../agents/database/pool-config-20261028/report.md)。

[本轮Issue4交接](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6467541006)已实际发表并单ID精确GET全文同，回执在本轮github-publication.json。

## 历史：原生目录审计修复

2026-10-28：先行设计cacd03b1，最终应用源26d6328ab882b06eb9f6026a29656999e122f57d。原schema反射漏判DESC、自增、引擎、表/列排序规则、CHECK执行性及必需索引可见性7项已在全新socket-only MySQL8.4.11真实复现并修复；31原生case（8兼容/23负例）符合原要求，最终53针对目标通过。先前7c94版完整本岗非integration106通过、17未选择，结果不相加。新增4条固定只读catalog查询；DDL/API/冻结/锁与marker协议不改。限定Bandit先因B608失败，改完整字面SQL后绿，不放宽门禁。固定cloc当前5933，较5862净增71，仍超833；这是正确性修复，不宣传减量。

四个自有临时实例已正常停止、数据保留，原PID7980/13306不操作。完整CI、覆盖率、根复审、Linux及正式性能/独立验收仍未运行；原始红/绿与精确源、提示词、恢复差异和运行边界见[本轮报告](../../agents/database/catalog-audit-20261028/report.md)。以下保留旧阶段历史，不能用其当前字样替代本次状态。

## 历史：OUTPUT-EXCLUSIVE-01窄修复待复审

数据库AI，ROLE-database-OUTPUT-EXCLUSIVE-v1。原c4e8 P2保留，root暂不整合；设计3981e6d先行，窄source `3fc58d18614c394cc588a16b316cf89c1810ecf1` 仅838/836两文件。

- 旧exists→finally路径w写会覆盖后出现结果/跟随悬空link，836零DB main旧源真实2红；首次basetemp父目录缺失2setup errors另保留，不算产品红。
- 改为一次O_CREAT|O_EXCL|O_NOFOLLOW/0600开叶节点，持固定fd写JSON，不重开路径/截断/失败降级；fdopen失败close，recipe异常记失败后原异常传播。已有对象/竞争新结果拒绝；路径替换只写原inode，不能承诺外部路径名不可变。
- 源commit后836全11pass/0failure/error/skip，每main断言DB/application导入为空；一条原JUnit warning保留。两源Ruff/format通过，未执行真实recipes/19矩阵/SQLite/MySQL/HTTP/负载/全CI。
- 15份c4e8原公件/旧prompt、原recipes/provenance逐字不变，旧71Rows/旧E seal保留。新[报告](../../agents/database/output-guard/report.md)、verification/fs观测、红绿日志/JUnit及evidence-seal.json归档；不以旧矩阵证明新工具全套通过。
- [Issue4阶段评论](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6383619265)已精确GET全文同。等待原审核岗对准确SHA复审；未关闭P2，不将输出guard修复称性能/502修复，生产及原公开性能失败不变。无私有env/独立用例或root工作区写入。
- 全量diff-check因原始失败log/XML尾空格exit2保留；源码/说明限定check exit0，未修剪原日志，未冒称全量检查通过。补充E seal不改窄source3fc或测试结果。


## 2026-10-25 请求级诊断首阶段

- 设计df6fa10、诊断源edc3e2a；见[本阶段报告](../../agents/database/performance-20261025/report.md)。仅tmp/833诊断代码，无生产/DDL/API/池或锁变更。
- 实际同6个hook回归在时钟修正前后均绿（非12独立测试）；两次有限SQLite各6请求/12cursor语句/242映射行，记录保留。最终样本wall0.295–1.037ms，只验证toy行和仪表，不是HTTP/MySQL或云成绩。
- 各层UTC/perf/mono/threadCPU、生命周期及形状哈希已供后端/root组合；计时inclusive，单engine/Result范围明确，不能从acquire或cursor时间猜纯等待。
- 本机无Docker，不连接既存库；root仅准入后续freshCI t44_diagnostics，新MySQL/HTTP尚未执行。原云失败、0完整组、规模超限不被本阶段关闭。

## 2026-10-25 公开MySQL分层和项目S候选开发验证准备

- 本岗读取并核root真实freshCI40169575755公开样本，56精确join/48measured；不是自己运行MySQL。SQL数9/10/4/27或29，消费/codec CPU较小；transition底层commit3.785ms/CPU.165ms只说明此样本非线程CPU时间，未定位旧云锁/502根因。详见[报告](../../agents/database/graph-lock-20261025/report.md)。
- 项目S只允许三个读图action、writer仍X、members/target/pred锁不减、全程不升级；sorted IN/ORDER BY不是实际取锁全序证明，有限样本不抬升为安全准入。
- 设计9e0caf2、最终工具源3e11b1a交root/BE，6个真实MySQL低层probe待root freshCI执行；本地同8guard/join检查通过、首轮测试类型错误原JUnit保留。没有生产或收费资源改动，正式性能和规模出口仍未关闭。

## 同日后续：S+point修订

- root/BE修订为sorted unique逐个scalar id+project/limit1 X，D前驱新增D锁SELECT；本岗先24ca1db设计勘误后ee12656工具，仅tmp/833观察/验证，不改生产。
- batch/point真实gateway与cursor形状/序列断言、真实捕获SQL的EXPLAIN、P_S三表readiness已供freshCI；本地仍同8guard绿，不是MySQL分支/race通过。新增[修订报告](../../agents/database/graph-lock-20261025/point-lock-report.md)保留旧source证据，明确显式task请求顺序与其他内部/FK资源边界。

## 同日新性能库fixture准备

- 设计2f6c1f9/工具d8addfd，复用冻结seed显式Collector，在root唯一授权新库一次准备并读回40P/6000T/9000E/11400reviews+3600decisions=15000，assessments额外3600；原18业务表空、schema18/226前后通过、35FK及指针/轮次/组状态核验。仅数据准备，不是性能/独立验收。
- P1集中400DEVELOPING future与400disjoint overdue，其余5200分39项目，偏斜和压力组无依赖明确公开；5合成用户/800ID及seed/anchor/source/hash在[本轮报告](../../agents/database/performance-fixture-20261025/report.md)和public-inventory。生产/DDL无变更，8:04:21后本岗未再写库；root后来签5身份会话单列。恢复只封E，无新增测试/SQL。

## 2026-10-25 实际源码规模优化首批

- 独立树codex/database-size-optimize-20261025，935产品基线。seed默认构造/注解与按需buffer、migrations目录/完成路径、Rows比较/结果集合校验、Outbox双阶段claim共用算法，保留public接口/DDL及guard。
- 原cloc2.10净省48，400–500目标尚未达到；不压格式/改统计。新迁移差分9场景和claim差分7场景保留SQL/commit/锁顺序语义；原975小/6000固定全库摘要保持。详见本岗[size报告](../../agents/database/size-optimize-20261025/report.md)。
- 仅开发SQLite/mock验证；最后seed冻结插入顺序补充待验证。原云/独立/规模门禁未关闭，组合CI由根统一执行。SQLGlot仅根准入下一小原型，首批未新增依赖。
- 首批手工汇总纠正：原JSON持久Python1691→1642净49；第二批使用冻结DDL默认省19，累计1691→1623净68。新默认值基线差分3+原980非integration12通过；原975最终锁序全量3通过，后续active默认的小seed2通过，大seed未重复。
- SQLGlot严格425差分原型撤回：完整投影只省9，离线590次解析约13.4倍耗时；未改生产导入/依赖，无计入。根准入另版seed算法，但仍需先设计/实测，不将预期计成果。

## VERSION2 seed候选待根取舍

- 独立分支codex/database-seed-v2-optimize-20261025，稳定回退5f77938。slot时间轴、通用证据注解、派生ID/指针列和DAG枚举，VERSION2与旧marker拒绝；public CLI参数/结果键不变。seed348→326再省22，累计产品持久Python1691→1601净90，未达到额外80–120目标。
- 新全量性质13场景33.10s通过（实际包括6000任务全35FK/JSON/角色/指针/版本/时间、另空库batch127重现、版本marker/无写参数与rollback）；首轮2红是新增测试统计了只读UoW，改到seed结束立即核单commit，红保留。随后新增旧marker直接读取拒绝，当前源该小变更仍需再验证。
- 原975业务断言未降低，按VERSION选择快照；V1两golden与935来源显式保留但当前未执行V1历史代码。V2快照在语义/重现性质后才冻结；旧黄金小数据真实红保留。只是开发候选，无MySQL/独立/性能或组合CI成功声明。
- 最终精确1076677当前源975/新性质小目标14绿1.84s（2未选）+975默认6000单目标1绿25.95s（2未选），原JUnit warning保留；原全性质13绿属于最后旧marker查询保护前，分范围记录不相加。
- 原计数器当前完整产品6245/exit1，净90仍超1145；持久签名AST全同、冻结specs/DDL净差异0，Ruff通过。两分支已push；[Issue4交接](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6397356591)单ID GET全文一致。根待采用稳定68或V2额外22、精确审核与CI/freshMySQL；不称规模/独立/正式性能闭合。


2026-10-31 / ROLE-database-CLAIM-NATIVE-20261031-v1：真实MySQL8.4.11/RC拒绝INSERT-first候选，16同key出现11个1213，原90b同场景及后续10检查通过。原pool rollback/durability不减，独立socket-only server已停，无云或产品修改。详agents/database/claim-insert-first-native/REPORT.md及原PUBLIC。


2026-10-31 已锁任务复用候选a59a90a1开发原生RC正确性通过，12并发1成功11版本冲突、最新锁行可见及上下文拒绝；原夹具缺证据422保留。非压测/独立验收，详agents/database/locked-task-native/REPORT.md。

2026-10-31 global DB latency: disabled-by-default acquire/execute_fetch/commit/rollback/close wall+CPU spans;69 existing SQLite+5 synthetic boundaries pass, real P95/root cause unproven. No cloud/durability change. See agents/database/global-latency/REPORT.md.

2026-10-31 GET dc556cd3 native MySQL8.4.11 actualRC four auth/expiry/validation priority checks passed; own socket server shutdown0, no cloud/HTTP/P95 proof. Raw getrc1.PUBLIC.json retained.
