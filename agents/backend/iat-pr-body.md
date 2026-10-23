冻结v1完整工作流后端：38个HTTP操作、严格请求/提交前data/响应Schema、opaque会话撤销、领域状态机、项目/排期/依赖/评审/发布决策，以及数据库UoW幂等/CAS/审计/outbox编排；默认接入消息/调度。

已发布独立v1发现的业务/契约偏差按冻结范围修复：新评估清旧批准且过期pending评估不能再激活；createTask负责人匹配迭代容量；非法任务选择器独立拒绝审计可持久化；公开任务/返工计划差异不截断；必需证据与只读验证壳/候选错误正确分类。冻结Schema、锁序、CAS、幂等和事务保持。

开发HTTP/SQLite先留原始失败，最终55通过，Ruff/Bandit通过；源479fc8f product39946771417四任务全成功：JUnit362通过/0失败/错误/跳过，含985的5项真MySQL HTTP用例；全43个t44文件无exclude，行2524/2850=88.56%，分支78.11%，综合86.33%。所有证据在agents/backend/iat*.log/xml/json。PR仍draft，独立复测/正式性能/3500–5100源码范围尚未通过。

955首次诊断窗口只有setup：96e4源18083/profile库baseline两次正常启动/退出；bootstrap登录收到非JSON502，无fixture/主负载样本。startup hook原失败与后续502保留，工具固定回环直连绕开系统代理并保留非JSON状态，静态检查通过但尚未重试。生产代码与479一致。已通知root所有本岗诊断进程停止、LO可恢复；下轮需另协调CPU窗口，不得用短跑代400VU/600秒或在无样本时推定瓶颈。

Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1
Refs: #3 #4
