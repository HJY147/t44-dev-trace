# 实际派工

Prompt-Ref: ROLE-database-SELECT-RESUME-20261028-v1。操作者为 AI 数据库岗；总协调派工，不能记为学生亲改。

你是T44数据库岗新的查询优化子任务。在 /Users/yang/Desktop/nothing/软件开发大作业 读AGENTS，创建独立codex/database-select-resume-20261028 worktree .agent-worktrees/database-select-resume-20261028 从a12e9e70b963bacafda3242bb6d82e53ee912ff1，不改root/原database794工作树。已知API实际高CPU，性能岗从准确a12在隔离SQLite/原FastAPI采样发现 RowsGateway.rows默认fields=tuple(t.c)→select(*fields)，每次对所有列逐coercion/cachekey。建议仅默认表达式 tuple(t.c) 改(t,)，用SQLAlchemy Core select(table)等价展开全列；净有效行0，不能冒代码规模减少。先自己核语义/官方当前源码本地SQLAlchemy版本，不因别人推荐直接改。若可行实施一行可信候选，原fields显式投影完全保持；保留schema审计7种新反例/锁/where/order/limit/SQL绑定/返回mapping列及事务。性能岗稍后给精确MySQL/SQLite编译等价和无profile构建CPU证据，你可协调root拿PUBLIC报告，不读它的私有case。跑有意义既有gateway/persistence回归及必要正负例（不要镜像实现的测试），小改完成后提交push四件/报告/实际计数。新test临时tmp可预留787_database_select_resume_20261028（先检查未用，原790..795等不可碰）。别开云、别用用户原生MySQL/旧tmp796、不碰792独立private、老师研究正文、计数器，不删原审计。root当前云冻结a12，候选另source/CI后才考虑部署；性能和正式验收不预填通过。

本轮改进理由：将建议限定为待核候选，以准确基线差分与现有契约验证 Core 表展开的实际结果，不把源码形状或 CPU 估算代替行为和正式门禁。
