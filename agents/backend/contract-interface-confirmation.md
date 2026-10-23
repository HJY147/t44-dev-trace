Agent-Role: backend
Prompt-Ref: ROLE-backend-CONTRACT-v1
Refs: #3, #4, #13

与database岗位本轮实际协商确认如下；这是责任岗设计对齐，契约/DDL仍未冻结，不表示已经实现或测试。

- API/DB统一INT UNSIGNED ID、task.version/schedule_version/delivery_cycle/review_cycle；reject_review只增review_cycle，rework增delivery_cycle并重置review_cycle=1；改期留代码评审、使旧上线批准失效。API小时按四分之一小时存储，角色数组映射内部mask。
- 成功写、成功审计、需投递事件及outbox同事务；幂等唯一(actor_kind,actor_id,operationId,key)，请求摘要含路径和规范化body。先认领PROCESSING/owner_token/lease，主事务锁行，成功原子完成快照；拒绝回滚后独立事务同时审计和完成错误快照。审计不可用503；提交不确定沿用同键恢复；v1不自动清理完成记录。
- 锁序统一session FOR SHARE→幂等→project（需要时）→成员按user_id→任务按id。撤销CLI只session FOR UPDATE；普通写不反向追加project锁。依赖图修改项目串行检查，开始/解除回开发/返工锁前驱检查当前已交付；服务Token只存摘要并限项目/scope。
- 新升级事件CAS task.version++且count++，与事件/outbox/audit同事务；同键优先重放原202，不同键旧版本409；版本有效且业务事件已存在created=false，不再增加版本/计数。通知只增notification.version。UUID scan_run_id映射持久层scan_runs整数PK。
- 协调者质量约束：代码评审发布者/批准者非task.owner，评估审核人非assessment.created_by。可扩展level为1～255但仅rule_version有效清单生效；v1仍原三档。明文持久入口拒绝，初始化门面只接收安全摘要。

证据：`specs/contracts/openapi.json`、`specs/backend-design.md`；数据库岗自有设计文件由其归档。上述确认不替代DDL逐表审核和后续实际MySQL/HTTP/故障验证。
