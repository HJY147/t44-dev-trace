数据库AI；ROLE-database-PERF-PUBLIC-C-v1。仅核读指定839_PUBLIC_MINIMAL_FACTS_v1.md/hash c35b37...，无其他839/私有资料、不向839/测试发送开发信息。公开任务短窗P95流转3645.763385ms/查询3315.969690ms，10814稳态1个502；校验7273预热2个502、稳态0；完整正式组0保留，资源待公开，根因未知。

设计80e9d67→root离线限定cacd0af→工具d75866f0d4077dd0399672f6dc914a82de6b9399先提交后唯一执行。838路径tmp/838_database_public_diagnostics/838_database_public_diagnostics.py；只显式--run、本地内存SQLite合成表+MySQL方言编译，不读env/凭据、不连MySQL/HTTP/服务/负载。源13文件逐字/hash固定C0dfb55c；根6d02生产对C同。无生产/DDL/池/锁/认证/用例改变。

确认当前C Workflow已经project+task依赖谓词，不重记旧优化。listTasks本身无逐task N+1，正常project 10S/2U；validateContractPayload4或5S/1U；依赖列表11+P、升级列表10+3P。成员全project S锁随M物化、图编辑全图遍历随边数；不能未经并发设计删锁。源码默认5+10仅默认，不证明本轮运行池/worker值；Rows SELECT不含初始化/ping/commit/reset，不能据此解释502或把acquire叫纯poolwait。

一次SQLite真实生产Rows观测19配方/71执行（非HTTP trace/71验收）：依赖度0/4/32原二读2/2/2，候选skip-empty1/2/2；不消费依赖guard候选0只是配方、没执行生产动作。成员3/32均1读但物化3/32行；依赖页1/4/32原2/5/33，对照batch2/2/2，固定数据输出/顺序/缺引用失败一致。SHARE/UPDATE/CAS仅MySQL编译与SQLite顺序谓词，不是MySQL锁/RC/并发CAS或延迟收益。Import/显式run/禁止覆写边界通过，初次工具Ruff3项错误保留后修，未跑额外矩阵。

BE真实确认现有Rows足够，自己独立5cc856d guard-specific候选不动Runtime/global empty-IN/锁；DB不改services。请BE对接确认本岗边界仍适用，后续若单独审Tasks.addTaskDependency:139（不同于已修Workflow）existing查边缺project谓词、依赖页batch或升级3N批读，保授权/页序/全部通知/缺引用错误/RC非原子边界，不现在捆绑实施。

完整设计/当前索引与静态S/U账本/源码SHA/一次结果/限制见agents/database/perf-public-c/{design.md,static-path-receipt.json,offline-run1.json,report.md}。本轮MySQL/云SQL/HTTP/负载NOT_RUN；新MySQL阶段须另冻结开发schema/config与窗口。公开性能失败尚未修复/通过，实际DB生产变更0。Refs: #4。
