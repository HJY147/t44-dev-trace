# 仅原developer fixture的索引/普通EXPLAIN回执

数据库AI；先行设计0073a39，基线b40d888（公开BE d834）。唯一目标为原955/ABBA的`t44_profile`，MySQL8.4.11，fixture项目44/task6004；原私密fixture SHA256 1fd476ea96811e188e9483c35fc0e678b26b3333cfa89cbc8041db3180e0785c与本岗原回执一致，0600；env显式库与URL库均严格相等。未输出DSN/口令/Token/正文，未读其他私密材料。

2026-10-24T00:44:34.686085Z–00:44:34.718430Z，一次内联Python（既有backend/.venv，PyMySQL直接连接），未新增测试文件。连接前18083空闲、旧四server PID不存在；只查本库当前app可见PROCESSLIST，其他连接0，不声称跨账号全局证明。SELECT DATABASE/VERSION及项目/任务数字归属通过。四个元信息/归属查询、三表各SHOW INDEX/SHOW CREATE、四个普通EXPLAIN，共14条应用层语句，完整SQL/参数/原字段在result.json。没有执行被解释查询、ANALYZE、DML/DDL/seed/负载或变更服务/守护进程/全局设置；驱动正常握手/字符集会话初始化与最终rollback/close不混算为这14条。仅关闭本次连接，原fixture文件末次bytes仍相同。

## 显式DDL与实际自动键

[MySQL8.4官方规则](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html)：引用方外键列须按顺序位于索引前部；没有合适键才自动生成。因此不能由冻结DDL显式键列表推断实际没有自动键。

- task_dependencies实际只有PRIMARY(id)、uq_dependencies_edge(project_id,task_id,depends_on_task_id)、ix_dependencies_reverse(project_id,depends_on_task_id,task_id)、ix_dependencies_creator(created_by)。SHOW INDEX与SHOW CREATE均无task_id前导自动键。两个任务FK是(project_id,task_id)/(project_id,depends_on_task_id)，已有前两复合键满足。
- tasks实际比显式DDL多三个FK键：fk_tasks_latest_review(id,latest_review_id)、fk_tasks_approved_review(id,approved_review_id)、fk_tasks_approved_assessment(id,approved_assessment_id)。notifications多fk_notifications_event(project_id,task_id,event_id)。这是实际存在自动FK键的同库反例，不能一概写成“冻结DDL未显式列出所以没有”。原DDL hash仍c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4，未提出或实施DDL变更。

## 四个优化器估算（不是执行统计）

|固定绑定形状|type/key/key_len|rows估计|Extra|
|---|---|---:|---|
|当前依赖task_id=6004 ORDER BY id|index/PRIMARY/4，possible_keys=NULL|9216|Using where|
|仅对照：project_id=44 AND task_id=6004 ORDER BY id|ref/uq_dependencies_edge/8|1|Using filesort|
|tasks project_id=44 ORDER BY planned_end,id LIMIT20|ref/uq_tasks_project_id/4|1|Using filesort|
|notifications event_id=1 ORDER BY id|ref/uq_notifications_consumer/4|1|Using filesort|

第二形状没有实施到产品；第四event_id=1只是绑定形状，不声明该event/通知实际存在。前三用原fixture真实数字id，未造数据。RowsGateway默认ORDER BY id已在形状中保留，未用FORCE INDEX改变优化器选择。

SHOW INDEX Cardinality中tasks主键约5960、依赖主键9216只是既有开发库统计估计；未COUNT/更新统计或声称真实总量。fixture项目44当前读回仅确认指定task6004归属，没有测全库6000任务代表分布或400并发。所有rows/filtered/Using filesort只是当前统计下估算，不是实际扫描行数/时延、正式失败根因、瓶颈排序或收益证据。无第二次采样/负载/测试/coverage/独立验收结论。后续任何查询/索引优化须责任岗独立设计、保原授权/错误/锁语义并重新准入。

原Issue4 COMMENT全文GET/逐字核对另存github-readback.json，阶段发表正文github-issue4-comment.md。生产、DDL、用例和原冻结资料未改；操作者AI，不是学生本人修改。
