# 文档汇总岗位初始化任务

岗位 ID：documentation
阶段：团队建立与设计准备。此任务不授权实现业务系统。

先读项目 AGENTS.md、docs/collaboration/team.md、docs/collaboration/report-template.md，以及 specs/sources/ 下的 T44-taskbook.txt、submission-notes.txt、homework-requirements.txt。

## 职责

主动向各岗索取有证据的资料，汇总需求报告、设计报告、测试结果、AI规格说明及研究分析报告。

长期代码/配置责任目录：docs/reports/、reports/final/

本轮按总协调提供的岗位清单实际向岗位询问资料并留记录；没有消息回复时标为未回复。测试岗仅读取其已冻结的报告，不发送任何消息。不得替用户编写个人经历，不把初始化说成开发完成。

## 本轮文档汇总的具体任务

从 docs/collaboration/agent-registry.json 读取实际 agent ID，向 frontend、backend、database、messaging、scheduler、deployment、guidance、prompt_engineering 以及新增 reviewer 岗主动索取资料。使用 collaboration.followup_task 唤醒已完成岗位；最多同时唤醒两岗，因为总协调与你仍占两个执行槽位。每岗只需短答当前实际文件、实现/执行状态、待确认的接口、日志与提示词位置，并在自己的 WORKLOG 记下本次问答。不要重复开展设计、研究或开发。

你不得直接或间接向 testing 发送消息，不派生测试 agent，不阅读其内部用例或工作日志；只读取 reports/modules/testing.md 这份已经返回总协调的初始化报告和 records/handoffs/testing.json。报告明确其未执行产品测试。

将真实询问、收到的原文回答、agent ID、登记时间及证据位置写入 docs/reports/collection-log.md；尚未收到的不得代写回答。写 docs/reports/ai-specification-guide.md，解释 AGENTS、岗位任务、将来冻结业务规格如何约束 AI，区别组织规则和业务规格。最后写 reports/final/team-bootstrap-summary.md，汇总这次团队建立的事实及尚未实施内容，不冒充需求报告、完整设计报告或最终研究分析报告。

本轮不用继续追问独立测试岗；中性测试资料已经从总协调收件。以全部九岗真实答复和其交接文件为依据完成收集，简明即可。

## 本轮实际写入范围

- agents/documentation/WORKLOG.md
- reports/modules/documentation.md
- records/handoffs/documentation.json
- 上面明确指定的本岗附加资料目录，不得改 AGENTS.md、共享规范、其他 TASK.md、registry/ledger。

本轮模块报告保持紧凑，约30～60行，覆盖职责、未来代码范围、对接输入输出、现有产物、风险与待确认项、记录规范。日志只写自己实际做过的事情。交接单按团队规范字段填写，implementation_status 必须如实为未实现。prompt_refs 使用 ROLE-documentation-BOOTSTRAP-v1，并关联本任务文件。

不得联系testing或独立测试实例。文档岗位询问不向独立测试岗发送。其余对接可向已登记的责任岗发送清晰的问题，由总协调调度。结束时报告实际创建文件及未完成项。

## GitHub阶段提交与实际问取

用户已追加公开仓库和各岗亲自commit要求。仓库 HJY147/t44-dev-trace 已clone至本项目根目录，main初始提交1996d44；当前分支codex/team-bootstrap。测试归档已由另一个无历史归档实例独立提交为baa9a5816504b8439e170b274bc962da3f7143d9，并在Issue #8登记，不得联系测试岗。

本轮你作为文档收集与串行提交队列执行者：按 frontend、database、messaging、scheduler、deployment、backend、guidance、prompt_engineering、reviewer 顺序，一次只 followup_task 唤醒一个已完成岗位。读取 records/github/issues.json 和注册表定位真实 agent/Issue；发送中性询问并授予该岗唯一Git索引时段。等该岗返回commit SHA和Issue评论URL后再唤醒下一岗；不要同时发两岗commit任务。若任务失败如实记录并转总协调，不接管他人暂存或git reset。

每岗询问包含：实际产物和实现状态、尚未冻结接口、日志与prompt位置；让该岗在本岗WORKLOG记录真实问答，并核对是否有“当前无HEAD”等已过时表述（初次检查结果须保留为当时事实）。让该岗自行将自己的日志/模块报告/交接及其handoff中列明的附加产物git add并commit，提交前确认当前分支codex/team-bootstrap与暂存区为空，绝不git add .或暂存别岗文件。正文带Agent-Role、Prompt-Ref: ROLE-<role>-M0-COMMIT-v1、Refs: #对应Issue；只commit，不push、不checkout、不merge、不设置审核成功。

各岗另写自己的 agents/<role>/github-stage-comment.md（可在本次commit中提交），用gh issue comment对应Issue --repo HJY147/t44-dev-trace --body-file该文件，说明本岗阶段、真实产物、接口需求与未验证内容，注明Agent-Role与Prompt-Ref。六个开发岗再选择一个上/下游Issue提出一条具体接口问题（引用已有草案，未确认就说明未确认）；backend排在后面，可实际读取自己的Issue中的前述问题并给有依据的当前状态答复，不能把回复当作契约冻结。评论正文保存到本岗agents目录再通过body-file发送。所有操作均有用户明确授权。

你的collection-log完整保存实际派工正文、每岗返回原文、完整SHA和评论URL，作为这些真实prompt和协作事件的证据；无需改总协调共享ledger。你自己最后提交自己的日志/模块报告/交接、docs/reports/及reports/final/产物，正文带Agent-Role: documentation、Prompt-Ref: ROLE-documentation-M0-COMMIT-v1、Refs: #9，并在Issue #9评论。仅加入自己的文件，不加入总协调当前未提交的注册表、派工台账、Issue请求文件或其他岗产物。

最终把九岗实际commit与自身commit、评论、待办汇总返回总协调。所有记录标为组织初始化与设计准备，不是产品完成。新审核岗也必须真实询问；独立测试只引用其公开冻结报告，不发送消息。
