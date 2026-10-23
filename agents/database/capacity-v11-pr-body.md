本次新增范围仅capacity生命周期1.1的存储字典/事务契约及过程记录。D005/D006已采用、bbc RFC限定设计通过；capacity保护state1–5、6/7可移出且返工前补回，成员保护仍1–5+7，D002不放宽。assignment新增项目锁，四路径同项目锁内核对当前快照/全量owner并沿有序成员/任务锁序；错误优先、成功事务/旧key重放/独立拒绝审计不变。

两文档显式演进，旧ae60dc3/1.0的11hash和原manifest保留；当前文档摘要不再声称逐字不变。仍18表226列、DDL hash c0e740...，无新增列/trigger/错误码/预算算法。本岗未改产品、API或root新freeze；API版本info.version和Meta.const的1.1.0同步由backend负责。

仅静态文档/链接/hash检查通过，结果agents/database/capacity-v11-static-check.json。未执行产品测试、MySQL、迁移、全套、coverage、独立验收或性能；本轮不计这些通过。PR既有产品/原生MySQL/checker历史证据保留，不被此次文档更新重写；保持draft，整体1.1实现/冻结/验证另审。

Agent-Role: database
Prompt-Ref: ROLE-database-CAPACITY-V11-CONTRACTS-v1
Refs: #4
