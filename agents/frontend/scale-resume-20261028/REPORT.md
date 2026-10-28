# 前端规模复核结果｜2026-10-28

本轮结论为 **no-candidate；产品实际改动 0，实际减行 0**。当前范围未找到可信
净减超过 30 行的小候选，不以新的配置层、压行、搬文件或损坏视觉来制造规模收益。
这是本轮前端静态审查结论，不是全项目不可优化的证明。

基线 `a12e9e70b963bacafda3242bb6d82e53ee912ff1`，独立分支
`codex/frontend-scale-resume-20261028`。设计提交
`6c06e16d8894147ed5e85aceb6ed40a8036ab6fb` 已实际 commit/push，之后运行原样
`scripts/metrics/source_count.py`，cloc 2.10 原工具 SHA 校验通过。
计数绑定设计提交 6c06；其 backend/t44、frontend 与计数器对 a12 的 Git diff 为空。

| 固定口径 | 本轮实际结果 |
| --- | ---: |
| 应用有效物理行 | 5933 |
| 范围上限 | 5100 |
| 超出 | 833 |
| 前端计入文件 | 22 |
| 前端有效物理行 | 1099 |
| CSS 有效物理行 | 267 |
| CSS / 前端 | 24.29% |
| CSS / 全应用 | 4.50% |
| `--require-range` 退出码 | 1（实际规模门禁未通过） |

stdout 和完整 JSON 原样保留；stderr 0 字节。逐前端文件原始行、cloc 行、字节与
SHA-256 见清单。前端及计数器相对旧 SIZE-ROUND9 基线 `043fc464` 的 diff 也为空；
旧审计的 1099 前端行仍与本轮实测一致，不能把旧 5875 应用总数当作本轮总数。

## 结构性候选与真实收益边界

- FieldEditor 61 行、OperationForm 75 行已构成递归 schema 表单和统一操作流程。
  没有多份独立表单可删；版本采纳、403/409 刷新、幂等重试、会话/卸载检查保留。
- WorkspaceView 101 行已统一七页面，RecordList/RecordView 各 20 行；状态、理由
  原文、未核对条目及缺失说明有不同语义，不能用删除分支换取减行。
- WorkspaceView/TaskDrawer 的 loading/error 共同模板仅 4 个现有物理行。
  新包装组件还需 props、emit、模板和两次调用，毛收益已不足 30，预计净增。
- TaskDrawer 五操作已在同一模板行；通知、成员等按钮依参数、禁用条件及业务动作
  不同。改循环新增配置/派发路径，不能删出超过 30 行；没有为此制作产品原型。
- TaskDrawer 两段请求之间的 token/active 检查与 WorkspaceView context/sequence
  路径不同。旧轮估算 helper 净增，本轮未重做已无收益的旧探针。

## CSS 补充检查

本轮按媒体/支持条件递归枚举 210 条 qualified rules，并在同一
at-rule context 内按完整、有顺序的 declaration tuple 比对。此清单只做静态筛选，
没有证明跨行移动仍满足 cascade/specificity，也没有修改任何 selector 或属性。

| 相同声明 | 同 context 原位置 | 忽略 cascade 风险的毛收益上界 |
| --- | --- | ---: |
| margin: 0 | 全局 h1/h2/p 与 .record-detail .record-details | 1 |
| color: var(--muted) | 面包屑与 .record-detail dt | 1 |
| hover 色和下划线 | .text-link:hover 与 .text-button:hover | 1 |
| min-width: 0 | .business-records 与 .form-field | 1 |
| color: #a34839 | required/danger/field-error 与登录错误 | 1 |
| padding-inline: 18px | 1180px 断点 topbar 与 metric-card | 1 |
| display: none | 760px 断点四条隐藏规则 | 3 |
| 合计 | 7 组 | 9 |

即使忽略所有 cascade 风险并合并上述完全相同规则，最大可删规则行也只有 9，
不是已实现的安全净收益。另一个相同 `display:none` 声明组跨全局/1180px/760px，
适用范围不同，不能改成一个条件。部分重复属性抽 token/common class 后，原有
规则仍需保留差异属性，新 token/selector/class 反而增加行；不能用属性压行凑数。
现有 root token、玻璃共用 selector、表单/工具条/响应式规则已集中，保持米咖圆角
液态玻璃、reduced-transparency/reduced-motion/forced-colors 与窄屏退路。

## 实际执行与未执行

实际执行：历史记录/源码只读检查、独立 worktree、789 原子预留、设计 commit/push、
固定计数一次（内部 range 检查 exit1）、完整前端 SHA/基线字节比对、CSS 静态清单、
JSON/产物路径与 Git whitespace 检查。审计收集器整体 exit0 表示证据完成，不能
覆盖内部真实规模 exit1；没有产品/浏览器/API/数据库/云副作用。

没有新增或修改前端测试，没有运行 89 目标、coverage、typecheck/build、浏览器、
CI、MySQL、HTTP 或性能；历史 89 通过仍是历史来源的结论。本轮无产品变化，
不通过重复无关测试来扩大证据。总协调冻结 a12 的云证据完全不受本轮文档影响。
未读取 792 private 或其他未发布独立材料，未联系独立测试实例，未修改研究正文、
根工作树产品或统计器，未宣称独立验收、正式性能、规模门禁或学生手工改码通过。

证据：`tmp/789_frontend_scale_resume_20261028/` 的 reservation、收集器、
`789_committed_count.json`、`789_count.stdout`/`789_count.stderr`、
`789_source_inventory.json`、`789_css_static_audit.json`。
