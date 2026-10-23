# ROLE-database-POOL-RETENTION-v1：实际派工

来源总协调实际续派；操作者数据库AI，不冒充学生本人研究或手改。当前任务仅设计/静态/工具先提交，实际执行等root窗口。

> 新受限诊断任务，复用数据库岗，新独立worktree/branch从当前root(含backend ff7ffa已merge)出发。先读 specs/changes/pool-retention-diagnostic-rfc.md（root61b23e6先行设计），及公开 agents/backend/bc5-contract-diagnostic/result.md/continuation-summary.json。仅核锁定SQLAlchemy2.1.6实际pool源码+官方主来源并设计/实现一次工具参数ABBA；生产仍精确bc5，绝不改默认池/冻结/SQL/锁/全局资源。假设5保留+10溢出频繁建连，比较15保留+0溢出，峰值都15，代价更多空闲连接如实。只t44_profile/18083/1worker/已有privatefixture，复用955最小扩展、不新编号（如必须新工具先告诉root分配869）。一次ABBA并发32、每段1s预热+4s稳态，总≤120s，具体源/命令先commit；所有错误原样保留，四段P95不平均、不正式归因。先设计/静态/工具阶段提交并报告就绪，实际比较须我发执行窗口（native岗也在写360秒serve验证，不能同时跑本机负载）。可以用既有本岗DB账号与root已授予backend profile private env/fixture，但值不可输出；未开放独立私密资料。与backend通过Issue4/3真实对接，写本岗prompt/log/report/handoff/阶段commit，不伪造学生行为。

改进理由：在既有开发观测之上提出新的可证伪连接生命周期假设，先核准确依赖源码/总连接预算，并明确预热、稳态、清理/错误及未执行边界；不把旧正式失败归因给本机观察，不直接准入生产池改动。

对应产物agents/database/pool-retention/design.md、source-verification.json、原955最小扩展及本岗阶段记录；尚未运行的比较保留pending。
