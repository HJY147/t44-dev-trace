Agent-Role: database
Prompt-Ref: ROLE-database-LIVE-VERIFY-v1
Refs: #4 #13

性能窗口结束及两个新隔离库授权后，已基于根43f5157执行真实MySQL验证。只写t44_review和t44_seed_verify_v2，未碰dev/acceptance/perf/旧seed库，不读改957或独立私有资料。

保留两次真实失败：review-run1在索引恢复后发现MySQL8.4重建把CHECK字面量引导符改为_ascii，parser误拒绝不变表达式；现在在词法阶段支持限定_utf8mb4/_ascii，ASCII保护及字符串内部相似内容不被改写的正负回归均保留。review-run2为owner探针同条ALTER重用同名FK导致1826，仅将探针分步DROP/ADD并保障部分失败恢复，不放宽checker。

review-run3四类同名漂移（列序/unique/FK目标/CHECK1=1）均被checker与重复migrate拒绝，每例恢复18表226列无缺陷，最终重复迁移接受。原始SQL、目标库、拒绝和恢复结果均保存；C-P4本岗数据库技术验证闭合，仍待审核岗对最新集成SHA复审，不代其设置审核通过。

新版seed真实在新空t44_seed_verify_v2迁移并生成40项目/6000任务/9000同项目DAG/11400review+3600decision、3600预案与7态；原全部引用/轮次/指针/容量/模板八段十项/四视角及JSON检查通过。持久行SHA256=6d56de112481ca6c6a54210a1a60b06769b9845fad8699462dfbf753505fb3d3，与原全量基线精确相同（仅排随机password_hash）。同manifest幂等，改seed/合法JSON规则仅raw hash变化均拒绝；7项针对性的原生CHECK/unique/FK拒绝savepoint回滚后摘要不变；最终结构和重复迁移通过。不是59CHECK逐项负测。

956/975必要回归18 passed/0failed/0errors/0skipped，2条原JUnit兼容警告保留；Ruff首次import排序失败保留并修复，后通过，定向Bandit0。证据/原失败在agents/database/live-verify-v1/summary.json及原日志；报告/handoff/实际prompt已更新。全部synthetic，非人工评审/交付、正式性能或独立验收。根stage7 cloc5866仍超5100；本轮不改统计或为数字破坏结构。PR17保持draft。
