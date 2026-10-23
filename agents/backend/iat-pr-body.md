冻结v1完整工作流后端：38个HTTP操作、严格请求/提交前data/响应Schema、opaque会话撤销、领域状态机、项目/排期/依赖/评审/发布决策，以及数据库UoW幂等/CAS/审计/outbox编排；默认接入消息/调度。

已发布独立v1发现的业务/契约偏差按冻结范围修复：新评估清旧批准且过期pending评估不能再激活；createTask负责人匹配迭代容量；非法任务选择器独立拒绝审计可持久化；公开任务/返工计划差异不截断；必需证据与只读验证壳/候选错误正确分类。冻结Schema、锁序、CAS、幂等和事务保持。

开发HTTP/SQLite先留原始失败，最终55通过，Ruff/Bandit通过；985补真实MySQL回归待当前源CI。原65007a远端CI成功不当新提交通过。所有证据在agents/backend/iat*.log/xml/json。PR仍draft，独立复测/正式性能/3500–5100源码范围尚未通过。955仅准备未启动，18083独立profile库，需协调CPU窗口；不得用短跑代400VU/600秒。

Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1
Refs: #3 #4
