# 实际派工：bc5依赖边作用域最小候选

作者/后端操作者：AI；非用户改业务规则，非正式性能准入。

> 新增有界候选实施任务，非合并/正式性能准入：DB岗刚以本岗旧t44_profile夹具只读证实 task_dependencies无task_id前导自动键（复合FK由project前导键满足）；原where task_id+ORDERid EXPLAIN PRIMARY index/rows估9216/null possible_keys，带project对照ref uq_dependencies_edge/估1但filesort（只小夹具估算，不是运行收益）。这足以支持一个独立最小候选：以当前root集成bc5应用为基底（绝不基于db87），先写RFC提交并核冻结复合FK/Tasks作用域前提，再仅将 Workflow.actual线72 g.rows('task_dependencies',{'task_id':row['id']}) 增加project_id:c.project_id作用域。必须证明等价读集、row/c项目已核一致、空依赖/状态/错误优先/图锁/实时auth/事务不变；不改任何索引/DDL/冻结/输出/API或其他查询。先与DB岗通过Issue4索取准确只读计划证据（其最终SHA将随后给你），留下真实对接。独立codex/backend-dependency-query-candidate分支/自有worktree，先设计再实现；不新写镜像实现的测试，运行已有真正覆盖Workflow/dependency的必要目标，若失败保留再修合法兼容，随后准确源push全套CI并归档实际结果+cloc（不假定6307）。候选只留分支/draft PR，root应用和5178仍bc5，不能混入正在进行的H2两源、不要联系tester或读任何其私密文件。角色日志/module/handoff/prompt/原始命令记录与GitHub全文GET齐全。请约25分钟内交付一行产品候选+必要自测/CI状态/报告；若证明不成立立即停止代码留报告，不问用户。不要新起HTTP服务或改/访问独立/用户DB。
