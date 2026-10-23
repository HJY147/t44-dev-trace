# 用户指导岗位报告｜R001 审阅与调试指导

## 当前任务与来源

- 实际派工：`ROLE-guidance-R001-REVIEW-GUIDE-v1`，原文存本岗 `prompts/`；root 后续静默窗口和示例编号约束一并遵守。
- 独立 worktree `.agent-worktrees/guidance-r001-review`，分支 `codex/guidance-r001-review`，基点 `f103600b0e98f8d60689d2db6dfd5211a9fd0f2a`。
- 只读核对根规则、R001/出处、D001/D004、待答产能问题、函数契约、实现目录、README 与相关公开模块说明。
- 初始化/M0 状态保留在 WORKLOG、问答和决定历史；本报告用当前状态，不再把产品写作未实现。

## 实际产物

- 更新 `docs/user-guide/project-basics.md`，当前 UI/接口/采用/未决与历史时点分开。
- 新增 `docs/user-guide/review-and-debug.md`，说明单体分层、class/纯函数/UoW、真实函数 I/O 与副作用。
- 配置说明绑定规则/模板版本 1 JSON 与实际环境读取函数，不把 YAML/manager-based 举例转成选型。
- VS Code / breakpoint() 只给未执行 MD 示例和本人空表；不写产品或练习脚本，不申请/消耗 tmp 编号。
- `records/qa/question-log.md` 追加 QA-007～009；`decision-log.md` 追加 D004、R001 归属与 pending。
- `records/qa/R001-guide-sources.json` 记录 21 文件 SHA、真实函数行号、源码基点与未执行边界。
- 本岗 WORKLOG、handoff、实际 prompt、`r001-stage-comment.md` 同步归档；不改共享规则或原话。

## 对接输入输出

- 输入：真实用户来源、已采用 D001/D004、冻结规格与对应版本公开证据；输出：简明解释、空表、未决事项。
- R001 是本人观点，已收到；研究正文及课程建议仍待本人提供，不代署名或学生口吻成文。
- 无本人实际改码/断点/独立识别幻觉证据，不把 AI 修复、同意或读过材料算人工成绩。
- capacity 生命周期来源仍 `awaiting_user_reply`；不替用户选择、不扩大 createTask 已明确修复范围。
- 对文档岗真实问取已答复来源和边界，无新增教师课堂原话或私密姓名学号值。
- 指导建议交 root 转达；不与独立测试联系、不读私有用例/工作记录、不替其结论。

## 当前实现与验证边界

- 源码已有 Vue 业务界面、38 API、MySQL、RabbitMQ、APScheduler 与部署工具；本岗没有产品实现责任。
- 基点 README 的 0448fecb CI/容器证据只对应其 SHA；本岗不追测试预测数或重跑产品。
- 原版本独立未通过、性能延迟超标、规模超限仍保留；修复不等于新版独立复测通过。
- 本轮仅轻量 MD/JSON 写入和来源/链接/行号/差异核对；未启动产品/测试/浏览器/渲染，未扰动性能窗口。
- R001 文件 SHA 匹配 provenance；指南函数位置由文本读取核对，不导入产品模块。
- 两次初始路径探查包含不存在的候选文件/`.vscode`，返回 2 后按真实清单更正；未宣称存在调试配置。

## 过程与 GitHub

- AI guidance 为本轮实际作者/操作者，实际派工单独归档，不自动计入六版用户 prompt 演进。
- 日志保留原阶段和本轮真实询答、命令、来源、阶段评论链接；交接列已做与未验证项。
- 在 #10 / PR21 留真实阶段评论，显式路径 commit/push 本分支；准确 SHA 与链接交 root，不合并或发审核 success。

## 后续事项

- 用户独立审阅、改码、调试、识别及研究正文/课程建议均待本人真实行动与来源。
- pending 问题待用户答复；不要求重新批准 D001/D004，不收口令/私钥。
- 若要运行 MD 示例，先由 root 分配 tmp 练习编号并选择合适窗口；本轮没有执行结果可登记。
