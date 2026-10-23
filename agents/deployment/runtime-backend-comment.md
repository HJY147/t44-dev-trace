Agent-Role: deployment
Prompt-Ref: ROLE-deployment-RUNTIME-v1

对接部署 #7：收到后端关于 `t44.api:app`、独立 messaging/scheduling、同步 `DATABASE_URL`、`AMQP_URL` 和不透明会话的设计确认；这些入口当前尚未实现，不当作可运行证据。

部署将依赖 `backend/pyproject.toml`、可 `pip install --require-hashes -r backend/requirements.lock` 的哈希锁文件、`backend/t44/` 和 `backend/tests/`。CI 用 Python3.12、`PYTHONPATH=backend`，三类 marker `contract/integration/fault` 各自必须实际执行并有通过用例，完整套件对整个生产 `t44` 包统计覆盖率 >=80%，不排除未导入模块。请在编码时保留这些入口/marker 并确认锁文件格式。

CLI 包装拟为 `python -m t44.cli migrate --database <name>`、`init-user --username ... --display-name ... --password-stdin`、`revoke-sessions --user-id ...`、`revoke-session --session-id ...`；请确认迁移的显式选库参数、成功/失败退出码及数据库迁移版本核对入口。未确认部分会保留为阻塞项。健康为本地进程/TCP+数据库直探，不新增未鉴权业务接口。
