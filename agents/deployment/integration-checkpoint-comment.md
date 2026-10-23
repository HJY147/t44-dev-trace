Agent-Role: deployment
Prompt-Ref: ROLE-deployment-INTEGRATION-v1

已在本岗worktree合完整codex/integration并发布两个checkpoint：web构建路径修复8e8c839e6f3aeb29b51f05a5a8a22a36995e4298；tmp编号测试/FE root命令适配7e4dbda1e7afd82ce3c794dfdf025e6ca8870277。新的FE CI命令已本机真实执行成功，行覆盖率308/334=92.21%，全部src仍纳入，未排除组件；backend/全量真实服务门禁另由准确Actions结果证明。

本次继续接入已实现的service-token CLI：私密目录卷0700/文件0600，scheduler只读整个目录；credential-admin先新文件签发、原子发布，再撤销旧session。ops受控轮换先排空/停scheduler再续签并启动，Token不放.env/命令输出；共同持久flock卷防止同主机额外scanner。实际进程入口/环境均来自调度源码和本Issue6361329227，没有新增未鉴权health API。

独立docker-application job使用root预留的tmp/deployment/972_compose_application.py，必须真实build镜像、起完整Compose、项目库迁移、init-user/seed、HTTP/SPA/JSON413、4worker和独立进程、只读凭据/跨容器flock/轮换、停写一致性备份与新隔离库恢复，并核对表数/内容checksum/迁移结构。新971_credentials.py只做本岗凭据guard，不伪装产品用例；972仅main显式执行，不被static pytest自动执行。

当前只是待运行checkpoint，不宣称Docker已构建、应用集成或恢复成功。本机无Docker；托管Linux job原始日志/精确目标SHA将继续归档，失败按实际原因修复，不跳过或降低四项门禁。不租资源、不做云部署，不联系独立测试。
