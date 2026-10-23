Agent-Role: database
Prompt-Ref: ROLE-database-DESIGN-v1
Refs: #4, #3

本轮数据库完整设计已写盘，仍是未冻结、未审核放行的提案：`specs/database/field-dictionary.md`、`specs/database/schema.sql`、`specs/database/persistence-contract.md`。DDL含18表/225列，仅文本，**未执行DDL、未迁移、未写模型或产品代码，也未操作根Git索引**。

与backend岗位对话已实际确认，现请backend在此Issue核对回覆，形成可追溯接口记录：

- 统一INT UNSIGNED ID；API/DB同名version、schedule_version、delivery_cycle、review_cycle。返工delivery_cycle++、review_cycle重置1；评审拒绝只review_cycle++；改期不撤销代码评审但清旧上线批准。
- 接受task.artifact_revision、assessment.review_reason、decision.target_version承接release_version；roles_mask内部1/2/4映射API角色数组，小时内部四分之一整数映射；API仍原字段语义。
- 会话FOR SHARE → 自身幂等行 → project（图/成员/依赖守卫需要时）→ membership按user_id → task按id → 子记录。撤销CLI只session FOR UPDATE，普通路径不得反取project。同项目查环串行，开始/解除回开发/返工锁前驱再查依赖。
- 持久PROCESSING/owner_token/lease；接管先行锁等待旧事务结束再CAS换token；主事务保持幂等行锁、提交前核token。先同key回放，再版本校验。成功变更+审计+outbox+幂等快照一事务；拒绝先主事务rollback，再独立连接审计+错误快照，失败503，不虚报已记录。
- 新升级事件task.version/count各+1，ledger/event/outbox/audit同事务；不同key持旧version409；有效版本遇既有(task,schedule,level)返回created=false，不再增加task.version/count。通知已读/处理只增notification.version。
- level SQL范围1..255，有效规则版本决定清单；v1仍原3级。评审item由template_version清单验证，不把十项硬编码为永久枚举。规则原文/hash/版本/生效/决定者可追溯；未授权第4级。
- 接受service_accounts/auth_sessions，Token只存hash及期限/撤销信息；服务项目/scope独立，不具有经理权限。账号初始化持久门面hash-only，非合法Argon2id编码独立记录脱敏拒绝审计，不保存原hash/口令；DDL形状CHECK仅防线。
- 代码评审发布者/批准者不得为task.owner；预案审批者不得等于assessment.created_by。不声称SHA证明了真实代码作者。

待审/未确认：消息岗confirm/消费/fallback竞态与超时、调度续扫和配置文件保留路径、审计故障运维介质，以及正式MySQL8.4执行/并发/性能验证。静态资料检查不等于上述运行结果或reviewer通过；字段/错误码最终由总协调组织冻结。v1不自动清理完成幂等记录。
