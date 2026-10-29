# ROLE-database-DRY-R29B-20261029-v1

操作者：数据库 AI。实际收到的总协调任务原文：

> 你担任固定数据库岗下一轮，仅本地，不能操作云。目录仅 /Users/yang/Desktop/nothing/软件开发大作业。以 root a92e5e73da93ba23748c3bab113103036c395d50 建隔离worktree .agent-worktrees/database-dry-r29b，分支codex/database-dry-r29b，先读AGENTS.md。现严格 cloc5887，上限5100差787；已接受schema.py固定DDL简化 -11，原有DB校验已在原生CI796全通过。上轮没有≥798实际方案，别重复空规划。请在 persistence/seed.py、migrations.py、rows.py、scans.py 范围找职责相同的实际重复和可删的中间抽象，用清晰可读结构形成至少一个实际候选。不能删任何schema原生检查、CHECK语义优先级、DDLhash/版本/锁、SQL白名单、session/事务/幂等/保存点、seed exact数据性质；不能改冻结接口/DDL/现有测试断言；不能同一行挤多个语句或把实现移到 excluded JSON SQL/修改计数口径。勿变更架构栈/依赖。净增/无净减或风险大就如实拒绝不集成。用原回归和必要实质差异验证，测试文件在tmp递减新号（先查号，建议765_database_dry_r29b），不得读任何PRIVATE或未公开测试，不联系测试岗。岗位四件、真实prompt/失败/命令/阶段commit并push，最终精确SHA与真实LOC净差，不代root merge。尽快提供首个可审查实际差异。

后续实际指令原文：

> 请把实质跨岗请求/候选通过该repo GitHub issue或草稿PR留痕（用户已授权项目内交流），不用另外问用户。实际diff确定再写，不要只有新RFC，不必凑数字。保持a92e起点，无云/PRIVATE。

实际使用方法与改进理由：先核责任边界和精确父源，直接读取四个限定模块；仅将同构的原生 catalog 查询注册从有序三元组改为有序标签映射。标签成为键、查询与预期签名成为值，去掉四份元组中间结构；SQL、预期构造和比较逐字保留。不声称百行方案。原回归加精确旧源的查询/缺陷顺序和失败退出差分验证，实际计数决定是否建议集成。

对应产物：backend/t44/persistence/migrations.py；tmp/765_database_dry_r29b/765_catalog_equivalence.py；agents/database/dry-r29b/；本岗四件。未把建议写成另一个已执行提示词版本。
