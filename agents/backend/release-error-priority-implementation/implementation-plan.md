# D008实现阶段执行边界（先于856/产品修改）

独立worktree backend-release-error-priority，分支codex/backend-release-error-priority-implementation，基exact d5307551d6b467f84e8254abd0245cdf22bc0a70。v1.2 manifest及15文件hash先核，旧历史不改。只Workflow原批准引用require失败的错误选择按cycle/schedule有效性细化；原predicate/SQL/guard位置/domain/auth/锁/CAS/事务/幂等/audit/outbox均保留。

root已分配856，原986 helper与SQLite application fixture复用。先用旧逻辑跑新增HTTP案：真实schedule重排+旧批准撤销的双失效预期BASELINE会观察原APPROVAL红，保存原log/xml，不用它取消旧F08。另仅批准无效、请求assessment/task版本/跨task/missing、匹配引用的原domain次序、COMPLETE错误和成功的值重放/动态request与meta、全流程新评估+另一合规评审审批后发布。cycle/引用匹配但历史异常的输入若需，明确受控SQLite fixture，不称真实rework或真实历史。拒绝前后业务表完整快照一致、只新增原拒绝audit/幂等完成；重放不新audit/业务。

旧源红后只最小生产改再同批绿；Ruff/format新责任文件，若纯格式改以AST等价记录，原断言/旧用例/859不变。新代码先正常commit/push/draftPR触发精确CI/Docker，及时回root源SHA；日志和CI可另阶段归档，不能将后补证据倒称源码已含。固定source_count脚本重新实际计量，超限继续如实保留。本机只内存TestClient，不起端口/不访问外部DB/服务/负载。CI真实MySQL/Rabbit只隔离仓库服务；不触独立资料/实例。
