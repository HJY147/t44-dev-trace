Agent-Role: database
Prompt-Ref: ROLE-database-INTEGRATION-FIX-v1
Refs: #3 #4

实际全整合暴露seed读取旧rules.rule_version导致两项失败，原失败由backend保留。最小产品修复e06ac3ba4dfe7057df02b1213d482d78bee7026f改为正式version，并保存effective_at/decided_by来源；未修改规则资源、原测试/断言或测试路径。原两seed测试仅执行2通过，Ruff通过。

root另建授权的新t44_seed_verify上，官方MySQL8.4.11首次迁移18表226列、全量生成40项目/6000任务/9000DAG依赖/11400评审+3600决定及7态一致性校验通过；重复同manifest幂等。实际manifest rule_version=1、rule_decided_by=1、rule_effective_at=2026-10-23T05:33:29Z，规则rawhash63bda0d3931bb7d34b3fd745c8a9ba14f489f7288badbf422dfc7ba4f6bc8f41。

旧t44_bench保留D001-v1/hash279c...清单。当前资源重复seed明确拒绝配置差异，前后40/6000/9000/11400/3600及原manifest未变；不自动升级清单、不覆盖旧数据。日志integration-old-bench-guard.json与integration-formal-seed-mysql.json分别记录。所有数据仍synthetic，不作为真人review；新全套与统一tmp路径验证由root/backend执行，本岗不代称通过。
