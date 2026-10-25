# 本轮实际任务（归档标识）

> 新内部架构探针（先设计/原型，不改产品/旧冻结/计数）。项目现f4bd382d4668130793fc553df9ce6363c4656ea6，应用5862、超762，原seedV2/迁移默认字段90行削减已合且695CI+Docker过。固定cloc/保护功能/原MySQL13306不可动，禁止独立799/800/805/809/814 PRIVATE/runtime。请新worktree codex/database-canonical-ddl-probe，tmp796_database_ddl_probe。探查迁移约303行是否能真正用**已存在的MySQL服务器规范化输出作为DDL标准解析器**替代大段自写SQL parser：例如来自冻结schema.sql在受控pinned MySQL8.4真实生成的SHOW CREATE规范期望/结构反射契约（数据摘要是契约数据，绝不能把业务实现/函数塞JSON/SQL字符串骗行）。只允许忽略数据增长的表级AUTO_INCREMENT计数，列auto_increment/default/null/type/index/FK/CHECK35/engine/collation等任何有意义漂移必须保留检测；记录并完整比对所有原正/负兼容用例，不能借更严格hash默默拒绝原支持等价DDL，不能信任可被既有DB漂移污染的marker作基准，不能新建未授权数据库/索权/拉新paid资源。你可离线结合公开原tests/官方MySQL/SQLAlchemy文档调研、独立可抛**自己tmp SQLite只做非MySQL性质**，真实新MySQL实验必须先给root命令由root审批明确新资源（不要碰13306/根云）。把对pinned8.4与原声称8.0兼容/目标选择误差/生成reference成本/需要增加多少源码的净账说清。若无法保持原语义或只是逻辑迁移/换错误拒绝，明确拒绝这个路线，不为762强推；若可真实净省100–250且原契约行为完整，先给root设计/I/O/证明计划和预计净账再执行产品变更。模块报告/WORKLOG/handoff/prompt/Issue4留真迹，没做就写没做。目标是找可信架构变化，不反复做几个单行微调。

操作者数据库AI；非用户亲改，不将旧CI/原生MySQL结果算本探针执行。

## 总协调本次实际新资源批准

> 批准你**独立socket-only临时校准**明确两新DB/自有tmp796新datadir/10min硬停128M、不绑定TCP、不操作旧PID7980/13306/oldschemas。根刚实际核binary --no-defaults --version：/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/mysql-8.4/mysql-8.4.11-macos15-arm64/bin/mysqld => MySQLCommunity8.4.11 macos15arm64。这是唯一本次.runtime例外：仅执行这个已在用官方binary及其随包必需shlibs/plugins（明确--basedir同mysql-8.4.11-macos15-arm64），不得读任何旧datadir/config/日志/凭据、不要扫.runtime目录。其它私件禁令不变。先自己的新--initialize-insecure datadir，再--no-defaults --skip-networking --mysqlx=OFF --socket自己tmp下短绝对path（mac UNIX path长度限制，用项目根tmp796子短路径不要目录外/tmp），--pid-file明确ownpath，每次证实PIDdatadir属自己才停；不删除失败datadir或隐藏红。校准后只保留数据/关闭自己PID，不推预期。官方SHOWCREATE NOACTION/RESTRICT正是要保持原兼容性的反例，不能默默严格拒。结论无正收益也如实收口。

## 总协调对限定夹具修正的实际批准

> 批准同一已限定socket-only校准的新data2/s2/pid2，2个获批schema，570+30秒/128M/无TCP，唯独复核7个FK夹具拆DROP/ADD后真实正负差异；保留run1失败数据，禁旧PID7980/13306依旧。不要再问这类已在限定私有临时资源内的夹具修正/重跑；后续同scope小问题你自主修正，证据不可覆盖。如又增第三轮请使用新data3且同限制，只有范围/权限/费用变化才交root。原rawhash已被有效原生正例反证，不要为宣传收益把等价DDL改判不兼容；B标准结构归一化若净账不够就准确收口，别扩大多轮测试耗时。谢谢。
