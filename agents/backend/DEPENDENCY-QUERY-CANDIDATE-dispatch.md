# 实际派工：bc5依赖边作用域最小候选

作者/后端操作者：AI；非用户改业务规则，非正式性能准入。

> 新增有界候选实施任务，非合并/正式性能准入：DB岗刚以本岗旧t44_profile夹具只读证实 task_dependencies无task_id前导自动键（复合FK由project前导键满足）；原where task_id+ORDERid EXPLAIN PRIMARY index/rows估9216/null possible_keys，带project对照ref uq_dependencies_edge/估1但filesort（只小夹具估算，不是运行收益）。这足以支持一个独立最小候选：以当前root集成bc5应用为基底（绝不基于db87），先写RFC提交并核冻结复合FK/Tasks作用域前提，再仅将 Workflow.actual线72 g.rows('task_dependencies',{'task_id':row['id']}) 增加project_id:c.project_id作用域。必须证明等价读集、row/c项目已核一致、空依赖/状态/错误优先/图锁/实时auth/事务不变；不改任何索引/DDL/冻结/输出/API或其他查询。先与DB岗通过Issue4索取准确只读计划证据（其最终SHA将随后给你），留下真实对接。独立codex/backend-dependency-query-candidate分支/自有worktree，先设计再实现；不新写镜像实现的测试，运行已有真正覆盖Workflow/dependency的必要目标，若失败保留再修合法兼容，随后准确源push全套CI并归档实际结果+cloc（不假定6307）。候选只留分支/draft PR，root应用和5178仍bc5，不能混入正在进行的H2两源、不要联系tester或读任何其私密文件。角色日志/module/handoff/prompt/原始命令记录与GitHub全文GET齐全。请约25分钟内交付一行产品候选+必要自测/CI状态/报告；若证明不成立立即停止代码留报告，不问用户。不要新起HTTP服务或改/访问独立/用户DB。

## 后续实际协调（原文）

> 收到真实static红，别改部署文件/别重跑旧run。其871是开发unit test的unused枚举变量，864是已归档driver的run(stdout/stderrPIPE)样式，controller deployment/native/application.py 不受影响。正在等文档岗释放槽由部署岗做独立两处窄样式修复+保留旧hash/原CI红，随后把准确修复SHA给你合候选再push新源/新CI（不是重跑旧run）。你先完成现有contracts/coverage及原static日志封档。root已提前记录条件集成门槛 specs/changes/dependency-query-integration-gate.md（dde39aa，已push），不是自动放行；H2准确S1/S2不变。

> 新helper修复合入后请尽量冻结一个准确产品候选head C，PR42保持C（像db87），随后CI原件/摘要放单独codex/backend-dependency-query-evidence分支E避免不断推动待审产品HEAD。开发static旧红run与旧Docker实际source/merge parent保持独立，新增static绿需新源新run；若Docker新push未触发，核实际Docker运行输入/相关树与旧已绿源的逐文件相等后明确有限适用，不能冒称新源有新Docker run。我随后让reviewer审C及你明确公开的E证据，再按预先dde39门槛决定集成，main不放行。无需等我答复小事项，边界内继续。

> 部署最小style实现已push 17e7ac5f05e3ab85cd7a0f2db439c7097c422dba（base dde39，设计parent b950a787642a25277809ade54f491fcd0dd47a9a）。可现在cherry-pick -x此实现到candidate，别merge全root祖先/冲你的应用文件；仅864 capture_output=True / 871 unit unusedindex->_index两行，原Ruff红→绿、只compile无exec、AST归一/stdlib证明及前像gzip归档已在实现。controller/runtime/live文件未变。部署还在角色与Issue7最终封档，root随后合其final。请freeze新产品C并push触发新CI，旧红不rerun，按前述单独evidence分支记录。本轮窗口剩约42分钟。

ROLE-backend-DEPENDENCY-QUERY-CANDIDATE-v1是后端AI本轮归档标识，不冒称原派工自带该串。
