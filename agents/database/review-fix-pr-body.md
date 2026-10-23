迁移检查器原来只比较索引、外键和CHECK名称，可能接受同名但已改变列序、唯一性、外键目标或约束表达式的结构。本轮编写Inspector语义比较：有序列/unique/排序/前缀、FK目标及动作、保留逻辑优先级和字面量的冻结CHECK语法规范化；同名漂移应被拒绝，冻结DDL/API不变。

当前C-P4候选明确未运行、待性能窗后验证。root安排400并发及随后两个600秒正式批次，要求本岗只做源码编辑/Git记录并先保存draft；未执行pytest、真实t44_review迁移/变更探针、lint或构建。源格式化不能当检查通过。唯一新回归tmp/backend/persistence/956_schema_semantics.py已编写，专属review库已建但尚未使用；未读改审核957或独立私有用例。窗口结束必须实际验证正常结构接受、同名错误拒绝、错误重复迁移拒绝与恢复后接受；不能把此checkpoint标为C-P4闭合。

PR其余已有产品为18表226列Core/参数化Rows/事务与版本迁移、outbox/通知、持久扫描、confirmed缺通知恢复、公平性和生产synthetic seed。此前正式新库t44_seed_verify已生成40项目/6000任务/9000DAG/11400评审+3600决定并通过局部一致性及重复幂等，旧bench配置差异明确拒绝而不覆盖；这些历史模块结果不能替代本次checker验证、最终全套或独立验收。

当前统一代码规模仍超过5100，未声称达标；seed公共row-builder真实减重复尚未实施。PR保持draft，不设审核通过或合并main。

Agent-Role: database
Prompt-Ref: ROLE-database-REVIEW-FIX-v1
Refs: #4 #13
