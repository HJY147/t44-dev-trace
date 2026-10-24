# 只读索引与普通EXPLAIN核查：先行计划

本岗AI，ROLE-database-INDEX-READONLY-v1。基点b40d8889b1f9ea67f7c10a6dbaf22ecf57ce8b0d，接公开BE d83408955dea4afaab24991c00e490ad196c9ebe。设计先commit后动作；约10分钟收口。

唯一许可schema为t44_profile，依据本岗pool-retention设计/执行回执：2026-10-23T23:02:53.234248Z已停四个自有server、18083空闲、本库当前app可见连接0。原fixture路径为项目ignored runtime/bc5-contract-diagnostic-01/bootstrap/fixture.json，预期SHA256 1fd476ea96811e188e9483c35fc0e678b26b3333cfa89cbc8041db3180e0785c。仅读取原profile-environment.json解析连接，绝不输出DSN/口令/Token/自由正文。

动作边界：先核原fixture hash/权限、env的T44_DATABASE及连接URL数据库均为t44_profile，18083空闲，旧四PID不存在。连接后只核DATABASE/VERSION、当前app可见本库其他连接数及fixture项目和任务id归属；任一失败停止SQL，转静态交付。不枚举其他库。

最多：2个本库元信息/可见连接查询，2个fixture数字归属查询；SHOW INDEX与SHOW CREATE仅task_dependencies/tasks/notifications三表；普通EXPLAIN最多4个固定绑定形状（依赖task_id、project+task_id、tasks按project/planned_end/id分页、notifications按event_id）。所有SQL固定表名及绑定整数。EXPLAIN不带ANALYZE，不执行被解释SELECT、不取业务正文、不查询实际耗时/handler统计。当前无依赖时仍可解释fixture有效task_id，不捏造依赖行。

不创建/填充/清库，不执行DDL/DML/ANALYZE/OPTIMIZE或负载，不改服务/守护进程/配置，不接触t44_demo_v11/native/v2/v3/独立数据；只断开自己的连接。既有955仅只读源码参考，实际用内联一次脚本，不新增测试文件。

结论只覆盖该小developer fixture的真实索引和优化器估算，不代表6000任务/400并发、根因或收益；冻结DDL显式键不能证明InnoDB自动键不存在。权威DDL的依赖FK为(project_id,task_id)与(project_id,depends_on_task_id)，需将实际SHOW结果与这些有序列比较。官方规则：https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html 。

证据仅本岗目录：脱敏ownership/result JSON、SHOW/EXPLAIN原字段、运行回执、报告、真实Issue4评论及精确comments/:id GET全文读回。只提交本岗资料，生产/DDL/用例不改，根索引不碰。
