# 839公开发现后的最小后端候选与交接

后端AI设计/实施/本地测试。根基6d02cf1，应用基C=0dfb55c2191200d947c5423fd9ee74bb0812cc5a；先范围ca18de9、再设计6c1a00b，候选 **5cc856d6fa94b1fdde32605543b53822f9747f00**。候选只在独立分支，未部署/未合入云C。

唯一独立输入是指定839_PUBLIC_MINIMAL_FACTS_v1.md，SHA c35b37f47d822ef82b4f05627627a2b1f42eb7388c4f2a83d6c13493c5350d4a相同；没有读其它839/852/841资料、private引用或与tester交流。公开短窗3个502、延迟超限、0组600秒完成均保留；本候选不声称找到了502根因或让正式性能通过。

## 候选的输入/输出与实际范围

Workflow.transitionTask现在只对START、REWORK、UNBLOCK回DEVELOPING装载业务依赖，空前驱不发无必要IN SELECT。其它动作的纯域不消费dependency_states，传空tuple。原版本检查位置、review/assessment读取、D008错误槽、原域角色/状态/证据优先不变；Runtime图操作project X/依赖边读取/有序任务X、3次实时auth、2UoW、CAS、成功audit/outbox/COMPLETE同事务和拒绝退出后新审计事务均未动。

合法冻结数据前提与失效读差异已在设计写明：不以省读掩盖损坏数据；移除无用途的SQL后，不保证数据库故障在该已不存在语句上仍出现。剩余故障/ACK不明沿原分类。不改SQL门面、pool、代理、线程、DDL、15冻结文件/API/输出。原task_dependencies项目谓词早已在C内，未重复计收益。

## 实际开发证据

- 原C应用上新增3个真实SQLite/TestClient目标，SQLAlchemy事件只计SELECT表名、不存参数。业务状态/version、schema、成功audit、幂等重放以及未完成前驱仍拒绝开始均先通过；最后结构目标3红：BLOCK task4/dep1，UNBLOCK回pending task4/dep2，START空集task4/dep2。原件dependency-before.log/xml，不称业务漏洞。
- 候选后同3目标绿色，任务SELECT均3，依赖SELECT为0/1/2；仍含Runtime图锁前缀，没有去锁。连同原交付→回滚→返工、环/编辑锁、幂等/拒绝审计、角色/版本/人力错误优先、非空前驱全部交付859等共23绿/99 deselected。
- 另2个新HTTP目标采用明确受控持久状态边界（不是实际返工生命周期），证明UNBLOCK回develop/REWORK对未完成前驱仍409，task/outbox不变且独立拒绝audit成功；加原856的11项D008共13绿/121 deselected。两组共36个不重复开发目标，0失败/跳过；原856/859字节未改。没有gateway/matcher mock，没有外部HTTP服务/MySQL/云/负载。
- Ruff首次未显式指定backend配置，误用默认N999/88列，原失败保留。按原backend/pyproject.toml检查绿，新增test一处换行后format绿；未改规则、未格式化旧全文件。23+13运行均保留原TestClient弃用警告。
- validation.json核应用diff仅workflow.py；15现行冻结hash全匹配。准确候选按原脚本/原cloc2.10固定SHA bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83实际计量 **6316/5100，净+6，超1216，exit1**。原云C仍6310/超1210，不能沿用旧6307或假称性能修复减量。

全部命令、JUnit、源码blob/SHA与命令退出码在validation.json；scope来源、设计、原件同目录。新源正常push后独立CI自动触发，首次metadata在ci-initial.json；尚未归档完整CI、MySQL行锁/竞争或源码专审，不能用本地36目标替代。此阶段不等待平台跑完来占槽，不重跑旧CI。

## 下一步实际要测什么

优先同次资源与两层upstream证据解释502，具体字段/安全边界见design.md；未采到则保持未知。没有把30秒proxy_read当总时间、engine.acquire当纯poolwait、dispatch-to-entry当纯队列或inclusive cProfile当互斥CPU份额。不先改timeout、worker/pool或去auth/验证来做绿色。

DBowner已真实对齐：本岗不改其Rows/DDL/池，告知C已含项目谓词和A的2UoW/3auth；未来listTasks/索引/COUNT、全项目members锁、升级列表3N由各owner另设计，不能把项目X改SHARE。正式负载或微负载须root明确自有环境与窗口，当前未执行。

N07继续引用已封source-budget-current-C设计，没有可信等价删去1210的方案；候选反增6也如实保留。旧validator未应用-10/分页估-3是未证文本，不是实际节省，不足以填缺；不压排版/删功能/移动计量根/改统计或对独立oracle下注入结论。
