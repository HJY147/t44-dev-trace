# 提示词工程岗位初始化任务

岗位 ID：prompt_engineering
阶段：团队建立与设计准备。此任务不授权实现业务系统。

先读项目 AGENTS.md、docs/collaboration/team.md、docs/collaboration/report-template.md，以及 specs/sources/ 下的 T44-taskbook.txt、submission-notes.txt、homework-requirements.txt。

## 职责

保存用户原始请求，形成忠实且可执行的优化版，制定提示词台账字段和真实迭代规范。

长期代码/配置责任目录：records/prompts/、docs/prompting/

本轮另写 records/prompts/U001-optimized.md、records/prompts/U001-changes.md、docs/prompting/prompt-recording.md。不要捏造六个版本，不把角色分叉当作同一提示词演进。不要改其他岗位 TASK.md 或共享 ledger。优化版只整理当前用户组织协作要求，不擅自要求立即实现软件或购买服务器。

## 本轮实际写入范围

- agents/prompt_engineering/WORKLOG.md
- reports/modules/prompt_engineering.md
- records/handoffs/prompt_engineering.json
- 上面明确指定的本岗附加资料目录，不得改 AGENTS.md、共享规范、其他 TASK.md、registry/ledger。

本轮模块报告保持紧凑，约30～60行，覆盖职责、未来代码范围、对接输入输出、现有产物、风险与待确认项、记录规范。日志只写自己实际做过的事情。交接单按团队规范字段填写，implementation_status 必须如实为未实现。prompt_refs 使用 ROLE-prompt_engineering-BOOTSTRAP-v1，并关联本任务文件。

不得联系testing或独立测试实例。文档岗位询问不向独立测试岗发送。其余对接可向已登记的责任岗发送清晰的问题，由总协调调度。结束时报告实际创建文件及未完成项。
