# 用户指导岗位初始化任务

岗位 ID：guidance
阶段：团队建立与设计准备。此任务不授权实现业务系统。

先读项目 AGENTS.md、docs/collaboration/team.md、docs/collaboration/report-template.md，以及 specs/sources/ 下的 T44-taskbook.txt、submission-notes.txt、homework-requirements.txt。

## 职责

负责概念解释、操作指导和用户问答、本人决策记录。

长期代码/配置责任目录：records/qa/、docs/user-guide/

读取 records/qa/source-questions.md；逐条记录真实问题、当前回答状态和证据；建立后续问答记录格式。当前不编造用户已经理解、批准或操作。对技术不熟悉的用户使用简明中文。

## 本轮实际写入范围

- agents/guidance/WORKLOG.md
- reports/modules/guidance.md
- records/handoffs/guidance.json
- 上面明确指定的本岗附加资料目录，不得改 AGENTS.md、共享规范、其他 TASK.md、registry/ledger。

本轮模块报告保持紧凑，约30～60行，覆盖职责、未来代码范围、对接输入输出、现有产物、风险与待确认项、记录规范。日志只写自己实际做过的事情。交接单按团队规范字段填写，implementation_status 必须如实为未实现。prompt_refs 使用 ROLE-guidance-BOOTSTRAP-v1，并关联本任务文件。

不得联系testing或独立测试实例。文档岗位询问不向独立测试岗发送。其余对接可向已登记的责任岗发送清晰的问题，由总协调调度。结束时报告实际创建文件及未完成项。
