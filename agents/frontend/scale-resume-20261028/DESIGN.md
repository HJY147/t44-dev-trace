# 前端规模复核设计｜2026-10-28

AI frontend 岗从固定基线 `a12e9e70b963bacafda3242bb6d82e53ee912ff1` 新建
`codex/frontend-scale-resume-20261028` 独立 worktree。实际提示词为
`ROLE-frontend-SCALE-RESUME-20261028-v1`。总协调提供的应用口径为 5933 行，
上限 5100，超出 833；最终以未改动的固定计数器实际输出为准。

先读 AGENTS、岗位边界以及旧 `size-round9/DESIGN.md`、`REPORT.md` 和对应提示词。
旧轮已经审过递归表单、七页面工作台、异步 helper、映射搬 JSON 和 CSS 合并，
本轮不重做旧失败原型。当前基线相对旧 round9 基线 `043fc464` 的 `frontend/`
与 `scripts/metrics/source_count.py` Git diff 为空；仍逐项核对实际调用和模板。

准入条件为真实结构性消重净减超过 30 行；不能压行、增加分号合并语句、minify、
改变统计、移入漏计目录、删除功能或损坏米咖圆角液态玻璃、响应式和无障碍退路。
保留所有 89 前端既有目标；生命周期、token、卸载、幂等、版本和业务拒绝边界不弱化。

| 本轮具体检查 | 当前证据与候选预算 | 决定 |
| --- | --- | --- |
| 重复加载/错误状态模板 | WorkspaceView 与 TaskDrawer 各两条 DataState 调用，共 4 个现有物理行；即使删除全部，毛收益也仅 4 行。新包装组件还需要 props、emit、两分支及调用，预计净增 | 无法达到 >30，保留现有 DataState |
| 页面和记录操作按钮循环 | TaskDrawer 的五按钮已有同一模板行；工作台的项目/迭代/通知/成员操作各按业务上下文成组，参数、禁用条件与动作不同。改循环需要新增配置和派发分支，不能删除超过 30 个物理行 | 无可信净收益，不实现 |
| schema 表单字段 | FieldEditor 已递归处理 object/array/boolean/enum/number/time/text，OperationForm 已统一校验、提交、幂等重试、冲突刷新和版本采纳；没有一套独立表单可删 | 不重新抽象 |
| 列表、递归详情、页头与导航 | RecordList、RecordView、PageHeading、SidebarNavigation 已共用；RecordView 的理由/缺失/未核对原文分支不是可互换的重复 | 不删除语义差异 |
| 异步刷新生命周期 | 旧 round9 已估净增；本轮确认 TaskDrawer 两段请求之间显式 token/active 检查，WorkspaceView 的 context/watcher/sequence 路径不同 | 不重复旧 helper 原型 |
| 样式与字典 | 样式已有共用 selector/token；本轮再静态枚举同 media context 的完全相同规则，核算合并上界。字典搬 JSON 不构成真实减行 | 保留视觉与统计边界 |

以上是静态预算，没有做产品原型，不能称作实际节省。没有可信 >30 行候选时，
交付 no-candidate 审计、固定 cloc 输出及逐文件 SHA，不修改产品、不新建镜像测试，
不重跑无关浏览器、类型构建、CI、API、数据库或性能。新证据仅绑定本基线及本岗
文档提交，不影响总协调冻结 a12 的云性能声明，也不解除规模/独立验收等其他门禁。

临时证据号经总协调确认后以 `O_EXCL|O_NOFOLLOW` 预留
`tmp/789_frontend_scale_resume_20261028/789_RESERVATION.json`；只写本 worktree。
没有读取独立 792 private，没有操作云、根工作树产品、研究正文或独立测试岗。
