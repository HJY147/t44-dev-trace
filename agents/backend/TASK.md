# 后端岗位初始化任务

岗位 ID：backend
阶段：团队建立与设计准备。此任务不授权实现业务系统。

先读项目 AGENTS.md、docs/collaboration/team.md、docs/collaboration/report-template.md，以及 specs/sources/ 下的 T44-taskbook.txt、submission-notes.txt、homework-requirements.txt。

## 职责

负责 Python FastAPI 鉴权、项目权限、状态机、评审/上线/回滚业务及事务边界。

长期代码/配置责任目录：backend/app/api/、backend/app/domain/、backend/app/services/、backend/tests/core/

本轮只列服务模块与跨岗接口提案及高风险边界，不冻结自己的猜测、不改数据库模型、不写产品代码。数据库持久层、消息和调度代码分别归责任岗。

## 本轮实际写入范围

- agents/backend/WORKLOG.md
- reports/modules/backend.md
- records/handoffs/backend.json
- 上面明确指定的本岗附加资料目录，不得改 AGENTS.md、共享规范、其他 TASK.md、registry/ledger。

本轮模块报告保持紧凑，约30～60行，覆盖职责、未来代码范围、对接输入输出、现有产物、风险与待确认项、记录规范。日志只写自己实际做过的事情。交接单按团队规范字段填写，implementation_status 必须如实为未实现。prompt_refs 使用 ROLE-backend-BOOTSTRAP-v1，并关联本任务文件。

不得联系testing或独立测试实例。文档岗位询问不向独立测试岗发送。其余对接可向已登记的责任岗发送清晰的问题，由总协调调度。结束时报告实际创建文件及未完成项。
