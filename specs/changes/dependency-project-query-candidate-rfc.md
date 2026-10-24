# 依赖边查询项目谓词候选（先设计，未实施）

后端AI；基root b40d8889b1f9ea67f7c10a6dbaf22ecf57ce8b0d，应用逐字bc5aef9c62393134582affb7a690acb33ac2b833，**不基于db87**。候选仅Workflow.transitionTask原`g.rows('task_dependencies', {'task_id': row['id']})`增加受信`project_id: c.project_id`。不改SQL数量/ORDER BY/投影/锁、索引/DDL/冻结/API/输出/规则/其它读取。当前root/演示继续bc5；本提交只有RFC/prompt，不是实现或准入通过。

## 读集等价与前提

冻结DDL（schema.sql及schema_v1.sql SHA c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4）：tasks全局PK(id)且UNIQUE(project_id,id)；task_dependencies的(project_id,task_id)和(project_id,depends_on_task_id)复合FK分别指向tasks(project_id,id)。设当前task ID=t、其项目=p。任何合法边task_id=t，按全局PK与FK，其project_id必为p；因此`task_id=t`与`project_id=p AND task_id=t`读集相同，包括空集。对禁用约束/破坏FK的任意旧数据不作等价保证，不靠过滤修历史坏行。

Workflow开始`c.task(g)`已核task存在且row.project_id==c.project_id，否则RESOURCE_NOT_FOUND；随后原expected_version检查仍先于边读。Runtime.locked_scope同主事务先session→idem→必要project X→ordered members→ordered tasks X，目标task已锁；project字段无公开转移入口。候选不使用客户端body的project，不重排任何权限/版本/状态/证据/域守卫，不跳过空IN前驱SQL，不更改依赖算法/阻塞恢复/返工或CAS/审计/outbox/幂等/ACK不明语义。

## 有限计划依据与未知

根转述DB own-dev只读小夹具计划：原task_id+ORDER BY id为PRIMARY index、rows估9216、possible_keys null；增加project谓词为ref uq_dependencies_edge、rows估1且仍filesort。已向DB owner/Issue4索取最终SHA/准确公共原件，未把转述当本岗执行。复合FK由project前导键满足，无task_id前导自动索引；只在已确认合法读集上给优化器前导谓词。EXPLAIN估算不等于实际扫描/延迟/正式负载收益，不推原503或其它运行根因；索引保持原样。

## 验证与出口

只复用现有986真实SQLite HTTP覆盖：完整交付/回滚/返工、依赖不满足→前驱交付→开始、环拒绝/开发后编辑锁、删除依赖、角色/版本/严格union、当前返工人力守卫。SQLite fixture非用户/独立DB，不新起服务，不另造断言镜像谓词；原测试字节不改。先核oldsource/原测试适用性，再最小产品commit；错误原件保留。严格静态检查、14冻结和唯一生产差异核对，按现固定cloc实际计数（不预设6307），准确新SHA push后只一轮完整托管CI/44文件分母/原件。必要时CI待完成就交准确pending，不把定向通过当全套。

产品仅独立分支/draft PR；root/专审另决定合并与是否进一步测量。本轮不运行本机SQL、独立/用户库、真实服务或新负载，不读独立案例/日志/密文，不改其它岗文件。候选有效LOC预期不变但以实际为准；无法证明前提则停产品、只留报告。
