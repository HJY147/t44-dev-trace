冻结v1完整研发流程后端：38个HTTP操作、严格请求/提交前data/响应Schema、opaque会话撤销、项目/计划/依赖/评审/发布决策，经数据库UoW编排幂等/CAS/审计/outbox及独立拒绝审计，默认接入MQ和调度。

本轮收敛重复：删除无production消费者的domain re-export/__all__，直接导入typed命令和模型；受信Call.create共享创建上下文与读回，issue_session共享login/CLI会话发行。未改冻结API、稳定码、业务/安全守卫和事务边界。生产git物理diff相对003ef6b净减112行，整体源码目标仍待统一cloc。

729344e远端GHA39937742613的namespace遮蔽使18用例失败且Ruff I001/F823，原日志保留；当前cmd别名修复保留全部断言。新checkpoint等待远端CI，本机性能安静窗内未回归。上轮真实38/38 TCP/MySQL及314passed/3本机Rabbit skip、全t44行87.78%仅为原快照，不代表当前重构通过。PR保持draft，独立验收/正式性能结论由相应实际证据给出。

Agent-Role: backend
Prompt-Ref: ROLE-backend-REFACTOR-v1
Refs: #3 #4
