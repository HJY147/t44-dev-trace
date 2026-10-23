# ROLE-database-CAPACITY-V11-CONTRACTS-v1：实际派工

来源：总协调实际消息；操作者数据库岗AI。本轮只同步存储文档，不记为用户亲自改码。

> ROLE-database-CAPACITY-V11-CONTRACTS-v1：固定DB岗只做这次人力生命周期的存储契约/字典同步，不改DDL或产品实现。根当前eac253039cd85873d3b262e648b2b74d94d715a8，本地可merge准确SHA，独立worktree/index/分支codex/。先读AGENTS、D005/D006、U015/U016、specs/changes/capacity-lifecycle-v1.1.md以及设计限定通过报告 reports/reviews/capacity-v11-design-bbc4be681f19a386fbca40baf97a63ab902b3f89.md（reviewer d7c46a6）。这是显式1.1演进：旧1.0 11hash/父提交ae60dc3保留，不悄改v1历史或声称当前还逐字不变。
> 人已选择：接手人先登记迭代工时才能转派；新capacity保留本迭代状态1–5所有任务owner；6/7可移出容量，7返工前补回有效人力。项目成员/开发角色移除保护原1–5+7不变，D002转派状态边界不变，不新增预算算法。后端岗负责API/代码和specs/backend-design、权威OpenAPI/运行副本1.1.0（info.version+Meta.contract_version.const），root负责business-rules/requirements/AGENTS和最终新freeze父链。
> 请你负责 specs/database/field-dictionary.md 与 specs/database/persistence-contract.md：明确capacity快照是服务层在同一项目锁保护下核对现有任务/有效developer，assignment新增项目锁；createTask/changeIteration/rework同锁序session/idem→project→有序成员→有序task，拒绝不写版本/plan/diff，成功事务/幂等重放和独立拒绝审计不变。不新增列/表/trigger/魔法码；仍18/226、DDL原hash不变。现有原生MySQL和checker修复不重写、不拿文档更新重跑全套/coverage。
> 只必要静态对照/链接/hash检查；字段或错误定义若和已审RFC不一致先root提出，不越界改backend源。可向后端岗清晰同步本次文档输入输出，不联系独立tester，不读其私有材料。维护日志/模块报告/handoff/实际prompt与真实GitHub阶段评论，阶段commit/push精确SHA后释放slot。此岗文档同步不计产品/独立/性能通过，也不声称用户亲自改码。

改进理由：以人的D005/D006选择及已审RFC限定显式1.1差异；容量保护、成员保护、旧冻结历史和本轮文档静态检查分别记录。
