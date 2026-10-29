Agent-Role: database
Prompt-Ref: ROLE-database-SELECT-RESUME-20261028-v1

准确基线 a12e9e70b963bacafda3242bb6d82e53ee912ff1；独立分支 codex/database-select-resume-20261028，先行设计6a1cb86b，生产/验证源码82e92dfc420690980a6e16c88f209d08ab709e49，证据/四件提交2943271d844b89536e0f75a9f62ad99cea193f6f，均已push。

RowsGateway.rows仅默认fields从tuple(t.c)改为(t,)，由既有Core select(*fields)展开全部表列。显式投影、where/predicates、order/分页、share/update/skip_locked、参数绑定、映射codec及UoW逐字保持；原schema审计七种反例/31例原件、migrations/schema、冻结/依赖/原测试/CI/计数器Git对象相同。本地SQLAlchemy2.1.6的三源与官方rel_2_1_6字节/SHA相同，18表没有omit-from-statements列。

实际开发验证：18表×8情景×MySQL/SQLite=288对SQL/绑定/结果列一致；最终自有tmp787契约差分30 passed（含11拒绝目标及真实SQLite映射/UTC微秒/JSON/null/长文本/显式投影/提交回滚/rollback-only）。原persistence+812迁移/默认/全量6000seed非integration回归138 passed，17 deselected，保留2原JUnit warnings。重复轮次不累加。限定CI配置Ruff/Bandit和diff-check通过。固定cloc2.10对准确82e92实测应用5933；与a12产品基线5933逐文件相同，净有效行0，超5100上限833，--require-range exit1。没有规模达标声明。

仅根转发的性能PUBLIC c96dc391报告/manifest/query gzip被读取，实核raw887024B/SHA03876a7501eb0e2b9fe9f1a346c7dc42a7e2b9fb9a851dd68d1646b00c128462。其a12进程内一表达式纯构建ABBA约省5us/statement；不是82e候选端到端、MySQL/HTTP/云加速或高CPU/502根因证明。

本岗未连接原生MySQL/旧tmp796/原tmp794数据，未开服务/HTTP/云/负载，未读独立私件或写学生研究正文。当前云仍a12；准确源码review、完整开发CI/覆盖率、新真实MySQL结果/锁/故障、独立验收和正式性能仍待根调度，本岗不代发布review通过状态。

完整报告、commands/原日志/JUnit/边界/计数：[2943271d报告](https://github.com/HJY147/t44-dev-trace/blob/2943271d844b89536e0f75a9f62ad99cea193f6f/agents/database/select-resume-20261028/report.md)。AI数据库岗实施，不记为学生亲改。
