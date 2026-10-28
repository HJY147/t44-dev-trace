# 下一小批后端重复规则封装

后端AI操作，基于精确f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f建立独立worktree/branch，不混入旧20Z工具或正在云测的f7源。本轮目标是可审核、正收益的小重构，不承诺补齐当前5898−5100=798行。

候选一：Reviews内部`_assessment_versions(g, task_id)`，输入原受信gateway和已核归属的task.id，输出原`g.rows('release_assessments', {'task_id':id}, order_by=('-rollback_plan_version',), limit=1)`列表。两个调用点保持在原有权限/状态/责任人/资源检查之后；创建时空列表仍下一版本1，审核时仍原`[0]`空表异常，不新增SQL/锁/事务。统一查询策略避免两处排序/limit未来漂移，预计净约8–10行。

候选二：Tasks内部`_editable_task(g,c,code)`，输入原Call及操作自己的锁定错误码，按原顺序执行manager→c.task→prestart检查，返回原row。只替换转派/增依赖/删依赖三处相同前置，不合并后面的owner、version、capacity、去重/环检查或CAS；expected/current state、错误优先级、网关顺序/锁及审计diff不变。预计净约3行。新增方法为内部受信接口，不对外部HTTP/OpenAPI、持久化/消息/调度定义变更。

拒绝目前的更大候选：typed-row通用schema会改变多错误时的短路顺序或净增框架；wire/normalized递归虽然外形相似，Decimal/datetime/tuple语义不同；已有component37不能重复计收益。没有把逻辑移入排除项、删除检查/函数或压行。

先在tmp/779_backend_scale_next_20261028冻结行为差分用例，对原f7跑基线；再最小实现。以真实Call和可追踪内存网关比较旧/新结果、异常细节、数据库调用、行变更及audit before/after；新增方法本身不当测试目标。必要原HTTP评估/任务编辑用例保留全部断言并限定选择运行。固定cloc2.10+原source_count.py计已提交应用字节，报告真实净收益；不改统计口径/原测试/云源，不跑全CI，不接触独立私件。若无正收益则回退候选并如实停损。
