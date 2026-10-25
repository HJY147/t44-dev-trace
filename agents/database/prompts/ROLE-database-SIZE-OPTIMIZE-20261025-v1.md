# ROLE-database-SIZE-OPTIMIZE-20261025-v1

实际执行提示来自总协调，AI数据库岗，非用户亲自修改。用户已明确继续优化源码规模与性能并允许结构调整。

职责：仅 backend/t44/persistence 与本岗测试/记录，独立 worktree codex/database-size-optimize-20261025，基 e45a2b9，产品基线935ab5b93bea788672c2b4a088c79cfeed848954。目标尽可能净省400–500，但只计实测。保留签名、严格输入输出、权限、原子性、FK、迁移漂移检测、租约/CAS、事务、锁顺序及死锁防护。不删功能/测试/guard，不改口径、压格式、改后缀、把逻辑藏字符串或外部数据。跨模块接口先协调；完整CI交根统一执行。

禁读所有独立目录/新814/817/818/829、凭据、.runtime；总协调后仅授权读取唯一固定cloc2.10工具及执行既有backend/.venv Python，不读其他runtime数据。本阶段新测试tmp/812_database_size，仅SQLite/mock；不接触旧MySQL/管理接口/旧schema，不运行live。

后续明确准入：可在本分支试用精确pin SQLGlot仅替换手写CHECK parser，必要时评估DDL单一来源；可修改backend依赖清单/锁文件仅该新增项，不改既有共享venv。严格token/AST whitelist、未知节点fail-closed、优先级/charset/literal/引号保留；先小原型和差分反例、净预算，不够就撤回。此项是后续阶段，首批未包含新依赖。

改进理由：把旧仅报告/零节省改成真实产品补丁、精确固定计量与有意义回归，同时保留原失败与未验范围。
