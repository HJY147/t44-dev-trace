# 提示词工程岗位阶段报告

## 任务与依据

- 岗位：prompt_engineering；阶段：团队建立与 GitHub 协作设计准备。
- 依据：根 AGENTS、岗位 TASK、团队与 GitHub 工作流，以及 U001/U002/U003 原文。
- 职责：忠实优化、真实提示词留痕、亮点候选整理；当前不实现产品。
- 对应任务书 AC-09 与第 12 条，记录规范不代表最终数量指标已达标。

## 实际产物与状态

- `records/prompts/U001-optimized.md`、`U001-changes.md`：U001-O1，proposed。
- `records/prompts/U002-optimized.md`、`U002-changes.md`：U002-O1，proposed，关联 U003 公开补充。
- `records/prompts/ROLE-prompt_engineering-BOOTSTRAP-v1.md`：初始化实际派工正文。
- `records/prompts/ROLE-prompt_engineering-GITHUB-v1.md`：本轮实际派工正文。
- `docs/prompting/prompt-recording.md`：台账与真实迭代规范 v1。
- `docs/prompting/highlight-candidates.md`：U001/U002 用户原创亮点候选与证据清单。
- 本岗 WORKLOG、交接 JSON 和静态校验证据均单独留存。
- 长期责任目录：`records/prompts/`、`docs/prompting/`；产品实现状态仍为未实现。

## 输入输出及对接

- 输入：用户原文、实际派工、任务与规则、上下文版本、产物和作者证据。
- 输出：优化建议、变更说明、真实 prompt 引用、亮点候选及待补证据。
- 总协调登记共享 ledger；本岗未改共享台账、原文、共享规范和其他岗位文件。
- 文档岗后续可索取原文、说明与实际证据；尚无证据的 Issue/PR/commit 不补造。
- 版本：prompt-recording-v1 / U001-O1 / U002-O1；不冻结业务接口。
- 缺正文、缺使用证据或作者不明时标为待补，不计作已使用或人工改码。
- 未联系独立测试；只引用总协调核对后可公开的冻结结果。

## 设计与取舍

- 优化稿与实际派工分开，岗位分叉不能用于凑六版演进。
- U001/U002 原创归属用户，AI 整理不记为用户亲笔修改或人工代码修改。
- U003 明确公开开源；许可、分支和索引操作按实际项目决定分别留痕。
- 亮点描述设计意图；质量、效率、缺陷改善须实际数据支持。
- 审核与独立测试职责分开，同账号岗位分工不称物理隔离或多人审批。

## 执行与验证

- 已读取新增原文、项目工作流并创建本岗资料；命令与摘要见 WORKLOG。
- 初始化文档静态检查 14 项通过；证据为 bootstrap-validation JSON。
- GitHub 追加轮资料静态检查另存 `records/prompts/prompt_engineering-github-validation.json`。
- 当前 M0 已分配 Issue #11、`codex/team-bootstrap` 与独占索引时段；历史未分配记录保留。
- M0 实际问答、评论正文及派工已归档；仅提交本岗产物，不 push、合并或发布审核通过。
- 业务功能、模块自测、集成验证与独立验收均未运行。

## 风险与后续

- U001/U002 优化稿尚未实际派工；不能计成已使用版本。
- 六版演进、十二条人工修改、三条幻觉、五处最终代码映射仍待真实发生。
- 实际跨岗 Issue/PR、阶段 commit、审核及效果证据需后续补齐。
- 当前实际 prompt 为 ROLE-prompt_engineering-M0-COMMIT-v1，关联岗位 TASK、Issue #11 和派工快照。
- 本次提交结果由返回的完整 SHA 和文档岗收集记录核对；不在提交内预填自身 SHA。
