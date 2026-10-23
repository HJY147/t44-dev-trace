# 数据库模块报告：scan run共享草案净增1，不准入生产

- Agent-Role database；Prompt-Ref ROLE-database-SCAN-RUN-DEDUP-RFC-v1；基线162305f888ac094e38448ef95d4748248ae57bfc，独立codex/database-scan-dedup。
- 本轮只设计/RFC与候选预算，未改生产、DDL/API、14冻结件、依赖、测试断言或他岗源码。操作者AI，非学生亲改。
- 原审核B的28–47是估算。项目100列格式化+固定cloc2.10逐文件实测：scans109→129；facade205→186；联合314→315，净增1。真实生产节省0。
- 候选start_run接当前g、UUID、规则版本/快照/hash、now，输出id与已存在行；不创建/提交UoW，只复用原savepoint。初值一处维护，既有run仍核hash与version。
- scanner仍自有短UoW、始终INSERT、duplicate后FOR UPDATE、新行读回；API仍先普通SELECT、在调用方业务UoW、duplicate后普通读取，成功新建不多加SELECT。
- 规则冲突按具体callback分别为StatementRejected与RULE_VERSION_CONFLICT，不宽泛映射其他StatementRejected。候选未知API row的内部错误类型尚不等价，已明确不能投产。
- 完整事务/锁差异、异常范围、后续责任岗及未执行验证见agents/database/scan-run-rfc/design.md；cursor/checkpoint/kill恢复/tick不改。
- 若未来另有经准入方案，数据库岗只改persistence，固定调度岗消费facade；本候选已被总协调否决，不再排调度实施。
- 原件candidate-v1.patch、candidate-v2.patch、before-cloc.json、candidate-v2-cloc.json、line-budget.json保留；默认88列scratch格式化失误及原观察也记录，没有变口径凑数。
- git apply --check退出0、两候选ast.parse通过，仅语法和补丁适用性；没有pytest/MySQL/HTTP/MQ/seed/CI/覆盖率/性能结果。未读独立私有材料、未联系测试岗，未新增检查脚本。
- root后报5dcb73cc10c38deb14fae68d33318b04d538fecf全局5980/超880，本岗只核两个目标文件与基线相同，未新跑全局统计。规模和正式性能继续未通过。
- 过程/实发prompt/交接均更新；GitHub Issue4/Issue6实际阶段评论见本轮回执。旧AST隔离原型46/1且生产节省0的历史不覆盖、不重跑。
