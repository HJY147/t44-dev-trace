Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1

夜间工具准备checkpoint：5b0e1529e5e56e1e76aef557012da79807ad8e04，已push至codex/backend-contract-abba（独立工具分支，本条为PR16阶段沟通，不冒称其head已包含新分支）。生产backend/t44仍逐字同5dcb，14冻结文件未改。

新增tmp/backend/930_contract_abba.py：A4c20/B5dcb Git快照/actualimport+resource SHA双核验，自己的t44_profile/18083/1worker/40线程/pool5+10；未包裹API，ABBA四阶段各3类sanity+120均衡预热+8并发8秒，单连续控制器90秒有界监督/finally仅清自己的新PG/PID。凭据仅600指定文件，raw不存自由body/Token。完整工具说明agents/backend/abba-tool-preparation.md。

11项离线helper通过；显式backend/pyproject.toml既有Ruff/format通过。首次隐式配置检查失败已保留abba-tool-ruff-initial.log、abba-tool-format-initial.log，未降低检查选项。没有应用import/SQL/HTTP/pytest/build/load，实际进程生命周期与收益未验证。工具需等待总协调另外明确quiet窗口，尚未执行；旧03整体controller exit1、正式400VU×600秒性能失败及6051源码超限保持。本短对照不能替代独立性能验收或证明其它接口收益。
