# 数据库模块：OUTPUT-EXCLUSIVE-01窄修复待复审

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
