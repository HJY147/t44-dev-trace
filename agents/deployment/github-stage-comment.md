Agent-Role: deployment
Prompt-Ref: ROLE-deployment-M0-COMMIT-v1

当前为 M0 团队建立与设计准备，部署模块未实现。本轮实际资料：

- `agents/deployment/WORKLOG.md`：初始化、文档岗真实问答、实际命令与范围记录。
- `reports/modules/deployment.md`：打包/Compose/运行、云环境、备份恢复、发布回滚和门禁职责。
- `records/handoffs/deployment.json`：结构化状态、上下游输入输出、未验证项及提示词引用。
- 本岗 `agents/deployment/github-stage-comment.md` 与 `agents/deployment/github-interface-question.md`：本轮实际评论正文。

已核对资料存在、交接单 JSON 结构和未实现状态。当前 main 保护经 API 核对要求 `reviewer/stage`，`strict=true`、`enforce_admins=true`；产品静态检查、契约测试、覆盖率三项 CI 仍未实现，未把保护存在写成测试或审核通过。

待冻结前端构建/代理路径、后端启动/健康检查/配置、数据库版本/迁移/备份恢复、RabbitMQ 持久化/消费启停、调度单实例/重启续扫和门禁命令/覆盖率口径。另在调度岗 #6 问取运行契约，尚未确认。

尚未采购云资源、安装、构建、部署、迁移、备份恢复演练或压测。应用 8核16GB/80GB SSD、压测 4核8GB/40GB SSD 仅为已有建议，不保证 400 并发、10 分钟、P95 或吞吐达标。本次仅本岗资料 commit；不 push、不部署、不合并、不设置审核成功，不联系独立测试岗。
