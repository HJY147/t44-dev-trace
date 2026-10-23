# 数据库模块报告：Issue28固定有限历史读取已实现并自测

- Agent-Role database；Prompt-Ref ROLE-database-PLAN-HISTORY-v1；基线02c4b2a59cdcc3b3dc6bc7981735f4c1b74f181a；设计checkpoint e9a769a，独立codex/database-plan-history。
- 只实现RowsGateway.task_schedule_changes，完整契约见agents/database/plan-history/design.md；后端matcher/响应投影及UI仍由其责任岗拥有，本岗不称Issue28已关闭。
- 输入project_id/int与tuple[tuple[int,int],...]最多100（去重前）；严格int拒bool/串等，ID1..4294967295/Version1..2147483647，非法StatementRejected且0SQL。
- 固定schedule_changes完整codec行、project与iteration IS NULL、精确tuple-IN、稳定task/to_version/id排序；空0execute/有1execute；无LIMIT、跨乘积、N+1、额外连接/事务/提交/锁/cache。
- 完整列/ID范围/项目与pair/iteration/重复pair或id/硬bound违约PersistenceUnavailable并rollback-only。数据快照/理由/evidence的业务匹配归后端，不能把DB失败降成缺理由成功。
- 旧源目标真实AttributeError红；新SQLite/mock48通过，原993整文件66通过且包含同48；MySQL新增主读目标1通过、服务器异常目标1通过，最终为SQL账本同两目标2通过。数字重叠/重复，不能相加成独立案例。
- 原环境缺pytest、夹具漏project_members导致真实FK失败、I001排序失败均保留；只修环境选择/自有夹具/import，不改原断言/DDL/产品错误处理。
- MySQL仅t44_test自有有限随机名夹具，100精确pairs完整返回/交叉干扰/跨项目/iteration/0与1SQL/101/最大输入/长文JSON微秒UTC/不变性；104history及关联数据最后整事务回滚，用户不存在。
- 实际SQL及整数绑定/每case execute数见mysql-sql-ledger.json；不是正式性能。真实服务端失败受控为不存在owner表，不操作别人的表或服务器。
- 原14冻结件与02c4b2a字节/摘要全同，16旧RowsGateway方法及两文件旧函数字节同原；unchanged-boundaries.json。通用rows/get/count/savepoint/UoW原语义未改。
- 最终限定Ruff通过、rows定向Bandit0；无完整CI/coverage/HTTP/独立复测/负载结果，精确新源码审核及root组合CI待调度。
- cloc预算18..30→设计35..50→实际rows237→299/净+62，均如实保留；基线应用6124→产品提交3b7bc0c实测6186/--require-range退出1，仍超5100。不压行/移计数或削守卫。
- summary.json及原始log/JUnit可核对真实结果；本岗自测不代独立验收，AI修改不计学生亲改，main仍保护。
- 产品checkpoint 3b7bc0c92f92a20bc69ee76293f547fe9f1e9a9a已push；Issue4/28实际发布及comments/:id精确GET逐字readback已归档github-readback.json，评论6373901751/6373902163。
