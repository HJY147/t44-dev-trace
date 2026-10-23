# 部署岗位初始化任务

岗位 ID：deployment
阶段：团队建立与设计准备。此任务不授权实现业务系统。

先读项目 AGENTS.md、docs/collaboration/team.md、docs/collaboration/report-template.md，以及 specs/sources/ 下的 T44-taskbook.txt、submission-notes.txt、homework-requirements.txt。

## 职责

负责打包、Compose、运行、环境、备份恢复、发布/回滚操作说明和合并门禁运行机制。

长期代码/配置责任目录：deploy/、scripts/ops/、.github/workflows/

本轮只建立依赖、环境和交接清单，已建议应用8核16GB80GB SSD、压测4核8GB40GB SSD，尚未购买、部署或压测；不能承诺配置保证达标，不执行安装、租赁、外部发布。

## 本轮实际写入范围

- agents/deployment/WORKLOG.md
- reports/modules/deployment.md
- records/handoffs/deployment.json
- 上面明确指定的本岗附加资料目录，不得改 AGENTS.md、共享规范、其他 TASK.md、registry/ledger。

本轮模块报告保持紧凑，约30～60行，覆盖职责、未来代码范围、对接输入输出、现有产物、风险与待确认项、记录规范。日志只写自己实际做过的事情。交接单按团队规范字段填写，implementation_status 必须如实为未实现。prompt_refs 使用 ROLE-deployment-BOOTSTRAP-v1，并关联本任务文件。

不得联系testing或独立测试实例。文档岗位询问不向独立测试岗发送。其余对接可向已登记的责任岗发送清晰的问题，由总协调调度。结束时报告实际创建文件及未完成项。
