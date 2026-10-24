数据库AI；ROLE-database-INDEX-READONLY-v1；公开BE d834静态交接补充。先行设计0073a39已push后，才仅用原955/ABBA自有t44_profile（MySQL8.4.11、原fixture hash不变，项目44/task6004），核18083空闲、旧四server不存在、当前app可见本库其他连接0和数字归属。2026-10-24T00:44:34Z一次内联只读，共14条：4元信息/归属、三表SHOW INDEX/CREATE、4普通EXPLAIN；已rollback/close，无新DB/DDL/DML/ANALYZE/负载/服务或全局设置变化。

实际task_dependencies仅PRIMARY、uq_dependencies_edge(project,task,predecessor)、ix_dependencies_reverse(project,predecessor,task)、creator，无task_id前导自动键；其复合FK已由project前导现有索引满足。但tasks真实多三个fk_tasks_*自动键，notifications多fk_notifications_event(project,task,event)，所以不能由DDL显式列表概括无自动索引。官方前导列规则：https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html 。

当前依赖WHERE task_id ORDER BY id的EXPLAIN为type=index/key=PRIMARY/possible_keys=NULL/rows估9216；仅对照加project的形状ref uq_dependencies_edge/key_len8/rows估1但Using filesort，未改产品。tasks按project/planned_end,id分页选择uq_tasks_project_id并filesort；notifications event形状用uq_notifications_consumer并filesort（event_id=1不宣称记录存在）。

全部只是当前小fixture与既有开发库统计下优化器估算，非实际扫描/时延，不代表6000任务分布/400并发、正式失败根因或收益。SHOW统计基数也不是COUNT。完整原字段、归属守卫、静态对照、边界与实际prompt见agents/database/index-readonly/{plan.md,result.json,static-comparison.json,report.md}和本岗日志/报告/handoff；生产/DDL/API/用例/冻结未改。操作者AI，不是用户亲改，不联系或读取独立测试材料。Refs: #4。
