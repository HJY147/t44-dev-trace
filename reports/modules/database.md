# 数据库模块报告：C-P4远端修复与seed等价去重

## 当前事实
- 岗位database；本轮ROLE-database-REVIEW-FIX-v2，续3ed源码checkpoint；只改本岗目录，冻结DDL/API不变。
- C-P4为检查器误收同名错误结构，不是实库已漂移。本岗未读改审核957或独立私有资料。
- 原两run39938428158/39938417442真实失败是Bandit B105：解析器token与'('比较被误判口令。原job日志、artifact和hash保留agents/database/ci/review-fix-v2；958仅改局部名lexeme，无nosec/门禁或断言削弱。
- 4301a68托管product39940121559四job success，后端332 passed/0 failed/0 skipped；含15项956自岗回归与CI真实MySQL初始化接受。958总体run被后续push取消，不能称整次通过。
- 2dc2e6d保留原975小夹具及全部断言，增加默认40/6000/9000/15000组取得重构前全行摘要；其PR run39940459708四job成功，333 passed/0failed/0skip，小/默认全量摘要已取得；row-builder和固定摘要断言现提交待新远端比对。
- 同机安静窗口尚未获结束通知；本岗不运行本机pytest/MySQL迁移/seed/HTTP/构建。格式编辑不等于lint通过。

## C-P4实现与仍待验证
- migrations.py比较索引有序列/unique/排序/前缀及反射冲突、FK有序源/目标schema/表/列与动作、CHECK优先级/字面量/函数参数语义；未知CHECK语法拒绝。
- 仅规范化合理MySQL表示差异；额外普通非unique索引允许（含FK自动支持索引）。自岗956包含13个同名语义变化及正例/解析优先级回归。
- root已新建授权t44_review，本岗尚未触碰。窗口后须真实执行正确结构接受、同名列序/unique/FK目标/CHECK漂移拒绝、错误结构重复迁移拒绝及恢复接受；现有run_mysql_review入口限定此库且业务行必须为空。
- 托管CI、Inspector夹具不能替代此专库实际变更/恢复；C-P4不标关闭，也不设审核通过。

## seed去重与已有产品边界
- 受信add(row)集中时间/项目任务外键上下文，显式业务值仍走Rows校验；version/active/plan_version/escalation_count采用既有冻结server defaults，批准指针初始NULL构造复用。状态/轮次/JSON证据/manifest/批量单UoW语义保持。
- 等价回归摘要包含所有持久行及manifest，只排除故意随机的Argon2 hash；原七态、DAG/前驱、JSON模板、容量、批准指针/轮次、重复幂等、不覆盖和失败回滚断言保留。原数据全量基线已得，重构等价结果待新提交CI，不以静态推理声称等价通过。
- 该去重未搬业务到配置、未压行或改变统计口径；C-P4增加代码且全局仍超5100，不声明达标，精确cloc等待统一统计。
- 已有18表226列Core/Rows/Engine/UoW/hash-only入口、版本迁移、OutboxStore/ScanStore、confirmed缺通知恢复和claim公平性；业务事务及拒绝独立审计由backend Runtime编排，CommitUncertain不被rollback清理解释为未提交。
- 历史产品e06/记录5849已真实在新t44_seed_verify生成40项目/6000任务/9000DAG/11400评审+3600决定、3600预案及7态一致性/重复幂等；正式rule.version/effective_at/decided_by及原bytes hash入manifest。
- 旧t44_bench配置不同会拒绝且计数/manifest保留；integration-old-bench-guard.json、integration-formal-seed-mysql.json是真实历史模块证据，非本次重构结果。
- 全部数据synthetic，非真人review/交付、正式性能或独立验收。

## 交接与路径
- 产品入口backend/t44/persistence/{migrations,rows,delivery,scans,seed}.py；契约README.md，CLI由backend适配。
- 本岗测试当前tmp/backend/persistence/{993_foundation,989_rows,988_mysql,975_seed,956_schema_semantics}.py；旧日志backend/tests路径保留当时事实。
- 日志agents/database/WORKLOG.md；本轮实际prompt agents/database/prompts/ROLE-database-REVIEW-FIX-v2.md；交接records/handoffs/database.json；PR17保持draft并已重新attach。
- 尚缺：专库真实C-P4漂移恢复、seed重构提交后远端等价结果、最新整合SHA全套/统一规模；独立验收与正式性能不由本岗宣称。
