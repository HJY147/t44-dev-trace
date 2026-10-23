# 数据库模块报告：真实MySQL技术验证完成，待集成复审

- 本轮ROLE-database-LIVE-VERIFY-v1，干净同步43f51570e62e3160f7995c45bdddaf2f123242b3。总协调明确三批性能均停止后才恢复本机操作；实际prompt已原样归档。
- 仅写新隔离t44_review/t44_seed_verify_v2，不碰dev/acceptance/perf/旧seed库；私密四键仅构造Engine，未输出/提交凭据、DSN或读取admin文件。
- C-P4本岗技术验证已闭合，仍待审核岗复审最终集成SHA；未设置审核通过、未合并main。冻结DDL/API未变，未读改957或独立私有资料。

## 实际失败与修复
- review-run1真实暴露MySQL ALTER索引重建把CHECK字面量引导符改为_ascii，parser只支持_utf8mb4导致恢复后误拒绝。保留原始日志及Inspector实际/期望JSON；词法阶段支持限定引导符、ASCII内容保护，字符串内部相似文本保持原样，新增正/负断言。
- review-run2为owner探针同条ALTER DROP/ADD同名FK触发1826；保留原失败，只改探针分步执行并处理部分失败恢复。未削弱checker/956/975断言。
- review-run3四类真实同名漂移（索引列序、unique属性、FK目标、CHECK表达式）全部拒绝，错误结构重复迁移也拒绝；每例恢复后18表226列无缺陷，最终重复迁移接受。每条实际SQL/目标/拒绝与恢复结果均已记录。

## 新版seed真实MySQL
- 新空t44_seed_verify_v2首次迁移与默认生成成功：40项目、6000任务、9000同项目DAG、11400评审+3600决定、3600预案，7态分布/当前前驱已交付/轮次批准指针/模板证据/四视角/容量及JSON模型全量校验通过。
- 持久行摘要6d56de112481ca6c6a54210a1a60b06769b9845fad8699462dfbf753505fb3d3与原全量基线精确相同，含manifest/全部表，仅排故意随机的password_hash。实际模板/规则原bytes hash入manifest，不编造配置来源。
- 同manifest重复幂等；参数变更、合法JSON规则仅raw hash变化均明确拒绝并保留原数据。7项针对性原生CHECK/unique/FK拒绝（含四核心表）savepoint回滚后全摘要不变；结构与重复迁移最终通过。这不是每个可能DDL变异/59个CHECK逐项负测。
- 实际MySQL8.4.11、UTC、READ-COMMITTED及严格SQL模式；实际结果见seed-run1.log。全部为synthetic，不是人工review/交付、独立验收或正式性能证据。

## 必要检查与边界
- 956/975必要回归18 passed/0failed/0errors/0skip；保留2条record_property/xunit2兼容性警告。Ruff首次新import I001已留原失败并修正，后通过；定向Bandit0项。
- 当前全套/全局覆盖率未由本岗重新运行；此前0a676ee托管333通过是历史SHA证据，不能替代最新整合。根stage7 cloc5866仍超5100；本轮未改统计/进一步破坏结构凑数。
- 生产入口backend/t44/persistence/{migrations,rows,delivery,scans,seed}.py及README；稳定签名未变。业务事务/拒绝独立审计由backend Runtime编排，CommitUncertain清理不推断原提交失败。
- 自岗可复现CLI复用tmp/backend/persistence/956_schema_semantics.py（仅专属空业务review库）和975_seed.py（仅新专属空业务seed库）；后者写阶段重跑安全拒绝，生产seed_demo重复幂等已实际验证。
- 证据agents/database/live-verify-v1/summary.json及原始日志；WORKLOG、records/handoffs/database.json、prompts/ROLE-database-LIVE-VERIFY-v1.md均已更新。PR17保持draft，交总协调审核整合。
