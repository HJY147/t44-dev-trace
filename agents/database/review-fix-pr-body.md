迁移检查器原来只比较索引/FK/CHECK名称，会接受同名错误结构。现在比较有序列/unique/排序/前缀、外键目标及动作和保留优先级/字面量的CHECK语义；冻结DDL/API不变。

实际MySQL专库t44_review已验证四类同名漂移均拒绝，错误重复迁移拒绝，每例恢复与最终重复迁移接受。真实失败揭示ALTER重建会把ASCII字面量引导符规范化为_ascii，生产lexer已最小修复并加正负回归；owner探针同条ALTER重用FK名1826也保留原失败并修为分步DDL。证据agents/database/live-verify-v1/summary.json含原始日志/SQL/目标/结果。C-P4本岗技术验证闭合，待审核岗对最终集成SHA复审，未设置审核通过。

seed公共受信row构造复用上下文/冻结defaults/NULL指针，保留业务配置和所有断言。新空t44_seed_verify_v2已真实生成40/6000/9000/11400评审+3600决定、3600预案与7态，原完整业务一致性检查通过，持久行摘要与原全量基线6d56de11...精确相同（排随机password_hash）。同manifest重复幂等、参数/配置raw hash变化拒绝，7项针对性native CHECK/unique/FK拒绝回滚后全摘要不变；结构/重复迁移通过。

必要本岗956/975共18passed/0failed/0errors/0skip，保留2条JUnit警告；Ruff真实初次I001已保留并修复、后通过，定向Bandit0。此前0a托管333通过属历史SHA证据，不替代本轮集成全套。仅两个明确专库可写，其他库未动；未读改957或独立私有资料。数据全synthetic，非真人、正式性能或独立验收；应用规模stage7=5866仍超5100，不宣称达标，PR仍draft。

Agent-Role: database
Prompt-Ref: ROLE-database-LIVE-VERIFY-v1
Refs: #4 #13
