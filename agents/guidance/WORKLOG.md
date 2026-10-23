# guidance 工作日志

## 2026-10-23 初始化（ROLE-guidance-BOOTSTRAP-v1）

- 实际派工：总协调消息要求读取本岗 TASK，建立真实问答、选择记录和后续指导机制；不实现产品、不联系独立测试。
- 读取：根 `AGENTS.md`，`agents/guidance/TASK.md`，`docs/collaboration/team.md`、`report-template.md`，三份 `specs/sources/` 依据，`records/qa/source-questions.md`、`records/prompts/U001-original.md`。
- 实际只读命令：`pwd`；`rg --files` 定位项目规则、任务和本岗目录；`cat` 阅读上述材料；`date -Iseconds` 得到整理时间 2026-10-23T11:40:08+08:00。内存索引关键词检索无本项目相关材料，未用旧项目事实填补本项目。
- 向总协调发送一次状态消息，说明来源含四项早先问题/选择，服务器建议未采购未压测、技术方案未逐项获用户确认；未联系 testing 或独立测试实例。
- 用 `apply_patch` 新建问答规则、五项问答、用户选择/AI 建议台账和中文概念说明；没有修改 `source-questions.md` 或原始用户提示词。
- 真实性边界：早先问题只由来源摘要支持，未补造逐字消息和发生时间；已有技术方案与服务器配置记作 AI 建议，Python 和岗位组织要求记作用户表达，AI 起草模板记作用户委托。
- 新建本日志、模块报告、结构化交接单；全部业务实现、部署、性能实测与独立验收均未进行。
- 提示词：实际使用 `ROLE-guidance-BOOTSTRAP-v1`，对应 `agents/guidance/TASK.md` 及本次派工。此 ID 是岗位派工标识，不计作同一用户提示词的新增演进版本；本轮没有另行执行“优化版”提示词。
- 提示词约束的作用：限定初始化范围和真实证据来源，避免把建议、用户决定、AI 操作和已完成部署混写；对应本轮全部七个文件。
- 实际验证：运行内联 Python，解析交接 JSON 并检查团队规定的 12 个字段、`未实现` 状态、提示词 ID、七份产物存在且交接清单一致；模块报告 51 行，符合 30～60 行要求。结果：全部结构检查通过；这不属于产品测试或独立验收。

## 2026-10-23 文档岗实际问询与 M0 归档（ROLE-guidance-M0-COMMIT-v1）

- 实际询问者：documentation；接收时间约 2026-10-23T13:45:17+08:00。询问内容摘要：既有产物、业务实现/执行状态、未冻结对接、日志与 prompt 位置；同时授权在持有唯一 Git 索引期间归档指导岗并在 Issue #10 发布阶段评论。
- 已实际发送回答给 documentation：七份资料是问答/决策格式、中文概念说明及日志/报告/交接；业务代码、部署、压测、集成和独立验收均未执行；`gqa-v1` 是内部记录格式，不是业务接口冻结；后续需要真实用户来源与责任岗规格/命令/版本。
- 本次只读核对 `records/decisions/D001-business-rules.md`：用户实际回复“采用这套规则，继续设计和开发”，形成 business-rules v1。它属于用户决定，不属于用户亲自改码，也不等于其他技术选项逐项批准或实际生产发布授权。D001 不由本岗改动或提交。
- 保留初始化时的初查历史；已在问答、决定及指导资料追加 D001 当前事实，不以新事实改写旧查询时点。
- 实际执行 Git 只读核对：分支 `codex/team-bootstrap`，索引为空，HEAD 为 `29ec3401564243dc34f41e6a1bcca81b73528455`；未接管其他岗位未暂存文件。
- 本次实际 Prompt-Ref：`ROLE-guidance-M0-COMMIT-v1`，来源为 documentation 本次实际派工消息；约束仅归档本岗、发布真实阶段说明，不新增业务实现或提示词演进数量。初始 prompt 位于本岗 TASK，阶段 prompt 的执行证据为本节、交接单及 `github-stage-comment.md`。
- 实际执行 `gh issue comment 10 --repo HJY147/t44-dev-trace --body-file agents/guidance/github-stage-comment.md`，返回阶段评论 https://github.com/HJY147/t44-dev-trace/issues/10#issuecomment-6358357296 。未 push、checkout、merge 或宣布审核通过。
- 提交前再次核对分支为 `codex/team-bootstrap` 且索引为空；本轮结构检查确认交接 JSON 有效、八份本岗产物存在、模块报告 58 行、业务实现状态仍为未实现。随后仅显式暂存本岗八份文件，提交结果由实际 Git SHA 及文档岗归档记录。
