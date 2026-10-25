Agent-Role: backend AI
Prompt-Ref: ROLE-backend-SNAPSHOT-ALIAS-v1 / ROLE-backend-API-WIRE-v1

两个已推送的独立阶段，未改main或自行启动完整CI/云：

1. V2-SNAPSHOT-ALIAS-01修复：`d63fe18f3227e1779d3951072636efcdb6181550`，分支 `codex/backend-domain-v2-size-20261025`。准确旧base两项append/clear回归2红，候选172域+143原HTTP全部通过；原initializer校验AST语句/顺序保持，validated review_evidence成员序列改tuple快照。仅models.py增加6产品行，当前后端实净省370（先前376是修复前历史stage）。已通知指定审核岗窄复审，未冒其结论。
2. 单独API候选：`2914c7da0d24a839061b8b72727907a56fd33d6a`，分支 `codex/backend-api-wire-boundary-20261025`，base为d63。仅API两表达式复用原response-schema检查的normalized payload，完整payload wire2遍→1遍；Runtime、响应校验、schema-missing/error边界、trace/meta/replay/headers/计时位置保持。API244→244，新增LOC节省0，不能当作另减200。

API候选开发验证：12新边界+143未改HTTP用例155通过，另真实SQLite20/100任务页用例1通过；1759个实际响应的body和全部headers与exact-base render tail在相同Runtime/meta/time输入下逐字相同，0遗漏/差异。覆盖35操作、11状态；这是响应渲染差分，不冒独立旧Runtime完整运行。完整API AST仅逆转两表达式即可恢复；时区、Decimal、Enum、非有限值、缺schema、编码及引用异常另测。无Token或body原文落盘。

CPU结果不挑绿：初轮candidate/base约0.955、0.959、1.016、1.016；新增真实页约0.981、0.991、1.018，**整体render稳定提速未证明**。确定局部工作减少：5次20页wire递归5925→2965、100页29125→14565；profile自身CPU约半，不转成端点延迟或正式性能通过。全部原始正负样本保留。此候选供总协调/审核选择，不自动准入。

报告：`agents/backend/source-size-20261025/snapshot-alias-fix.md`、`api-wire-report.md`；源码hash/AST/JUnit/cloc/差分/CPU证据在 `tmp/811_backend_size/snapshot-alias-*` 和 `api-wire/validation.json`。WORKLOG/module/handoff/prompt均更新。两阶段push用[skip ci]遵守总协调不自行启动全CI的指令，未改工作流或main门禁。全局源规模、组合CI、MySQL/正式性能/独立验收仍由总协调处理；本岗无可信额外200行API/runtime结构预算，释放并行岗位供消息/调度继续攻关。所有作者/执行者为AI，不记用户手改。
