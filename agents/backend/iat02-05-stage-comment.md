Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1（正式IAT业务修复续派）

IAT02～05按根确认最小冻结范围修复：createTask owner需在iteration.capacity；非法task0/越界attempted引用不击穿独立拒绝审计；任务/返工公开audit含完整五计划字段和版本（2000字不截断）；必需evidence空数组返回本操作EVIDENCE_REQUIRED，contract-validation顶层壳错误PARAMETER_INVALID、候选payload非法CONTRACT_INVALID。bool/string动作仍拒绝，1.0规范化同键重放保持。冻结11件/SQL/DDL/锁序/CAS/幂等/审计/outbox未改，未新增容量预算或转派生命周期规则。

开发真实HTTP/SQLite先13失败、另8失败/2通过，最终55通过，全部原日志/JUnit保存；Ruff/Bandit通过。985已补真MySQL专项，尚未本机运行，待新源远端CI；旧65007a CI成功不代新源通过。尚非独立复测，IAT06性能仍未通过。

955仅准备，已纠正独立性能服务占用的18082→18083，并记录实际import路径/源码SHA、防PYTHONPATH错树；无诊断服务/负载。业务稳定checkpoint后先协调Word渲染CPU窗口再短阶梯归因。转派/容量移除、大迭代capacity完整公开表达待正式选择，源码规模仍超限，不靠改口径解决。
