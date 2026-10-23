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

## 2026-10-23 R001 审阅与调试指导（ROLE-guidance-R001-REVIEW-GUIDE-v1）

- 实际派工来自 root；先读当前 AGENTS，当前根 HEAD 为 `f103600b0e98f8d60689d2db6dfd5211a9fd0f2a`，新建独立 worktree/分支 `.agent-worktrees/guidance-r001-review` / `codex/guidance-r001-review`。未使用其他岗位索引。
- 只读 R001 原话/provenance、D001/D004、capacity pending、函数契约与实现约定、README 和相关公开模块说明；未读独立测试私有用例/工作日志，未联系独立测试。
- root 限定性能诊断 quiet 窗口只轻量 MD/JSON；本轮没有运行产品、测试、浏览器或渲染，不导入产品模块。旧初始化产品未实现与未采用是历史，追加当前实现/决定，不倒填当时记录。
- 实际回答 documentation 的 `ROLE-documentation-M2-QUALITY-v1` 问取：给出 R001/出处、D001/D004；R001 为本人观点而非教师课堂原话，研究正文/课程建议待本人；AI 过程、AI 发现/修复不等于学生独立收获或人工识别。没有提供姓名/学号值，没有代署名。
- 新增函数索引和审阅/调试指南：真实 `decide`、Runtime/Workflow/CAS/UoW 与前端请求函数 I/O；配置按真实版本化 JSON 和 env 说明；仅 MD 未执行示例与空表，不创建脚本、不消耗 tmp 编号、不凑人工修改/幻觉配额。
- 实际命令：git 状态/HEAD/worktree、`git worktree add -b`、cat/sed/nl/rg 只读源码/文档、gh 读取 #10/PR21、内联 Python 仅哈希/文本/JSON。R001 SHA 与 provenance 匹配，capacity 状态仍 awaiting_user_reply。
- 两次初始只读路径探查包含不存在的 `domain/transitions.py`、`persistence/gateway.py`、`.vscode`，rg 返回 2；已按 `rg --files` 更正到 state_machine.py、rows.py，指南不声称已有 launch.json。没有因探查失败运行产品。
- 一次合并补丁因同文件同时 delete/add 被 apply_patch 拒绝；没有部分写入，已拆分更正。这是本岗编辑过程错误，不是学生独立识别幻觉或产品缺陷。
- 实际 prompt 原文与产物映射存 `agents/guidance/prompts/ROLE-guidance-R001-REVIEW-GUIDE-v1.md`；来源是 root 实际派工，不是用户新写的 prompt，也不自动算六版演进。
- 必要事实核对结果：33 个本地链接存在，21 文件哈希/函数签名行号与索引一致，R001 哈希匹配出处，规则/模板 JSON 版本均1，capacity 仍 pending；`git diff --check` 退出0。仅文档核对，不是产品测试。
- 已实际发表阶段评论：Issue #10 https://github.com/HJY147/t44-dev-trace/issues/10#issuecomment-6364270074 ；PR21 https://github.com/HJY147/t44-dev-trace/pull/21#issuecomment-6364271593 。正文存本岗 r001-stage-comment.md，未发审核成功或合并。
- 提交前核对独立分支 codex/guidance-r001-review、索引为空；仅显式暂存 handoff 列出的10份本岗 MD/JSON。R001、D001/D004、pending 源文件和产品代码均未修改；不合并或发审核success。提交/推送准确SHA由 Git 回执和 root 交接登记。

## 2026-10-24 M6 初学者检查点（ROLE-guidance-M6-v1）

- root实际派工存`agents/guidance/prompts/ROLE-guidance-M6-v1.md`。先读AGENTS及本岗TASK/WORKLOG/report/handoff；从最新codex/integration的0783a42独立建`.agent-worktrees/guidance-m6`/`codex/guidance-m6`，只用自己的索引。
- 只读R001原文与provenance（哈希匹配）；R002只读公开provenance，不读私密原文、封面、任何tmp/independent内容、未发布测试或测试内部消息。只读已明确发布的v3冻结元数据，没有打开其中引用的私密路径。
- 用rg定位后按实际backend/t44与specs/contracts读取源码；初始探查backend/src、docs/contracts和新docs/guidance不存在，rg返回2后更正，不据错误候选路径编造入口。
- 向backend和frontend_logout各发1个实际教学澄清，收到两条AI回复并逐字存M6-actual-qa.md；没有人类访谈或测试岗联系。backend纠正本岗提问中的execute_operation/save_task/未提交泛称；实际入口为endpoint.handle→Runtime.execute→Business.dispatch→changeTaskPlan→cas/schedule_diff，后端候选已有0549提交。不是学生发现幻觉。
- 新建M6中文指南及5项待本人完成练习/空表，解释Vue与38op契约、FastAPI、SQL主事务/claim/拒绝audit、outbox/MQ/ACK、scanner另一入口、Git/审核/自测/独立验收差别；不写学生最终研究正文，无亲改/断点/实测新证据。
- 源码截止0783；45文件SHA和40函数位置归档M6-source-manifest.json，权威/运行OpenAPI字节一致、1.1.0/31paths/38ops。当前完整绿色仅832的437BE/65FE及Docker；DB3b7计数6186超5100，P95原失败和v2未完、v3冻结0执行保留。root后报Issue28新组合42243eb合并并触发CI，仅加时点补记，不等待或预判。
- GitHub连接器核对Issue10为本岗thread后，按已有授权发表阶段评论https://github.com/HJY147/t44-dev-trace/issues/10#issuecomment-6374412075；再次fetch全部评论，仅存新评论的精确正文/id/url/login并逐字比较为true，证据M6-issue10-readback.json。没有发审核success或合并。
- 实际执行仅git只读/worktree创建、rg/cat/nl/sed、内联Python文本/JSON/哈希、apply_patch及上述GitHub读写；未导入/启动产品、未运行测试/负载/浏览器/渲染，未申请或创建tmp练习脚本编号。
- 收尾只做文档本地链接、源码hash/函数位置、JSON、R001出处、问答原文/Issue评论一致与git diff核对；不是产品测试。结构核对的实际数值见docs/guidance/M6-document-checks.json。最终仅显式暂存本岗产物并commit [skip ci]/push自身分支，准确SHA与范围由Git回执交root。
