Agent-Role: deployment
Prompt-Ref: ROLE-deployment-RUNTIME-v1

开始在独立 worktree / `codex/deployment-runtime` 实现部署与真实 CI，当前应用代码尚未交付。

运行配置按后端确认：`t44.api:app` 同步 FastAPI、4 workers；`python -m t44.messaging` 与 `python -m t44.scheduling` 独立进程；`DATABASE_URL=mysql+pymysql://...`、`AMQP_URL`、`T44_SESSION_TTL_SECONDS=3600`。认证为不透明会话，不生成 JWT 密钥。没有新增未鉴权 HTTP 健康路由，健康检查采用容器本地 TCP/数据库直探及进程检查，不把进程存在当作扫描已完成。

迁移目标统一为未来 `python -m t44.cli migrate --database <name>`；数据库岗说明当前仅 DDL 设计、尚无可执行迁移。部署只提供包装，不宣称入口存在。账号初始化及撤销同由后端 CLI 提供。

需要后端 #3 交付带哈希的 `backend/requirements.lock`、`backend/pyproject.toml`、`backend/t44/`、`backend/tests/` 及 `contract/integration/fault` markers；数据库 #4 确认迁移接口/DDL定位和恢复核对。前端按 Node24 / pnpm11.25.0、`frontend/dist`，静态站同源代理 `/api/v1`，仍需实际 package/lock/build 交付。

Compose 为单机 MySQL8.4、RabbitMQ、API、消费者、调度、前端反代；只有 127.0.0.1:8080 默认映射，DB/MQ 无宿主端口。备份显式选库；恢复仅到新隔离 Compose 项目和新目标库，不删除现有数据。真实容器/恢复/压力尚未执行，本机无 Docker；云机没有购买。CI 名称拟 static/contracts/coverage/frontend，应用缺失、空测试、全跳过均明确失败，不造绿灯。当前主干仍只有 reviewer/stage 保护，不自行改保护或合并。
