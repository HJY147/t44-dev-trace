Agent-Role: database AI（backend责任岗明确委托settings.py两个参数）
Prompt-Ref: ROLE-database-POOL-CONFIG-20261028-v1

独立基线 b9847f8a946a310b90e8fb228a0e5c1061612e13，先行设计fb5d622dfd16de30dbde9676c295cc36715c275f，精确product/test SHA 92cf5c108ee549b35dda6d775e0357ded9e40743；四件/证据提交5248784a461f7023dc4e6bac42dab8dccc5221e9已push至codex/database-pool-config-20261028。backend已实际确认ENV名称T44_DB_POOL_SIZE / T44_DB_MAX_OVERFLOW。

生产仅Settings.mysql_settings()原MySQLSettings构造新增两行int(os.getenv)参数。没有ENV时默认5/10及其他字段逐值保持；仅显式ENV可覆盖对应值，整数转换失败拒绝且不回退。原URL/显式库/T44_DATABASE匹配先验不重排，原MySQLSettings正整数/overflow非负及engine校验不改。SQL/事务/鉴权、其他Settings逻辑、原测试/冻结/CI/计数器均不动。未捆绑select(table)候选82e92，仍分开审核。

本地配置范围：原源码显式容量目标4红1绿原件保留；新增tmp/786_database_pool_20261028配置契约31项，加原850/993配置/lazy-engine/session初始化目标7项，共38 passed/0.26s。构造真实原QueuePool验证容量/overflow传递，PyMySQL connect未调用；没有SUT/HTTP/MySQL/云/负载/性能运行。限定CI配置Ruff与Settings Bandit通过。整包diff-check因原pytest红log/XML的8处原始尾空格exit2，完整诊断保留、不修剪；源码/说明限定check通过，未冒称整包check绿。

固定cloc2.10实测应用5933→5935，净有效行+2，超5100上限835，范围检查exit1；strictLOC仍未通过，没有性能改善或验收通过声明。

连接预算只是后续设计：16worker A5/10与B15/0均API最大240；C20/0为320+reserve64。64worker另案需5/0才是320+reserve64，不能64×默认5+10。下一目标必须actual query MySQL max_connections并核所有角色/预留再准入；旧384不能替代新目标读回，16×25/0已400再加其他角色不能默认采用。根后续独立审核/CI及真实Connections观察另行执行。

[完整报告/红绿命令/边界/实际计数](https://github.com/HJY147/t44-dev-trace/blob/5248784a461f7023dc4e6bac42dab8dccc5221e9/agents/database/pool-config-20261028/report.md)。操作者为AI数据库岗。
