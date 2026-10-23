# 数据库模块报告：capacity生命周期1.1存储文档同步

- 实际派工ROLE-database-CAPACITY-V11-CONTRACTS-v1；基于指定eac253039cd85873d3b262e648b2b74d94d715a8。本轮操作者数据库岗AI，非用户亲自改码。
- 已读D005/D006、U015/U016、已审RFC及bbc限定设计报告；只更新specs/database/field-dictionary.md与persistence-contract.md及本岗记录，不改DDL、产品、API、旧freeze或他岗文件。
- 两文档显式演进至1.1存储语义，保留ae60dc3原1.0与11hash；不声称当前仍逐字匹配旧文档摘要。新freeze父链由root负责，当前未代为生成或宣称已冻结。
- capacity保护本迭代state1–5全部owner，6/7可移出，7返工前补回有效developer/工时；项目成员/开发角色保护仍1–5+7，D002转派边界不变，无新增预算算法。
- 四路径createTask/changeIteration/rework/changeTaskAssignment统一session/idem→project→有序成员→有序task；assignment新增项目锁。服务获项目锁后重读当前JSON快照/全量任务与有效developer，不依赖锁前/另一事务预检。
- backend已真实确认全量owner集合检查及保留原权限/状态/version/证据/依赖守卫优先；新增检查CAS前完成，复用422 CAPACITY_REFERENCE_INVALID/审计稳定码30。失败不写业务version/plan/diff；成功同事务、旧成功key重放、独立拒绝审计边界不变。
- 必要静态结果：18表226列；两份DDL SHA256=c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4；226项字段/SQL声明不变，原11hash从ae60dc3均可恢复，v1.json未改，19个本地链接/锚点通过，已审RFC原hash相符。
- 证据agents/database/capacity-v11-static-check.json；本轮未跑产品/SQL/迁移/pytest/全套/coverage/独立验收/性能。该文档同步不计任何产品或独立/性能通过。
- 原C-P4/checker与真实MySQL证据保留agents/database/live-verify-v1/summary.json和0e3e999历史提交，不重写，也不拿它证明1.1新增行为已运行。
- backend负责1.1 API/代码/权威运行副本及info.version+Meta.const，root负责共享需求/业务规则/AGENTS和新freeze；本岗仍待其实际实现/新版运行验证及整体审核，不越界完成或声明这些工作。
- 日志agents/database/WORKLOG.md；实际prompt agents/database/prompts/ROLE-database-CAPACITY-V11-CONTRACTS-v1.md；交接records/handoffs/database.json；阶段Issue/PR另列真实URL。未接触独立测试私有资料。
