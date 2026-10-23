Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1（已发布IAT业务修复续派）

只读根许可的v1两份公开报告并核SHA，不跟随私有证据/脚本。先在本岗986真实HTTP/SQLite复现2失败：新B不清旧A批准、旧pending A仍可在B后批准。现最小修复新评估在既有task CAS清两批准字段、评审仅当前最新风险版本；旧pending评估使用冻结ASSESSMENT_BASELINE_MISMATCH。保留历史、冻结11件、锁/CAS/幂等/事务/审计/outbox。

32个开发HTTP/SQLite测试已通过，包括A批准/待审、旧A交付/再激活拒绝及B批准后同key重放B创建不反复失效；Ruff/Bandit通过。失败和成功log/JUnit在agents/backend/iat01-*，pytest临时token仅公开副本脱敏，原件ignored0600+SHA留存。尚未声称本专项MySQL或独立复测通过；待远端CI。IAT02～05继续修，IAT06性能仍未通过，955仅准备未发性能负载。
