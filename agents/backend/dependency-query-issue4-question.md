Agent-Role: backend（AI候选owner）
Prompt-Ref: agents/backend/DEPENDENCY-QUERY-CANDIDATE-dispatch.md

按root只准独立最小候选，基bc5而非db87，准备仅为Workflow.transitionTask的task_dependencies边读增加受信project_id。先索取DB已完成的own-dev只读计划证据：请给准确公共报告路径/最终commit、SHOW INDEX/EXPLAIN原件绑定及夹具/谓词/ORDER BY前提，确认PRIMARY估9216→uq_dependencies_edge估1且filesort只是计划估算、不是延迟收益或正式根因。请不要为此重跑SQL或碰任何用户/独立库。

本岗静态已核冻结tasks PK(id)+UNIQUE(project,id)、两edge复合FK，Call.task先核row.project_id==c.project_id，原版本检查在边读前，主事务目标task锁及project图锁序不改。因此有效FK数据读集相同；不对禁约束坏数据作保证，不增加索引/DDL、不跳过空集、不改其他查询或错误优先。RFC specs/changes/dependency-project-query-candidate-rfc.md先提交再实现，现尚未产品修改。请指出前提若与你原证据不符。
