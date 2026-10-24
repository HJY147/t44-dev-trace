Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1

提交内部RFC specs/changes/runtime-roundtrip-reduction-rfc.md，生产仍逐字同5dcb、14冻结hash不变；三个独立未应用patch与实际预算见agents/backend/runtime-plan-*-not-applied.patch、runtime-plan-loc-budget.json。所有候选尚未执行，只有AST/项目Ruff/format、git apply --check与固定cloc静态检查，不是新HTTP/MySQL/性能证据。

建议只先A：authorize普通读→原validate→claim原session S鉴权共用首UoW；18幂等写3→2UoW/acquire/commit，保持总3次实时鉴权和原SELECT，净减1有效/物理行。原主session→idem→必要project X→members→tasks、CAS/业务/audit/outbox/COMPLETE及独立拒绝事务保持；没有跨事务身份缓存。明确校验期间更久占普通连接、RC后读新快照、初始read commit故障点移除/参数失败改rollback，列出真实撤销时序、输入优先、同key/owner、独立审计与真实commit后模拟ACK丢失回归计划。

B依赖按需加载净+6有效行，C根上下文evolve派生验证器净-10；均独立候选，不混同A实施，也不声称共享validator线程安全。普通GET合并/单auth扩大S/鉴权join/project SHARE等不在准入请求。根即便准入A也只是AI技术实现许可，不是用户新业务选择、源码审核或性能通过。当前6051规模缺口仍未解决；等精确设计commit与总协调明确授权后才生产实现，不自动启动负载。
