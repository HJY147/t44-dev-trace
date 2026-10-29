# 实际最小整合修复派工

AI总协调发给database AI的实际原文，不是用户亲自改码或事后优化版：

> 真实跨模块缺陷需最小修复 ROLE-database-INTEGRATION-FIX-v1，暂用唯一空槽。BE整合scheduler新规则资源后全套312pass/2fail/3localRabbit skip，两个fail都是seed.py:369仍取旧rules['rule_version']，正式资源字段version（你独立seed树旧资源之前通过不能代全整合）。请merge codex/integration完整a8scheduler资源/baBE后，修真实版本/生成人metadata映射及必要对应回归，不能改冻结资源或弱断言；实际t44_bench已有旧hash清单，重复seed遇资源hash变化应明确拒绝，不要覆盖。以新独立empty schema生成验证可申请root新建项目临时库，不清现有数据。先给最小产品修复checkpoint SHA，root/BE再全套验证。用户刚要求所有测试文件统一tmp/降序999_、998_... root马上机械迁移，不要本轮新增/改原测试文件以免冲突；必要回归可在已有测试仅执行不编辑，root迁移后再补。只改本岗生产seed+日志报告；原全套失败保留。

实际修复对应：e06ac3ba4dfe7057df02b1213d482d78bee7026f把seed manifest读正式version并保存effective_at/decided_by来源；原seed测试仅执行不编辑。integration-old-bench-guard.json记录新配置重复拒绝且旧数据/manifest未变。新空库由root另建授权，不清现有4库。原全套失败保留在backend自己的integration-full-first.log；本岗不把旧独立树通过当新全套通过。
