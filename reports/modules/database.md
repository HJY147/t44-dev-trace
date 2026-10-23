# 数据库模块报告：C-P4源码checkpoint待验证

## 当前状态与范围
- 岗位database，实际派工ROLE-database-REVIEW-FIX-v1；同步根7ce7171，不改冻结DDL/API或他岗源码。
- 审核转派C-P4指出旧check_schema只比较索引/FK/CHECK名称，可能误收同名错误结构；这不是已经发生实库漂移。本岗未读改审核957或独立私有资料。
- 已编写语义比较与唯一956自岗回归；**未运行、待性能窗后验证**，不得标C-P4已过或审核通过。
- root正式400并发及后续两个600秒性能批次期间仅允许源码编辑/Git记录；本岗没有执行pytest/真MySQL迁移/seed/构建。源格式化不等于lint或验证通过。

## 本轮源码
- backend/t44/persistence/migrations.py：索引有序列、unique、排序、前缀/类型及index/unique反射冲突；外键有序源/目标schema/表/列及动作；CHECK表达式保留优先级/字面量/函数参数的冻结语法规范化。
- 仅合理归一MySQL反引号/关键字函数大小写/utf8mb4字面量前缀/冗余括号、NO ACTION/RESTRICT及同库schema；不通过删除所有括号来比较。
- CHECK/FK/unique集合差异拒绝；额外普通非unique索引允许（含MySQL自动FK支持索引）。未知CHECK语法不能被当作相等接受。
- tmp/backend/persistence/956_schema_semantics.py：新自岗Inspector形状回归，以及显式t44_review/空业务表限制的受控DDL变更与恢复探针；没有削弱原审核用例。
- t44_review已由root真实新建授权，本岗尚未迁移/测试。后续必须证明正常结构接受，同名列序/unique/FK目标/CHECK变化拒绝，错误结构重复迁移也拒绝，恢复后接受。
- seed受信row-builder合并重复字段尚未启动，不将代码压行/改变统计政策当减量；已知全局规模仍超5100，不声明过门槛。

## 已有产品与历史验证边界
- 已有18表226列Core元数据、参数化Rows/Pred、UoW/Engine、hash-only初始化、OutboxStore/ScanStore、生产seed入口；本轮C-P4待证不抹除这些真实产物，也不以历史通过代替当前checker验证。
- factory每次新Session，每连接UTC/strict/READ COMMITTED；业务成功/审计/outbox/idem同事务与拒绝独立事务由backend Runtime编排，CommitUncertain不被rollback清理解释为未提交。
- 最新已验证seed产品e06、记录5849b107c5f87a4d21a858a64bb93606c9648d2a：正式rule.version/effective_at/decided_by映射，新t44_seed_verify真MySQL40项目/6000任务/9000DAG/11400评审+3600决定、7态全量一致性及重复幂等通过。
- 旧t44_bench的D001-v1/hash279c...与当前正式hash63bd...不同会明确拒绝；计数/原manifest前后不变，integration-old-bench-guard.json；不覆盖旧数据。
- integration-formal-seed-mysql.json记录正式配置生成，integration-fix-seed-tests.log记录原两seed测试2通过；这些是历史局部验证，不是当前C-P4回归。
- confirmed恢复14项、claim公平性修前真失败/修后通过、Rows迁移后原18断言+Rows/seed23项及实际Runtime真库证据保留；数据均synthetic，非真人review/交付、性能结论或独立验收。
- 原自测现在路径tmp/backend/persistence/993_foundation.py、989_rows.py、988_mysql.py、975_seed.py；旧日志backend/tests/...命令仍是执行当时事实，不重写历史。

## 交接
- 当前只可审源码保存，PR17仍draft，等待root窗口结束后正式续派验证/修复及有依据seed减重复。
- 本岗日志agents/database/WORKLOG.md，实际prompt归档agents/database/prompts/ROLE-database-REVIEW-FIX-v1.md，结构化交接records/handoffs/database.json。
- 未执行当前全套/覆盖率/真实MySQLC-P4/独立验收，不声称已完成产品审核；最终整合规模与门禁仍由root统一确认。
