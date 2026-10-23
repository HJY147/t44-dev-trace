单机运行、备份恢复和产品门禁此前没有配置。本PR提供Compose、固定摘要的Dockerfiles、Nginx与运维包装，以及static/contracts/coverage/frontend真实工作流；当前后端应用/锁/CLI与业务测试尚未交付，不能直接运行完整产品，PR保持草稿。

运行包含MySQL8.4、RabbitMQ、4worker API、独立消费者/调度与Vue静态反代，只有loopback8080映射宿主。API前缀不重写，支持history fallback；日志仅追踪ID/状态/耗时。大请求统一JSON413且audit_id=null，契约1MiB限制仍须后端实现，代理上限2MiB。健康为本地进程/TCP与数据库探测，无新增未鉴权HTTP接口。

ops工具生成私有随机凭据，显式选库并包装未来后端CLI；备份有清单/校验和，恢复只到新隔离项目/新库，不清空活库或卷。CLI入口尚待责任岗交付，mysqldump/恢复尚未实跑。

CI使用真实MySQL/RabbitMQ services和迁移，contract/integration/fault分别要求非空真实通过；完整生产Python与TS/Vue分别强制行覆盖率>=80%，函数/分支报告，不以语言平均或排除未测组件凑数。应用、测试、报告缺失或跳过占位均失败，原始日志/JUnit/覆盖率上传为artifact。

验证：官方Compose schema、Ruff、actionlint与diff检查通过；11项部署安全测试、6项CI守卫测试通过（临时文件/mock Docker/合成报告，属于本岗测试）。产品static/contracts/coverage本地入口因缺实现退出1。首次push的[真实Actions](https://github.com/HJY147/t44-dev-trace/actions/runs/39912067161)在实现提交3857b2e完成，四项均因缺应用/测试/前端manifest失败；Compose/Nginx语法步骤成功，没有产品测试结果。开发机无Docker，未在本机构建或启动产品，未执行迁移/备份恢复、独立验收或压测。后续自动运行须以准确提交为准。

本岗报告与交接：`reports/modules/deployment.md`、`records/handoffs/deployment.json`；原始命令/日志：`agents/deployment/runtime-validation/`；实际派工：`agents/deployment/prompts/ROLE-deployment-RUNTIME-v1.md`。不修改main保护、不合并、不发布reviewer成功，不租赁资源。公开镜像/Action版本来源已固定留痕。

Agent-Role: deployment
Prompt-Ref: ROLE-deployment-RUNTIME-v1
Refs: #7
