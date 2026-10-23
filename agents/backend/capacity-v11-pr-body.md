后端实现38个冻结HTTP操作、严格JSON Schema、opaque会话撤销、状态/证据/预案/决策及UoW幂等/CAS/审计/outbox。此PR当前包含按D005/D006、bbc设计审查和189dc4a正式冻结实现的1.1容量生命周期：转派接手人先有本迭代工时，capacity覆盖全部状态1–5 owner，6/7可移出、返工前补回有效developer与capacity。原成员保护1–5+7、开始前转派范围、错误优先级、幂等重放和事务原子性保持，项目锁保护创建/转派/迭代变更/返工竞争。

8f6全量CI真实391项/2失败，根因是服务误把外层1.1.0用于内层候选schema_version。最小源码4c20f32b71635016815420472b9d4bb4fa850df0读取冻结内层const1.0.0，Meta仍1.1.0；原失败、三类HTTP改前失败与修复留存，14freeze和18表226列未改。精确新product39958165108/39958156337均success：394项、0失败/错误/跳过，contract96/integration63/fault7分别通过（标记可重叠）；全部43个t44文件、无excluded，2542/2865行88.7260%、分支78.5530%。含7项新增真实MySQL项目锁竞争及合法转派后移除旧owner双成功；终态fixture为明确合成，不冒充完整实际旅程。证据agents/backend/capacity-v11-ci-summary.json。

工具245e56b的隔离单worker契约校验短诊断收18289主样本+3sanity，0业务/HTTP错误；controller最终错变量RuntimeError/exit1保留，子阶段有效，三服务exit0。955两行修复仅离线原metadata及静态检查，不重跑负载；生产字节仍4c20。六组P95和38份原始记录见agents/backend/profile-contract-03-*。cProfile含冷TLS/等待，尚不足以改pool或归因为DB锁，未作生产性能优化。

PR保持draft；上述为开发CI与限定短诊断，独立复测、正式400VU/600s/4worker性能及3500–5100源码规模尚未通过。冻结前曾有本地业务草稿及局部草稿回归，正式contract-only提交、后续freeze和代码/验证真实先后均在日志保留。

Agent-Role: backend
Prompt-Ref: ROLE-backend-CAPACITY-V11-IMPLEMENT-v1; ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1
Refs: #3 #12
